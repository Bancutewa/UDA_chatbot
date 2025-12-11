"""
Chat Interface - Streamlit UI for the chatbot
"""
import streamlit as st
from typing import Optional

from ..services.chat_service import chat_service
from ..core.config import config
from ..core.logger import logger
from ..ui.schedule_interface import schedule_interface
from ..ui.data_interface import data_interface


class ChatInterface:
    """Streamlit interface for the chatbot"""

    def __init__(self):
        self.chat_service = chat_service
        self.current_user_session = None

    def render_sidebar(self, user_session=None):
        """Render the sidebar with chat sessions"""
        with st.sidebar:
            st.header("💬 Chat Sessions")

            # API Status
            api_status = "✅ Connected" if config.GEMINI_API_KEY else "❌ Missing"
            st.caption(f"🔑 API: {api_status}")

            # New Chat button
            if st.button("➕ New Chat", key="new_chat_button", use_container_width=True):
                # Get current user ID from session
                current_user_id = user_session.user_id if user_session else None

                new_session = self.chat_service.create_session(current_user_id)
                st.session_state.current_session_id = new_session["id"]
                st.rerun()

            st.divider()

            # Sessions list - get user-specific sessions if logged in
            if user_session:
                # Get sessions for current user
                sessions = self.chat_service.get_all_sessions(user_session.user_id)
                st.caption(f"📝 {len(sessions)} cuộc trò chuyện của bạn")
            else:
                # Show all sessions if not logged in
                sessions = self.chat_service.get_all_sessions()
                st.caption("📝 Tất cả cuộc trò chuyện")

            # Sort sessions by updated_at (newest first)
            sessions_sorted = sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True)

            for session in sessions_sorted:
                session_id = session["id"]
                title = session["title"]
                message_count = len(session["messages"])
                created_at = session.get("created_at", "")

                # Format timestamp for display
                if created_at:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        time_display = dt.strftime("%H:%M")
                        date_display = dt.strftime("%d/%m")
                        timestamp = f"{date_display} {time_display}"
                    except:
                        timestamp = "N/A"
                else:
                    timestamp = "N/A"

                # Create container for each session item
                with st.container():
                    # Header row with title and options menu
                    col1, col2 = st.columns([4, 1])

                    # Session title and click action
                    with col1:
                        if session_id == st.session_state.get("current_session_id"):
                            st.markdown(f"**🟢 {title}**")
                        else:
                            if st.button(f"💬 {title}", key=f"session_{session_id}", use_container_width=True):
                                st.session_state.current_session_id = session_id
                                st.rerun()

                    # Options menu button
                    with col2:
                        if st.button("⋮", key=f"menu_{session_id}", help="Options"):
                            st.session_state[f"show_menu_{session_id}"] = not st.session_state.get(f"show_menu_{session_id}", False)

                    # Session info row
                    col_info1, col_info2 = st.columns([3, 1])
                    with col_info1:
                        st.caption(f"🕒 {timestamp}")
                    with col_info2:
                        st.caption(f"{message_count}💬")

                    # Menu options (expandable)
                    if st.session_state.get(f"show_menu_{session_id}", False):
                        st.divider()
                        menu_col1, menu_col2 = st.columns(2)

                        with menu_col1:
                            if st.button("✏️ Đổi tên", key=f"rename_{session_id}"):
                                st.session_state[f"renaming_{session_id}"] = True

                        with menu_col2:
                            if st.button("🗑️ Xóa", key=f"delete_{session_id}", type="secondary"):
                                # Confirm deletion
                                if st.session_state.get(f"confirm_delete_{session_id}", False):
                                    self.chat_service.delete_session(session_id)
                                    if st.session_state.get("current_session_id") == session_id:
                                        # Filter remaining sessions by user
                                        all_remaining = self.chat_service.get_all_sessions()
                                        user_remaining = [s for s in all_remaining if s.get("user_id") == user_session.user_id] if user_session else all_remaining
                                        st.session_state.current_session_id = user_remaining[0]["id"] if user_remaining else None
                                    st.success("Đã xóa cuộc trò chuyện!")
                                    del st.session_state[f"confirm_delete_{session_id}"]
                                    del st.session_state[f"show_menu_{session_id}"]
                                    st.rerun()
                                else:
                                    st.session_state[f"confirm_delete_{session_id}"] = True
                                    st.warning("Nhấn lại để xác nhận xóa!")

                    # Rename input (expandable)
                    if st.session_state.get(f"renaming_{session_id}", False):
                        st.divider()
                        new_title = st.text_input(
                            "Tên mới:",
                            value=title,
                            key=f"title_input_{session_id}"
                        )
                        if st.button("💾 Lưu", key=f"save_rename_{session_id}"):
                            self.chat_service.update_session_title(session_id, new_title)
                            del st.session_state[f"renaming_{session_id}"]
                            del st.session_state[f"show_menu_{session_id}"]
                            st.rerun()

                        if st.button("❌ Hủy", key=f"cancel_rename_{session_id}"):
                            del st.session_state[f"renaming_{session_id}"]
                            st.rerun()

            if user_session:
                schedule_container = st.container()
                schedule_interface.render_user_summary(user_session, schedule_container)

            # Admin panel - only for admin users
            if user_session and user_session.role == "admin":
                st.divider()
                st.subheader("⚙️ Quản Trị Viên")

                if st.button("👥 Quản Lý Người Dùng", key="admin_user_management_button", use_container_width=True):
                    st.session_state.show_user_management = True
                    st.rerun()

                if st.button("📅 Lịch Xem Nhà", key="admin_schedule_button", use_container_width=True):
                    st.session_state.show_schedule_management = True
                    st.rerun()

                if st.button("🗄️ Quản Lý Dữ Liệu", key="admin_data_button", use_container_width=True):
                    st.session_state.show_data_management = True
                    st.rerun()

    def render_main_chat(self, session_id: Optional[str], user_session=None):
        """Render the main chat interface"""
        if not session_id:
            st.info("👋 Chọn hoặc tạo một cuộc trò chuyện mới!")
            return

        session = self.chat_service.get_session(session_id)
        if not session:
            st.error("Session không tồn tại!")
            return

        st.title(f"🤖 {session['title']}")

        # Display messages
        messages = session["messages"]
        if messages:
            for message in messages:
                with st.chat_message(message["role"]):
                    content = message["content"]
                    if message["role"] == "assistant":
                        # Handle special display responses
                        if st.session_state.get('audio_display_response'):
                            display_content = st.session_state.audio_display_response
                            del st.session_state.audio_display_response
                            st.markdown(display_content, unsafe_allow_html=True)
                        else:
                            st.markdown(content, unsafe_allow_html=True)
                    else:
                        st.markdown(content)
        else:
            st.info("👋 Bắt đầu cuộc trò chuyện mới!")

        # Chat input
        if config.GEMINI_API_KEY:
            if user_input := st.chat_input("Hỏi tôi...", disabled=not config.GEMINI_API_KEY):
                # Add user message
                self.chat_service.add_message(session_id, "user", user_input)

                # Display user message
                with st.chat_message("user"):
                    st.markdown(user_input)

                # Process with LangChain Agent
                with st.chat_message("assistant"):
                    with st.spinner("🤖 Đang suy nghĩ..."):
                        try:
                            # Simplified Invoke using Agent Memory (MongoDB)
                            # Passing session_id as thread_id so Agent manages history
                            from ..agents.estate_agent import estate_agent
                            
                            bot_response = estate_agent.invoke(user_input, thread_id=session_id)
                            
                            st.markdown(bot_response)
                            
                            self.chat_service.add_message(session_id, "assistant", bot_response)

                             # Auto-update title from first message
                            if len(session["messages"]) == 2:  # user + assistant
                                self.chat_service.update_session_title_from_first_message(session_id)

                        except Exception as e:
                            error_msg = f"❌ Lỗi xử lý: {str(e)}"
                            st.error(error_msg)
                            logger.error(f"Chat Error: {e}")
        else:
            st.error("❌ Thiếu API key! Vui lòng thiết lập GEMINI_API_KEY.")

    def render(self, user_session=None):
        """Main render method"""
        # Store current user session
        self.current_user_session = user_session

        # Clean up sessions without any conversation history (ChatGPT-like behavior)
        active_session_id = st.session_state.get("current_session_id")
        user_id = user_session.user_id if user_session else None
        self.chat_service.cleanup_empty_sessions(
            user_id=user_id,
            exclude_session_id=active_session_id
        )

        # Initialize current session
        if "current_session_id" not in st.session_state:
            # Get current user ID for session creation
            current_user_id = user_session.user_id if user_session else None
            sessions = self.chat_service.get_all_sessions()

            # Filter sessions by user_id if user is logged in
            if user_session and sessions:
                user_sessions = [s for s in sessions if s.get("user_id") == user_session.user_id]
                if user_sessions:
                    st.session_state.current_session_id = user_sessions[0]["id"]
                else:
                    new_session = self.chat_service.create_session(current_user_id)
                    st.session_state.current_session_id = new_session["id"]
            elif sessions:
                st.session_state.current_session_id = sessions[0]["id"]
            else:
                new_session = self.chat_service.create_session(current_user_id)
                st.session_state.current_session_id = new_session["id"]

        current_session_id = st.session_state.current_session_id

        # Render components
        if st.session_state.get("show_user_management"):
            # Show admin user management panel
            from ..ui.auth_interface import auth_interface
            auth_interface.show_user_management(user_session)
        elif st.session_state.get("show_schedule_management"):
            schedule_interface.render_admin_calendar(user_session)
        elif st.session_state.get("show_data_management"):
            data_interface.render()
        else:
            # Show normal chat interface
            self.render_sidebar(user_session)
            self.render_main_chat(current_session_id, user_session)


# Global instance
chat_interface = ChatInterface()
