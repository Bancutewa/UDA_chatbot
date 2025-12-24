"""
Assignment Interface - Handle assignment confirmation/rejection from email links
"""
import streamlit as st
from typing import Optional

from ..services.assignment_service import assignment_service
from ..core.logger import logger
from ..core.exceptions import ValidationError, AuthenticationError


class AssignmentInterface:
    """UI for assignment confirmation/rejection"""

    def render_confirm_page(self, token: str):
        """Render confirmation page"""
        st.title("✅ Xác Nhận Lịch Hẹn")
        
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

