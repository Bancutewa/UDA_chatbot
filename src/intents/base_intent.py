"""
Base class cho các intent handlers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from agno.agent import Agent


class BaseIntent(ABC):
    """Abstract base class cho tất cả intent handlers"""

    def __init__(self, agent: Optional[Agent] = None):
        self.agent = agent

    @property
    @abstractmethod
    def intent_name(self) -> str:
        """Tên của intent này"""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """System prompt cho intent này"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Mô tả intent cho LLM (dùng để tạo prompt tự động)"""
        pass

    @property
    @abstractmethod
    def keywords(self) -> list[str]:
        """Danh sách từ khóa để fallback (khi LLM fail)"""
        pass

    @abstractmethod
    def get_response(self, data: Dict[str, Any], context: Optional[str] = None) -> str:
        """
        Xử lý response cho intent này

        Args:
            data: Dữ liệu từ intent analysis (có thể có message, description, etc.)
            context: Context từ lịch sử chat (optional)

        Returns:
            Response string
        """
        pass

    def get_agent_instructions(self) -> list[str]:
        """Lấy instructions cho agent (mặc định là system prompt)"""
        return [self.system_prompt]
