"""
Chat Service - Handle chat logic and context formatting
"""
from typing import List, Dict, Optional

from ..repositories.chat_history_repo import chat_history_repo
from ..schemas.conversation_state import ConversationState, DialogState
from ..core.logger import logger
from ..core import settings

class ChatService:
    """Service for chat operations"""

    def __init__(self):
        self.repository = chat_history_repo

    def create_session(self, user_id: str = None, title: str = "New Chat") -> Dict:
        """Create new chat session"""
        import uuid
        session_id = str(uuid.uuid4())
        return self.repository.create_session(session_id, title, user_id)

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        return self.repository.get_session(session_id)

    def add_message(self, session_id: str, role: str, content: str):
        """Add message to session"""
        self.repository.add_message(session_id, role, content)

    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Get messages for session"""
        return self.repository.get_session_messages(session_id)

    def format_conversation_context(self, session_id: str, max_messages: int = settings.MAX_CONTEXT_MESSAGES) -> str:
        """
        Format conversation context for LLM

        Args:
            session_id: Session ID
            max_messages: Maximum messages to include

        Returns:
            Formatted context string
        """
        messages = self.get_session_messages(session_id)

        if not messages:
            return "Không có lịch sử hội thoại."

        # Get recent messages
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages

        context_parts = []
        for msg in recent_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"][:200]  # Limit content length
            context_parts.append(f"{role}: {content}")

        return "\n".join(context_parts)

    def update_session_title_from_first_message(self, session_id: str):
        """Auto-update session title from first user message"""
        session = self.get_session(session_id)
        if not session or not session["messages"]:
            return

        # Check if session has auto-generated title
        if session["title"].startswith("New Chat") or session["title"].startswith("Chat "):
            # Find first user message
            for msg in session["messages"]:
                if msg["role"] == "user":
                    first_message = msg["content"][:50]
                    if len(msg["content"]) > 50:
                        first_message += "..."

                    self.repository.update_session_title(session_id, first_message)
                    logger.info(f"Auto-updated session title: {session_id} -> {first_message}")
                    break

    def delete_session(self, session_id: str):
        """Delete session"""
        self.repository.delete_session(session_id)

    def get_all_sessions(self, user_id: str = None) -> List[Dict]:
        """Get all sessions for a user, or all sessions if no user specified"""
        # Create fresh repository instance to avoid caching issues
        from ..repositories.chat_history_repo import ChatHistoryRepository
        fresh_repo = ChatHistoryRepository()

        if user_id:
            # For MongoDB, get sessions for specific user
            return fresh_repo.get_all_sessions(user_id)
        else:
            # For JSON fallback or when no user specified
            return fresh_repo.get_all_sessions()

    def cleanup_empty_sessions(
        self,
        user_id: Optional[str] = None,
        exclude_session_id: Optional[str] = None
    ) -> int:
        """
        Remove chat sessions without any messages.

        Args:
            user_id: Only clean sessions belonging to this user when provided.
            exclude_session_id: Keep this session even if empty (active chat).

        Returns:
            Number of sessions removed.
        """
        sessions = self.get_all_sessions(user_id)
        empty_session_ids = [
            session["id"]
            for session in sessions
            if not session.get("messages")
            and session["id"] != exclude_session_id
        ]

        for session_id in empty_session_ids:
            logger.info(f"Removing empty chat session: {session_id}")
            self.delete_session(session_id)

        return len(empty_session_ids)

    def get_state(self, session_id: str) -> ConversationState:
        """Get conversation state for a session"""
        session = self.get_session(session_id)
        if not session:
            return ConversationState()
            
        state_data = session.get("metadata", {}).get("state")
        if state_data:
            try:
                return ConversationState(**state_data)
            except Exception:
                return ConversationState()
        return ConversationState()

    def update_state(self, session_id: str, state: ConversationState):
        """Update conversation state for a session"""
        session = self.get_session(session_id)
        if not session:
            return
            
        metadata = session.get("metadata", {})
        metadata["state"] = state.model_dump()
        
        self.repository.update_session_metadata(session_id, metadata)

# Global instance
chat_service = ChatService()
