"""
BDS Agent - Agent for real estate queries
"""
from .llm_agent import llm_agent
from ..core.settings import BDS_SYSTEM_PROMPT
from ..core.logger import logger

class BDSAgent:
    """Real estate agent for BDS queries"""

    def __init__(self):
        try:
            self.agent = llm_agent.create_agent(
                name="BDS Agent",
                instructions=[BDS_SYSTEM_PROMPT],
                description="AI chuyên gia bất động sản Việt Nam",
                markdown=True,
                debug_mode=False
            )
            logger.info("BDS Agent initialized")
        except Exception as e:
            logger.error(f"Failed to initialize BDS Agent: {e}")
            self.agent = None

    def answer_bds_query(self, query: str, context: str = "") -> str:
        """
        Answer BDS query with RAG context

        Args:
            query: User question about real estate
            context: RAG context from vector database

        Returns:
            Answer string
        """
        if not self.agent:
            return "❌ Dịch vụ bất động sản tạm thời không khả dụng."

        try:
            prompt = f"""
            # Câu hỏi của người dùng:
            {query}

            # Thông tin tham khảo từ cơ sở dữ liệu:
            {context if context else "Không có thông tin tham khảo."}

            Hãy trả lời câu hỏi một cách chuyên nghiệp và chính xác.
            """

            response = self.agent.run(prompt)
            return response.content if hasattr(response, 'content') else str(response)

        except Exception as e:
            logger.error(f"BDS query failed: {e}")
            return "❌ Có lỗi xảy ra khi xử lý câu hỏi bất động sản. Vui lòng thử lại."

    def is_available(self) -> bool:
        """Check if BDS agent is available"""
        return self.agent is not None

# Global instance
bds_agent = BDSAgent()
