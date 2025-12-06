from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any

from src.services.auth_service import auth_service
from src.schemas.user import (
    UserCreate,
    UserResponse,
    TokenResponse,
    LoginRequest,
    UserSession,
    UserUpdate
)
from src.api import deps

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    try:
        # OAuth2PasswordRequestForm has username and password fields
        login_data = LoginRequest(
            username=form_data.username, 
            password=form_data.password
        )
        return auth_service.authenticate_user(login_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate
) -> Any:
    """
    Create new user
    """
    try:
        user = auth_service.register_user(user_in)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.get("/me", response_model=UserSession)
async def read_users_me(
    current_user: UserSession = Depends(deps.get_current_user),
) -> Any:
    """
    Get current user
    """
    return current_user

# Example of another endpoint using the dependency
@router.put("/me", response_model=UserResponse)
async def update_user_me(
    user_in: UserUpdate,
    current_user: UserSession = Depends(deps.get_current_user)
) -> Any:
    """
    Update own user
    """
    try:
        user = auth_service.update_user(current_user.user_id, user_in, current_user)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
         raise HTTPException(status_code=400, detail=str(e))
