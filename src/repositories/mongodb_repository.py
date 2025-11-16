"""
MongoDB Repository - MongoDB database layer for chat sessions
"""
import os
from typing import Dict, List, Optional
from datetime import datetime

try:
    from pymongo import MongoClient, errors
    from pymongo.collection import Collection
    from pymongo.database import Database
    MONGODB_AVAILABLE = True
except ImportError:
    MongoClient = None
    MONGODB_AVAILABLE = False

from ..core.config import config
from ..core.logger import logger
from ..core.exceptions import DatabaseConnectionError

class MongoDBRepository:
    """Repository for chat history using MongoDB"""

    def __init__(self):
        if not MONGODB_AVAILABLE:
            raise ImportError("pymongo not installed. Run: pip install pymongo")

        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.collection: Optional[Collection] = None

        self._connect()

    def _connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(config.MONGODB_URL, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[config.DATABASE_NAME]
            self.collection = self.db['chat_sessions']

            # Create indexes
            self.collection.create_index([("updated_at", -1)])
            self.collection.create_index([("user_id", 1)])

            logger.info(f"MongoDB repository connected to {config.MONGODB_URL}")

        except errors.ServerSelectionTimeoutError as e:
            logger.error(f"MongoDB connection timeout: {e}")
            raise DatabaseConnectionError(f"MongoDB connection failed: {e}")
        except errors.ConfigurationError as e:
            logger.error(f"MongoDB configuration error: {e}")
            raise DatabaseConnectionError(f"MongoDB config error: {e}")
        except Exception as e:
            logger.error(f"MongoDB connection error: {e}")
            raise DatabaseConnectionError(f"MongoDB error: {e}")

    def is_available(self) -> bool:
        """Check if MongoDB is available"""
        return self.client is not None and MONGODB_AVAILABLE

    def create_session(self, session_id: str, title: str = "New Chat", user_id: str = "default") -> Dict:
        """Create a new chat session"""
        session = {
            "_id": session_id,
            "user_id": user_id,
            "title": title,
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        try:
            self.collection.insert_one(session)
            logger.info(f"Created MongoDB chat session: {session_id}")
            return self._format_session(session)
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise DatabaseConnectionError(f"Create session failed: {e}")

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        try:
            session = self.collection.find_one({"_id": session_id})
            return self._format_session(session) if session else None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    def update_session_title(self, session_id: str, title: str):
        """Update session title"""
        try:
            result = self.collection.update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "title": title,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            if result.modified_count > 0:
                logger.info(f"Updated session title: {session_id} -> {title}")
            else:
                logger.warning(f"Session not found for update: {session_id}")
        except Exception as e:
            logger.error(f"Failed to update session title: {e}")
            raise DatabaseConnectionError(f"Update title failed: {e}")

    def add_message(self, session_id: str, role: str, content: str):
        """Add message to session"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        }

        try:
            result = self.collection.update_one(
                {"_id": session_id},
                {
                    "$push": {"messages": message},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            if result.modified_count > 0:
                logger.debug(f"Added message to session: {session_id}")
            else:
                logger.warning(f"Session not found for message: {session_id}")
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
            raise DatabaseConnectionError(f"Add message failed: {e}")

    def delete_session(self, session_id: str):
        """Delete session"""
        try:
            result = self.collection.delete_one({"_id": session_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted session: {session_id}")
            else:
                logger.warning(f"Session not found for deletion: {session_id}")
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            raise DatabaseConnectionError(f"Delete session failed: {e}")

    def get_all_sessions(self, user_id: str = "default") -> List[Dict]:
        """Get all sessions for a user, sorted by updated_at"""
        try:
            sessions = list(self.collection.find(
                {"user_id": user_id}
            ).sort("updated_at", -1))

            return [self._format_session(session) for session in sessions]
        except Exception as e:
            logger.error(f"Failed to get all sessions: {e}")
            return []

    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Get messages for a specific session"""
        session = self.get_session(session_id)
        return session["messages"] if session else []

    def migrate_from_json(self, json_file_path: str = None):
        """Migrate data from JSON file to MongoDB"""
        if not json_file_path:
            json_file_path = config.CHAT_SESSIONS_FILE

        if not os.path.exists(json_file_path):
            logger.info("No JSON file to migrate")
            return

        try:
            import json
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_sessions = json.load(f)

            migrated_count = 0
            for session_id, session_data in json_sessions.items():
                # Convert JSON format to MongoDB format
                mongo_session = {
                    "_id": session_id,
                    "user_id": "default",  # Default user for migration
                    "title": session_data.get("title", "Migrated Chat"),
                    "messages": session_data.get("messages", []),
                    "created_at": datetime.fromisoformat(session_data.get("created_at", datetime.utcnow().isoformat())),
                    "updated_at": datetime.fromisoformat(session_data.get("updated_at", datetime.utcnow().isoformat()))
                }

                try:
                    self.collection.insert_one(mongo_session)
                    migrated_count += 1
                except errors.DuplicateKeyError:
                    logger.warning(f"Session {session_id} already exists, skipping")
                except Exception as e:
                    logger.error(f"Failed to migrate session {session_id}: {e}")

            logger.info(f"Migrated {migrated_count} sessions from JSON to MongoDB")

            # Backup original file
            backup_file = f"{json_file_path}.backup"
            os.rename(json_file_path, backup_file)
            logger.info(f"Original JSON file backed up to: {backup_file}")

        except Exception as e:
            logger.error(f"Migration failed: {e}")

    def _format_session(self, mongo_session: Dict) -> Dict:
        """Format MongoDB session to application format"""
        if not mongo_session:
            return None

        return {
            "id": mongo_session["_id"],
            "user_id": mongo_session.get("user_id", "default"),
            "title": mongo_session.get("title", "Untitled"),
            "messages": mongo_session.get("messages", []),
            "created_at": mongo_session.get("created_at"),
            "updated_at": mongo_session.get("updated_at")
        }

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global instance (only create if MongoDB is configured)
mongodb_repo = None
if config.USE_MONGODB:
    try:
        mongodb_repo = MongoDBRepository()
    except Exception as e:
        logger.warning(f"MongoDB initialization failed: {e}. Falling back to JSON storage.")
        mongodb_repo = None
