from typing import Optional, List, Dict, Any
from langchain.tools import tool
from qdrant_client.http import models

from ..services.qdrant_service import qdrant_service
from ..services.embedding_service import embedding_service
from ..core.logger import logger

@tool
def search_listings(
    khu_vuc: Optional[str] = None,
    du_an: Optional[str] = None,
    gia_min: Optional[int] = None,
    gia_max: Optional[int] = None,
    so_phong_ngu: Optional[int] = None,
    dien_tich_min: Optional[int] = None,
    dien_tich_max: Optional[int] = None,
    huong: Optional[str] = None
) -> List[Dict]:
    """
    Tìm danh sách bất động sản phù hợp với tiêu chí của người dùng.

    Các tham số:
    - khu_vuc: Quận/Huyện hoặc khu vực (ví dụ: "Thủ Đức", "Quận 7").
    - du_an: Tên dự án cụ thể (ví dụ: "Vinhomes Grand Park").
    - gia_min: Giá tối thiểu (VND).
    - gia_max: Giá tối đa (VND).
    - so_phong_ngu: Số phòng ngủ mong muốn.
    - dien_tich_min: Diện tích tối thiểu (m2).
    - dien_tich_max: Diện tích tối đa (m2).
    - huong: Hướng căn hộ (ví dụ: "Đông", "Tây Nam").

    Return:
    - Danh sách căn hộ phù hợp dạng list[dict].
    """
    logger.info(f"Tool search_listings called with: khu_vuc={khu_vuc}, du_an={du_an}, price={gia_min}-{gia_max}")
    
    # 1. Build Filter
    must_filters = []
    
    # Note: Text filters (du_an, dia_chi, huong) require Qdrant Text Index.
    # Since we are migrating and might not have indexes, we rely on Vector Search for these fields.
    # Only using numeric/exact filters that are likely safe or critical.

    if so_phong_ngu is not None:
        must_filters.append(
            models.FieldCondition(
                key="so_phong_ngu",
                match=models.MatchValue(value=so_phong_ngu)
            )
        )
        
    # 'huong' is usually short, so MatchValue might work if indexed as keyword, 
    # but to be safe and avoid 400 error, we skip strict filtering and let vector search handle it.
    # if huong: ... 

    if gia_min is not None or gia_max is not None:
        range_filter = models.Range(
            gte=float(gia_min) if gia_min else None,
            lte=float(gia_max) if gia_max else None
        )
        must_filters.append(
            models.FieldCondition(
                key="gia_ban",
                range=range_filter
            )
        )
        
    if dien_tich_min is not None or dien_tich_max is not None:
        range_filter = models.Range(
            gte=float(dien_tich_min) if dien_tich_min else None,
            lte=float(dien_tich_max) if dien_tich_max else None
        )
        must_filters.append(
            models.FieldCondition(
                key="dien_tich",
                range=range_filter
            )
        )
    
    query_filter = models.Filter(must=must_filters) if must_filters else None
    
    # 2. Search
    # We include all criteria in the search text for Semantic Search
    search_text = f"{du_an or ''} {khu_vuc or ''} {huong or ''} {so_phong_ngu or ''} phòng ngủ"
    vector = embedding_service.encode([search_text])[0].tolist()
    
    results = qdrant_service.query_points(
        collection_name=qdrant_service.collection_name,
        query=vector,
        query_filter=query_filter,
        limit=5 # Limit for chat display
    )
    
    # 3. Format Output
    listings = []
    for point in results.points:
        listings.append(point.payload)
        
    return listings

@tool
def get_listing_details(listing_id: str) -> Dict:
    """
    Lấy đầy đủ thông tin chi tiết của một bất động sản.

    Các tham số:
    - listing_id: Mã căn hộ/BĐS (ví dụ: "TD-2210").

    Return:
    - Thông tin chi tiết dạng dict (giá, diện tích, số phòng, tiện ích, pháp lý,...).
    """
    logger.info(f"Tool get_listing_details called for {listing_id}")
    
    # We need to search by ID. 
    # Usually ID is stored in payload 'ma_can' or point ID?
    # Let's assume 'ma_can' in payload.
    
    must_filters = [
        models.FieldCondition(
            key="ma_can",
            match=models.MatchValue(value=listing_id)
        )
    ]
    
    # Using scroll since we look for exact match
    results = qdrant_service.client.scroll(
        collection_name=qdrant_service.collection_name,
        scroll_filter=models.Filter(must=must_filters),
        limit=1
    )
    
    points, _ = results
    if points:
        return points[0].payload
    
    return {"error": f"Không tìm thấy căn hộ có mã {listing_id}"}

@tool
def compare_listings(listing_ids: List[str]) -> Dict:
    """
    So sánh nhiều bất động sản theo các tiêu chí:
    - Giá
    - Diện tích
    - Số phòng ngủ
    - Vị trí
    - Tiện ích

    Các tham số:
    - listing_ids: Danh sách mã căn hộ cần so sánh (2 hoặc 3 mã).

    Return:
    - dict chứa kết quả so sánh từng tiêu chí.
    """
    logger.info(f"Tool compare_listings called for {listing_ids}")
    
    results = {}
    
    for lid in listing_ids:
        details = get_listing_details.invoke(lid) # Invoke internal logic? Or just reuse logic?
        # Better reuse logic directly
        # Re-implementing simplified lookup for batch
        
        must_filters = [
            models.FieldCondition(
                key="ma_can",
                match=models.MatchValue(value=lid)
            )
        ]
        points, _ = qdrant_service.client.scroll(
            collection_name=qdrant_service.collection_name,
            scroll_filter=models.Filter(must=must_filters),
            limit=1
        )
        if points:
            results[lid] = points[0].payload
        else:
            results[lid] = "Không tìm thấy"
            
    return results

@tool
def suggest_similar_listings(listing_id: str) -> List[Dict]:
    """
    Gợi ý các bất động sản tương tự với căn đang xem.

    Tiêu chí tương tự có thể bao gồm:
    - Cùng khu vực
    - Tương đương diện tích
    - Tương đương số phòng ngủ
    - Tương đương mức giá

    Các tham số:
    - listing_id: Mã căn dùng làm mẫu đối chiếu.

    Return:
    - Danh sách căn tương tự dạng list[dict].
    """
    logger.info(f"Tool suggest_similar_listings called for {listing_id}")
    
    # 1. Get the source listing to get its vector (if plausible) or re-encode its text
    must_filters = [
        models.FieldCondition(
            key="ma_can",
            match=models.MatchValue(value=listing_id)
        )
    ]
    points, _ = qdrant_service.client.scroll(
        collection_name=qdrant_service.collection_name,
        scroll_filter=models.Filter(must=must_filters),
        limit=1,
        with_vectors=True
    )
    
    if not points:
        return [{"error": "Không tìm thấy căn mẫu"}]
        
    source_point = points[0]
    source_vector = source_point.vector
    
    # 2. Search nearest neighbors
    # Need to exclude the source point itself
    results = qdrant_service.query_points(
        collection_name=qdrant_service.collection_name,
        query=source_vector,
        limit=5
    )
    
    suggestions = []
    for point in results.points:
        if point.id != source_point.id and point.payload.get('ma_can') != listing_id:
             suggestions.append(point.payload)
             
    return suggestions
