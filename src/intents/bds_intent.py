"""
Intent handler cho BDS (real estate) queries
"""
from typing import Dict, Any, Optional
from .base_intent import BaseIntent

from ..services.bds_service import bds_service


class BDSIntent(BaseIntent):
    """Intent handler cho câu hỏi bất động sản"""

    @property
    def intent_name(self) -> str:
        return "estate_query"

    @property
    def system_prompt(self) -> str:
        return ("Bạn là AI chuyên gia bất động sản tại Việt Nam.\n"
                "Sử dụng dữ liệu từ RAG context để trả lời câu hỏi.\n"
                "Không bịa đặt số liệu, giá cả, hoặc thông tin.\n"
                "Nếu không có thông tin trong context → trả lời không biết.\n"
                "Luôn trả lời bằng tiếng Việt.")

    def get_response(self, data: Dict[str, Any], context: Optional[str] = None) -> str:
        """
        Xử lý response cho BDS query

        Args:
            data: Chứa key "query" với câu hỏi BĐS
            context: Context từ RAG (optional, sẽ được service xử lý)

        Returns:
            Answer về bất động sản
        """
        query = data.get("query", "").strip()

        if not query:
            return "❌ Vui lòng cung cấp câu hỏi về bất động sản."

        try:
            result = bds_service.answer_query(query)
            return result
        except Exception as e:
            return f"❌ Lỗi xử lý câu hỏi bất động sản: {str(e)}"
