from typing import Optional, Dict
from langchain.tools import tool
from qdrant_client.http import models
from datetime import datetime

from ..services.schedule_service import schedule_service
from ..services.qdrant_service import qdrant_service
from ..schemas.user import UserSession, UserRole, UserStatus
from ..utils.listing_utils import extract_district_from_listing
from ..core.logger import logger
from ..core.exceptions import ValidationError, DatabaseConnectionError
import json

# Module-level variable to store current thread_id (set by agent)
_current_thread_id = None

@tool
def book_appointment(
    listing_id: str,
    time: str,
    phone: str,
    customer_name: Optional[str] = None,
    email: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict:
    """
    Đặt lịch xem bất động sản cho khách hàng.

    Các tham số:
    - listing_id: Mã căn muốn xem.
    - time: Thời gian hẹn (chuẩn ISO hoặc mô tả tự nhiên như '9h sáng mai').
    - phone: Số điện thoại của khách hàng.
    - customer_name: Tên khách hàng (không bắt buộc).
    - email: Email của khách hàng (chỉ cần cho guest, user đã đăng nhập sẽ tự động lấy từ tài khoản).
    - session_id: ID của chat session/thread_id (QUAN TRỌNG: Nếu user đã đăng nhập, phải truyền thread_id vào đây để hệ thống lấy đúng user_id).

    Return:
    - dict xác nhận lịch hẹn (thời gian, mã căn, nhân viên phụ trách...).
    """
    logger.info(f"Tool book_appointment called: listing_id={listing_id}, time={time}, session_id={session_id}")
    
    try:
        # Try to get listing details to extract district
        district = None
        property_type = "bất động sản"
        
        try:
            # Query Qdrant directly to get listing details
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
                property_type = listing_details.get("loai_can") or listing_details.get("property_type") or "bất động sản"
                logger.info(f"Extracted district '{district}' and property_type '{property_type}' from listing {listing_id}")
        except Exception as e:
            logger.warning(f"Could not fetch listing details for {listing_id}: {e}")
        
        # Construct payload with extracted information
        payload = {
            "time_text": time,
            "district": district or "",  # Will be extracted from raw_message if empty
            "property_type": property_type,
            "listing_id": listing_id,  # Add listing_id to payload
            "user_email": email,  # Store email for sending confirmation later
            "notes": f"Phone: {phone}, Name: {customer_name}, Listing: {listing_id}" + (f", Email: {email}" if email else "")
        }
        
        # Build comprehensive raw_message with all available info
        raw_message = f"Đặt lịch xem căn {listing_id}"
        if customer_name:
            raw_message += f" cho {customer_name}"
        raw_message += f" vào {time}"
        if district:
            raw_message += f" tại {district}"
        if phone:
            raw_message += f" (SĐT: {phone})"
        
        # Use provided session_id, or get from module-level variable (set by agent), or generate one
        # Priority: 1) parameter session_id, 2) module-level _current_thread_id, 3) generate new
        global _current_thread_id
        booking_session_id = session_id or _current_thread_id or f"booking_{listing_id}_{int(datetime.now().timestamp())}"
        
        if not session_id and _current_thread_id:
            logger.info(f"Using thread_id from agent context: {_current_thread_id}")
        
        # Try to get real user_id from chat session FIRST, before creating guest session
        # This ensures logged-in users get their real user_id saved in the schedule
        real_user_id = None
        if booking_session_id:
            try:
                from ..services.chat_service import chat_service
                chat_session = chat_service.get_session(booking_session_id)
                if chat_session and chat_session.get("user_id"):
                    potential_user_id = chat_session.get("user_id")
                    # Only use if it's a real user_id (not guest)
                    if potential_user_id and not potential_user_id.startswith("guest_"):
                        real_user_id = potential_user_id
                        logger.info(f"Found real user_id from chat session: {real_user_id}")
            except Exception as e:
                logger.debug(f"Could not get user_id from chat session: {e}")
        
        # Create user session - use real user_id if found, otherwise create guest session
        if real_user_id:
            # User is logged in, get full user info
            try:
                from ..repositories.user_repository import UserRepository
                user_repo = UserRepository()
                user = user_repo.get_user_by_id(real_user_id)
                if user:
                    user_session = UserSession(
                        user_id=user.id,
                        username=user.full_name or user.username or customer_name or "Khách hàng",
                        role=user.role,
                        status=user.status
                    )
                    logger.info(f"Using logged-in user session: user_id={user.id}, email={user.email}")
                else:
                    # User ID found but user not in DB, fallback to guest
                    logger.warning(f"User ID {real_user_id} found in chat session but user not in database, using guest session")
                    user_session = UserSession(
                        user_id=f"guest_{phone or 'unknown'}",
                        username=customer_name or "Khách hàng",
                        role=UserRole.USER,
                        status=UserStatus.ACTIVE
                    )
            except Exception as e:
                logger.warning(f"Error getting user info for {real_user_id}: {e}, using guest session")
                user_session = UserSession(
                    user_id=f"guest_{phone or 'unknown'}",
                    username=customer_name or "Khách hàng",
                    role=UserRole.USER,
                    status=UserStatus.ACTIVE
                )
        else:
            # No real user_id found, create guest session
            user_session = UserSession(
                user_id=f"guest_{phone or 'unknown'}",
                username=customer_name or "Khách hàng",
                role=UserRole.USER,
                status=UserStatus.ACTIVE
            )
            logger.info(f"Using guest session: user_id={user_session.user_id}")
        
        try:
            event = schedule_service.create_booking(
                user_session=user_session,
                payload=payload,
                raw_message=raw_message,
                session_id=booking_session_id
            )
            
            # Verify event was created successfully
            if not event or not event.get("id"):
                logger.error(f"Schedule service returned invalid event: {event}")
                return {
                    "status": "error",
                    "message": "Không thể tạo lịch hẹn. Vui lòng thử lại sau."
                }
            
            logger.info(f"Booking successful: event_id={event['id']}, listing_id={listing_id}")
            
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
        except ValidationError as ve:
            logger.warning(f"Booking validation failed: {ve}")
            return {"status": "error", "message": str(ve)}
        except DatabaseConnectionError as dbe:
            logger.error(f"Database error during booking: {dbe}")
            return {"status": "error", "message": str(dbe)}
        
    except Exception as e:
        logger.error(f"Booking tool failed with unexpected error: {e}", exc_info=True)
        return {"status": "error", "message": f"Lỗi hệ thống: {str(e)}"}
