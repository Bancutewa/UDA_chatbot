"""
Qdrant Repository - Vector database for embeddings
"""
from typing import List, Dict, Optional, Any
import numpy as np

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QdrantClient = None
    QDRANT_AVAILABLE = False

from ..core.config import config
from ..core.logger import logger
from ..core.exceptions import DatabaseConnectionError

class QdrantRepository:
    """Repository for vector storage using Qdrant"""

    def __init__(self):
        if not QDRANT_AVAILABLE:
            logger.warning("Qdrant client not available. Vector operations will be disabled.")
            self.client = None
            return

        try:
            # Initialize with API key if available
            if config.QDRANT_API_KEY:
                self.client = QdrantClient(
                    url=config.QDRANT_URL,
                    api_key=config.QDRANT_API_KEY
                )
            else:
                self.client = QdrantClient(url=config.QDRANT_URL)

            self.collection_name = "bds_vectors"

            # Create collection if not exists
            self._ensure_collection()

            logger.info(f"Qdrant repository initialized at {config.QDRANT_URL}")

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant repository: {e}")
            self.client = None

    def _ensure_collection(self):
        """Ensure collection exists"""
        if not self.client:
            return

        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=config.VECTOR_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Qdrant collection already exists: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to create Qdrant collection: {e}")

    def is_available(self) -> bool:
        """Check if Qdrant is available"""
        return self.client is not None and QDRANT_AVAILABLE

    def add_vectors(self, vectors: List[List[float]], payloads: List[Dict[str, Any]]) -> bool:
        """
        Add vectors with payloads to collection

        Args:
            vectors: List of vector embeddings
            payloads: List of metadata payloads

        Returns:
            Success status
        """
        if not self.client:
            logger.warning("Qdrant not available, skipping vector addition")
            return False

        try:
            points = [
                PointStruct(
                    id=i,
                    vector=vector,
                    payload=payload
                )
                for i, (vector, payload) in enumerate(zip(vectors, payloads))
            ]

            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            logger.info(f"Added {len(points)} vectors to Qdrant")
            return True

        except Exception as e:
            logger.error(f"Failed to add vectors to Qdrant: {e}")
            return False

    def search_vectors(self,
                      query_vector: List[float],
                      limit: int = 10,
                      score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for similar vectors

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score

        Returns:
            List of search results with scores and payloads
        """
        if not self.client:
            logger.warning("Qdrant not available, returning empty results")
            return []

        try:
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold
            )

            results = []
            for hit in search_results:
                results.append({
                    "score": hit.score,
                    "payload": hit.payload,
                    "id": hit.id
                })

            logger.info(f"Qdrant search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []

    def delete_vectors(self, point_ids: List[int]) -> bool:
        """Delete vectors by IDs"""
        if not self.client:
            return False

        try:
            self.client.delete(
                collection_name=self.collection_name,
                points=point_ids
            )
            logger.info(f"Deleted {len(point_ids)} vectors from Qdrant")
            return True
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            return False

    def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """Get collection information"""
        if not self.client:
            return None

        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": info.config.name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None

# Global instance
qdrant_repo = QdrantRepository()
