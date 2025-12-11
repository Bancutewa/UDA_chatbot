from typing import Optional, Dict
from langchain.tools import tool

from ..services.schedule_service import schedule_service
from ..schemas.user import UserSession
from ..core.logger import logger
import json

@tool
def book_appointment(
    listing_id: str,
    time: str,
    phone: str,
    customer_name: Optional[str] = None
) -> Dict:
    """
    Đặt lịch xem bất động sản cho khách hàng.

    Các tham số:
    - listing_id: Mã căn muốn xem.
    - time: Thời gian hẹn (chuẩn ISO hoặc mô tả tự nhiên như '9h sáng mai').
    - phone: Số điện thoại của khách hàng.
    - customer_name: Tên khách hàng (không bắt buộc).

    Return:
    - dict xác nhận lịch hẹn (thời gian, mã căn, nhân viên phụ trách...).
    """
    logger.info(f"Tool book_appointment called: {listing_id} at {time}")
    
    try:
        # Mock UserSession for internal service compatibility if needed
        # Or modify schedule_service to accept raw data. 
        # schedule_service.create_booking expects user_session object usually.
        # Check schedule_service signature:
        # create_booking(*, user_session: Optional[UserSession], payload: Dict, raw_message: str, ...)
        
        # We construct a mock payload
        payload = {
            "time_text": time,
            "district": "", # Will be inferred or skipped
            "notes": f"Phone: {phone}, Name: {customer_name}"
        }
        
        # We need a system user or guest session
        guest_session = UserSession(
            user_id="guest_agent_user",
            username=customer_name or "Guest",
            full_name=customer_name or "Guest Customer",
            role="user"
        )
        
        event = schedule_service.create_booking(
            user_session=guest_session,
            payload=payload,
            raw_message=f"Đặt lịch xem căn {listing_id} vào {time}",
            session_id="agent_tool_call"
        )
        
        return {
            "status": "success",
            "message": "Đã đặt lịch thành công!",
            "appointment": {
                "id": event["id"],
                "time": event["requested_time"],
                "location": event.get("district"),
                "listing_id": listing_id
            }
        }
        
    except Exception as e:
        logger.error(f"Booking tool failed: {e}")
        return {"status": "error", "message": str(e)}
