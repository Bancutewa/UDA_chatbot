from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Any
from pydantic import BaseModel

from src.services.qdrant_service import qdrant_service
from src.services.embedding_service import embedding_service
from src.api import deps

# Schemas
class ListingFilter(BaseModel):
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    area_min: Optional[float] = None
    area_max: Optional[float] = None
    bedrooms: Optional[int] = None
    district: Optional[str] = None
    project: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    filters: Optional[ListingFilter] = None

router = APIRouter()

@router.post("/search")
async def search_listings(
    request: SearchRequest,
    # current_user = Depends(deps.get_current_user) # Optional: make public or protected
) -> Any:
    """
    Search for real estate listings using semantic search
    """
    try:
        # Generate embedding for query
        vector = embedding_service.encode([request.query])[0].tolist()
        
        # TODO: Construct Qdrant filter based on request.filters if needed
        # For now, simplistic search
        
        results = qdrant_service.query_points(
            collection_name=qdrant_service.collection_name,
            query=vector,
            limit=request.limit
        )
        
        # Format results
        listings = []
        for point in results.points:
            listings.append({
                "id": point.id,
                "score": point.score,
                "data": point.payload
            })
            
        return listings
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest")
async def get_latest_listings(
    limit: int = 10
) -> Any:
    """
    Get latest listings (scroll)
    """
    try:
        # This is a bit tricky with pure vector search, usually needs scroll API
        # but we can query with a dummy vector or use scroll if exposed in service
        
        # Fallback to a generic search or scroll if available in client
        # Using scroll from client directly
        response = qdrant_service.client.scroll(
            collection_name=qdrant_service.collection_name,
            limit=limit,
            with_payload=True
        )
        
        points, _ = response
        
        return [p.payload for p in points]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
