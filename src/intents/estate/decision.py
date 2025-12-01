"""
Layer 2: Decision (Dialog Management)
Responsible for deciding the next action based on STM.
"""
from typing import Dict, Any, List
from ...schemas.conversation_state import ConversationState, DialogState
from ...core.logger import logger

class EstateDecision:
    """Decision Layer for Real Estate"""

    def decide(self, state: ConversationState) -> Dict[str, Any]:
        """
        Decide next action based on state.
        Output: { "action": "ACTION_NAME", "payload": {...} }
        """
        slots = state.slots
        
        # 1. Check for required slots for SEARCH
        # Required: (du_an) OR (gia_ban OR dien_tich OR so_phong_ngu)
        # We want at least ONE criteria to search.
        has_criteria = bool(
            slots.get("du_an") or 
            slots.get("gia_ban") or 
            slots.get("dien_tich") or 
            slots.get("so_phong_ngu")
        )
        
        if not has_criteria:
            return {
                "action": "ASK_SLOT",
                "payload": { "slot": "criteria" } # Generic ask
            }

        # 2. Ready to Search
        return {
            "action": "SEARCH_LISTINGS",
            "payload": {
                "filters": {
                    "du_an": slots.get("du_an"),
                    "gia_ban": slots.get("gia_ban"),
                    "dien_tich": slots.get("dien_tich"),
                    "so_phong_ngu": slots.get("so_phong_ngu")
                }
            }
        }

# Singleton
estate_decision = EstateDecision()
