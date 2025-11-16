"""
User repository for MongoDB operations
"""
from datetime import datetime
from typing import Optional, List
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from ..core.config import config
from ..core.logger import logger
from ..core.exceptions import DatabaseConnectionError, ValidationError
from ..schemas.user import UserCreate, UserUpdate, UserInDB, UserResponse


class UserRepository:
    """Repository for user operations"""

    def __init__(self):
        try:
            self.collection: Collection = config.mongodb_client[config.DATABASE_NAME]["users"]
            self._create_indexes()
            logger.info("User repository initialized")
        except Exception as e:
            logger.error(f"Failed to initialize user repository: {e}")
            raise DatabaseConnectionError(f"Failed to connect to user repository: {e}")

    def _create_indexes(self):
        """Create database indexes"""
        try:
            # Unique index on username
            self.collection.create_index("username", unique=True)
            # Unique index on email
            self.collection.create_index("email", unique=True)
            # Index on created_at for sorting
            self.collection.create_index("created_at")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")

    def create_user(self, user_data: UserCreate, hashed_password: str) -> UserInDB:
        """Create a new user"""
        try:
            now = datetime.utcnow()
            user_doc = {
                "username": user_data.username,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "hashed_password": hashed_password,
                "role": user_data.role.value,
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }

            result = self.collection.insert_one(user_doc)
            user_doc["id"] = str(result.inserted_id)

            return UserInDB(**user_doc)

        except DuplicateKeyError as e:
            if "username" in str(e):
                raise ValidationError("Username already exists")
            elif "email" in str(e):
                raise ValidationError("Email already exists")
            else:
                raise ValidationError("User already exists")
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise DatabaseConnectionError(f"Failed to create user: {e}")

    def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """Get user by username"""
        try:
            user_doc = self.collection.find_one({"username": username})
            if user_doc:
                user_doc["id"] = str(user_doc["_id"])
                return UserInDB(**user_doc)
            return None
        except Exception as e:
            logger.error(f"Failed to get user by username: {e}")
            raise DatabaseConnectionError(f"Failed to get user: {e}")

    def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID"""
        try:
            from bson import ObjectId
            user_doc = self.collection.find_one({"_id": ObjectId(user_id)})
            if user_doc:
                user_doc["id"] = str(user_doc["_id"])
                return UserInDB(**user_doc)
            return None
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            raise DatabaseConnectionError(f"Failed to get user: {e}")

    def update_user(self, user_id: str, update_data: UserUpdate) -> Optional[UserInDB]:
        """Update user information"""
        try:
            from bson import ObjectId
            update_dict = update_data.dict(exclude_unset=True)
            if update_dict:
                update_dict["updated_at"] = datetime.utcnow()
                if "role" in update_dict and hasattr(update_dict["role"], "value"):
                    update_dict["role"] = update_dict["role"].value

                result = self.collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {"$set": update_dict}
                )

                if result.modified_count > 0:
                    return self.get_user_by_id(user_id)

            return None
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            raise DatabaseConnectionError(f"Failed to update user: {e}")

    def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        try:
            from bson import ObjectId
            result = self.collection.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            raise DatabaseConnectionError(f"Failed to delete user: {e}")

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """Get all users with pagination"""
        try:
            users = []
            cursor = self.collection.find(
                {},
                {"hashed_password": 0}  # Exclude password from response
            ).skip(skip).limit(limit).sort("created_at", -1)

            for user_doc in cursor:
                user_doc["id"] = str(user_doc["_id"])
                users.append(UserResponse(**user_doc))

            return users
        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            raise DatabaseConnectionError(f"Failed to get users: {e}")

    def count_users(self) -> int:
        """Count total users"""
        try:
            return self.collection.count_documents({})
        except Exception as e:
            logger.error(f"Failed to count users: {e}")
            return 0

    def is_available(self) -> bool:
        """Check if repository is available"""
        try:
            self.collection.database.command("ping")
            return True
        except Exception:
            return False
