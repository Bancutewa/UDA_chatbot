from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional

from src.agents.intent_agent import intent_agent
from src.services.chat_service import chat_service # For context if needed, though NLU might be stateless

router = APIRouter()

class NLURequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = {}

class NLUResponse(BaseModel):
    intent: str
    confidence: float = 1.0 # Placeholder as current agent might not return confidence
    entities: Dict[str, Any] = {}
    original_message: str

@router.post("/analyze", response_model=NLUResponse)
async def analyze_intent(request: NLURequest):
    """
    Analyze the intent of a message
    """
    try:
        # We can use the intent_agent to analyze
        # Note: intent_agent.analyze_intent requires (message, context)
        intent_result = intent_agent.analyze_intent(request.message, request.context)
        
        # The result is typically a dict with 'intent', 'message', etc.
        intent_name = intent_result.get("intent", "general_chat")
        
        return {
            "intent": intent_name,
            "original_message": request.message,
            "entities": intent_result, # Return full result as entities/metadata
            "confidence": 1.0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
