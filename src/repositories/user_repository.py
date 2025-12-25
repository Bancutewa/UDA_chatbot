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
from ..schemas.user import UserCreate, UserUpdate, UserInDB, UserResponse, UserStatus


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

    def create_user(self, user_data: UserCreate, hashed_password: str, verification_code: Optional[str] = None, verification_expires_at: Optional[datetime] = None) -> UserInDB:
        """Create a new user"""
        try:
            now = datetime.utcnow()
            user_doc = {
                "username": user_data.username,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "hashed_password": hashed_password,
                "role": user_data.role.value,
                "status": UserStatus.PENDING.value,
                "created_at": now,
                "updated_at": now
            }
            
            if verification_code:
                user_doc["verification_code"] = verification_code
            if verification_expires_at:
                user_doc["verification_expires_at"] = verification_expires_at

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
            # Support both real MongoDB ObjectId and non-persistent/guest IDs
            # Guest / temporary users (e.g. "guest_0123456789") are not stored in MongoDB,
            # so ObjectId(...) would raise an error. In that case we simply return None.
            if not ObjectId.is_valid(user_id):
                logger.warning(f"get_user_by_id called with non-ObjectId value: {user_id}")
                return None

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

    def update_verification_info(self, user_id: str, verification_code: str, expires_at: datetime) -> bool:
        """Update user verification info"""
        try:
            from bson import ObjectId
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {
                    "verification_code": verification_code,
                    "verification_expires_at": expires_at,
                    "updated_at": datetime.utcnow()
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update verification info: {e}")
            raise DatabaseConnectionError(f"Failed to update verification info: {e}")

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
                
                # Handle missing fields for backward compatibility
                # Ensure status field exists (default to ACTIVE if missing)
                if "status" not in user_doc or not user_doc["status"]:
                    user_doc["status"] = UserStatus.ACTIVE.value
                elif isinstance(user_doc["status"], str):
                    # Already a string, keep it
                    pass
                else:
                    # Convert enum to string if needed
                    user_doc["status"] = user_doc["status"].value if hasattr(user_doc["status"], "value") else str(user_doc["status"])
                
                # Ensure role field exists (default to USER if missing)
                if "role" not in user_doc or not user_doc["role"]:
                    user_doc["role"] = "user"
                elif isinstance(user_doc["role"], str):
                    # Already a string, keep it
                    pass
                else:
                    # Convert enum to string if needed
                    user_doc["role"] = user_doc["role"].value if hasattr(user_doc["role"], "value") else str(user_doc["role"])
                
                # Ensure created_at and updated_at exist
                if "created_at" not in user_doc:
                    user_doc["created_at"] = datetime.utcnow()
                if "updated_at" not in user_doc:
                    user_doc["updated_at"] = datetime.utcnow()
                
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

    def get_users_by_role(self, role: str) -> List[UserResponse]:
        """Get users by role (e.g., get all Sale users)"""
        try:
            users = []
            cursor = self.collection.find(
                {"role": role},
                {"hashed_password": 0}  # Exclude password from response
            ).sort("created_at", -1)

            for user_doc in cursor:
                user_doc["id"] = str(user_doc["_id"])
                
                # Handle missing fields for backward compatibility
                if "status" not in user_doc or not user_doc["status"]:
                    user_doc["status"] = UserStatus.ACTIVE.value
                elif isinstance(user_doc["status"], str):
                    pass
                else:
                    user_doc["status"] = user_doc["status"].value if hasattr(user_doc["status"], "value") else str(user_doc["status"])
                
                if "role" not in user_doc or not user_doc["role"]:
                    user_doc["role"] = "user"
                elif isinstance(user_doc["role"], str):
                    pass
                else:
                    user_doc["role"] = user_doc["role"].value if hasattr(user_doc["role"], "value") else str(user_doc["role"])
                
                if "created_at" not in user_doc:
                    user_doc["created_at"] = datetime.utcnow()
                if "updated_at" not in user_doc:
                    user_doc["updated_at"] = datetime.utcnow()
                
                users.append(UserResponse(**user_doc))

            return users
        except Exception as e:
            logger.error(f"Failed to get users by role: {e}")
            raise DatabaseConnectionError(f"Failed to get users by role: {e}")

    def is_available(self) -> bool:
        """Check if repository is available"""
        try:
            self.collection.database.command("ping")
            return True
        except Exception:
            return False
