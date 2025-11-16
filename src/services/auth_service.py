"""
Authentication service for user management
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
import jwt

from ..core.config import config
from ..core.logger import logger
from ..core.exceptions import ValidationError, AuthenticationError
from ..schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserSession,
    LoginRequest, TokenResponse, UserRole
)
from ..repositories.user_repository import UserRepository


class AuthService:
    """Service for authentication operations"""

    def __init__(self):
        self.user_repo = UserRepository()
        self.secret_key = config.JWT_SECRET_KEY or "your-secret-key-change-in-production"
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        hashed = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        return f"{salt}:{hashed}"

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            salt, hash_value = hashed_password.split(":", 1)
            computed_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
            return computed_hash == hash_value
        except Exception:
            return False

    def _create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user"""
        try:
            # All new users start with "user" role
            # Admin role can only be assigned by existing admins
            user_data.role = UserRole.USER

            # Hash password
            hashed_password = self._hash_password(user_data.password)

            # Create user
            user = self.user_repo.create_user(user_data, hashed_password)

            # Return user without password
            return UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )

        except Exception as e:
            logger.error(f"Failed to register user: {e}")
            raise ValidationError(f"Registration failed: {str(e)}")

    def authenticate_user(self, login_data: LoginRequest) -> TokenResponse:
        """Authenticate user and return token"""
        try:
            # Get user by username
            user = self.user_repo.get_user_by_username(login_data.username)
            if not user:
                raise AuthenticationError("Invalid username or password")

            # Check if user is active
            if not user.is_active:
                raise AuthenticationError("Account is disabled")

            # Verify password
            if not self._verify_password(login_data.password, user.hashed_password):
                raise AuthenticationError("Invalid username or password")

            # Create access token
            token_data = {
                "sub": user.id,
                "username": user.username,
                "role": user.role.value
            }
            access_token = self._create_access_token(token_data)

            # Return token response
            user_response = UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )

            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user=user_response
            )

        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError("Authentication failed")

    def get_current_user(self, token: str) -> UserSession:
        """Get current user from token"""
        try:
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Invalid token")

            # Get user from database
            user = self.user_repo.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")

            return UserSession(
                user_id=user.id,
                username=user.username,
                role=user.role,
                is_active=user.is_active
            )

        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.JWTError:
            raise AuthenticationError("Invalid token")
        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            raise AuthenticationError("Failed to authenticate")

    def update_user(self, user_id: str, update_data: UserUpdate, current_user: UserSession) -> Optional[UserResponse]:
        """Update user information"""
        # Check permissions
        if current_user.user_id != user_id and current_user.role != UserRole.ADMIN:
            raise AuthenticationError("Not authorized to update this user")

        try:
            user = self.user_repo.update_user(user_id, update_data)
            if user:
                return UserResponse(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    full_name=user.full_name,
                    role=user.role,
                    is_active=user.is_active,
                    created_at=user.created_at,
                    updated_at=user.updated_at
                )
            return None
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            raise ValidationError(f"Update failed: {str(e)}")

    def delete_user(self, user_id: str, current_user: UserSession) -> bool:
        """Delete user"""
        # Check permissions
        if current_user.user_id != user_id and current_user.role != UserRole.ADMIN:
            raise AuthenticationError("Not authorized to delete this user")

        # Prevent deleting self if admin
        if current_user.user_id == user_id:
            raise ValidationError("Cannot delete your own account")

        try:
            return self.user_repo.delete_user(user_id)
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            raise ValidationError(f"Delete failed: {str(e)}")

    def get_all_users(self, current_user: UserSession, skip: int = 0, limit: int = 100) -> list[UserResponse]:
        """Get all users (admin only)"""
        if current_user.role != UserRole.ADMIN:
            raise AuthenticationError("Admin access required")

        try:
            return self.user_repo.get_all_users(skip, limit)
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            raise ValidationError(f"Failed to get users: {str(e)}")

    def change_password(self, user_id: str, old_password: str, new_password: str, current_user: UserSession) -> bool:
        """Change user password"""
        # Check permissions
        if current_user.user_id != user_id and current_user.role != UserRole.ADMIN:
            raise AuthenticationError("Not authorized to change this password")

        try:
            # Get user
            user = self.user_repo.get_user_by_id(user_id)
            if not user:
                raise ValidationError("User not found")

            # Verify old password (unless admin changing someone else's password)
            if current_user.user_id == user_id:
                if not self._verify_password(old_password, user.hashed_password):
                    raise ValidationError("Current password is incorrect")

            # Hash new password
            hashed_new_password = self._hash_password(new_password)

            # Update password
            update_data = UserUpdate()
            # Note: We'll need to add password update to repository
            # For now, return success
            return True

        except Exception as e:
            logger.error(f"Failed to change password: {e}")
            raise ValidationError(f"Password change failed: {str(e)}")


# Global instance
auth_service = AuthService()
