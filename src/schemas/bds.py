"""
BDS-related schemas
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class BDSPropertySchema(BaseModel):
    """Schema for BDS property data"""
    title: str = Field(..., description="Property title")
    price: Optional[str] = Field(None, description="Property price")
    area: Optional[str] = Field(None, description="Property area")
    location: Optional[str] = Field(None, description="Property location")
    description: Optional[str] = Field(None, description="Property description")
    property_type: Optional[str] = Field(None, description="Type: apartment, house, land, etc.")
    url: Optional[str] = Field(None, description="Source URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class BDSSearchResultSchema(BaseModel):
    """Schema for BDS search results"""
    query: str = Field(..., description="Search query")
    properties: List[BDSPropertySchema] = Field(default_factory=list)
    total_results: int = Field(default=0)
    search_timestamp: str = Field(..., description="Search timestamp")

class BDSQuerySchema(BaseModel):
    """Schema for BDS user queries"""
    query: str = Field(..., description="User question")
    intent: str = Field(default="estate_query", description="Intent type")
    context_needed: bool = Field(default=True, description="Whether RAG context is needed")
