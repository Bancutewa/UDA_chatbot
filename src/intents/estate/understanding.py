"""
Layer 1: Understanding (NLU)
Responsible for extracting slots and updating STM.
"""
from typing import Dict, Any, List, Optional
import json
from ...agents.llm_agent import llm_agent
from ...schemas.conversation_state import ConversationState
from ...core.logger import logger

class EstateUnderstanding:
    """NLU Layer for Real Estate"""

    def __init__(self):
        self.agent = llm_agent.create_agent(
            name="Estate NLU",
            instructions=[
                "Bạn là chuyên gia NLU bất động sản.",
                "Nhiệm vụ: Trích xuất thông tin (slots) từ câu nói người dùng.",
                "Các slots cần quan tâm:",
                "- du_an: Tên dự án (VD: Sky89, River Panorama)",
                "- gia_ban: Giá bán (VD: {min: 2 tỷ, max: 3 tỷ})",
                "- dien_tich: Diện tích (VD: {min: 70, max: 80})",
                "- so_phong_ngu: Số phòng ngủ (VD: {min: 2, max: 3})",
                "Luôn trả về JSON hợp lệ. Nếu không có thông tin, trả về null hoặc bỏ qua field đó."
            ],
            description="NLU Agent for Estate",
            markdown=False
        )

    def process(self, message: str, current_state: ConversationState) -> ConversationState:
        """
        Process user message and update state.
        1. Extract slots from message.
        2. Merge with current slots (Newest Wins).
        3. Handle negations (e.g., "không phải quận 7").
        """
        try:
            # 1. Extract slots
            extracted_slots = self._extract_slots(message)
            logger.info(f"Extracted slots: {extracted_slots}")

            # 2. Merge logic
            updated_slots = current_state.slots.copy()
            
            # Simple Newest Wins merge
            for key, value in extracted_slots.items():
                if value is not None:
                    updated_slots[key] = value
            
            # TODO: Handle negations (advanced)
            
            # Update state
            current_state.slots = updated_slots
            return current_state

        except Exception as e:
            logger.error(f"Error in EstateUnderstanding: {e}")
            return current_state

    def _extract_slots(self, message: str) -> Dict[str, Any]:
        """Call LLM to extract slots"""
        prompt = f"""
        Phân tích câu nói: "{message}"
        Trích xuất các thông tin sau dưới dạng JSON:
        {{
            "du_an": string | null,
            "gia_ban": {{ "min": number, "max": number }} | null,
            "dien_tich": {{ "min": number, "max": number }} | null,
            "so_phong_ngu": {{ "min": number, "max": number }} | null
        }}
        Lưu ý:
        - Giá bán: chuyển về VNĐ (tỷ -> 000,000,000).
        - Nếu người dùng nói "dưới 3 tỷ" -> max: 3000000000.
        - Nếu người dùng nói "trên 2 tỷ" -> min: 2000000000.
        - Nếu người dùng nói "tầm 2 tỷ" -> min: 1900000000, max: 2100000000 (ước lượng +- 5%).
        - Số phòng ngủ: Nếu nói "2 đến 3 phòng ngủ" -> min: 2, max: 3. Nếu nói "2 phòng ngủ" -> min: 2, max: 2.
        - Dự án: Tên tòa nhà hoặc dự án (VD: Sky89, River Panorama, ...). Nếu không rõ, để null.
        """
        
        response = self.agent.run(prompt)
        text = response.content if hasattr(response, 'content') else str(response)
        
        # Clean JSON
        text = text.strip()
        if text.startswith('```json'): text = text[7:]
        if text.endswith('```'): text = text[:-3]
        
        try:
            return json.loads(text)
        except:
            logger.warning(f"Failed to parse NLU JSON: {text}")
            return {}

# Singleton
estate_understanding = EstateUnderstanding()
