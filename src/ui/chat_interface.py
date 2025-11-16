"""
Chat Interface - Streamlit UI for the chatbot
"""
import streamlit as st
from typing import Optional

from ..services.chat_service import chat_service
from ..agents.intent_agent import intent_agent
from ..core.config import config
from ..core.logger import logger


class ChatInterface:
    """Streamlit interface for the chatbot"""

    def __init__(self):
        self.chat_service = chat_service
        self.intent_agent = intent_agent
        self.current_user_session = None

    def render_sidebar(self, user_session=None):
        """Render the sidebar with chat sessions"""
        with st.sidebar:
            st.header("💬 Chat Sessions")

            # API Status
            api_status = "✅ Connected" if config.GEMINI_API_KEY else "❌ Missing"
            st.caption(f"🔑 API: {api_status}")

        # New Chat button
        if st.button("➕ New Chat", use_container_width=True):
            # Get current user ID from session
            current_user_id = None
            if hasattr(self, 'current_user_session') and self.current_user_session:
                current_user_id = self.current_user_session.user_id

            new_session = self.chat_service.create_session(current_user_id)
            st.session_state.current_session_id = new_session["id"]
            st.rerun()

            st.divider()

            # Sessions list - filter by user_id if logged in
            all_sessions = self.chat_service.get_all_sessions()

            if user_session:
                # Only show sessions belonging to current user
                sessions = [s for s in all_sessions if s.get("user_id") == user_session.user_id]
            else:
                # Show all sessions if not logged in
                sessions = all_sessions

            for session in sessions:
                session_id = session["id"]
                title = session["title"]
                message_count = len(session["messages"])

                # Highlight current session
                if session_id == st.session_state.get("current_session_id"):
                    st.markdown(f"**🟢 {title}** ({message_count} msgs)")
                else:
                    if st.button(f"💬 {title} ({message_count})", key=f"session_{session_id}", use_container_width=True):
                        st.session_state.current_session_id = session_id
                        st.rerun()

                # Options menu
                if st.button("⋮", key=f"menu_{session_id}", help="Options"):
                    st.session_state[f"show_menu_{session_id}"] = not st.session_state.get(f"show_menu_{session_id}", False)

                # Menu options
                if st.session_state.get(f"show_menu_{session_id}", False):
                    with st.container():
                        if st.button("✏️ Rename", key=f"rename_{session_id}"):
                            st.session_state[f"renaming_{session_id}"] = True

                        if st.button("🗑️ Delete", key=f"delete_{session_id}"):
                            self.chat_service.delete_session(session_id)
                            if st.session_state.get("current_session_id") == session_id:
                                remaining = self.chat_service.get_all_sessions()
                                st.session_state.current_session_id = remaining[0]["id"] if remaining else None
                            st.rerun()

                # Rename input
                if st.session_state.get(f"renaming_{session_id}", False):
                    new_title = st.text_input("New title:", value=title, key=f"title_input_{session_id}")
                    if st.button("💾 Save", key=f"save_rename_{session_id}"):
                        self.chat_service.update_session_title(session_id, new_title)
                        del st.session_state[f"renaming_{session_id}"]
                        st.rerun()

            # Admin panel - only for admin users
            if user_session and user_session.role == "admin":
                st.divider()
                st.subheader("⚙️ Quản Trị Viên")

                if st.button("👥 Quản Lý Người Dùng", use_container_width=True):
                    st.session_state.show_user_management = True
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
            if user_input := st.chat_input("Hỏi tôi hoặc yêu cầu 'vẽ một con chó'...", disabled=not config.GEMINI_API_KEY):
                # Add user message
                self.chat_service.add_message(session_id, "user", user_input)

                # Display user message
                with st.chat_message("user"):
                    st.markdown(user_input)

                # Process with intent analysis and get response
                with st.chat_message("assistant"):
                    with st.spinner("🤖 Đang suy nghĩ..."):
                        try:
                            # Analyze intent
                            intent_result = self.intent_agent.analyze_intent(user_input, session_id)

                            # Get context for conversation
                            context = self.chat_service.format_conversation_context(session_id)

                            # Route to appropriate intent handler
                            from ..intents.intent_registry import intent_registry
                            intent_name = intent_result.get("intent", "general_chat")

                            intent_handler = intent_registry.get_intent_instance(intent_name)
                            if intent_handler:
                                bot_response = intent_handler.get_response(intent_result, context)
                            else:
                                bot_response = f"❌ Không tìm thấy handler cho intent: {intent_name}"

                            # Handle special responses (like audio)
                            if intent_name == "generate_audio" and hasattr(intent_handler, 'get_display_response'):
                                display_response = intent_handler.get_display_response()
                                if display_response:
                                    st.session_state.audio_display_response = display_response

                            # Display response - skip if audio display response is set
                            display_response = st.session_state.get('audio_display_response', bot_response)
                            if 'audio_display_response' in st.session_state:
                                del st.session_state.audio_display_response  # Clean up after use

                            if display_response.strip():  # Only display if there's content
                                st.markdown(display_response, unsafe_allow_html=True)

                        except Exception as e:
                            error_msg = f"❌ Lỗi xử lý: {str(e)}"
                            st.error(error_msg)
                            bot_response = error_msg

                # Save assistant response (use history response for audio, regular response for others)
                history_response = bot_response
                if intent_name == "generate_audio" and hasattr(intent_handler, 'get_history_response'):
                    history_response = intent_handler.get_history_response() or bot_response

                self.chat_service.add_message(session_id, "assistant", history_response)

                # Auto-update title from first message
                if len(session["messages"]) == 2:  # user + assistant
                    self.chat_service.update_session_title_from_first_message(session_id)
        else:
            st.error("❌ Thiếu API key! Vui lòng thiết lập GEMINI_API_KEY.")

    def render(self, user_session=None):
        """Main render method"""
        # Store current user session
        self.current_user_session = user_session

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
        else:
            # Show normal chat interface
            self.render_sidebar(user_session)
            self.render_main_chat(current_session_id, user_session)


# Global instance
chat_interface = ChatInterface()
