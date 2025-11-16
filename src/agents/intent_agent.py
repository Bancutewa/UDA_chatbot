"""
Intent Agent - Intent analyzer agent
"""
import json
from typing import Dict, Optional

from .llm_agent import llm_agent
from ..core.settings import SYSTEM_INTENT_PROMPT
from ..core.logger import logger
from ..core.exceptions import IntentAnalysisError

class IntentAgent:
    """Intent analysis agent using LLM"""

    def __init__(self):
        self.agent = llm_agent.create_agent(
            name="Intent Analyzer",
            instructions=[SYSTEM_INTENT_PROMPT, "Luôn trả về JSON hợp lệ."],
            description="AI phân tích ý định của người dùng",
            markdown=False,
            debug_mode=False
        )
        logger.info("Intent Agent initialized")

    def analyze_intent(self, message: str, context: Optional[str] = None) -> Dict:
        """
        Analyze user intent from message

        Args:
            message: User message
            context: Optional conversation context

        Returns:
            Dict with intent analysis result
        """
        try:
            if context:
                prompt = f"""
                # Lịch sử hội thoại (để tham khảo):
                {context}

                # Câu hỏi MỚI của người dùng:
                "{message}"

                Trả về JSON phân tích câu hỏi MỚI.
                """
            else:
                prompt = f"""
                # Câu hỏi của người dùng:
                "{message}"

                Trả về JSON phân tích câu hỏi.
                """

            response = self.agent.run(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Clean response
            cleaned = response_text.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            try:
                result = json.loads(cleaned)
                logger.debug(f"Intent analysis result: {result}")
                return result
            except json.JSONDecodeError:
                logger.warning(f"JSON decode error for response: {response_text}")
                # Fallback logic
                return self._fallback_intent_analysis(message, response_text)

        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            raise IntentAnalysisError(f"Intent analysis failed: {e}")

    def _fallback_intent_analysis(self, message: str, response_text: str) -> Dict:
        """Fallback intent analysis when JSON parsing fails"""

        message_lower = message.lower()

        # Check for image generation keywords
        if any(keyword in message_lower for keyword in ['vẽ', 'tạo ảnh', 'generate image', 'hình ảnh', 'bức ảnh']):
            return {"intent": "generate_image", "description": message}

        # Check for audio generation keywords
        elif any(keyword in message_lower for keyword in ['đọc', 'phát', 'audio', 'âm thanh', 'podcast']):
            return {"intent": "generate_audio", "description": message}

        # Check for estate keywords
        elif any(keyword in message_lower for keyword in ['nhà', 'đất', 'bất động sản', 'mua nhà', 'bán nhà', 'cho thuê']):
            return {"intent": "estate_query", "query": message}

        # Default to general chat
        else:
            return {"intent": "general_chat", "message": message}

# Global instance
intent_agent = IntentAgent()
