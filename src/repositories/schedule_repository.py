"""
Repository for property visit schedules (MongoDB with JSON fallback)
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

try:
    from pymongo import ReturnDocument  # type: ignore
except ImportError:  # pragma: no cover
    ReturnDocument = None

from ..core.config import config
from ..core.logger import logger
from ..core.exceptions import DatabaseConnectionError


class ScheduleRepository:
    """Persist and fetch visit schedules."""

    def __init__(self):
        self.file_path = config.VISIT_SCHEDULES_FILE
        self.use_mongodb = False
        self.collection = None

        if config.USE_MONGODB:
            try:
                client = config.mongodb_client
                self.collection = client[config.DATABASE_NAME]["visit_schedules"]
                self.collection.create_index([("requested_time", 1)])
                self.collection.create_index([("user_id", 1)])
                self.use_mongodb = True
                logger.info("Using MongoDB for visit schedules storage")
            except Exception as exc:
                logger.warning(f"MongoDB unavailable for schedules, fallback to JSON. Reason: {exc}")
                self.collection = None
                self.use_mongodb = False

    # ---------------- JSON helpers ---------------- #
    def _load_events(self) -> Dict[str, Dict]:
        if not os.path.exists(self.file_path):
            return {}
        try:
            with open(self.file_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as exc:
            logger.warning(f"Failed to load schedules JSON: {exc}")
            return {}

    def _save_events(self, events: Dict[str, Dict]):
        try:
            with open(self.file_path, "w", encoding="utf-8") as fh:
                json.dump(events, fh, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.error(f"Unable to persist schedules JSON: {exc}")
            raise DatabaseConnectionError(f"Save schedules failed: {exc}")

    # ---------------- Mongo helpers ---------------- #
    @staticmethod
    def _ensure_datetime(value) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            cleaned = value.replace("Z", "+00:00") if value.endswith("Z") else value
            try:
                return datetime.fromisoformat(cleaned)
            except ValueError:
                pass
        return datetime.utcnow()

    @staticmethod
    def _format_event(event: Dict) -> Dict:
        if not event:
            return {}
        formatted = dict(event)
        if "_id" in formatted:
            formatted["id"] = str(formatted.pop("_id"))
        
        # Convert all datetime fields to ISO format strings
        datetime_fields = ["requested_time", "created_at", "updated_at", "assigned_at", "sale_response_at"]
        for field in datetime_fields:
            if field in formatted and isinstance(formatted[field], datetime):
                formatted[field] = formatted[field].isoformat()
        
        return formatted

    # ---------------- CRUD operations ---------------- #
    def create(self, event: Dict) -> Dict:
        event_id = event.get("id") or str(uuid.uuid4())
        event = {**event, "id": event_id}

        if self.use_mongodb and self.collection is not None:
            mongo_event = dict(event)
            mongo_event["_id"] = mongo_event.pop("id")
            mongo_event["requested_time"] = self._ensure_datetime(mongo_event.get("requested_time"))
            mongo_event["created_at"] = self._ensure_datetime(mongo_event.get("created_at"))
            mongo_event["updated_at"] = self._ensure_datetime(mongo_event.get("updated_at"))
            try:
                self.collection.insert_one(mongo_event)
                return self._format_event(mongo_event)
            except Exception as exc:
                logger.error(f"MongoDB insert schedule failed: {exc}")
                raise DatabaseConnectionError(f"Create schedule failed: {exc}")

        # JSON fallback
        events = self._load_events()
        events[event_id] = event
        self._save_events(events)
        return event

    def list(self, user_id: Optional[str] = None) -> List[Dict]:
        if self.use_mongodb and self.collection is not None:
            query = {"user_id": user_id} if user_id else {}
            try:
                logger.debug(f"MongoDB list query: {query}")
                cursor = self.collection.find(query).sort("requested_time", 1)
                events = [self._format_event(doc) for doc in cursor]
                logger.info(f"MongoDB list returned {len(events)} events (user_id={user_id})")
                if events:
                    logger.debug(f"Sample event IDs from MongoDB: {[e.get('id') for e in events[:3]]}")
                return events
            except Exception as exc:
                logger.error(f"MongoDB fetch schedules failed: {exc}", exc_info=True)
                return []

        events = self._load_events()
        values = list(events.values())
        if user_id:
            values = [evt for evt in values if evt.get("user_id") == user_id]
        values.sort(key=lambda item: item.get("requested_time", ""))
        return values

    def get(self, schedule_id: str) -> Optional[Dict]:
        if self.use_mongodb and self.collection is not None:
            try:
                doc = self.collection.find_one({"_id": schedule_id})
                return self._format_event(doc)
            except Exception as exc:
                logger.error(f"MongoDB get schedule failed: {exc}")
                return None

        events = self._load_events()
        return events.get(schedule_id)

    def update_status(self, schedule_id: str, status: str, admin_note: Optional[str] = None) -> Optional[Dict]:
        if self.use_mongodb and self.collection is not None:
            try:
                update_fields = {
                    "status": status,
                    "updated_at": datetime.utcnow(),
                }
                if admin_note is not None:
                    update_fields["admin_note"] = admin_note

                return_document = ReturnDocument.AFTER if ReturnDocument else True
                result = self.collection.find_one_and_update(
                    {"_id": schedule_id},
                    {"$set": update_fields},
                    return_document=return_document,
                )
                return self._format_event(result)
            except Exception as exc:
                logger.error(f"MongoDB update schedule failed: {exc}")
                raise DatabaseConnectionError(f"Update schedule failed: {exc}")

        events = self._load_events()
        if schedule_id not in events:
            return None
        events[schedule_id]["status"] = status
        events[schedule_id]["updated_at"] = datetime.utcnow().isoformat()
        if admin_note is not None:
            events[schedule_id]["admin_note"] = admin_note
        self._save_events(events)
        return events[schedule_id]

    def update_assignment(self, schedule_id: str, assignment_data: Dict) -> Optional[Dict]:
        """Update assignment-related fields"""
        if self.use_mongodb and self.collection is not None:
            try:
                update_fields = {
                    **assignment_data,
                    "updated_at": datetime.utcnow(),
                }
                
                return_document = ReturnDocument.AFTER if ReturnDocument else True
                result = self.collection.find_one_and_update(
                    {"_id": schedule_id},
                    {"$set": update_fields},
                    return_document=return_document,
                )
                return self._format_event(result)
            except Exception as exc:
                logger.error(f"MongoDB update assignment failed: {exc}")
                raise DatabaseConnectionError(f"Update assignment failed: {exc}")

        events = self._load_events()
        if schedule_id not in events:
            return None
        events[schedule_id].update(assignment_data)
        events[schedule_id]["updated_at"] = datetime.utcnow().isoformat()
        self._save_events(events)
        return events[schedule_id]

    def delete(self, schedule_id: str) -> bool:
        if self.use_mongodb and self.collection is not None:
            try:
                result = self.collection.delete_one({"_id": schedule_id})
                return result.deleted_count > 0
            except Exception as exc:
                logger.error(f"MongoDB delete schedule failed: {exc}")
                raise DatabaseConnectionError(f"Delete schedule failed: {exc}")

        events = self._load_events()
        if schedule_id in events:
            del events[schedule_id]
            self._save_events(events)
            return True
        return False


schedule_repository = ScheduleRepository()

