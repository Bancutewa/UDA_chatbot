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
from ..schemas.user import UserSession
from ..core.exceptions import ValidationError, DatabaseConnectionError


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
            with open(config.ADMIN_CALENDAR_FILE, "w", encoding="utf-8") as fh:
                json.dump(events, fh, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.warning(f"Không thể đồng bộ calendar admin: {exc}")

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
        
        if not district:
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
        full_name = user_session.full_name if user_session and hasattr(user_session, "full_name") else user_info["user_name"]
        base_event = {
            "id": str(uuid.uuid4()),
            "user_id": user_info["user_id"],
            "user_name": full_name,
            "district": district,
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

