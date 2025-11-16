"""
BDS Service - Handle real estate query logic
"""
from typing import Optional

from ..agents.bds_agent import bds_agent
from ..services.rag_service import rag_service
from ..core.logger import logger

class BDSService:
    """Service for real estate operations"""

    def __init__(self):
        self.agent = bds_agent
        self.rag_service = rag_service

    def answer_query(self, query: str) -> str:
        """
        Answer BDS query using RAG

        Args:
            query: User question about real estate

        Returns:
            Answer string
        """
        if not self.agent.is_available():
            return "❌ Dịch vụ bất động sản hiện không khả dụng."

        try:
            # Get relevant context from RAG
            context = self.rag_service.search_relevant_context(query)

            # Generate answer using BDS agent
            answer = self.agent.answer_bds_query(query, context)

            logger.info(f"BDS query answered: {query[:50]}...")
            return answer

        except Exception as e:
            logger.error(f"BDS query failed: {e}")
            return "❌ Có lỗi xảy ra khi xử lý câu hỏi bất động sản. Vui lòng thử lại."

    def is_available(self) -> bool:
        """Check if BDS service is available"""
        return self.agent.is_available() and self.rag_service.is_available()

# Global instance
bds_service = BDSService()
