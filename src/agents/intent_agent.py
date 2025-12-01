"""
Intent Agent - Intent analyzer agent
"""
import json
from typing import Dict, Optional

from .llm_agent import llm_agent
from ..intents.intent_registry import intent_registry
from ..core.logger import logger
from ..core.exceptions import IntentAnalysisError

class IntentAgent:
    """Intent analysis agent using LLM"""

    def __init__(self):
        system_prompt = intent_registry.generate_system_prompt()
        logger.debug(f"Intent Agent System Prompt: {system_prompt}")
        self.agent = llm_agent.create_agent(
            name="Intent Analyzer",
            instructions=[system_prompt, "Luôn trả về JSON hợp lệ."],
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
        return intent_registry.get_fallback_intent(message)

# Global instance
intent_agent = IntentAgent()
