import os
from typing import List, Dict, Any, Optional, Union

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent 
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
from ..tools.audio_tools import generate_audio_tool
from ..tools.image_tools import generate_image_tool

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
            project_info_tool,
            generate_audio_tool,
            generate_image_tool
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
                logger.info("MongoDB Checkpointer initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize MongoDB Checkpointer: {e}")
        else:
            logger.warning("MONGODB_URL not set, memory will not be persisted.")

        self.agent = self._create_agent()
        
    def _create_agent(self):
        # 1. Load Context Data (The Gió + Factsheet)
        context_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'dataset', 'context.md')
        try:
            with open(context_file_path, 'r', encoding='utf-8') as f:
                context_data = f.read()
            logger.info(f"Loaded context.md with {len(context_data)} chars")
            print(f"DEBUG: Loaded context.md with {len(context_data)} chars") # Print to console for visibility
        except Exception as e:
            logger.error(f"Failed to load context.md: {e}")
            print(f"DEBUG: Failed to load context.md: {e}")
            context_data = "Hiện chưa có dữ liệu chi tiết về dự án."

        # System Prompt Optimized
        # System Prompt Optimized based on User Request
        system_prompt = f"""
### ROLE
Bạn là "Chuyên gia Tư vấn Bất động sản Cao cấp" đại diện cho các sàn phân phối. Nhiệm vụ của bạn là tư vấn thông minh, khéo léo và thúc đẩy khách hàng thực hiện giao dịch (xem nhà, đặt chỗ).

### ĐỊNH DANH ĐA DỰ ÁN (MULTI-PROJECT LOGIC)
- Khi khách hỏi về một dự án cụ thể, hãy ưu tiên tra cứu `project_info_tool` để xác định phân khúc và đặc điểm, sau đó áp dụng văn phong tư vấn tương ứng.
- Nếu khách chưa nói tên dự án, hãy khéo léo hỏi để định vị nhu cầu trước khi tư vấn sâu.

### DỮ LIỆU NỀN TẢNG (CONTEXT - Data 1):
{context_data}

### NGUYÊN TẮC KẾT HỢP DỮ LIỆU
1. KHI TRA CỨU TỔNG QUAN (Sử dụng dữ liệu trong CONTEXT hoặc project_info_tool):
   - Không chỉ đưa ra con số khô khan. Hãy dùng ngôn ngữ trong "CONTEXT" (Data 1) để tăng sức hấp dẫn.
   - Ví dụ: Thay vì nói "Dự án có 3 mặt sông", hãy nói "Dự án sở hữu vị trí 'Ngọc đới ôm eo', vượng khí ngập tràn với 3 mặt giáp sông".

2. KHI TRA CỨU CĂN CỤ THỂ (Sử dụng search_listings / get_listing_details):
   - Kết hợp Fact từ Data 2 (Mã căn, diện tích thông thủy từ Tool) với Insight từ Data 1.
   - **QUY TẮC HIỆU SUẤT DIỆN TÍCH (BẮT BUỘC)**: Mỗi khi đưa ra thông số diện tích, hãy LUÔN kèm câu so sánh: "Hiệu suất sử dụng tại đây đạt **88.9%** (cao vượt trội so với mức 75-80% của thị trường), giúp anh/chị tối ưu từng mét vuông sống."
   - Khi tính toán diện tích: Chủ động giải thích sự khác biệt giữa **Tim tường** và **Thông thủy**.

3. KHI SO SÁNH (Sử dụng compare_listings):
   - Luôn nhấn mạnh vào "Tầm nhìn" và "Chênh lệch tầng". Dùng Data 1 để giải thích tại sao căn tầng cao lại đáng giá hơn 10-25 triệu so với tầng thấp.

### QUY TRÌNH XỬ LÝ (PIPELINE)
- Bước 1: Xác định nhu cầu & Dự án khách quan tâm.
- Bước 2: Gọi Tool tương ứng (nếu cần dữ liệu realtime/căn cụ thể) hoặc tra cứu Context (nếu là thông tin chung).
- Bước 3: Mix kết quả từ Tool với "Văn phong bán hàng" (Marketing Tone) trong Data 1.
- Bước 4: Luôn kết thúc bằng một lời kêu gọi hành động (CTA) hoặc gợi ý bước tiếp theo (Ví dụ: "Anh/Chị có muốn xem layout 3D của căn này không?", "Anh/Chị muốn em gửi bảng tính dòng tiền không?").

### CHIẾN THUẬT XỬ LÝ TÌNH HUỐNG (OBJECTION HANDLING)
- Nếu khách lo lắng về tài chính: Trích dẫn ngay chính sách "Vay 70%, ân hạn gốc 36 tháng, miễn lãi 24 tháng". Hãy nhấn mạnh: "Chỉ cần 400 triệu ban đầu là sở hữu được rồi".
- Nếu khách lo về tiến độ: Nhắc đến uy tín của "An Gia" và nhà thầu "Ricons - Top 5 Việt Nam".
- Nếu khách lo về quản lý: Nhấn mạnh đơn vị "CBRE - Số 1 thế giới".
- Sự phản đối về thiết kế (Ví dụ: hành lang hẹp): Dùng Data 1: "Hành lang rộng tới 1m6, chuẩn resort 5 sao, thoải mái di chuyển đồ đạc".

### LƯU Ý QUAN TRỌNG
- **Tư vấn phong thủy**: Lồng ghép các yếu tố "Ngọc đới ôm eo", "View sông Đồng Nai" để tăng giá trị.
- **Tạo sự khan hiếm (Urgency)**: Với mỗi kết quả tìm kiếm căn, hãy đính kèm thông tin chính sách ưu đãi (Vòng quay may mắn, thời hạn ưu đãi) để hối thúc khách.
- **Hình ảnh hóa (Visualization)**: Khi khách hỏi về View hoặc Thiết kế, hãy chủ động dùng `generate_image_tool` để tạo ảnh minh họa tầm nhìn hoặc layout giúp khách dễ hình dung.
- **Tuyệt đối trung thực**: Nếu không có dữ liệu chắc chắn, hãy nói chưa có thông tin, không bịa đặt số liệu.

Hãy bắt đầu cuộc hội thoại thật chuyên nghiệp nhưng đầy cảm xúc!
"""
        
        # Initialize Summary Model
        summary_model = ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            google_api_key=config.GEMINI_API_KEY,
            temperature=0.1,
            convert_system_message_to_human=True
        )

        # Using create_agent
        return create_agent(
            model=self.model, 
            tools=self.tools, 
            system_prompt=system_prompt, 
            checkpointer=self.checkpointer,
            middleware=[
                SummarizationMiddleware(
                    model=summary_model, 
                    trigger=("tokens", 4000), 
                    keep=("messages", 20)
                )
            ]
        )

    def invoke(self, input_text: str, thread_id: str) -> str:
        """
        Run the agent with input and thread_id for memory persistence.
        """
        try:
            # Store thread_id in a module-level variable so tools can access it
            # This is a workaround since LangChain doesn't automatically pass context to tools
            import src.tools.booking_tools as booking_tools_module
            booking_tools_module._current_thread_id = thread_id
            
            # Config with thread_id
            config_run = {"configurable": {"thread_id": thread_id}}
            
            # Invoke Agent
            # LangGraph agent returns a dictionary with state keys (messages, etc.)
            response = self.agent.invoke(
                {"messages": [{"role": "user", "content": input_text}]},
                config=config_run
            )
            
            # Extract final response
            if isinstance(response, dict) and "messages" in response:
                messages = response["messages"]
                # The last message should be the AI's final response
                final_message = messages[-1]
                content = final_message.content
                
                # Handle complex content if any
                if isinstance(content, list):
                    text_parts = [block.get('text', '') for block in content if isinstance(block, dict) and block.get('type') == 'text']
                    if not text_parts and len(content) > 0:
                         # Fallback for other str types in list
                         text_parts = [str(c) for c in content]
                    return "\n".join(text_parts)
                return str(content)
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Agent invoke error: {e}", exc_info=True)
            return "Xin lỗi, hệ thống đang gặp sự cố khi xử lý yêu cầu của bạn."

# Singleton instance
estate_agent = EstateAgent()
