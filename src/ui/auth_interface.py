"""
Authentication UI components for Streamlit
"""
import streamlit as st
from typing import Optional

from ..services.auth_service import auth_service
from ..schemas.user import LoginRequest, UserCreate, UserRole, UserSession
from ..core.logger import logger


class AuthInterface:
    """Authentication UI components"""

    def __init__(self):
        self.auth_service = auth_service

    def show_login_form(self) -> Optional[UserSession]:
        """Display login form and return user session if successful"""
        st.title("🔐 Đăng Nhập")

        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập", key="login_username")
            password = st.text_input("Mật khẩu", type="password", key="login_password")
            submit_button = st.form_submit_button("Đăng Nhập", use_container_width=True)

            if submit_button:
                if not username or not password:
                    st.error("Vui lòng nhập đầy đủ thông tin!")
                    return None

                try:
                    with st.spinner("Đang đăng nhập..."):
                        login_data = LoginRequest(username=username, password=password)
                        token_response = self.auth_service.authenticate_user(login_data)

                        # Store session
                        user_session = UserSession(
                            user_id=token_response.user.id,
                            username=token_response.user.username,
                            role=token_response.user.role,
                            is_active=token_response.user.is_active
                        )

                        # Store in session state
                        st.session_state.user_session = user_session
                        st.session_state.auth_token = token_response.access_token

                        st.success(f"Chào mừng {token_response.user.full_name}!")

                        # Rerun to show main app
                        st.rerun()

                        return user_session

                except Exception as e:
                    st.error(f"Đăng nhập thất bại: {str(e)}")
                    return None

        # Link to register
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Chưa có tài khoản? Đăng ký ngay", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()

        return None

    def show_register_form(self) -> Optional[UserSession]:
        """Display registration form"""
        st.title("📝 Đăng Ký Tài Khoản Mới")

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
                    st.error("Vui lòng điền đầy đủ thông tin có dấu *!")
                    return None

                if password != confirm_password:
                    st.error("Mật khẩu xác nhận không khớp!")
                    return None

                if len(password) < 6:
                    st.error("Mật khẩu phải có ít nhất 6 ký tự!")
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

                        # Auto login after registration
                        st.info("Đang đăng nhập tự động...")
                        login_data = LoginRequest(username=username, password=password)
                        token_response = self.auth_service.authenticate_user(login_data)

                        user_session = UserSession(
                            user_id=token_response.user.id,
                            username=token_response.user.username,
                            role=token_response.user.role,
                            is_active=token_response.user.is_active
                        )

                        st.session_state.user_session = user_session
                        st.session_state.auth_token = token_response.access_token

                        st.rerun()
                        return user_session

                except Exception as e:
                    st.error(f"Đăng ký thất bại: {str(e)}")
                    return None

        # Back to login
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Đã có tài khoản? Đăng nhập", use_container_width=True):
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

            # Admin panel
            if user_session.role == UserRole.ADMIN:
                st.divider()
                st.subheader("⚙️ Quản Trị Viên")

                if st.button("👥 Quản Lý Người Dùng", use_container_width=True):
                    st.session_state.show_user_management = True
                    st.rerun()

            # Logout
            st.divider()
            if st.button("🚪 Đăng Xuất", use_container_width=True):
                self.logout()

    def show_user_management(self, current_user: UserSession):
        """Show user management interface for admins"""
        st.title("👥 Quản Lý Người Dùng")

        try:
            users = self.auth_service.get_all_users(current_user)

            if not users:
                st.info("Chưa có người dùng nào.")
                return

            # Users table
            st.subheader(f"Tổng cộng {len(users)} người dùng")

            for user in users:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 1])

                    with col1:
                        st.write(f"**{user.username}**")
                    with col2:
                        st.write(user.email)
                    with col3:
                        role_color = "🟢" if user.role == UserRole.ADMIN else "🔵"
                        st.write(f"{role_color} {user.role.value}")
                    with col4:
                        status_color = "✅" if user.is_active else "❌"
                        st.write(f"{status_color} {'Active' if user.is_active else 'Inactive'}")
                    with col5:
                        if user.id != current_user.user_id:
                            if st.button("✏️", key=f"edit_{user.id}", help="Edit user"):
                                st.session_state.edit_user_id = user.id
                                st.rerun()

                st.divider()

            # Edit user form
            if "edit_user_id" in st.session_state:
                edit_user_id = st.session_state.edit_user_id
                edit_user = next((u for u in users if u.id == edit_user_id), None)

                if edit_user:
                    st.subheader(f"Chỉnh sửa: {edit_user.username}")

                    with st.form(f"edit_user_{edit_user_id}"):
                        new_role = st.selectbox(
                            "Vai trò",
                            [UserRole.USER.value, UserRole.ADMIN.value],
                            index=0 if edit_user.role == UserRole.USER else 1
                        )
                        is_active = st.checkbox("Kích hoạt", value=edit_user.is_active)

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Lưu Thay Đổi"):
                                try:
                                    from ..schemas.user import UserUpdate
                                    update_data = UserUpdate(
                                        role=UserRole(new_role),
                                        is_active=is_active
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
        if st.button("⬅️ Quay Lại Chat", use_container_width=True):
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
        if "edit_user_id" in st.session_state:
            del st.session_state.edit_user_id

        st.rerun()

    def render(self):
        """Main render method for authentication"""
        # Check if user is logged in
        user_session = st.session_state.get("user_session")

        if user_session:
            # User is logged in
            if st.session_state.get("show_user_management"):
                self.show_user_management(user_session)
            else:
                # Show profile in sidebar and return control to main app
                self.show_user_profile(user_session)
                return user_session
        else:
            # User not logged in - show auth forms
            if st.session_state.get("show_register", False):
                self.show_register_form()
            else:
                self.show_login_form()

        return None


# Global instance
auth_interface = AuthInterface()
