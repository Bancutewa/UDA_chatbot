"""
Chat-related schemas
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class MessageSchema(BaseModel):
    """Schema for chat messages"""
    role: str = Field(..., description="Role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class ChatSessionSchema(BaseModel):
    """Schema for chat sessions"""
    id: str = Field(..., description="Session ID")
    title: str = Field(..., description="Session title")
    messages: List[MessageSchema] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class IntentAnalysisSchema(BaseModel):
    """Schema for intent analysis results"""
    intent: str = Field(..., description="Detected intent")
    message: Optional[str] = Field(None, description="Chat message")
    description: Optional[str] = Field(None, description="Image/audio description")
    query: Optional[str] = Field(None, description="BDS query")
