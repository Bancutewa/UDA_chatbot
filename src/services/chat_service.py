"""
Chat Service - Handle chat logic and context formatting
"""
from typing import List, Dict, Optional

from ..repositories.chat_history_repo import chat_history_repo
from ..core.logger import logger

class ChatService:
    """Service for chat operations"""

    def __init__(self):
        self.repo = chat_history_repo

    def create_session(self, title: str = "New Chat") -> Dict:
        """Create new chat session"""
        import uuid
        session_id = str(uuid.uuid4())
        return self.repo.create_session(session_id, title)

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        return self.repo.get_session(session_id)

    def add_message(self, session_id: str, role: str, content: str):
        """Add message to session"""
        self.repo.add_message(session_id, role, content)

    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Get messages for session"""
        return self.repo.get_session_messages(session_id)

    def format_conversation_context(self, session_id: str, max_messages: int = 5) -> str:
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

                    self.repo.update_session_title(session_id, first_message)
                    logger.info(f"Auto-updated session title: {session_id} -> {first_message}")
                    break

    def delete_session(self, session_id: str):
        """Delete session"""
        self.repo.delete_session(session_id)

    def get_all_sessions(self) -> List[Dict]:
        """Get all sessions"""
        return self.repo.get_all_sessions()

# Global instance
chat_service = ChatService()
