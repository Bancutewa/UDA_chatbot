import os
from typing import List, Dict, Any, Optional, Union

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.mongodb import MongoDBSaver
from langchain.agents.middleware import SummarizationMiddleware
from pymongo import MongoClient

from ..core.config import config
from ..core.logger import logger

# Import Tools
from ..tools.listing_tools import search_listings, get_listing_details, compare_listings, suggest_similar_listings
from ..tools.booking_tools import book_appointment
from ..tools.rag_tools import project_info_tool

class EstateAgent:
    """
    Agent for Real Estate using langgraph.prebuilt.create_react_agent with MongoDB Memory
    """
    
    def __init__(self):
        self.tools = [
            search_listings, 
            get_listing_details, 
            compare_listings, 
            suggest_similar_listings, 
            book_appointment, 
            project_info_tool
        ]
        self.model = ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            google_api_key=config.GEMINI_API_KEY,
            temperature=0.2,
            convert_system_message_to_human=True
        )
        
        # Initialize MongoDB Checkpointer
        self.checkpointer = None
        if config.MONGODB_URL:
            try:
                # Reuse client from config if possible or create new one
                self.mongo_client = MongoClient(config.MONGODB_URL)
                self.checkpointer = MongoDBSaver(self.mongo_client, db_name=config.DATABASE_NAME)
            except Exception as e:
                logger.error(f"Failed to initialize MongoDB Checkpointer: {e}")
        else:
            logger.warning("MONGODB_URL not set, memory will not be persisted.")

        self.agent = self._create_agent()
        
    def _create_agent(self):
        # System Prompt
        system_prompt = """Bạn là trợ lý AI tư vấn bất động sản Việt Nam chuyên nghiệp.
        
        Nhiệm vụ của bạn:
        - Phân tích yêu cầu của người dùng
        - Quyết định tool phù hợp nhất để xử lý
        - Không trả lời dựa trên suy đoán nếu cần dữ liệu → phải gọi tool
        - Khi tool trả kết quả, hãy giải thích mạch lạc và đưa gợi ý thêm
        - Khi user thiếu thông tin để gọi tool → hãy hỏi bổ sung

        Nguyên tắc chọn tool:
        1) search_listings:
           - Khi tìm căn theo tiêu chí: "Tìm căn 2 phòng ngủ dưới 3 tỷ", "Có căn nào gần đây không?"
        
        2) get_listing_details:
           - Khi xem chi tiết: "Cho xem chi tiết căn TD-2210", "Căn này diện tích bao nhiêu?"
        
        3) compare_listings:
           - Khi so sánh: "So sánh căn TD-2210 và TD-1608"
        
        4) suggest_similar_listings:
           - Khi tìm tương tự: "Có căn nào giống căn này không?", "Gợi ý căn tương tự"
        
        5) book_appointment:
           - Khi đặt lịch: "Đặt lịch xem lúc 9h sáng mai", "Book lịch"
           
        6) project_info_tool:
           - Khi hỏi chung chung: "Tiện ích dự án là gì?", "Pháp lý thế nào?"
           
        Tránh:
        - Không bịa đặt dữ liệu
        - Luôn trả lời bằng tiếng Việt lịch sự, chuyên nghiệp.
        """
        
        # Using create_react_agent from langgraph.prebuilt which supports checkpointer correctly
        return create_react_agent(
            model=self.model, 
            tools=self.tools, 
            prompt=system_prompt, # check prompt param for langgraph prebuilt version
            checkpointer=self.checkpointer
        )

    def invoke(self, input_text: str, thread_id: str) -> str:
        """
        Run the agent with input and thread_id for memory persistence.
        """
        try:
            # Config with thread_id
            config_run = {"configurable": {"thread_id": thread_id}}
            
            # Invoke Agent
            response = self.agent.invoke(
                {"messages": [{"role": "user", "content": input_text}]},
                config=config_run
            )
            
            # Extract final response
            if isinstance(response, dict) and "messages" in response:
                content = response["messages"][-1].content
                # Handle complex content (list of blocks)
                if isinstance(content, list):
                    text_parts = [block.get('text', '') for block in content if block.get('type') == 'text']
                    return "\n".join(text_parts)
                return str(content)
            return str(response)
            
        except Exception as e:
            logger.error(f"Agent invoke error: {e}", exc_info=True)
            return "Xin lỗi, hệ thống đang gặp sự cố khi xử lý yêu cầu của bạn."

# Singleton instance
estate_agent = EstateAgent()
