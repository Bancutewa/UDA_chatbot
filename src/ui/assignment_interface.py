"""
Assignment Interface - Handle assignment confirmation/rejection from email links
"""
import streamlit as st
from typing import Optional, Tuple

from ..services.assignment_service import assignment_service
from ..core.logger import logger
from ..core.exceptions import ValidationError, AuthenticationError
from ..schemas.user import UserRole, UserSession


class AssignmentInterface:
    """UI for assignment confirmation/rejection"""

    def _validate_token_and_user(self, token: str, check_schedule: bool = True) -> Tuple[bool, Optional[str], Optional[str], Optional[Dict]]:
        """
        Validate token, user, and optionally check if schedule still exists.
        Returns: (is_valid, error_message, sale_id_from_token, schedule_info)
        """
        try:
            # Verify token and get sale_id
            payload = assignment_service.decode_assignment_token(token)
            sale_id_from_token = payload.get("sale_id")
            schedule_id_from_token = payload.get("schedule_id")
            
            if not sale_id_from_token:
                return False, "Token không hợp lệ: thiếu thông tin Sale.", None, None
            
            if not schedule_id_from_token:
                return False, "Token không hợp lệ: thiếu thông tin lịch hẹn.", sale_id_from_token, None
            
            # Get current logged-in user
            user_session = st.session_state.get("user_session")
            
            if not user_session:
                return False, "Vui lòng đăng nhập để xác nhận lịch hẹn.", sale_id_from_token, None
            
            # Check if user is a Sale
            if user_session.role != UserRole.SALE:
                return False, f"Chỉ Sale mới có thể xác nhận lịch hẹn này. Bạn đang đăng nhập với role {user_session.role.value}.", sale_id_from_token, None
            
            # Check if logged-in user matches the sale in token
            if user_session.user_id != sale_id_from_token:
                return False, "Bạn không phải là Sale được phân công cho lịch hẹn này. Vui lòng đăng nhập bằng tài khoản Sale đúng.", sale_id_from_token, None
            
            # Check if schedule still exists (if requested)
            schedule_info = None
            if check_schedule:
                from ..repositories.schedule_repository import schedule_repository
                schedule_info = schedule_repository.get(schedule_id_from_token)
                
                if not schedule_info:
                    return False, "Lịch hẹn này đã bị xóa hoặc không còn tồn tại. Vui lòng liên hệ Admin để biết thêm thông tin.", sale_id_from_token, None
                
                # Check if schedule is still in "assigned" status
                current_status = schedule_info.get("status", "")
                if current_status != "assigned":
                    status_messages = {
                        "pending": "Lịch hẹn này chưa được phân công.",
                        "confirmed": "Lịch hẹn này đã được xác nhận trước đó.",
                        "rejected": "Lịch hẹn này đã bị từ chối trước đó.",
                        "cancelled": "Lịch hẹn này đã bị hủy.",
                    }
                    message = status_messages.get(current_status, f"Lịch hẹn này đã ở trạng thái '{current_status}', không thể xác nhận hoặc từ chối.")
                    return False, message, sale_id_from_token, schedule_info
                
                # Double-check assignment
                if schedule_info.get("assigned_to_sale_id") != sale_id_from_token:
                    return False, "Lịch hẹn này không còn được phân công cho bạn. Có thể đã được phân công lại cho Sale khác.", sale_id_from_token, schedule_info
            
            return True, None, sale_id_from_token, schedule_info
            
        except ValidationError as e:
            return False, str(e), None, None
        except Exception as e:
            logger.error(f"Error validating token and user: {e}")
            return False, f"Có lỗi xảy ra khi xác thực: {str(e)}", None, None

    def render_confirm_page(self, token: str):
        """Render confirmation page"""
        st.title("✅ Xác Nhận Lịch Hẹn")
        
        # Validate token, user, and schedule
        is_valid, error_message, sale_id, schedule_info = self._validate_token_and_user(token, check_schedule=True)
        
        if not is_valid:
            st.error(f"❌ {error_message}")
            if sale_id:
                st.info(f"💡 Lịch hẹn này được phân công cho Sale ID: {sale_id}")
            if schedule_info:
                # Show schedule details if available (even if status is wrong)
                st.info(f"📅 Trạng thái hiện tại: {schedule_info.get('status', 'N/A')}")
            st.info("Vui lòng liên hệ Admin nếu bạn cần hỗ trợ.")
            return
        
        try:
            if st.button("Xác Nhận Lịch Hẹn", type="primary", use_container_width=True):
                with st.spinner("Đang xử lý..."):
                    success = assignment_service.sale_confirm_assignment(token)
                    if success:
                        st.success("✅ Bạn đã xác nhận lịch hẹn thành công!")
                        st.info("Lịch hẹn đã được xác nhận và sẽ hiển thị trong calendar của khách hàng.")
                        st.markdown("---")
                        st.markdown("Bạn có thể đóng trang này.")
                    else:
                        st.error("❌ Có lỗi xảy ra khi xác nhận lịch hẹn.")
            else:
                st.info("Vui lòng nhấn nút bên trên để xác nhận lịch hẹn.")
                
        except ValidationError as e:
            st.error(f"❌ {str(e)}")
            st.info("Vui lòng liên hệ Admin nếu bạn cần hỗ trợ.")
        except Exception as e:
            logger.error(f"Error in confirm page: {e}")
            st.error(f"❌ Có lỗi xảy ra: {str(e)}")

    def render_reject_page(self, token: str):
        """Render rejection page"""
        st.title("❌ Từ Chối Lịch Hẹn")
        
        # Validate token, user, and schedule
        is_valid, error_message, sale_id, schedule_info = self._validate_token_and_user(token, check_schedule=True)
        
        if not is_valid:
            st.error(f"❌ {error_message}")
            if sale_id:
                st.info(f"💡 Lịch hẹn này được phân công cho Sale ID: {sale_id}")
            if schedule_info:
                # Show schedule details if available (even if status is wrong)
                st.info(f"📅 Trạng thái hiện tại: {schedule_info.get('status', 'N/A')}")
            st.info("Vui lòng liên hệ Admin nếu bạn cần hỗ trợ.")
            return
        
        try:
            reason = st.text_area(
                "Lý do từ chối (tùy chọn):",
                placeholder="Nhập lý do từ chối lịch hẹn này...",
                height=100
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Xác Nhận Từ Chối", type="primary", use_container_width=True):
                    with st.spinner("Đang xử lý..."):
                        success = assignment_service.sale_reject_assignment(token, reason if reason else None)
                        if success:
                            st.success("✅ Bạn đã từ chối lịch hẹn.")
                            st.info("Admin sẽ nhận được thông báo và có thể phân công lại cho Sale khác.")
                            st.markdown("---")
                            st.markdown("Bạn có thể đóng trang này.")
                        else:
                            st.error("❌ Có lỗi xảy ra khi từ chối lịch hẹn.")
            
            with col2:
                if st.button("Hủy", use_container_width=True):
                    st.info("Bạn đã hủy thao tác.")
                    
        except ValidationError as e:
            st.error(f"❌ {str(e)}")
            st.info("Vui lòng liên hệ Admin nếu bạn cần hỗ trợ.")
        except Exception as e:
            logger.error(f"Error in reject page: {e}")
            st.error(f"❌ Có lỗi xảy ra: {str(e)}")

    def render(self):
        """Main render method - handles query params"""
        # Get query params from URL
        # Streamlit query params can be accessed via st.query_params (dict-like)
        try:
            query_params = st.query_params
            token = query_params.get("token", "")
            
            if not token:
                st.error("❌ Token không hợp lệ hoặc đã hết hạn.")
                st.info("Vui lòng sử dụng link từ email để truy cập trang này.")
                return
            
            # Validate token and user first (before showing any UI)
            # Don't check schedule here to allow showing action buttons, but check in individual pages
            is_valid, error_message, sale_id, _ = self._validate_token_and_user(token, check_schedule=False)
            
            if not is_valid:
                st.error(f"❌ {error_message}")
                if sale_id:
                    st.info(f"💡 Lịch hẹn này được phân công cho Sale ID: {sale_id}")
                st.info("Vui lòng liên hệ Admin nếu bạn cần hỗ trợ.")
                return
            
            # Determine action from URL path or query params
            # Check if we're on /assignment/confirm or /assignment/reject route
            # For Streamlit, we'll use query params: ?token=xxx&action=confirm or ?token=xxx&action=reject
            action = query_params.get("action", "").lower()
            page = query_params.get("page", "").lower()
            
            # Check URL path (if available)
            # In Streamlit, we can check the current page name or use query params
            if "confirm" in action or "confirm" in page:
                self.render_confirm_page(token)
            elif "reject" in action or "reject" in page:
                self.render_reject_page(token)
            else:
                # Default: show both options
                st.title("📅 Xử Lý Lịch Hẹn")
                st.info("Vui lòng chọn hành động:")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Xác Nhận", type="primary", use_container_width=True):
                        st.session_state.assignment_action = "confirm"
                        st.session_state.assignment_token = token
                        st.rerun()
                
                with col2:
                    if st.button("❌ Từ Chối", type="secondary", use_container_width=True):
                        st.session_state.assignment_action = "reject"
                        st.session_state.assignment_token = token
                        st.rerun()
                
                # Handle action from button click
                if st.session_state.get("assignment_action") == "confirm":
                    self.render_confirm_page(st.session_state.get("assignment_token", token))
                elif st.session_state.get("assignment_action") == "reject":
                    self.render_reject_page(st.session_state.get("assignment_token", token))
        except Exception as e:
            logger.error(f"Error in assignment interface render: {e}")
            st.error(f"❌ Có lỗi xảy ra: {str(e)}")


# Global instance
assignment_interface = AssignmentInterface()

