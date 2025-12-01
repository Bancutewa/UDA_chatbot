"""
Layer 2: Decision (Dialog Management)
Responsible for deciding the next action based on STM and NLU result.
"""
from typing import Dict, Any, Optional
from ...schemas.conversation_state import ConversationState, DialogState
from ...core.logger import logger
from ...core import settings
from ...services.validators import slot_validator

class EstateDecision:
    """Decision Layer for Real Estate"""

    def decide(self, state: ConversationState, nlu_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decide next action based on state and NLU result.
        Output: { "action": "ACTION_NAME", "payload": {...} }
        """
        slots = state.slots
        intent = nlu_result.get("intent", "search_apartment")
        confidence = nlu_result.get("confidence", 1.0)

        # 1. Check Confidence
        if confidence < settings.NLU_CONFIDENCE_THRESHOLD:
            return {
                "action": "ASK_REPHRASE",
                "payload": {}
            }

        # 2. Handle specific intents
        if intent == "show_details":
            if slots.get("ma_can_ho"):
                return {
                    "action": "SHOW_DETAILS",
                    "payload": { "ma_can_ho": slots["ma_can_ho"] }
                }
            else:
                # If missing ID, maybe fallback to search or ask?
                # For now, treat as search if no ID
                pass

        if intent == "book_appointment":
            # Check for required booking info
            if slots.get("ma_can_ho") and slots.get("sdt") and slots.get("thoi_gian"):
                return {
                    "action": "BOOK_APPOINTMENT",
                    "payload": slots
                }
            else:
                # Missing info, ask for it
                missing = []
                if not slots.get("ma_can_ho"): missing.append("ma_can_ho")
                if not slots.get("sdt"): missing.append("sdt")
                if not slots.get("thoi_gian"): missing.append("thoi_gian")
                return {
                    "action": "ASK_SLOT",
                    "payload": { "slot": missing[0] } # Ask for first missing
                }

        # 3. Default: Search Logic
        # Required: du_an OR (gia_ban OR dien_tich OR so_phong_ngu)
        has_criteria = bool(
            slots.get("du_an") or 
            slots.get("gia_ban") or 
            slots.get("dien_tich") or 
            slots.get("so_phong_ngu")
        )
        
        if not has_criteria:
            return {
                "action": "ASK_SLOT",
                "payload": { "slot": "criteria" }
            }

        # 3.5 Validate Slots
        validation_errors = slot_validator.validate_slots(slots)
        if validation_errors:
            return {
                "action": "NO_RESULT", # Or a specific VALIDATION_ERROR action?
                # Let's use NO_RESULT with a specific message for now, or handle in Response
                "payload": {
                    "suggestions": [],
                    "message": " ".join(validation_errors) # Pass error message
                }
            }

        # 4. Ready to Search
        return {
            "action": "SEARCH_LISTINGS",
            "payload": {
                "filters": {
                    "du_an": slots.get("du_an"),
                    "toa": slots.get("toa"),
                    "tang": slots.get("tang"),
                    "gia_ban": slots.get("gia_ban"),
                    "dien_tich": slots.get("dien_tich"),
                    "so_phong_ngu": slots.get("so_phong_ngu"),
                    "so_phong_wc": slots.get("so_phong_wc"),
                    "huong": slots.get("huong"),
                    "noi_that": slots.get("noi_that"),
                    "view": slots.get("view")
                }
            }
        }

# Singleton
estate_decision = EstateDecision()
