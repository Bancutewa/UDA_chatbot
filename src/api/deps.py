from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError

from src.core.config import config
from src.services.auth_service import auth_service
from src.schemas.user import TokenPayload, UserSession

# OAuth2 scheme
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)

def get_current_user(
    token: str = Depends(reusable_oauth2)
) -> UserSession:
    """
    Get current user from token
    """
    try:
        return auth_service.get_current_user(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
