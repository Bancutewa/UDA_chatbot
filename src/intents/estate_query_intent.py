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
            updated_state, nlu_result = estate_understanding.process(message, current_state)
            
            # 3. Decision
            action_plan = estate_decision.decide(updated_state, nlu_result)
            logger.info(f"Decision: {action_plan}")
            
            # Update state with last action
            updated_state.last_action = action_plan.get("action")
            
            # 4. Response (NLG)
            response_data = estate_response.execute(action_plan, updated_state)
            
            # 5. Update STM from response
            if "session_update" in response_data:
                for key, value in response_data["session_update"].items():
                    if hasattr(updated_state, key):
                        setattr(updated_state, key, value)

            # Save State
            chat_service.update_state(session_id, updated_state)
            
            # 6. Format for UI
            return self._format_response_for_ui(response_data)

        except Exception as e:
            logger.error(f"Error in EstateQueryIntent: {e}", exc_info=True)
            return "Xin lỗi, hệ thống đang gặp sự cố khi xử lý yêu cầu tìm kiếm của bạn."

    def _format_response_for_ui(self, response_data: Dict[str, Any]) -> str:
        """Convert structured response to markdown for Streamlit"""
        messages = response_data.get("messages", [])
        apartments = response_data.get("apartments", [])
        
        output_parts = []
        
        # Add text messages
        for msg in messages:
            output_parts.append(msg.get("content", ""))
            
        # Add apartment cards if any
        if apartments:
            output_parts.append("\n\n---\n\n**Kết quả tìm kiếm:**\n")
            for i, apt in enumerate(apartments, 1):
                card = self._format_apartment_card(apt, i)
                output_parts.append(card)
                
        return "\n".join(output_parts)

    def _format_apartment_card(self, apt: Dict[str, Any], index: int) -> str:
        """Format single apartment data as markdown card"""
        du_an = apt.get("du_an", "Căn hộ")
        toa = apt.get("toa", "")
        tang = apt.get("tang", "")
        ma_can = apt.get("ma_can", "")
        
        title = f"**{index}. {du_an}**"
        if toa: title += f" - Tòa {toa}"
        if tang: title += f" - Tầng {tang}"
        if ma_can: title += f" ({ma_can})"
        
        details = []
        if ma_can: details.append(f"🆔 Mã căn: `{ma_can}`")
        if apt.get("dien_tich"): details.append(f"📐 Diện tích: {apt['dien_tich']}m²")
        if apt.get("so_phong_ngu"): details.append(f"🛏️ PN: {apt['so_phong_ngu']}")
        if apt.get("huong"): details.append(f"🧭 Hướng: {apt['huong']}")
        if apt.get("gia_ban"): 
            gia = f"{apt['gia_ban']:,} VND".replace(",", ".")
            details.append(f"💰 Giá: {gia}")
        
        return f"{title}\n" + " | ".join(details) + "\n"

# Singleton
estate_query_intent = EstateQueryIntent()
