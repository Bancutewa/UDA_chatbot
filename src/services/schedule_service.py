"""
Schedule service - create and manage property visit appointments.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import uuid

import dateparser
from dateparser.search import search_dates
import re
import unicodedata

from ..core.config import config
from ..core.logger import logger
from ..repositories.schedule_repository import schedule_repository
from ..schemas.user import UserSession, UserRole
from ..core.exceptions import ValidationError, DatabaseConnectionError, AuthenticationError
from ..services.qdrant_service import qdrant_service
from ..utils.listing_utils import extract_district_from_listing
from qdrant_client.http import models


class ScheduleService:
    """Business logic for visit schedules."""

    WEEKDAY_PATTERN = re.compile(
        r'(thứ\s*(?:hai|ba|tư|tu|bốn|bon|năm|nam|sáu|sau|bảy|bay|[2-7])|chủ nhật|chu nhat|cn)'
        r'(?:\s*(tuần\s*(?:này|sau|tới)))?',
        flags=re.UNICODE
    )

    def __init__(self):
        self.repo = schedule_repository

    # ------------------ Helpers ------------------ #
    def _parse_datetime(self, payload: Dict, fallback_text: Optional[str] = None) -> Tuple[Optional[datetime], str]:
        """
        Attempt to extract datetime from structured payload.
        Returns tuple of (datetime, human_readable_source)
        """
        base_dt = datetime.now()

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
            parsed = self._parse_single_candidate(candidate, base_dt=base_dt)
            if parsed:
                parsed = self._apply_time_hint(parsed, str(candidate))
                return parsed, str(candidate)

            relative_dt = self._parse_relative_weekday(str(candidate), base_dt)
            if relative_dt:
                relative_dt = self._apply_time_hint(relative_dt, str(candidate))
                return relative_dt, str(candidate)

        if fallback_text:
            # Thử parse "ngày mốt", "ngày kia", "mai" trước
            relative_date = self._parse_relative_date(fallback_text, base_dt)
            if relative_date:
                relative_date = self._apply_time_hint(relative_date, fallback_text)
                return relative_date, fallback_text
            
            parsed = self._parse_single_candidate(fallback_text, base_dt=base_dt)
            if parsed:
                parsed = self._apply_time_hint(parsed, fallback_text)
                return parsed, fallback_text

            search_result = self._search_datetime_in_text(fallback_text, base_dt)
            if search_result:
                parsed_dt, phrase = search_result
                parsed_dt = self._apply_time_hint(parsed_dt, phrase)
                return parsed_dt, phrase

            relative_dt = self._parse_relative_weekday(fallback_text, base_dt)
            if relative_dt:
                relative_dt = self._apply_time_hint(relative_dt, fallback_text)
                return relative_dt, fallback_text

        return None, ""

    @staticmethod
    def _search_datetime_in_text(text: str, base_dt: datetime) -> Optional[Tuple[datetime, str]]:
        try:
            matches = search_dates(
                text,
                languages=["vi", "en"],
                settings={
                    "PREFER_DATES_FROM": "future",
                    "RELATIVE_BASE": base_dt,
                },
            )
            if matches:
                phrase, dt = matches[0]
                return dt, phrase
        except Exception as exc:
            logger.debug(f"search_dates failed for '{text}': {exc}")
        return None

    @staticmethod
    def _parse_single_candidate(value, base_dt: Optional[datetime] = None) -> Optional[datetime]:
        if base_dt is None:
            base_dt = datetime.now()
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
                    "RELATIVE_BASE": base_dt,
                },
            )
            if parsed:
                return parsed
        return None

    @staticmethod
    def _extract_time_from_text(text: Optional[str]) -> Optional[Tuple[int, int, Optional[str]]]:
        if not text:
            return None
        lowered = text.lower()
        
        # Pattern cho "rưỡi" trước (ưu tiên cao hơn)
        pattern_ruoi = re.compile(
            r'(\d{1,2})\s*(?:giờ|g|h)?\s*(rưỡi|ruoi)',
            flags=re.UNICODE
        )
        for match in pattern_ruoi.finditer(lowered):
            hour = int(match.group(1))
            if hour > 23:
                continue
            return hour, 30, None
        
        # Pattern cho giờ đầy đủ: "7 giờ sáng", "5 giờ 30 chiều", "17h30"
        pattern_full = re.compile(
            r'(\d{1,2})\s*(?:[:h]|giờ|g)\s*(\d{1,2})?\s*(?:phút)?\s*(sáng|chiều|tối|trưa|am|pm)?',
            flags=re.UNICODE
        )
        for match in pattern_full.finditer(lowered):
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            suffix = match.group(3)
            if hour > 23 or minute > 59:
                continue
            # Nếu có suffix (sáng/chiều/tối/trưa/am/pm) thì luôn trả về
            if suffix:
                return hour, minute, suffix
            # Nếu không có suffix nhưng hour >= 12, có thể là 24h format
            if hour >= 12:
                return hour, minute, None
            # Nếu hour < 12 và không có suffix, cần kiểm tra context
            # Nhưng để đơn giản, nếu không có suffix và hour < 12 thì skip
            # (sẽ được xử lý bởi logic khác)
        return None

    @staticmethod
    def _normalize_text(text: Optional[str]) -> str:
        if not text:
            return ""
        normalized = unicodedata.normalize("NFKD", text)
        return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()

    @classmethod
    def _weekday_to_int(cls, token: str) -> Optional[int]:
        normalized = cls._normalize_text(token)
        normalized = " ".join(normalized.split())
        if normalized in ("chu nhat", "chunhat", "cn"):
            return 6
        if normalized.startswith("thu"):
            remainder = normalized.replace("thu", "", 1).strip()
            mapping = {
                "hai": 0, "2": 0,
                "ba": 1, "3": 1,
                "tu": 2, "bon": 2, "4": 2,
                "nam": 3, "5": 3,
                "sau": 4, "6": 4,
                "bay": 5, "7": 5,
            }
            return mapping.get(remainder)
        return None

    @staticmethod
    def _parse_relative_date(text: Optional[str], base_dt: datetime) -> Optional[datetime]:
        """Parse relative dates like 'mai', 'ngày mốt', 'ngày kia'"""
        if not text:
            return None
        normalized = ScheduleService._normalize_text(text)
        days_offset = None
        
        # Sử dụng regex để match chính xác hơn, tránh match nhầm
        if re.search(r'\b(ngay\s+)?mai\b', normalized):
            days_offset = 1
        elif re.search(r'\bngay\s+mot\b', normalized) or re.search(r'\bmot\b', normalized):
            days_offset = 2
        elif re.search(r'\b(ngay\s+)?kia\b', normalized):
            days_offset = 2
        
        if days_offset is not None:
            target_date = (base_dt + timedelta(days=days_offset)).date()
            return datetime.combine(target_date, datetime.min.time())
        return None

    @classmethod
    def _parse_relative_weekday(cls, text: Optional[str], base_dt: datetime) -> Optional[datetime]:
        if not text:
            return None
        for match in cls.WEEKDAY_PATTERN.finditer(text.lower()):
            weekday_token = match.group(1)
            modifier = match.group(2) or ""
            weekday = cls._weekday_to_int(weekday_token)
            if weekday is None:
                continue
            days_ahead = (weekday - base_dt.weekday()) % 7
            modifier_norm = cls._normalize_text(modifier)
            if "sau" in modifier_norm or "toi" in modifier_norm:
                days_ahead = days_ahead + 7 if days_ahead else 7
            elif "nay" in modifier_norm:
                if days_ahead < 0:
                    days_ahead += 7
            else:
                if days_ahead == 0:
                    days_ahead = 7
            target_date = (base_dt + timedelta(days=days_ahead)).date()
            return datetime.combine(target_date, datetime.min.time())
        return None

    @classmethod
    def _apply_time_hint(cls, dt: datetime, text: Optional[str]) -> datetime:
        if not text:
            return dt

        normalized_full = cls._normalize_text(text)

        hint = cls._extract_time_from_text(text)
        if hint:
            hour, minute, suffix = hint
            suffix_norm = cls._normalize_text(suffix) if suffix else ""
            
            # Xử lý suffix trực tiếp từ regex match
            if suffix_norm:
                if suffix_norm in ("chieu", "toi", "pm") and hour < 12:
                    hour += 12
                elif suffix_norm in ("sang", "am"):
                    if hour == 12:
                        hour = 0
                    # Giữ nguyên hour nếu < 12 (đã đúng)
                elif suffix_norm == "trua":
                    hour = 12 if hour == 0 else hour
            else:
                # Không có suffix trong match, kiểm tra toàn bộ text
                if "chieu" in normalized_full or "toi" in normalized_full or "pm" in normalized_full:
                    if hour < 12:
                        hour += 12
                elif "sang" in normalized_full or "am" in normalized_full:
                    if hour >= 12:
                        hour -= 12
                elif "trua" in normalized_full:
                    hour = 12 if hour == 0 else hour
            
            return dt.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Fallback: không tìm thấy giờ cụ thể, chỉ điều chỉnh dựa trên text
        if ("chieu" in normalized_full or "toi" in normalized_full or "pm" in normalized_full) and dt.hour < 12:
            return dt + timedelta(hours=12)
        if ("sang" in normalized_full or "am" in normalized_full) and dt.hour >= 12:
            return dt - timedelta(hours=12)
        if "trua" in normalized_full and dt.hour < 12:
            return dt.replace(hour=12, minute=0, second=0, microsecond=0)
        return dt

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
            # Ensure all datetime fields are serialized to strings
            serializable_events = []
            for event in events:
                serializable_event = {}
                for key, value in event.items():
                    if isinstance(value, datetime):
                        serializable_event[key] = value.isoformat()
                    else:
                        serializable_event[key] = value
                serializable_events.append(serializable_event)
            
            with open(config.ADMIN_CALENDAR_FILE, "w", encoding="utf-8") as fh:
                json.dump(serializable_events, fh, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.warning(f"Không thể đồng bộ calendar admin: {exc}", exc_info=True)

    @staticmethod
    def _extract_user_messages_from_context(context: str) -> str:
        """Extract only user messages from formatted context (User: ... Assistant: ...)"""
        if not context:
            return ""
        
        user_messages = []
        for line in context.split('\n'):
            line = line.strip()
            if line.startswith('User:') or line.startswith('user:'):
                # Extract message after "User:"
                msg = line.split(':', 1)[1].strip() if ':' in line else line
                if msg:
                    user_messages.append(msg)
        
        # Nếu không có format "User:", trả về toàn bộ context
        return ' '.join(user_messages) if user_messages else context

    @staticmethod
    def _extract_district_from_text(text: str) -> Optional[str]:
        """Extract district from text like 'quận 7', 'quận 1', etc."""
        if not text:
            return None
        
        normalized = ScheduleService._normalize_text(text)
        # Pattern để tìm "quận X", "quan X", "q.X", etc.
        pattern = re.compile(r'quan\s*(\d+)', flags=re.UNICODE)
        match = pattern.search(normalized)
        if match:
            return f"Quận {match.group(1)}"
        return None
    
    @staticmethod
    def _get_district_from_listing(listing_id: str) -> Optional[str]:
        """Get district from listing data in Qdrant by listing_id."""
        if not listing_id:
            return None
        
        try:
            must_filters = [
                models.FieldCondition(
                    key="ma_can",
                    match=models.MatchValue(value=listing_id)
                )
            ]
            
            results = qdrant_service.client.scroll(
                collection_name=qdrant_service.collection_name,
                scroll_filter=models.Filter(must=must_filters),
                limit=1
            )
            
            points, _ = results
            if points and points[0].payload:
                listing_details = points[0].payload
                # Use centralized utility to extract district
                district = extract_district_from_listing(listing_details)
                return district
        except Exception as e:
            logger.warning(f"Error fetching district from listing_id '{listing_id}': {e}")
        
        return None

    def _validate_booking_info(self, payload: Dict, raw_message: str, context: Optional[str] = None) -> Tuple[Optional[datetime], Optional[str], Optional[str], List[str]]:
        """
        Validate booking information and return missing fields.
        Combines information from current message and conversation context.
        Returns: (visit_datetime, district, source_time, missing_fields)
        """
        missing_fields = []
        
        # Ưu tiên parse từ tin nhắn hiện tại trước
        visit_datetime, source_time = self._parse_datetime(payload, fallback_text=raw_message)
        
        # Nếu không có trong tin nhắn hiện tại, thử từ context (chỉ user messages)
        if not visit_datetime and context:
            user_context = self._extract_user_messages_from_context(context)
            if user_context:
                context_dt, context_source = self._parse_datetime({}, fallback_text=user_context)
                if context_dt:
                    visit_datetime = context_dt
                    source_time = context_source or source_time
        
        if not visit_datetime:
            missing_fields.append("thời gian")
        
        # Ưu tiên extract district từ tin nhắn hiện tại trước
        district = payload.get("district") or payload.get("location")
        if not district:
            district = self._extract_district_from_text(raw_message)
        
        # Nếu không có trong tin nhắn hiện tại, thử từ context (chỉ user messages)
        if not district and context:
            user_context = self._extract_user_messages_from_context(context)
            if user_context:
                district = self._extract_district_from_text(user_context)
        
        # Nếu vẫn chưa có district nhưng có listing_id, tự động lấy từ listing data
        if not district and payload.get("listing_id"):
            listing_id = payload.get("listing_id")
            try:
                district = self._get_district_from_listing(listing_id)
                if district:
                    logger.info(f"Auto-extracted district '{district}' from listing_id '{listing_id}'")
            except Exception as e:
                logger.warning(f"Could not extract district from listing_id '{listing_id}': {e}")
        
        # Chỉ yêu cầu district nếu không có listing_id hoặc không thể lấy được từ listing
        if not district and not payload.get("listing_id"):
            missing_fields.append("khu vực")
        
        return visit_datetime, district, source_time, missing_fields

    # ------------------ Public API ------------------ #
    def create_booking(
        self,
        *,
        user_session: Optional[UserSession],
        payload: Dict,
        raw_message: str,
        session_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> Dict:
        # Try to get real user_id from chat session if available AND user_session is still guest
        # If user_session already has a real user_id (from booking_tools), don't override it
        if session_id and user_session and user_session.user_id.startswith("guest_"):
            try:
                from ..services.chat_service import chat_service
                chat_session = chat_service.get_session(session_id)
                logger.debug(f"Chat session for booking: session_id={session_id}, user_id={chat_session.get('user_id') if chat_session else None}")
                if chat_session and chat_session.get("user_id"):
                    real_user_id = chat_session.get("user_id")
                    # If we found a real user_id (not guest), create proper user_session
                    if real_user_id and not real_user_id.startswith("guest_"):
                        from ..repositories.user_repository import UserRepository
                        user_repo = UserRepository()
                        user = user_repo.get_user_by_id(real_user_id)
                        if user:
                            # Create proper user_session with real user data
                            from ..schemas.user import UserRole, UserStatus
                            user_session = UserSession(
                                user_id=user.id,
                                username=user.full_name or user.username,
                                role=user.role,
                                status=user.status
                            )
                            logger.info(f"Using real user session for booking (from chat session): user_id={user.id}, email={user.email}")
                        else:
                            logger.warning(f"Chat session has user_id={real_user_id} but user not found in database")
                    else:
                        logger.debug(f"Chat session user_id is guest or invalid: {real_user_id}")
                else:
                    logger.debug(f"Chat session has no user_id: session_id={session_id}")
            except Exception as e:
                logger.warning(f"Could not get user_id from chat session: {e}", exc_info=True)
        elif user_session and not user_session.user_id.startswith("guest_"):
            logger.info(f"User session already has real user_id: {user_session.user_id}, skipping chat session lookup")
        visit_datetime, district, source_time, missing_fields = self._validate_booking_info(payload, raw_message, context)
        
        # Nếu thiếu thông tin, raise ValidationError với message hỏi lại
        if missing_fields:
            if len(missing_fields) == 1:
                field = missing_fields[0]
                if field == "thời gian":
                    raise ValidationError(
                        "Xin vui lòng cho tôi biết rõ thời gian muốn xem nhà (ví dụ: '10h sáng thứ 7 tuần này', '7 giờ sáng ngày mai')."
                    )
                elif field == "khu vực":
                    raise ValidationError(
                        "Xin vui lòng cho tôi biết khu vực muốn xem nhà (ví dụ: 'quận 7', 'quận 1')."
                    )
            else:
                # Thiếu nhiều thông tin
                fields_str = " và ".join(missing_fields)
                raise ValidationError(
                    f"Để đặt lịch xem nhà, tôi cần biết {fields_str}. "
                    f"Bạn có thể cung cấp đầy đủ thông tin không? "
                    f"(Ví dụ: 'đặt lịch xem nhà quận 7 lúc 10h sáng thứ 7 tuần này')"
                )

        user_info = self._default_user(user_session)
        # Use username from user_session (which is set to customer_name in booking tool)
        user_name = user_info["user_name"]
        final_user_id = user_info["user_id"]
        
        # Log final user_id to debug
        logger.info(f"Final user_id for booking: {final_user_id}, is_guest={final_user_id and final_user_id.startswith('guest_') if final_user_id else True}")
        
        # Get email: from payload (guest) or from user record (logged in user)
        user_email = payload.get("user_email")
        if not user_email and user_session and not user_session.user_id.startswith("guest_"):
            # User is logged in, get email from user record
            try:
                from ..repositories.user_repository import UserRepository
                user_repo = UserRepository()
                user = user_repo.get_user_by_id(user_session.user_id)
                if user:
                    user_email = user.email
                    logger.info(f"Retrieved email from user record: {user_email}")
            except Exception as e:
                logger.warning(f"Could not get email from user record: {e}")
        
        # Get phone from payload (stored separately, not in notes)
        user_phone = payload.get("phone", "")
        
        base_event = {
            "id": str(uuid.uuid4()),
            "user_id": final_user_id,
            "user_name": user_name,
            "user_email": user_email,  # Email from user record (if logged in) or from payload (if guest)
            "user_phone": user_phone,  # Phone stored separately for easy access
            "district": district,
            "property_type": payload.get("property_type") or "bất động sản",
            "listing_id": payload.get("listing_id"),  # Add listing_id if provided
            "notes": payload.get("notes") or payload.get("requirements") or "",  # Notes only for customer notes/requirements
            "status": "pending",
            "requested_time": visit_datetime.isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "source_time_text": source_time,
            "raw_message": raw_message,
            "session_id": session_id,
        }

        try:
            logger.info(f"Creating schedule event: user_id={base_event.get('user_id')}, listing_id={base_event.get('listing_id')}, district={base_event.get('district')}")
            event = self.repo.create(base_event)
            
            # Verify event was created successfully
            if not event:
                logger.error("Repository returned None/empty event")
                raise DatabaseConnectionError("Không thể tạo lịch hẹn. Repository trả về kết quả rỗng.")
            
            if not event.get("id"):
                logger.error(f"Repository returned event without id: {event}")
                raise DatabaseConnectionError("Không thể tạo lịch hẹn. Event không có ID.")
            
            # Verify event was actually saved by trying to retrieve it
            retrieved_event = self.repo.get(event["id"])
            if not retrieved_event:
                logger.error(f"Event {event['id']} was created but cannot be retrieved from database")
                raise DatabaseConnectionError("Lịch hẹn đã được tạo nhưng không thể truy vấn lại. Vui lòng kiểm tra database.")
            
            self._sync_admin_calendar()
            logger.info(f"Tạo lịch xem nhà thành công: event_id={event['id']}, user_id={event.get('user_id')}, listing_id={event.get('listing_id')}")
            return event
        except DatabaseConnectionError:
            raise
        except Exception as exc:
            logger.error(f"Create schedule failed: {exc}", exc_info=True)
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

        district = event.get("district", "Không xác định")
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
        events = self.repo.list()
        logger.info(f"Loaded {len(events)} events from database for list_all()")
        if events:
            logger.debug(f"Sample event IDs: {[e.get('id') for e in events[:3]]}")
        return events

    def get(self, schedule_id: str) -> Optional[Dict]:
        return self.repo.get(schedule_id)

    def update_status(self, schedule_id: str, status: str, admin_note: Optional[str] = None) -> Optional[Dict]:
        updated = self.repo.update_status(schedule_id, status, admin_note)
        if updated:
            self._sync_admin_calendar()
        return updated

    def delete(self, schedule_id: str, current_user: Optional[UserSession] = None) -> bool:
        """Delete schedule (Admin only)"""
        # Permission check: Only Admin can delete schedules
        if current_user and current_user.role != UserRole.ADMIN:
            raise AuthenticationError("Chỉ quản trị viên mới có quyền xóa lịch hẹn")
        
        result = self.repo.delete(schedule_id)
        if result:
            self._sync_admin_calendar()
        return result


schedule_service = ScheduleService()

