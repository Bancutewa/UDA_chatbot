from typing import List, Dict
from langchain.tools import tool
from qdrant_client.http import models

from ..services.qdrant_service import qdrant_service
from ..services.embedding_service import embedding_service
from ..core.logger import logger

@tool
def project_info_tool(topic: str) -> str:
    """
    Tra cứu thông tin chung về dự án, tiện ích, pháp lý, hoặc thị trường (RAG Lookup).
    Dùng khi người dùng hỏi về thông tin chung chung không phải tìm căn cụ thể.
    Ví dụ: "Vinhomes Grand Park có tiện ích gì?", "Pháp lý dự án này thế nào?"

    Các tham số:
    - topic: Chủ đề hoặc câu hỏi cần tra cứu.

    Return:
    - Đoạn văn bản thông tin tìm thấy.
    """
    logger.info(f"Tool project_info_tool called: {topic}")
    
    # 1. Vector Search
    vector = embedding_service.encode([topic])[0].tolist()
    
    results = qdrant_service.query_points(
        collection_name=qdrant_service.collection_name,
        query=vector,
        limit=3 
    )
    
    if not results.points:
        return "Không tìm thấy thông tin liên quan."
        
    # 2. Synthesize Context
    # Since we store Listing Data mainly, maybe this tool searches a distinct 'Knowledge Base' collection?
    # Or implies extracting info from listing descriptions?
    # For MVP, we assume we extract useful text from listing descriptions or a separate collection.
    # If the user only has listing data, we return relevant listing descriptions.
    
    contexts = []
    for point in results.points:
        # Assuming payload has 'text_representation' or 'description'
        text_rep = point.payload.get('text_representation', '')
        contexts.append(text_rep)
        
    return "\n---\n".join(contexts)
