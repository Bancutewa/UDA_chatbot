"""
Qdrant Service - Handle vector database operations
Ported from reference implementation
"""
import logging
import os
import uuid
from typing import List, Dict, Any, Optional, Union
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from ..core.config import config
from ..core.logger import logger
from .embedding_service import embedding_service

class QdrantService:
    """
    Service for interacting with Qdrant Vector Database.
    Handles collection management, point upsertion, and searching.
    """

    def __init__(self):
        """Initialize Qdrant client"""
        self.url = config.QDRANT_URL
        self.api_key = config.QDRANT_API_KEY
        self.collection_name = config.QDRANT_COLLECTION

        try:
            # Increase timeout for large uploads
            self.client = QdrantClient(
                url=self.url, 
                api_key=self.api_key,
                timeout=60
            )
            logger.info(f"Connected to Qdrant at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise e

    def create_collection_if_not_exists(self, collection_name: str, vector_size: int = 768, distance: Distance = Distance.COSINE):
        """Create a collection if it doesn't exist"""
        try:
            collections = self.client.get_collections()
            exists = any(c.name == collection_name for c in collections.collections)
            
            if not exists:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=distance)
                )
                logger.info(f"Created collection '{collection_name}' with vector size {vector_size}")
            else:
                logger.info(f"Collection '{collection_name}' already exists")
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            raise e

    def upsert_points(self, collection_name: str, points: List[PointStruct]):
        """Upsert points (vectors + payload) into the collection"""
        try:
            operation_info = self.client.upsert(
                collection_name=collection_name,
                wait=True,
                points=points
            )
            logger.info(f"Upserted {len(points)} points to '{collection_name}'. Status: {operation_info.status}")
            return operation_info
        except Exception as e:
            logger.error(f"Error upserting points to {collection_name}: {e}")
            raise e

    def query_points(self, collection_name: str, query: List[float], limit: int = 10, query_filter: Optional[models.Filter] = None, with_payload: bool = True) -> models.QueryResponse:
        """
        Search using query_points API (more flexible)
        """
        try:
            results = self.client.query_points(
                collection_name=collection_name,
                query=query,
                query_filter=query_filter,
                limit=limit,
                with_payload=with_payload,
                # using="default" # Removed to use default unnamed vector
            )
            return results
        except Exception as e:
            logger.error(f"Error querying points in {collection_name}: {e}")
            raise e

    def create_payload_index(self, collection_name: str, field_name: str, field_schema: Optional[models.PayloadSchemaType] = None):
        """Create an index for a payload field"""
        try:
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=field_schema
            )
            logger.info(f"Created index for field '{field_name}' in '{collection_name}'")
        except Exception as e:
            logger.error(f"Error creating index for {field_name} in {collection_name}: {e}")
            raise e

    def upload_from_json(self, json_path: str, collection_name: Optional[str] = None):
        """
        Upload apartment data from JSON file to Qdrant.
        """
        import json
        
        try:
            # Load JSON data
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'data' not in data or not isinstance(data['data'], list):
                raise ValueError("Invalid JSON structure: missing 'data' array")
            
            records = data['data']
            logger.info(f"Loaded {len(records)} records from {json_path}")
            
            # Use configured collection if not provided
            target_collection = collection_name or self.collection_name
            
            # Get vector dimension from embedding service
            vector_size = embedding_service.vector_dimension
            
            # Create collection if not exists
            self.create_collection_if_not_exists(target_collection, vector_size=vector_size)
            
            # Create indexes for important fields
            important_fields = [
                ('ma_can', models.PayloadSchemaType.KEYWORD),
                ('toa', models.PayloadSchemaType.KEYWORD),
                ('tang', models.PayloadSchemaType.INTEGER),
                ('so_phong_ngu', models.PayloadSchemaType.INTEGER),
                ('nhu_cau', models.PayloadSchemaType.KEYWORD),
                ('du_an', models.PayloadSchemaType.KEYWORD),
                ('gia_ban', models.PayloadSchemaType.INTEGER), # For range filter
                ('dien_tich', models.PayloadSchemaType.FLOAT), # For range filter
            ]
            
            for field_name, field_type in important_fields:
                try:
                    self.create_payload_index(target_collection, field_name, field_type)
                except Exception as e:
                    logger.warning(f"Could not create index for {field_name}: {e}")
            
            # Prepare points for upload
            points = []
            for idx, record in enumerate(records):
                # Generate text representation for embedding
                text_parts = []
                
                if record.get('ma_can'): text_parts.append(f"Mã căn: {record['ma_can']}")
                if record.get('toa'): text_parts.append(f"Tòa: {record['toa']}")
                if record.get('tang'): text_parts.append(f"Tầng: {record['tang']}")
                if record.get('so_phong_ngu'): text_parts.append(f"{record['so_phong_ngu']} phòng ngủ")
                if record.get('so_phong_wc'): text_parts.append(f"{record['so_phong_wc']} phòng WC")
                if record.get('dien_tich'): text_parts.append(f"Diện tích: {record['dien_tich']} m²")
                
                if record.get('gia_ban'):
                    price = record['gia_ban']
                    if isinstance(price, dict):
                        if price.get('min') and price.get('max'):
                            text_parts.append(f"Giá: {price['min']//1000000}-{price['max']//1000000} triệu")
                        elif price.get('max'):
                            text_parts.append(f"Giá: dưới {price['max']//1000000} triệu")
                    elif isinstance(price, (int, float)):
                        text_parts.append(f"Giá: {price//1000000} triệu")
                
                if record.get('huong'): text_parts.append(f"Hướng: {record['huong']}")
                if record.get('view'): text_parts.append(f"View: {record['view']}")
                if record.get('noi_that'): text_parts.append(f"Nội thất: {record['noi_that']}")
                if record.get('nhu_cau'): text_parts.append(f"Nhu cầu: {record['nhu_cau']}")
                
                text_representation = ". ".join(text_parts)
                
                # Generate embedding
                vector = embedding_service.encode([text_representation])[0].tolist()
                
                # Create point
                point_id = str(uuid.uuid4())
                point = PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        **record,
                        'text_representation': text_representation,
                        'source_file': data.get('source_file'),
                        'batch_id': data.get('batch_id')
                    }
                )
                points.append(point)
            
            # Upload in batches
            batch_size = 50
            total_uploaded = 0
            
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                self.upsert_points(target_collection, batch)
                total_uploaded += len(batch)
                logger.info(f"Uploaded batch {i//batch_size + 1}: {total_uploaded}/{len(points)} points")
            
            return {
                'success': True,
                'total_records': len(records),
                'uploaded': total_uploaded,
                'collection': target_collection,
                'source_file': data.get('source_file')
            }
            
        except Exception as e:
            logger.error(f"Error uploading from JSON: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

# Global instance
qdrant_service = QdrantService()
