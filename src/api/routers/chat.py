from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel

from src.services.chat_service import chat_service
from src.agents.intent_agent import intent_agent
from src.intents.intent_registry import intent_registry
from src.schemas.chat import ChatSessionSchema, MessageSchema
from src.schemas.user import UserSession
from src.api import deps

router = APIRouter()

class CreateSessionRequest(BaseModel):
    title: Optional[str] = None

class SendMessageRequest(BaseModel):
    content: str

class RenameSessionRequest(BaseModel):
    title: str

@router.get("/sessions", response_model=List[dict])
async def get_sessions(
    current_user: UserSession = Depends(deps.get_current_user)
) -> Any:
    """
    Get all sessions for the current user
    """
    return chat_service.get_all_sessions(current_user.user_id)

@router.post("/sessions", response_model=dict)
async def create_session(
    current_user: UserSession = Depends(deps.get_current_user)
) -> Any:
    """
    Create a new chat session
    """
    return chat_service.create_session(current_user.user_id)

@router.get("/sessions/{session_id}", response_model=dict)
async def get_session(
    session_id: str,
    current_user: UserSession = Depends(deps.get_current_user)
) -> Any:
    """
    Get a specific session
    """
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check ownership
    if session.get("user_id") != current_user.user_id:
         raise HTTPException(status_code=403, detail="Not authorized")
         
    return session

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: UserSession = Depends(deps.get_current_user)
) -> Any:
    """
    Delete a session
    """
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.get("user_id") != current_user.user_id:
         raise HTTPException(status_code=403, detail="Not authorized")
         
    chat_service.delete_session(session_id)
    return {"status": "success"}

@router.patch("/sessions/{session_id}")
async def update_session_title(
    session_id: str,
    request: RenameSessionRequest,
    current_user: UserSession = Depends(deps.get_current_user)
) -> Any:
    """
    Rename a session
    """
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.get("user_id") != current_user.user_id:
         raise HTTPException(status_code=403, detail="Not authorized")
         
    chat_service.update_session_title(session_id, request.title)
    return {"status": "success", "title": request.title}

@router.post("/sessions/{session_id}/message")
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    current_user: UserSession = Depends(deps.get_current_user)
) -> Any:
    """
    Send a message to the bot and get a response
    """
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if session.get("user_id") != current_user.user_id:
         raise HTTPException(status_code=403, detail="Not authorized")

    user_input = request.content
    
    # Add user message
    chat_service.add_message(session_id, "user", user_input)

    try:
        # Analyze intent
        context = chat_service.format_conversation_context(session_id)
        intent_result = intent_agent.analyze_intent(user_input, context)

        intent_name = intent_result.get("intent", "general_chat")
        
        # Prepare metadata for intent handler
        intent_metadata = {
            "session_id": session_id,
            "user_session": current_user.dict()
        }
        intent_result.setdefault("message", user_input)
        intent_result["metadata"] = intent_metadata

        intent_handler = intent_registry.get_intent_instance(intent_name)
        
        if intent_handler:
            bot_response = intent_handler.get_response(intent_result, context)
        else:
            bot_response = f"❌ Không tìm thấy handler cho intent: {intent_name}"
            # Fallback
            intent_name = "general_chat"

        # Handle special responses (like audio) - keeping it simple for API for now, 
        # just returning the text response or whatever get_response returns.
        # If get_response returns rich content (HTML/Markdown), the frontend will handle it.
        
        # Save assistant response
        history_response = bot_response
        if intent_name == "generate_audio" and hasattr(intent_handler, 'get_history_response'):
             history_response = intent_handler.get_history_response() or bot_response
             
        chat_service.add_message(session_id, "assistant", history_response)

        # Auto-update title
        if len(session["messages"]) == 2:
            chat_service.update_session_title_from_first_message(session_id)
            
        return {
            "response": bot_response,
            "intent": intent_name
        }

    except Exception as e:
        chat_service.add_message(session_id, "assistant", f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
