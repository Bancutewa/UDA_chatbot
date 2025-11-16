"""
Chat History Repository - Unified interface for chat sessions (MongoDB/JSON)
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

from ..core.config import config
from ..core.logger import logger
from ..core.exceptions import DatabaseConnectionError

# Import MongoDB repo if available
try:
    from .mongodb_repository import mongodb_repo
    MONGODB_AVAILABLE = mongodb_repo is not None and mongodb_repo.is_available()
except ImportError:
    mongodb_repo = None
    MONGODB_AVAILABLE = False

class ChatHistoryRepository:
    """Repository for chat history with MongoDB/JSON fallback"""

    def __init__(self):
        self.file_path = config.CHAT_SESSIONS_FILE
        self.use_mongodb = MONGODB_AVAILABLE

        if self.use_mongodb:
            logger.info("Using MongoDB for chat history storage")
            self.mongo_repo = mongodb_repo
        else:
            logger.info("Using JSON file for chat history storage (MongoDB not available)")

    def _load_sessions(self) -> Dict[str, Dict]:
        """Load sessions from JSON file"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load chat sessions: {e}")
        return {}

    def _save_sessions(self, sessions: Dict[str, Dict]):
        """Save sessions to JSON file"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save chat sessions: {e}")
            raise DatabaseConnectionError(f"Save failed: {e}")

    def create_session(self, session_id: str, title: str = "New Chat") -> Dict:
        """Create a new chat session"""
        if self.use_mongodb:
            return self.mongo_repo.create_session(session_id, title)
        else:
            # JSON fallback
            sessions = self._load_sessions()
            session = {
                "id": session_id,
                "title": title,
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            sessions[session_id] = session
            self._save_sessions(sessions)
            logger.info(f"Created new chat session (JSON): {session_id}")
            return session

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        if self.use_mongodb:
            return self.mongo_repo.get_session(session_id)
        else:
            # JSON fallback
            sessions = self._load_sessions()
            return sessions.get(session_id)

    def update_session_title(self, session_id: str, title: str):
        """Update session title"""
        if self.use_mongodb:
            self.mongo_repo.update_session_title(session_id, title)
        else:
            # JSON fallback
            sessions = self._load_sessions()
            if session_id in sessions:
                sessions[session_id]["title"] = title
                sessions[session_id]["updated_at"] = datetime.now().isoformat()
                self._save_sessions(sessions)
                logger.info(f"Updated session title (JSON): {session_id} -> {title}")

    def add_message(self, session_id: str, role: str, content: str):
        """Add message to session"""
        if self.use_mongodb:
            self.mongo_repo.add_message(session_id, role, content)
        else:
            # JSON fallback
            sessions = self._load_sessions()
            if session_id in sessions:
                message = {
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                }
                sessions[session_id]["messages"].append(message)
                sessions[session_id]["updated_at"] = datetime.now().isoformat()
                self._save_sessions(sessions)

    def delete_session(self, session_id: str):
        """Delete session"""
        if self.use_mongodb:
            self.mongo_repo.delete_session(session_id)
        else:
            # JSON fallback
            sessions = self._load_sessions()
            if session_id in sessions:
                del sessions[session_id]
                self._save_sessions(sessions)
                logger.info(f"Deleted session (JSON): {session_id}")

    def get_all_sessions(self) -> List[Dict]:
        """Get all sessions sorted by updated_at"""
        if self.use_mongodb:
            return self.mongo_repo.get_all_sessions()
        else:
            # JSON fallback
            sessions = self._load_sessions()
            session_list = list(sessions.values())
            session_list.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return session_list

    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Get messages for a specific session"""
        if self.use_mongodb:
            return self.mongo_repo.get_session_messages(session_id)
        else:
            # JSON fallback
            session = self.get_session(session_id)
            return session["messages"] if session else []

# Global instance
chat_history_repo = ChatHistoryRepository()
