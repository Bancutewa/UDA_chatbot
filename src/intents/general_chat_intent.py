"""
Intent handler cho general chat
"""
import time
from typing import Dict, Any, Optional, Generator
from agno.agent import Agent
from .base_intent import BaseIntent

from ..agents.llm_agent import llm_agent


class GeneralChatIntent(BaseIntent):
    """Intent handler cho trò chuyện thông thường"""

    def __init__(self, agent: Optional[Agent] = None):
        super().__init__(agent)
        # Create agent for general chat if not provided
        if not self.agent:
            self.agent = llm_agent.create_agent(
                name="General Chat Agent",
                instructions=[self.system_prompt],
                description="Agent cho trò chuyện thông thường",
                markdown=True
            )

    @property
    def intent_name(self) -> str:
        return "general_chat"

    @property
    def system_prompt(self) -> str:
        return ("Bạn là một chatbot AI thông minh, thân thiện và hữu ích.\n"
                "Luôn trả lời bằng tiếng Việt trừ khi người dùng yêu cầu khác.\n"
                "Trả lời một cách tự nhiên, hấp dẫn và mang tính xây dựng.\n"
                "Nếu có ngữ cảnh từ lịch sử trò chuyện, hãy sử dụng để trả lời phù hợp.")

    def get_response(self, data: Dict[str, Any], context: Optional[str] = None) -> str:
        """
        Xử lý response cho general chat

        Args:
            data: Chứa key "message" với nội dung tin nhắn
            context: Lịch sử hội thoại (optional)

        Returns:
            Response từ agent
        """
        message_content = data.get("message", "")

        if not context:
            context = "Không có lịch sử hội thoại."

        conversation_prompt = f"""
        Lịch sử hội thoại (ngữ cảnh):
        {context}

        Câu hỏi mới của người dùng: {message_content}

        Hãy trả lời câu hỏi mới một cách tự nhiên và hữu ích (bằng tiếng Việt).
        """

        response = self.agent.run(conversation_prompt)
        return response.content if hasattr(response, 'content') else str(response)

    def get_streaming_response(self, data: Dict[str, Any], context: Optional[str] = None) -> Generator[str, None, None]:
        """
        Xử lý streaming response cho general chat

        Args:
            data: Chứa key "message" với nội dung tin nhắn
            context: Lịch sử hội thoại (optional)

        Yields:
            Các chunk của response để streaming
        """
        message_content = data.get("message", "")

        if not context:
            context = "Không có lịch sử hội thoại."

        conversation_prompt = f"""
        Lịch sử hội thoại (ngữ cảnh):
        {context}

        Câu hỏi mới của người dùng: {message_content}

        Hãy trả lời câu hỏi mới một cách tự nhiên và hữu ích (bằng tiếng Việt).
        """

        # Get full response first (since Agno doesn't support streaming yet)
        response = self.agent.run(conversation_prompt)
        full_response = response.content if hasattr(response, 'content') else str(response)

        # Simulate streaming by yielding chunks
        yield from self._simulate_streaming(full_response)

    def _simulate_streaming(self, text: str, chunk_size: int = 10) -> Generator[str, None, None]:
        """
        Simulate streaming by yielding text in chunks

        Args:
            text: Full text to stream
            chunk_size: Size of each chunk

        Yields:
            Text chunks
        """
        words = text.split()
        current_chunk = ""

        for word in words:
            current_chunk += word + " "

            # Yield chunk when it reaches chunk_size or at punctuation
            if len(current_chunk) >= chunk_size or word.endswith(('.', '!', '?', ':', ';')):
                yield current_chunk.strip()
                current_chunk = ""
                time.sleep(0.05)  # Small delay to simulate real streaming

        # Yield any remaining text
        if current_chunk.strip():
            yield current_chunk.strip()
