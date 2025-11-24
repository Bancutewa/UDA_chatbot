"""
Intent handler for scheduling property visits.
"""
from typing import Any, Dict, Optional

from .base_intent import BaseIntent
from ..services.schedule_service import schedule_service
from ..schemas.user import UserSession
from ..core.exceptions import ValidationError, DatabaseConnectionError


class ScheduleVisitIntent(BaseIntent):
    """Handle schedule_visit intents."""

    intent_name = "schedule_visit"
    system_prompt = (
        "Bạn là trợ lý đặt lịch xem nhà. "
        "Nhiệm vụ của bạn là xác định thời gian, khu vực (quận/huyện) và loại bất động sản người dùng muốn xem."
    )

    def __init__(self, agent=None):
        super().__init__(agent)
        self.schedule_service = schedule_service

    @staticmethod
    def _build_user_session(metadata: Dict[str, Any]) -> Optional[UserSession]:
        user_data = metadata.get("user_session") if metadata else None
        if user_data:
            try:
                return UserSession(**user_data)
            except Exception:
                return None
        return None

    @staticmethod
    def _extract_payload(data: Dict[str, Any]) -> Dict[str, Any]:
        keys = [
            "district",
            "location",
            "preferred_time",
            "time_text",
            "visit_time",
            "property_type",
            "notes",
            "requirements",
            "iso_datetime",
        ]
        payload = {}
        for key in keys:
            if data.get(key):
                payload[key] = data[key]

        if "details" in data and isinstance(data["details"], dict):
            for key, value in data["details"].items():
                if key not in payload and value:
                    payload[key] = value
        return payload

    def get_response(self, data: Dict[str, Any], context: Optional[str] = None) -> str:
        metadata = data.get("metadata", {})
        user_session = self._build_user_session(metadata)
        session_id = metadata.get("session_id")
        payload = self._extract_payload(data)
        raw_message = data.get("message") or data.get("raw_text") or data.get("description", "")

        try:
            event = self.schedule_service.create_booking(
                user_session=user_session,
                payload=payload,
                raw_message=raw_message,
                session_id=session_id,
            )
            return self.schedule_service.format_confirmation(event)
        except ValidationError as exc:
            return f"⚠️ {exc}"
        except DatabaseConnectionError as exc:
            return f"❌ {exc}"
        except Exception:
            return "❌ Có lỗi khi đặt lịch. Bạn có thể nói lại thời gian và khu vực muốn xem nhà không?"

