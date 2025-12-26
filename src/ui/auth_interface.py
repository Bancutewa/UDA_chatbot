"""
Authentication UI components for Streamlit
"""
import streamlit as st
from typing import Optional

from ..services.auth_service import auth_service
from ..services.auth_service import auth_service
from ..schemas.user import LoginRequest, UserCreate, UserRole, UserSession, UserStatus
from ..core.logger import logger


class AuthInterface:
    """Authentication UI components"""

    def __init__(self):
        self.auth_service = auth_service

    def show_login_form(self) -> Optional[UserSession]:
        """Display login form and return user session if successful"""
        st.title("🔐 Đăng Nhập")

        # Error container - always visible at top, outside form
        error_container = st.container()
        
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập", key="login_username")
            password = st.text_input("Mật khẩu", type="password", key="login_password")
            submit_button = st.form_submit_button("Đăng Nhập", use_container_width=True)

            if submit_button:
                if not username or not password:
                    error_container.error("Vui lòng nhập đầy đủ thông tin!")
                else:
                    try:
                        with st.spinner("Đang đăng nhập..."):
                            login_data = LoginRequest(username=username, password=password)
                            token_response = self.auth_service.authenticate_user(login_data)

                            # Store session
                            user_session = UserSession(
                                user_id=token_response.user.id,
                                username=token_response.user.username,
                                role=token_response.user.role,
                                status=token_response.user.status
                            )

                            # Store in session state
                            st.session_state.user_session = user_session
                            st.session_state.auth_token = token_response.access_token

                            st.success(f"Chào mừng {token_response.user.full_name}!")

                            # Rerun to show main app
                            st.rerun()

                            return user_session

                    except Exception as e:
                        error_container.error(f"Đăng nhập thất bại: {str(e)}")

        # Link to register - always visible at bottom, outside form
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Chưa có tài khoản? Đăng ký ngay", key="switch_to_register_button", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()

        return None

    def show_verification_form(self) -> Optional[UserSession]:
        """Display verification form"""
        st.title("✉️ Xác thực Email")
        
        pending_username = st.session_state.get("pending_username")
        if not pending_username:
            st.error("Không tìm thấy thông tin đăng ký. Vui lòng đăng ký lại.")
            if st.button("Quay lại đăng ký"):
                st.session_state.show_verification = False
                st.session_state.show_register = True
                del st.session_state.pending_username
                st.rerun()
            return None

        st.info(f"Mã xác thực đã được gửi đến email đăng ký của tài khoản **{pending_username}**.")
        st.caption("Vui lòng kiểm tra hộp thư (bao gồm cả thư rác). Mã có hiệu lực trong 15 phút.")

        with st.form("verification_form"):
            otp = st.text_input("Mã xác thực (6 số)", max_chars=6)
            col1, col2 = st.columns(2)
            
            with col1:
                submit_button = st.form_submit_button("Xác Thực", use_container_width=True)
            
            with col2:
                # We can't put a button inside a form that doesn't submit
                # So we just use submit button
                pass

        if submit_button:
            if not otp or len(otp) != 6:
                st.error("Vui lòng nhập mã xác thực hợp lệ!")
                return None

            try:
                with st.spinner("Đang xác thực..."):
                    if self.auth_service.verify_email(pending_username, otp):
                        st.success("✅ Xác thực thành công!")
                        
                        # Auto login logic requires password, which we don't have here unless we stored it in session (unsafe)
                        # Or we can just prompt to login
                        
                        st.info("Vui lòng đăng nhập để tiếp tục.")
                        
                        # Cleanup session
                        del st.session_state.pending_username
                        st.session_state.show_verification = False
                        st.session_state.show_register = False
                        
                        if st.button("Đi tới Đăng Nhập"):
                            st.rerun()
                        
                        # Auto redirect to login after short delay? 
                        # Streamlit doesn't support easy delay redirects without sleep
                        
                        return None
            except Exception as e:
                st.error(f"Xác thực thất bại: {str(e)}")

        st.divider()
        if st.button("Gửi lại mã xác thực"):
             try:
                 if self.auth_service.resend_verification_email(pending_username):
                     st.success("Đã gửi lại mã xác thực!")
                 else:
                     st.error("Không thể gửi lại mã.")
             except Exception as e:
                 st.error(f"Lỗi: {str(e)}")

        if st.button("Quay lại Đăng Nhập"):
            st.session_state.show_verification = False
            st.session_state.show_register = False
            if "pending_username" in st.session_state:
                del st.session_state.pending_username
            st.rerun()
             
        return None

    def show_register_form(self) -> Optional[UserSession]:
        """Display registration form"""
        st.title("📝 Đăng Ký Tài Khoản Mới")

        # Error container - always visible
        error_container = st.container()

        with st.form("register_form"):
            col1, col2 = st.columns(2)

            with col1:
                username = st.text_input("Tên đăng nhập *", key="reg_username")
                password = st.text_input("Mật khẩu *", type="password", key="reg_password")
                confirm_password = st.text_input("Xác nhận mật khẩu *", type="password", key="reg_confirm_password")

            with col2:
                full_name = st.text_input("Họ và tên *", key="reg_full_name")
                email = st.text_input("Email *", key="reg_email")
                # Role is automatically set to USER during registration

            submit_button = st.form_submit_button("Đăng Ký", use_container_width=True)

            if submit_button:
                # Validation
                if not all([username, password, confirm_password, full_name, email]):
                    error_container.error("Vui lòng điền đầy đủ thông tin có dấu *!")
                    return None

                if password != confirm_password:
                    error_container.error("Mật khẩu xác nhận không khớp!")
                    return None

                if len(password) < 6:
                    error_container.error("Mật khẩu phải có ít nhất 6 ký tự!")
                    return None

                try:
                    with st.spinner("Đang tạo tài khoản..."):
                        user_data = UserCreate(
                            username=username,
                            email=email,
                            full_name=full_name,
                            password=password
                            # Role is automatically set to USER in auth_service.register_user()
                        )

                        user_response = self.auth_service.register_user(user_data)

                        st.success(f"🎉 Tài khoản {user_response.username} đã được tạo thành công!")
                        
                        # Store pending username and switch to verification
                        st.session_state.pending_username = username
                        st.session_state.show_verification = True
                        st.session_state.show_register = False
                        st.rerun()
                        
                        return None

                except Exception as e:
                    error_container.error(f"Đăng ký thất bại: {str(e)}")
                    return None

        # Back to login - always visible at bottom
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Đã có tài khoản? Đăng nhập", key="switch_to_login_button", use_container_width=True):
                st.session_state.show_register = False
                st.rerun()

        return None

    def show_user_profile(self, user_session: UserSession):
        """Display user profile and management options"""
        with st.sidebar:
            st.header("👤 Tài Khoản")

            # User info
            st.write(f"**Tên:** {user_session.username}")
            st.write(f"**Vai trò:** {user_session.role.value.upper()}")

            # Actions - New Chat and Schedule management
            st.divider()
            
            # New Chat button
            from ..services.chat_service import chat_service
            if st.button("➕ Cuộc Trò Chuyện Mới", key="sidebar_new_chat_button", use_container_width=True):
                # Clear admin page flags to return to chat
                st.session_state.show_user_management = False
                st.session_state.show_schedule_management = False
                st.session_state.show_data_management = False
                
                # Create new session
                current_user_id = user_session.user_id
                new_session = chat_service.create_session(current_user_id)
                st.session_state.current_session_id = new_session["id"]
                st.rerun()
            
            if st.button("📅 Quản Lý Lịch Hẹn", key="sidebar_schedule_button", use_container_width=True):
                # Clear other page flags
                st.session_state.show_user_management = False
                st.session_state.show_data_management = False
                st.session_state.show_schedule_management = True
                st.rerun()
            
            if st.button("🚪 Đăng Xuất", key="logout_button", use_container_width=True):
                self.logout()

            # Admin panel only
            if user_session.role == UserRole.ADMIN:
                st.divider()
                st.subheader("⚙️ Quản Trị Viên")

                # User management (Admin only)
                if st.button("👥 Quản Lý Người Dùng", key="sidebar_user_management_button", use_container_width=True):
                    # Clear other page flags
                    st.session_state.show_schedule_management = False
                    st.session_state.show_data_management = False
                    st.session_state.show_user_management = True
                    st.rerun()
                
                # Data management (Admin only)
                if st.button("🗄️ Quản Lý Dữ Liệu", key="sidebar_data_button", use_container_width=True):
                    # Clear other page flags
                    st.session_state.show_user_management = False
                    st.session_state.show_schedule_management = False
                    st.session_state.show_data_management = True
                    st.rerun()

    def show_user_management(self, current_user: UserSession):
        """Show user management interface for admins only"""
        # Only Admin can access
        if current_user.role != UserRole.ADMIN:
            st.error("❌ Chỉ quản trị viên mới có quyền truy cập quản lý người dùng.")
            if st.button("⬅️ Quay lại chat", use_container_width=True):
                st.session_state.show_user_management = False
                st.rerun()
            return
        
        st.title("👥 Quản Lý Người Dùng")

        try:
            all_users = self.auth_service.get_all_users(current_user)

            if not all_users:
                st.info("Chưa có người dùng nào.")
                return

            # Filter section
            st.subheader("🔍 Lọc & Tìm kiếm")
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                search_query = st.text_input(
                    "🔎 Tìm kiếm (username/email)",
                    value=st.session_state.get("user_search_query", ""),
                    key="user_search_input",
                    placeholder="Nhập username hoặc email..."
                )
                st.session_state.user_search_query = search_query
            
            with filter_col2:
                role_options = ["Tất cả", "Admin", "Sale", "User"]
                saved_role = st.session_state.get("user_role_filter", "Tất cả")
                role_index = role_options.index(saved_role) if saved_role in role_options else 0
                role_filter = st.selectbox(
                    "👤 Lọc theo vai trò",
                    options=role_options,
                    index=role_index,
                    key="user_role_filter_select"
                )
                st.session_state.user_role_filter = role_filter
            
            with filter_col3:
                status_options = ["Tất cả", "Hoạt động", "Chờ xác thực", "Vô hiệu hóa"]
                saved_status = st.session_state.get("user_status_filter", "Tất cả")
                status_index = status_options.index(saved_status) if saved_status in status_options else 0
                status_filter = st.selectbox(
                    "📊 Lọc theo trạng thái",
                    options=status_options,
                    index=status_index,
                    key="user_status_filter_select"
                )
                st.session_state.user_status_filter = status_filter
            
            # Apply filters
            users = all_users.copy()
            
            # Filter by search query
            if search_query:
                search_lower = search_query.lower()
                users = [
                    u for u in users
                    if search_lower in u.username.lower() or search_lower in u.email.lower()
                ]
            
            # Filter by role
            if role_filter != "Tất cả":
                role_mapping = {
                    "Admin": UserRole.ADMIN,
                    "Sale": UserRole.SALE,
                    "User": UserRole.USER
                }
                if role_filter in role_mapping:
                    users = [u for u in users if u.role == role_mapping[role_filter]]
            
            # Filter by status
            if status_filter != "Tất cả":
                status_mapping = {
                    "Hoạt động": UserStatus.ACTIVE,
                    "Chờ xác thực": UserStatus.PENDING,
                    "Vô hiệu hóa": UserStatus.INACTIVE
                }
                if status_filter in status_mapping:
                    users = [u for u in users if u.status == status_mapping[status_filter]]
            
            st.divider()
            
            # Users table
            if len(users) == 0:
                st.warning(f"⚠️ Không tìm thấy người dùng nào phù hợp với bộ lọc.")
                st.info("💡 Thử thay đổi bộ lọc để xem thêm kết quả.")
            else:
                st.subheader(f"📊 Kết quả: {len(users)} / {len(all_users)} người dùng")

            for user in users:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 1])

                    with col1:
                        st.write(f"**{user.username}**")
                    with col2:
                        st.write(user.email)
                    with col3:
                        # Role color: Admin=🟢, Sale=🟡, User=🔵
                        if user.role == UserRole.ADMIN:
                            role_color = "🟢"
                        elif user.role == UserRole.SALE:
                            role_color = "🟡"
                        else:
                            role_color = "🔵"
                        st.write(f"{role_color} {user.role.value}")
                    with col4:
                        if user.status == UserStatus.ACTIVE:
                            st.write("✅ Hoạt động")
                        elif user.status == UserStatus.PENDING:
                            st.write("⏳ Chờ xác thực")
                        else:
                            st.write("❌ Vô hiệu hóa")
                    with col5:
                        # Only Admin can edit users
                        if current_user.role == UserRole.ADMIN and user.id != current_user.user_id:
                            if st.button("✏️", key=f"edit_{user.id}", help="Edit user"):
                                st.session_state.edit_user_id = user.id
                                st.rerun()

                st.divider()

            # Edit user form (Admin only)
            if current_user.role == UserRole.ADMIN and "edit_user_id" in st.session_state:
                edit_user_id = st.session_state.edit_user_id
                edit_user = next((u for u in users if u.id == edit_user_id), None)

                if edit_user:
                    st.subheader(f"Chỉnh sửa: {edit_user.username}")

                    with st.form(f"edit_user_{edit_user_id}"):
                        # Role selector includes all three roles
                        role_options = [UserRole.ADMIN.value, UserRole.SALE.value, UserRole.USER.value]
                        current_role_index = role_options.index(edit_user.role.value) if edit_user.role.value in role_options else 0
                        new_role = st.selectbox(
                            "Vai trò",
                            role_options,
                            index=current_role_index
                        )
                        new_status = st.selectbox(
                            "Trạng thái",
                            [s.value for s in UserStatus],
                            index=[s.value for s in UserStatus].index(edit_user.status.value)
                        )

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Lưu Thay Đổi"):
                                try:
                                    from ..schemas.user import UserUpdate
                                    update_data = UserUpdate(
                                        role=UserRole(new_role),
                                        status=UserStatus(new_status)
                                    )
                                    updated_user = self.auth_service.update_user(
                                        edit_user_id, update_data, current_user
                                    )
                                    if updated_user:
                                        st.success("Cập nhật thành công!")
                                        del st.session_state.edit_user_id
                                        st.rerun()
                                    else:
                                        st.error("Cập nhật thất bại!")
                                except Exception as e:
                                    st.error(f"Lỗi: {str(e)}")

                        with col2:
                            if st.form_submit_button("🗑️ Xóa Người Dùng", type="secondary"):
                                try:
                                    if self.auth_service.delete_user(edit_user_id, current_user):
                                        st.success("Xóa người dùng thành công!")
                                        del st.session_state.edit_user_id
                                        st.rerun()
                                    else:
                                        st.error("Xóa người dùng thất bại!")
                                except Exception as e:
                                    st.error(f"Lỗi: {str(e)}")

                    if st.button("❌ Hủy", key=f"cancel_edit_{edit_user_id}"):
                        del st.session_state.edit_user_id
                        st.rerun()

        except Exception as e:
            st.error(f"Lỗi khi tải danh sách người dùng: {str(e)}")

        # Back button
        st.divider()
        if st.button("⬅️ Quay Lại Chat", key="back_to_chat_button", use_container_width=True):
            st.session_state.show_user_management = False
            st.rerun()

    def logout(self):
        """Logout user"""
        if "user_session" in st.session_state:
            del st.session_state.user_session
        if "auth_token" in st.session_state:
            del st.session_state.auth_token
        if "show_register" in st.session_state:
            del st.session_state.show_register
        if "show_user_management" in st.session_state:
            del st.session_state.show_user_management
        if "show_schedule_management" in st.session_state:
            del st.session_state.show_schedule_management
        if "show_verification" in st.session_state:
            del st.session_state.show_verification
        if "pending_username" in st.session_state:
            del st.session_state.pending_username

        st.rerun()

    def render(self):
        """Main render method for authentication"""
        # Check if user is logged in
        user_session = st.session_state.get("user_session")

        if user_session:
            # User is logged in
            # Don't render show_user_management here - let chat_interface handle it with sidebar
            # Just show profile in sidebar and return control to main app
            self.show_user_profile(user_session)
            return user_session
        else:
            # User not logged in - show auth forms
            if st.session_state.get("show_verification", False):
                self.show_verification_form()
            elif st.session_state.get("show_register", False):
                self.show_register_form()
            else:
                self.show_login_form()

        return None


# Global instance
auth_interface = AuthInterface()
