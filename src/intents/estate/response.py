"""
Layer 3: Response (NLG)
Responsible for executing actions and generating responses.
"""
from typing import Dict, Any, List, Optional
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range, ScoredPoint

from ...services.qdrant_service import qdrant_service
from ...services.embedding_service import embedding_service
from ...agents.llm_agent import llm_agent
from ...schemas.conversation_state import ConversationState, DialogState
from ...core.logger import logger
from ...core import settings

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

    def execute(self, action_plan: Dict[str, Any], state: ConversationState) -> Dict[str, Any]:
        """
        Execute action and return structured response.
        
        Returns:
            {
                "messages": [{"type": "text", "content": "..."}],
                "apartments": [...],
                "session_update": {
                    "dialog_state": "...",
                    "slots": {...},
                    "episodic_summary": "..."
                }
            }
        """
        action = action_plan.get("action")
        payload = action_plan.get("payload", {})
        
        logger.info(f"Executing action: {action} with payload: {payload}")
        
        response_data = {
            "messages": [],
            "apartments": [],
            "session_update": {}
        }

        try:
            if action == "ASK_SLOT":
                content = self._handle_ask_slot(payload)
                response_data["messages"].append({"type": "text", "content": content})
                response_data["session_update"] = self._update_stm(action, payload)
                
            elif action == "SEARCH_LISTINGS":
                search_result = self._handle_search(payload)
                response_data["messages"].append({"type": "text", "content": search_result["message"]})
                response_data["apartments"] = search_result["apartments"]
                response_data["session_update"] = self._update_stm(action, search_result)
                
            elif action == "NO_RESULT":
                content = self._handle_no_result(payload)
                response_data["messages"].append({"type": "text", "content": content})
                response_data["session_update"] = self._update_stm(action, payload)
                
            elif action == "ASK_REPHRASE":
                content = self._handle_ask_rephrase()
                response_data["messages"].append({"type": "text", "content": content})
                response_data["session_update"] = self._update_stm(action, payload)

            elif action == "SHOW_DETAILS":
                content, apartment = self._handle_show_details(payload)
                response_data["messages"].append({"type": "text", "content": content})
                if apartment:
                    response_data["apartments"] = [apartment]
                response_data["session_update"] = self._update_stm(action, payload)

            elif action == "BOOK_APPOINTMENT":
                content = self._handle_book_appointment(payload)
                response_data["messages"].append({"type": "text", "content": content})
                response_data["session_update"] = self._update_stm(action, payload)
                
            else:
                response_data["messages"].append({"type": "text", "content": "Em chưa hiểu rõ ý anh/chị. Anh/chị có thể nói lại được không ạ?"})
                
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}", exc_info=True)
            response_data["messages"].append({"type": "text", "content": "Xin lỗi, hệ thống gặp sự cố khi xử lý yêu cầu."})

        return response_data

    def _handle_ask_slot(self, payload: Dict[str, Any]) -> str:
        """Generate question to ask for missing slot"""
        slot = payload.get("slot")
        if slot == "criteria":
            return "Anh/chị vui lòng cho em biết thêm yêu cầu về dự án (Q7 Riverside, River Panorama), giá bán, hoặc số phòng ngủ để em tìm kiếm chính xác hơn ạ."
        elif slot == "gia_ban":
            return "Anh/chị dự kiến tài chính khoảng bao nhiêu ạ?"
        elif slot == "du_an":
            return "Anh/chị quan tâm dự án nào ạ? (Q7 Riverside hay River Panorama)"
        else:
            return f"Anh/chị có yêu cầu gì về {slot} không ạ?"

    def _handle_no_result(self, payload: Dict[str, Any]) -> str:
        """Handle no result case with suggestions"""
        # Check if there's a specific error message (e.g. validation error)
        if payload.get("message"):
            return f"⚠️ {payload['message']}"

        suggestions = payload.get("suggestions", [])
        msg = "Tiếc quá, hiện tại em chưa tìm thấy căn nào phù hợp với các tiêu chí trên."
        if suggestions:
            msg += f" Anh/chị có thể thử {', '.join(suggestions).lower()} xem sao ạ?"
        else:
            msg += " Anh/chị thử thay đổi yêu cầu (ví dụ: giá, tầng, hướng) xem sao ạ?"
        return msg

    def _handle_ask_rephrase(self) -> str:
        """Ask user to rephrase"""
        return "Em chưa nghe rõ yêu cầu của anh/chị. Anh/chị có thể mô tả lại chi tiết hơn được không ạ? (Ví dụ: Tìm căn 2 phòng ngủ Q7 Riverside giá dưới 3 tỷ)"

    def _handle_show_details(self, payload: Dict[str, Any]) -> tuple[str, Optional[Dict]]:
        """Show details of a specific apartment"""
        ma_can = payload.get("ma_can_ho")
        if not ma_can:
            return "Dạ, em chưa rõ mã căn anh/chị muốn xem ạ.", None

        try:
            # Query Qdrant for specific apartment by ma_can
            results = qdrant_service.query_points(
                collection_name=qdrant_service.collection_name,
                query=[0.0] * 768, # Dummy vector, we rely on filter
                query_filter=Filter(
                    must=[
                        FieldCondition(key="ma_can", match=MatchValue(value=ma_can))
                    ]
                ),
                limit=1
            )
            
            if results.points:
                point = results.points[0]
                apartment = point.payload
                
                # Format detailed response
                details = []
                details.append(f"🏢 **Căn hộ {apartment.get('ma_can', '')}**")
                if apartment.get('du_an'): details.append(f"- Dự án: {apartment['du_an']}")
                if apartment.get('toa'): details.append(f"- Tòa: {apartment['toa']}")
                if apartment.get('tang'): details.append(f"- Tầng: {apartment['tang']}")
                if apartment.get('dien_tich'): details.append(f"- Diện tích: {apartment['dien_tich']}m²")
                if apartment.get('so_phong_ngu'): details.append(f"- Phòng ngủ: {apartment['so_phong_ngu']}")
                if apartment.get('so_phong_wc'): details.append(f"- WC: {apartment['so_phong_wc']}")
                if apartment.get('huong'): details.append(f"- Hướng: {apartment['huong']}")
                if apartment.get('view'): details.append(f"- View: {apartment['view']}")
                if apartment.get('noi_that'): details.append(f"- Nội thất: {apartment['noi_that']}")
                if apartment.get('gia_ban'): 
                    gia = f"{apartment['gia_ban']:,}".replace(",", ".")
                    details.append(f"- Giá bán: {gia} VND")
                
                msg = "\n".join(details)
                return f"Dạ, đây là thông tin chi tiết căn {ma_can} ạ:\n\n{msg}", apartment
            else:
                return f"Dạ, em tìm không thấy thông tin căn {ma_can} trong hệ thống ạ.", None
                
        except Exception as e:
            logger.error(f"Error fetching details for {ma_can}: {e}")
            return f"Xin lỗi, em gặp sự cố khi lấy thông tin căn {ma_can}.", None

    def _handle_book_appointment(self, payload: Dict[str, Any]) -> str:
        """Handle booking appointment"""
        ma_can = payload.get("ma_can_ho")
        thoi_gian = payload.get("thoi_gian")
        sdt = payload.get("sdt")
        return f"Em đã ghi nhận lịch xem căn {ma_can} vào lúc {thoi_gian}. Em sẽ liên hệ qua số {sdt} để xác nhận ạ."

    def _handle_search(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search and generate response"""
        filters = payload.get("filters", {})
        
        # 1. Build Qdrant Filter
        query_filter = self._build_qdrant_filters(filters)
        
        # 2. Construct Query Text
        query_text = self._construct_search_query_text(filters)
        
        # 3. Get Embedding
        vector = embedding_service.encode([query_text])[0].tolist()
        
        # 4. Execute Query
        try:
            results = qdrant_service.query_points(
                collection_name=qdrant_service.collection_name,
                query=vector,
                query_filter=query_filter,
                limit=settings.MAX_SEARCH_RESULTS
            )
            
            points = results.points
            
            if not points:
                return {
                    "message": "Tiếc quá, em không tìm thấy căn nào phù hợp với các tiêu chí trên.",
                    "apartments": []
                }
                
            # 5. Format Results
            apartments = self._format_search_results(points)
            
            # Generate summary message
            message = f"Em tìm thấy {len(apartments)} căn phù hợp với yêu cầu của anh/chị:\n"
            
            return {
                "message": message,
                "apartments": apartments
            }

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                "message": "Xin lỗi, hệ thống gặp sự cố khi tìm kiếm.",
                "apartments": []
            }

    def _build_qdrant_filters(self, filters: Dict[str, Any]) -> Optional[Filter]:
        """Build Qdrant Filter from slot filters"""
        must_conditions = []
        
        # 1. Project (Dự án) - Exact match
        if filters.get("du_an"):
            must_conditions.append(
                FieldCondition(key="du_an", match=MatchValue(value=filters["du_an"]))
            )
            
        # 2. Tower (Tòa) - Exact match
        if filters.get("toa"):
            must_conditions.append(
                FieldCondition(key="toa", match=MatchValue(value=filters["toa"]))
            )

        # 3. Price (Giá bán) - Range
        price = filters.get("gia_ban")
        if price:
            if isinstance(price, dict):
                r = Range()
                if price.get("min"): r.gte = float(price["min"])
                if price.get("max"): r.lte = float(price["max"])
                must_conditions.append(FieldCondition(key="gia_ban", range=r))
            elif isinstance(price, (int, float)):
                must_conditions.append(FieldCondition(key="gia_ban", range=Range(lte=float(price))))

        # 4. Area (Diện tích) - Range
        area = filters.get("dien_tich")
        if area:
            if isinstance(area, dict):
                r = Range()
                if area.get("min"): r.gte = float(area["min"])
                if area.get("max"): r.lte = float(area["max"])
                must_conditions.append(FieldCondition(key="dien_tich", range=r))
            elif isinstance(area, (int, float)):
                must_conditions.append(FieldCondition(key="dien_tich", range=Range(gte=float(area))))

        # 5. Bedrooms (Số phòng ngủ) - Exact or Range
        bedrooms = filters.get("so_phong_ngu")
        if bedrooms:
            if isinstance(bedrooms, dict):
                r = Range()
                if bedrooms.get("min"): r.gte = float(bedrooms["min"])
                if bedrooms.get("max"): r.lte = float(bedrooms["max"])
                must_conditions.append(FieldCondition(key="so_phong_ngu", range=r))
            else:
                must_conditions.append(
                    FieldCondition(key="so_phong_ngu", match=MatchValue(value=int(bedrooms)))
                )

        
        # 6. Bathrooms (Số phòng WC) - Exact match
        bathrooms = filters.get("so_phong_wc")
        if bathrooms:
            must_conditions.append(
                FieldCondition(key="so_phong_wc", match=MatchValue(value=int(bathrooms)))
            )

        # 7. Direction (Hướng) - Match
        if filters.get("huong"):
            must_conditions.append(
                FieldCondition(key="huong", match=MatchValue(value=filters["huong"]))
            )

        # 7. Furniture (Nội thất) - Match
        if filters.get("noi_that"):
            must_conditions.append(
                FieldCondition(key="noi_that", match=MatchValue(value=filters["noi_that"]))
            )

        return Filter(must=must_conditions) if must_conditions else None

    def _construct_search_query_text(self, filters: Dict[str, Any]) -> str:
        """Create semantic search query text"""
        query_parts = []
        
        if filters.get("du_an"): query_parts.append(f"dự án {filters['du_an']}")
        if filters.get("toa"): query_parts.append(f"tòa {filters['toa']}")
        if filters.get("so_phong_ngu"): query_parts.append(f"{filters['so_phong_ngu']} phòng ngủ")
        if filters.get("so_phong_wc"): query_parts.append(f"{filters['so_phong_wc']} phòng vệ sinh")
        if filters.get("huong"): query_parts.append(f"hướng {filters['huong']}")
        if filters.get("noi_that"): query_parts.append(f"nội thất {filters['noi_that']}")
        
        if filters.get("gia_ban"): 
            p = filters['gia_ban']
            if isinstance(p, dict):
                min_p = p.get('min', 0)
                max_p = p.get('max', 'vô cực')
                # Convert to billion/million for text
                query_parts.append(f"giá từ {min_p} đến {max_p}")
            else:
                query_parts.append(f"giá {p}")
        
        return " ".join(query_parts) if query_parts else "căn hộ"

    def _format_search_results(self, points: List[ScoredPoint]) -> List[Dict[str, Any]]:
        """Format Qdrant points to apartment dicts"""
        apartments = []
        for point in points:
            payload = point.payload
            apartments.append(payload)
        return apartments

    def _update_stm(self, action: str, data: Any) -> Dict[str, Any]:
        """
        Generate STM update based on action and results.
        Returns dict to merge into ConversationState.
        """
        update = {}
        
        # Update Dialog State
        if action == "ASK_SLOT":
            update["dialog_state"] = DialogState.COLLECTING
        elif action == "SEARCH_LISTINGS":
            update["dialog_state"] = DialogState.PRESENTING
        elif action == "SHOW_DETAILS":
            update["dialog_state"] = DialogState.DETAIL
        elif action == "BOOK_APPOINTMENT":
            update["dialog_state"] = DialogState.BOOKED
        elif action == "NO_RESULT":
            update["dialog_state"] = DialogState.COLLECTING
        
        # Update Episodic Summary (Simple version for now)
        # In future, use LLM to summarize
        if action == "SEARCH_LISTINGS":
            count = len(data.get("apartments", []))
            update["episodic_summary"] = f"Đã tìm thấy {count} căn hộ phù hợp."
            
        return update

# Singleton
estate_response = EstateResponse()
