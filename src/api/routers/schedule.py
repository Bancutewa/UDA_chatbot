from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.services.schedule_service import schedule_service
from src.schemas.user import UserSession, UserRole
from src.api import deps

router = APIRouter()

class ScheduleUpdate(BaseModel):
    status: str
    admin_note: Optional[str] = None

@router.get("/")
async def list_schedules(
    current_user: UserSession = Depends(deps.get_current_user)
) -> Any:
    """
    List schedules. 
    Admins see all. Users see their own.
    """
    if current_user.role == UserRole.ADMIN:
        return schedule_service.list_all()
    else:
        return schedule_service.list_for_user(current_user.user_id)

@router.get("/{schedule_id}")
async def get_schedule(
    schedule_id: str,
    current_user: UserSession = Depends(deps.get_current_user)
) -> Any:
    """
    Get schedule details.
    """
    schedule = schedule_service.get(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    if current_user.role != UserRole.ADMIN and schedule.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return schedule

@router.patch("/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    update: ScheduleUpdate,
    current_user: UserSession = Depends(deps.get_current_user)
) -> Any:
    """
    Update schedule status (Admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
        
    updated = schedule_service.update_status(schedule_id, update.status, update.admin_note)
    if not updated:
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    return updated

@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    current_user: UserSession = Depends(deps.get_current_user)
) -> Any:
    """
    Delete schedule.
    """
    schedule = schedule_service.get(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if current_user.role != UserRole.ADMIN and schedule.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    success = schedule_service.delete(schedule_id)
    if not success:
         raise HTTPException(status_code=500, detail="Failed to delete schedule")
         
    return {"status": "success"}
