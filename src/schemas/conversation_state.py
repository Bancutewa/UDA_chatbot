"""
Conversation State Schema
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum

class DialogState(str, Enum):
    IDLE = "IDLE"
    COLLECTING = "COLLECTING"  # Collecting slots
    PRESENTING = "PRESENTING"  # Showing results
    DETAIL = "DETAIL"          # Showing details
    BOOKED = "BOOKED"          # Appointment booked
    ANSWERED = "ANSWERED"      # RAG question answered

class ConversationState(BaseModel):
    """Short-Term Memory (STM) for the conversation"""
    
    dialog_state: DialogState = Field(default=DialogState.IDLE)
    slots: Dict[str, Any] = Field(default_factory=dict)
    missing_slots: List[str] = Field(default_factory=list)
    last_action: Optional[str] = None
    last_intent: Optional[str] = None
    last_intent_confidence: float = Field(default=1.0)
    episodic_summary: Optional[str] = None
    
    # Context for specific flows
    last_viewed_apartment: Optional[str] = None
    last_search_filters: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True
