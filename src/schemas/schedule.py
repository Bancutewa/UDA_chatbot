"""
Pydantic schemas for visit schedules.
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ScheduleStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class ScheduleCreate(BaseModel):
    district: str = Field(default="Quận 7")
    property_type: Optional[str] = Field(default="bất động sản")
    requested_time: datetime
    notes: Optional[str] = None
    source_time_text: Optional[str] = None


class ScheduleResponse(ScheduleCreate):
    id: str
    status: ScheduleStatus = ScheduleStatus.PENDING
    user_id: Optional[str]
    user_name: str
    created_at: datetime
    updated_at: datetime
    raw_message: Optional[str]
    session_id: Optional[str]

