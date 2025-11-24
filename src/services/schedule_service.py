"""
Schedule service - create and manage property visit appointments.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import uuid

import dateparser
from dateparser.search import search_dates

from ..core.config import config
from ..core.logger import logger
from ..repositories.schedule_repository import schedule_repository
from ..schemas.user import UserSession
from ..core.exceptions import ValidationError, DatabaseConnectionError


class ScheduleService:
    """Business logic for visit schedules."""

    def __init__(self):
        self.repo = schedule_repository

    # ------------------ Helpers ------------------ #
    def _parse_datetime(self, payload: Dict, fallback_text: Optional[str] = None) -> Tuple[Optional[datetime], str]:
        """
        Attempt to extract datetime from structured payload.
        Returns tuple of (datetime, human_readable_source)
        """
        candidates = [
            payload.get("iso_datetime"),
            payload.get("datetime"),
            payload.get("scheduled_for"),
        ]

        time_text_keys = ["preferred_time", "time_text", "visit_time", "when", "time"]
        for key in time_text_keys:
            if payload.get(key):
                candidates.append(payload[key])

        for candidate in candidates:
            if not candidate:
                continue
            parsed = self._parse_single_candidate(candidate)
            if parsed:
                return parsed, str(candidate)

        if fallback_text:
            parsed = self._parse_single_candidate(fallback_text)
            if parsed:
                return parsed, fallback_text

            search_result = self._search_datetime_in_text(fallback_text)
            if search_result:
                return search_result

        return None, ""

    @staticmethod
    def _search_datetime_in_text(text: str) -> Optional[Tuple[datetime, str]]:
        try:
            matches = search_dates(
                text,
                languages=["vi", "en"],
                settings={
                    "PREFER_DATES_FROM": "future",
                    "RELATIVE_BASE": datetime.now(),
                },
            )
            if matches:
                phrase, dt = matches[0]
                return dt, phrase
        except Exception as exc:
            logger.debug(f"search_dates failed for '{text}': {exc}")
        return None

    @staticmethod
    def _parse_single_candidate(value) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                cleaned = value.replace("Z", "+00:00") if value.endswith("Z") else value
                return datetime.fromisoformat(cleaned)
            except ValueError:
                pass

            parsed = dateparser.parse(
                value,
                languages=["vi", "en"],
                settings={
                    "PREFER_DATES_FROM": "future",
                    "RELATIVE_BASE": datetime.now(),
                },
            )
            if parsed:
                return parsed
        return None

    @staticmethod
    def _default_user(user_session: Optional[UserSession]) -> Dict:
        if user_session:
            return {
                "user_id": user_session.user_id,
                "user_name": user_session.username,
            }
        return {"user_id": None, "user_name": "Khách chưa đăng nhập"}

    def _sync_admin_calendar(self):
        try:
            events = self.repo.list()
            with open(config.ADMIN_CALENDAR_FILE, "w", encoding="utf-8") as fh:
                json.dump(events, fh, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.warning(f"Không thể đồng bộ calendar admin: {exc}")

    # ------------------ Public API ------------------ #
    def create_booking(
        self,
        *,
        user_session: Optional[UserSession],
        payload: Dict,
        raw_message: str,
        session_id: Optional[str] = None,
    ) -> Dict:
        visit_datetime, source_time = self._parse_datetime(payload, fallback_text=raw_message)
        if not visit_datetime:
            raise ValidationError(
                "Xin vui lòng cho tôi biết rõ thời gian muốn xem nhà (ví dụ: '10h sáng thứ 7 tuần này')."
            )

        user_info = self._default_user(user_session)
        base_event = {
            "id": str(uuid.uuid4()),
            "user_id": user_info["user_id"],
            "user_name": user_info["user_name"],
            "district": payload.get("district") or payload.get("location") or "Quận 7",
            "property_type": payload.get("property_type") or "bất động sản",
            "notes": payload.get("notes") or payload.get("requirements") or "",
            "status": "pending",
            "requested_time": visit_datetime.isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "source_time_text": source_time,
            "raw_message": raw_message,
            "session_id": session_id,
        }

        try:
            event = self.repo.create(base_event)
            self._sync_admin_calendar()
            logger.info(f"Tạo lịch xem nhà thành công: {event['id']}")
            return event
        except DatabaseConnectionError:
            raise
        except Exception as exc:
            logger.error(f"Create schedule failed: {exc}")
            raise DatabaseConnectionError("Không thể lưu lịch hẹn, vui lòng thử lại sau.")

    def format_confirmation(self, event: Dict) -> str:
        visit_time = event.get("requested_time")
        try:
            if visit_time:
                visit_dt = datetime.fromisoformat(visit_time.replace("Z", "+00:00"))
                visit_display = visit_dt.strftime("%H:%M, %d/%m/%Y")
            else:
                visit_display = "chưa xác định"
        except Exception:
            visit_display = visit_time

        district = event.get("district", "Quận 7")
        property_type = event.get("property_type", "bất động sản")

        lines = [
            "✅ Đã đặt lịch xem nhà thành công!",
            f"- Bất động sản: {property_type}",
            f"- Khu vực: {district}",
            f"- Thời gian: {visit_display}",
            "Bạn sẽ nhận được xác nhận từ đội ngũ tư vấn trong thời gian sớm nhất.",
        ]
        return "\n".join(lines)

    def list_for_user(self, user_id: str) -> List[Dict]:
        return self.repo.list(user_id=user_id)

    def list_all(self) -> List[Dict]:
        return self.repo.list()

    def get(self, schedule_id: str) -> Optional[Dict]:
        return self.repo.get(schedule_id)

    def update_status(self, schedule_id: str, status: str, admin_note: Optional[str] = None) -> Optional[Dict]:
        updated = self.repo.update_status(schedule_id, status, admin_note)
        if updated:
            self._sync_admin_calendar()
        return updated

    def delete(self, schedule_id: str) -> bool:
        result = self.repo.delete(schedule_id)
        if result:
            self._sync_admin_calendar()
        return result


schedule_service = ScheduleService()

