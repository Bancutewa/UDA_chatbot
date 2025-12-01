"""
Layer 3: Response (NLG)
Responsible for executing actions and generating responses.
"""
from typing import Dict, Any, List
from ...services.qdrant_service import qdrant_service
from ...agents.llm_agent import llm_agent
from ...core.logger import logger

class EstateResponse:
    """Response Layer for Real Estate"""

    def __init__(self):
        self.nlg_agent = llm_agent.create_agent(
            name="Estate NLG",
            instructions=[
                "Bạn là trợ lý bất động sản thân thiện.",
                "Nhiệm vụ: Tạo câu trả lời tự nhiên dựa trên kết quả tìm kiếm hoặc yêu cầu hỏi thêm thông tin.",
                "Luôn trả lời bằng tiếng Việt, ngắn gọn, súc tích."
            ],
            description="NLG Agent for Estate",
            markdown=True
        )

    def execute(self, action_plan: Dict[str, Any]) -> str:
        """
        Execute action and return response string.
        """
        action = action_plan.get("action")
        payload = action_plan.get("payload", {})
        
        if action == "ASK_SLOT":
            return self._handle_ask_slot(payload)
            
        elif action == "SEARCH_LISTINGS":
            return self._handle_search(payload)
            
        elif action == "NO_RESULT":
            return "Hiện tại em chưa tìm thấy căn nào phù hợp với yêu cầu của anh/chị. Anh/chị có muốn thay đổi tiêu chí (ví dụ: khu vực khác, giá cao hơn) không ạ?"
            
        else:
            return "Em chưa hiểu rõ ý anh/chị. Anh/chị có thể nói lại được không ạ?"

    def _handle_ask_slot(self, payload: Dict[str, Any]) -> str:
        """Generate question to ask for missing slot"""
        slot = payload.get("slot")
        if slot == "criteria":
            return "Anh/chị vui lòng cho em biết thêm yêu cầu về dự án, giá bán, hoặc số phòng ngủ để em tìm kiếm chính xác hơn ạ."
        elif slot == "gia_ban":
            return "Anh/chị dự kiến tài chính khoảng bao nhiêu ạ?"
        else:
            return f"Anh/chị có yêu cầu gì về {slot} không ạ?"

    def _handle_search(self, payload: Dict[str, Any]) -> str:
        """Execute search and generate response"""
        filters = payload.get("filters", {})
        
    def _handle_search(self, payload: Dict[str, Any]) -> str:
        """Execute search and generate response"""
        filters = payload.get("filters", {})
        
        # Construct Qdrant filter
        from qdrant_client.models import Filter, FieldCondition, MatchValue, Range, Prefetch
        
        must_conditions = []
        
        # 1. Project (Dự án)
        if filters.get("du_an"):
            # Use MatchValue for exact match (assuming index exists)
            # Or use text search if no index? Let's assume index.
            must_conditions.append(
                FieldCondition(key="du_an", match=MatchValue(value=filters["du_an"]))
            )
            
        # 2. Price (Giá bán)
        price = filters.get("gia_ban")
        if price:
            if isinstance(price, dict):
                r = Range()
                if price.get("min"): r.gte = float(price["min"])
                if price.get("max"): r.lte = float(price["max"])
                must_conditions.append(FieldCondition(key="gia_ban", range=r))
            elif isinstance(price, (int, float)):
                must_conditions.append(FieldCondition(key="gia_ban", range=Range(lte=float(price))))

        # 3. Area (Diện tích)
        area = filters.get("dien_tich")
        if area:
            if isinstance(area, dict):
                r = Range()
                if area.get("min"): r.gte = float(area["min"])
                if area.get("max"): r.lte = float(area["max"])
                must_conditions.append(FieldCondition(key="dien_tich", range=r))
            elif isinstance(area, (int, float)):
                must_conditions.append(FieldCondition(key="dien_tich", range=Range(gte=float(area))))

        # 4. Bedrooms (Số phòng ngủ)
        bedrooms = filters.get("so_phong_ngu")
        if bedrooms:
            if isinstance(bedrooms, dict):
                 # Range for bedrooms (e.g. 2-3 bedrooms)
                r = Range()
                if bedrooms.get("min"): r.gte = float(bedrooms["min"])
                if bedrooms.get("max"): r.lte = float(bedrooms["max"])
                must_conditions.append(FieldCondition(key="so_phong_ngu", range=r))
            else:
                # Exact match
                must_conditions.append(
                    FieldCondition(key="so_phong_ngu", match=MatchValue(value=int(bedrooms)))
                )

        query_filter = Filter(must=must_conditions) if must_conditions else None
        
        # Construct query text for embedding (Semantic Search)
        query_parts = []
        if filters.get("du_an"): query_parts.append(f"dự án {filters['du_an']}")
        if filters.get("gia_ban"): 
            p = filters['gia_ban']
            if isinstance(p, dict):
                query_parts.append(f"giá từ {p.get('min', 0)//1000000} đến {p.get('max', 'vô cực')//1000000} triệu")
            else:
                query_parts.append(f"giá {p}")
        
        query_text = " ".join(query_parts) if query_parts else "căn hộ"
        
        # Get embedding
        from ...services.embedding_service import embedding_service
        vector = embedding_service.encode([query_text])[0].tolist()
        
        # Execute Query using query_points with Prefetch (Hybrid Search)
        try:
            # We use prefetch to combine vector search with filtering
            # But query_points directly supports filter + vector.
            # The user example showed prefetch, which is for more complex cases or multi-stage.
            # Simple query_points with query=vector and query_filter=filter works for "Semantic + Filter".
            # Let's stick to the simple and robust way first, as per Qdrant docs for Hybrid.
            
            results = qdrant_service.query_points(
                collection_name=qdrant_service.collection_name,
                query=vector,
                query_filter=query_filter,
                limit=5
            )
            
            points = results.points
            
            if not points:
                return "Tiếc quá, em không tìm thấy căn nào phù hợp với các tiêu chí trên. Anh/chị thử thay đổi yêu cầu xem sao ạ?"
                
            # Format results
            response = f"Em tìm thấy {len(points)} căn phù hợp:\n\n"
            
            for point in points:
                payload = point.payload
                price = payload.get('gia_ban')
                price_str = f"{price//1000000} triệu" if isinstance(price, (int, float)) else str(price)
                
                response += f"- **{payload.get('du_an', 'Căn hộ')}** ({payload.get('khu_vuc', '')})\n"
                response += f"  • {payload.get('so_phong_ngu', '?')} PN | {payload.get('dien_tich', '?')}m²\n"
                response += f"  • Giá: {price_str}\n"
                response += f"  • {payload.get('text_representation', '')[:100]}...\n\n"
                
            return response

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return "Xin lỗi, hệ thống gặp sự cố khi tìm kiếm."

# Singleton
estate_response = EstateResponse()
