"""
Estate Query Intent - Main Orchestrator
Integrates Understanding, Decision, and Response layers.
"""
from typing import Dict, Any, Optional, List
from .base_intent import BaseIntent
from ..services.chat_service import chat_service
from .estate.understanding import estate_understanding
from .estate.decision import estate_decision
from .estate.response import estate_response
from ..core.logger import logger

class EstateQueryIntent(BaseIntent):
    """Intent handler for Real Estate Queries (3-Layer Architecture)"""

    @property
    def intent_name(self) -> str:
        return "estate_query"

    @property
    def description(self) -> str:
        return "Người dùng muốn tìm kiếm, hỏi thông tin về bất động sản (nhà, đất, căn hộ). Từ khóa: tìm nhà , căn hộ, phòng, mua bán, giá, khu vực, dự án."

    @property
    def keywords(self) -> List[str]:
        return ["nhà", "đất", "căn hộ", "chung cư", "biệt thự", "bất động sản", "mua", "bán", "thuê", "giá"]

    @property
    def system_prompt(self) -> str:
        return "Bạn là trợ lý bất động sản thông minh. Nhiệm vụ của bạn là giúp người dùng tìm kiếm thông tin về bất động sản."

    def get_response(self, data: Dict[str, Any], context: Optional[str] = None) -> str:
        """
        Orchestrate the 3 layers:
        1. Load State
        2. Understanding (NLU) -> Update State
        3. Decision (Dialog Policy) -> Action
        4. Response (NLG) -> Output
        5. Save State
        """
        try:
            # Get session ID from metadata
            metadata = data.get("metadata", {})
            session_id = metadata.get("session_id")
            message = data.get("message", "") or data.get("query", "")

            if not session_id:
                logger.warning("No session_id provided for EstateQueryIntent")
                return "Xin lỗi, đã có lỗi xảy ra (thiếu session ID)."

            # 1. Load State
            current_state = chat_service.get_state(session_id)
            logger.info(f"Loaded state: {current_state}")

            # 2. Understanding (NLU)
            updated_state = estate_understanding.process(message, current_state)
            
            # 3. Decision
            action_plan = estate_decision.decide(updated_state)
            logger.info(f"Decision: {action_plan}")
            
            # Update state with last action
            updated_state.last_action = action_plan.get("action")
            
            # 4. Response (NLG)
            response_text = estate_response.execute(action_plan)
            
            # 5. Save State
            chat_service.update_state(session_id, updated_state)
            
            return response_text

        except Exception as e:
            logger.error(f"Error in EstateQueryIntent: {e}", exc_info=True)
            return "Xin lỗi, hệ thống đang gặp sự cố khi xử lý yêu cầu tìm kiếm của bạn."
