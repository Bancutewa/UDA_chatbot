"""
User schemas for authentication
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    SALE = "sale"
    USER = "user"


class UserStatus(str, Enum):
    """User status enumeration"""
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    """Schema for user creation"""
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """Schema for user update"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class UserInDB(UserBase):
    """Schema for user in database"""
    id: str
    hashed_password: str
    status: UserStatus = UserStatus.PENDING
    created_at: datetime
    updated_at: datetime

    # Verification fields
    verification_code: Optional[str] = None
    verification_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """Schema for user response"""
    id: str
    status: UserStatus
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserSession(BaseModel):
    """Schema for user session"""
    user_id: str
    username: str
    role: UserRole
    status: UserStatus
