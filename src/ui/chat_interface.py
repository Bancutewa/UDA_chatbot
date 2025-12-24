"""
Chat Interface - Streamlit UI for the chatbot
"""
import streamlit as st
from typing import Optional
from datetime import datetime

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

            # Removed schedule summary from sidebar - users can access full schedule page instead

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
                        # Render content with media support
                        self._render_message_content(content)
                    else:
                        st.markdown(content)


        else:
            st.info("👋 Bắt đầu cuộc trò chuyện mới!")

        # Chat input area
        if config.GEMINI_API_KEY:
            # 1. Audio Input
            audio_value = st.audio_input("Ghi âm giọng nói")
            
            user_input = None
            
            # Handle Audio Input
            if audio_value:
                # Check if this audio has already been processed to avoid loops
                # Streamlit reruns on interaction. We can use session state to track processed audio.
                audio_key = f"audio_{hash(audio_value)}"
                if audio_key not in st.session_state:
                     with st.spinner("🎙️ Đang nghe..."):
                         from ..services.audio_service import audio_service
                         transcribed_text = audio_service.transcribe(audio_value)
                         
                         if transcribed_text:
                             user_input = transcribed_text
                             st.session_state[audio_key] = True # Mark as processed
                         else:
                             st.warning("Không nghe rõ, vui lòng thử lại.")
            
            # 2. Text Input (takes precedence if user types whilst a recording exists, though unlikely)
            text_input = st.chat_input("Hỏi tôi...", disabled=not config.GEMINI_API_KEY)
            if text_input:
                user_input = text_input

            # Process User Input (from either source)
            if user_input:
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
                            
                            self._render_message_content(bot_response)
                            
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
            
            # Get sessions filtered by user_id if logged in
            if user_session:
                sessions = self.chat_service.get_all_sessions(user_session.user_id)
            else:
                sessions = self.chat_service.get_all_sessions()

            # Use first session if available, otherwise create new
            if sessions:
                st.session_state.current_session_id = sessions[0]["id"]
            else:
                new_session = self.chat_service.create_session(current_user_id)
                st.session_state.current_session_id = new_session["id"]

        current_session_id = st.session_state.current_session_id
        
        # IMPORTANT: If user is logged in, ensure current session has correct user_id
        # This fixes the issue where session was created before login
        if user_session and current_session_id:
            try:
                session = self.chat_service.get_session(current_session_id)
                if session and (not session.get("user_id") or session.get("user_id") != user_session.user_id):
                    # Update session with correct user_id
                    from ..repositories.chat_history_repo import ChatHistoryRepository
                    repo = ChatHistoryRepository()
                    if hasattr(repo, 'mongo_repo') and repo.mongo_repo:
                        # MongoDB: update user_id
                        repo.mongo_repo.collection.update_one(
                            {"_id": current_session_id},
                            {"$set": {"user_id": user_session.user_id, "updated_at": datetime.utcnow()}}
                        )
                        logger.info(f"Updated session {current_session_id} with user_id={user_session.user_id}")
            except Exception as e:
                logger.warning(f"Could not update session user_id: {e}")

        # Render sidebar first (always visible)
        self.render_sidebar(user_session)
        
        # Check for assignment pages (from email links)
        query_params = st.query_params
        if "token" in query_params and ("assignment" in query_params.get("page", "") or "confirm" in query_params.get("action", "").lower() or "reject" in query_params.get("action", "").lower()):
            from ..ui.assignment_interface import assignment_interface
            assignment_interface.render()
            return
        
        # Render components
        if st.session_state.get("show_user_management"):
            # Show admin user management panel
            from ..ui.auth_interface import auth_interface
            auth_interface.show_user_management(user_session)
        elif st.session_state.get("show_schedule_management"):
            schedule_interface.render_admin_calendar(user_session)
        elif st.session_state.get("show_data_management"):
            data_interface.render(user_session)
        else:
            # Show normal chat interface
            self.render_main_chat(current_session_id, user_session)


    def _render_message_content(self, content: str):
        """Render message content with auto-detected media"""
        import re
        import os
        import base64

        # 1. Render main text
        st.markdown(content, unsafe_allow_html=True)
        
        # 2. Detect and render Audio
        # Flexible pattern to catch audio file paths or "Audio generated successfully"
        # Matches paths ending in .mp3 inside the content string, specifically looking for typical data/ structure
        audio_matches = re.finditer(r"(?:data[/\\]audio_generations[/\\]|[^ \t\n\r\f\v]+\.mp3)", content)
        
        # More robust regex to find the specific path output by agent
        # Example: "data/audio_generations\audio_d8...mp3"
        # We look for a substring that looks like a valid audio path present in the content
        
        candidates = []
        # Extract potential paths that exist
        words = content.split()
        for word in words:
            # Clean punctuation from ends
            clean_word = word.strip('."\',()')
            if clean_word.endswith('.mp3') and 'audio' in clean_word:
                 candidates.append(clean_word)
        
        # Also try regex for the specific pattern observed
        regex_match = re.search(r"(data[/\\]audio_generations[/\\][\w-]+\.mp3)", content.replace('\\', '/'))
        if regex_match:
             candidates.append(regex_match.group(1))

        # Render unique valid audio files
        processed_audio = set()
        for filepath in candidates:
            # Normalize path separators
            filepath = filepath.replace('/', os.sep).replace('\\', os.sep)
            
            if filepath in processed_audio:
                continue
                
            if os.path.exists(filepath):
                try:
                    with open(filepath, "rb") as f:
                        audio_bytes = f.read()
                    st.audio(audio_bytes, format="audio/mp3")
                    processed_audio.add(filepath)
                except Exception as e:
                    logger.error(f"Failed to render audio {filepath}: {e}")

        # 3. Detect and render Images
        # Regex to find https://image.pollinations.ai/... ending with space or punctuation
        # We capture the full URL until a space or end of string
        image_urls = re.findall(r"(https://image\.pollinations\.ai/prompt/[^ \s\)\"']+)", content)
        
        if image_urls:
            # Check if likely in markdown already
            # Heuristic: if content has ![...](url), we skip explicit st.image for that url
            for url in image_urls:
                # Basic check if URL is inside a markdown link structure
                if f"]({url})" not in content:
                     st.image(url, caption="Generated Image", use_container_width=True)

        # 4. Detect and render Local Images (Gemini Generated)
        # Look for paths like data/generated_images/uuid.png
        local_image_matches = re.finditer(r"(data[/\\]generated_images[/\\][\w-]+\.png)", content.replace('\\', '/'))
        
        processed_images = set()
        for match in local_image_matches:
            image_path = match.group(1)
            # Normalize path
            image_path = image_path.replace('/', os.sep).replace('\\', os.sep)
            
            if image_path in processed_images:
                continue
                
            if os.path.exists(image_path):
                try:
                    st.image(image_path, caption="Generated Image", use_container_width=True)
                    processed_images.add(image_path)
                except Exception as e:
                    logger.error(f"Failed to render image {image_path}: {e}")


# Global instance
chat_interface = ChatInterface()
