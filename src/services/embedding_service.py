"""
Embedding Service - Handle text vectorization
"""
from typing import List, Any
from sentence_transformers import SentenceTransformer
from ..core.config import config
from ..core.logger import logger

class EmbeddingService:
    """Service for generating text embeddings"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.model_name = config.EMBEDDING_MODEL_NAME
        try:
            logger.info(f"Loading embedding model: {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            self._initialized = True
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise e

    @property
    def vector_dimension(self) -> int:
        """Get vector dimension of the model"""
        return self.model.get_sentence_embedding_dimension()

    def encode(self, texts: List[str]) -> Any:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of strings to encode
            
        Returns:
            List of vectors (numpy arrays)
        """
        try:
            return self.model.encode(texts)
        except Exception as e:
            logger.error(f"Error encoding texts: {e}")
            raise e

def get_embedding_service():
    """Get singleton instance of EmbeddingService"""
    return EmbeddingService()

# Global instance
embedding_service = get_embedding_service()
