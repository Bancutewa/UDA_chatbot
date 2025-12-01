"""
Layer 1: Understanding (NLU)
Responsible for extracting slots and updating STM.
"""
from typing import Dict, Any, Tuple
import json
from ...agents.llm_agent import llm_agent
from ...schemas.conversation_state import ConversationState
from ...core.logger import logger
from ...core import settings
from ...services.preprocessing_service import preprocessing_service

class EstateUnderstanding:
    """NLU Layer for Real Estate"""

    def __init__(self):
        self.agent = llm_agent.create_agent(
            name="Estate NLU",
            instructions=[
                "Bạn là chuyên gia NLU bất động sản.",
                "Nhiệm vụ: Trích xuất thông tin (slots) và ý định (intent) từ câu nói người dùng.",
                "Các slots cần quan tâm:",
                "- du_an: Tên dự án (VD: Q7Riverside, RiverPanorama)",
                "- toa: Tòa nhà (VD: M1, RP1)",
                "- tang: Tầng (VD: 5, 10)",
                "- gia_ban: Giá bán (VD: {min: 2 tỷ, max: 3 tỷ})",
                "- dien_tich: Diện tích (VD: {min: 70, max: 80})",
                "- so_phong_ngu: Số phòng ngủ (VD: {min: 2, max: 3})",
                "- so_phong_wc: Số phòng vệ sinh (VD: 1, 2, 3)",
                "- huong: Hướng (VD: Đông Nam, Tây Bắc)",
                "- noi_that: Nội thất (VD: Full, Cơ Bản, Trống)",
                "- view: View (VD: Sông, Công viên)",
                "Luôn trả về JSON hợp lệ."
            ],
            description="NLU Agent for Estate",
            markdown=False
        )

    def process(self, message: str, current_state: ConversationState) -> Tuple[ConversationState, Dict[str, Any]]:
        """
        Process user message and update state.
        Returns: (updated_state, nlu_result)
        """
        try:
            # 1. Extract slots & intent
            nlu_output = self._extract_slots(message)
            logger.info(f"NLU Output: {nlu_output}")
            
            extracted_slots = nlu_output.get("slots", {})
            intent = nlu_output.get("intent", "search_apartment")
            confidence = nlu_output.get("confidence", 1.0)

            # 1.5 Preprocessing / Normalization
            extracted_slots = self._normalize_slots(extracted_slots)

            # 2. Merge logic
            updated_slots = current_state.slots.copy()
            
            # Handle negations (Basic implementation)
            # If user says "không phải quận 7", we should remove "du_an" if it was "Q7Riverside"
            # But LLM is better at this. Let's assume LLM handles negation in extraction
            # e.g. if LLM returns "du_an": null explicitly when user negates?
            # For now, we stick to Newest Wins for non-null values.
            
            for key, value in extracted_slots.items():
                if value == "CLEAR":
                    updated_slots[key] = None
                elif value is not None:
                    updated_slots[key] = value
            
            # Update state
            current_state.slots = updated_slots
            current_state.last_intent = intent
            current_state.last_intent_confidence = confidence
            
            nlu_result = {
                "intent": intent,
                "confidence": confidence,
                "slots": extracted_slots
            }
            
            return current_state, nlu_result

        except Exception as e:
            logger.error(f"Error in EstateUnderstanding: {e}", exc_info=True)
            return current_state, {"intent": "search_apartment", "confidence": 0.0, "slots": {}}

    def _extract_slots(self, message: str) -> Dict[str, Any]:
        """Call LLM to extract slots"""
        prompt = f"""
        Phân tích câu nói: "{message}"
        Trích xuất các thông tin sau dưới dạng JSON:
        {{
            "intent": "search_apartment" | "show_details" | "book_appointment" | "general_chat",
            "confidence": number (0.0 - 1.0),
            "slots": {{
                "du_an": string | null,
                "toa": string | null,
                "tang": number | null,
                "gia_ban": {{ "min": number, "max": number }} | null,
                "dien_tich": {{ "min": number, "max": number }} | null,
                "so_phong_ngu": number | {{ "min": number, "max": number }} | null,
                "so_phong_wc": number | null,
                "huong": string | null,
                "noi_that": string | null,
                "view": string | null,
                "ma_can_ho": string | null (nếu user hỏi cụ thể mã căn),
                "sdt": string | null (cho booking),
                "thoi_gian": string | null (cho booking)
            }}
        }}
        Lưu ý:
        - Giá bán: chuyển về VNĐ (tỷ -> 000,000,000).
        - Dự án: Chuẩn hóa về "Q7Riverside" hoặc "RiverPanorama".
        - Hướng: Chuẩn hóa về "Đông", "Tây", "Nam", "Bắc", "Đông Nam", "Đông Bắc", "Tây Nam", "Tây Bắc".
        - Nội thất: Chuẩn hóa về "Full", "Cơ Bản", "Trống".
        - Xử lý phủ định/đính chính:
            - Nếu user nói "không cần nội thất" -> "noi_that": "Trống"
            - Nếu user nói "không phải quận 7" -> "du_an": "CLEAR" (để xóa ngữ cảnh cũ)
            - Nếu user nói "bỏ qua giá" -> "gia_ban": "CLEAR"
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

    def _normalize_slots(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize extracted slots using PreprocessingService"""
        normalized = slots.copy()
        
        # Normalize Project
        if normalized.get("du_an"):
            normalized["du_an"] = preprocessing_service.normalize_project(normalized["du_an"]) or normalized["du_an"]
            
        # Normalize Direction
        if normalized.get("huong"):
            normalized["huong"] = preprocessing_service.normalize_direction(normalized["huong"]) or normalized["huong"]
            
        # Normalize Furniture
        if normalized.get("noi_that"):
            normalized["noi_that"] = preprocessing_service.normalize_furniture(normalized["noi_that"]) or normalized["noi_that"]
            
        # Normalize Price (if string) - though LLM usually returns object
        # If LLM fails to parse price object and returns string, we could try to fix it here
        # But for now, LLM prompt asks for object.
        
        # Normalize Area (if string)
        if normalized.get("dien_tich"):
            # If it's a dict {min, max}, we might need to normalize values inside?
            # Or if it's a string "70m2"
            val = normalized["dien_tich"]
            if isinstance(val, str):
                normalized["dien_tich"] = preprocessing_service.normalize_area(val) or val
        
        return normalized

# Singleton
estate_understanding = EstateUnderstanding()
