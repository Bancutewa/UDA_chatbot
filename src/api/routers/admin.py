from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Body

from src.services.auth_service import auth_service
from src.schemas.user import UserSession, UserRole, UserResponse
from src.api import deps

router = APIRouter()

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserSession = Depends(deps.get_current_user)
) -> Any:
    """
    Get all users (Admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
        
    return auth_service.get_all_users(current_user, skip, limit)

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: UserSession = Depends(deps.get_current_user)
) -> Any:
    """
    Delete a user (Admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
        
    success = auth_service.delete_user(user_id, current_user)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete user")
        
    return {"status": "success", "message": "User deleted"}
