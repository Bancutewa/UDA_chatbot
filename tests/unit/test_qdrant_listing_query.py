import unittest
from unittest.mock import MagicMock, patch, ANY
import sys
import os

# Add src to path if needed (2 levels up: tests/unit -> project root)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.qdrant_service import QdrantService
from qdrant_client.models import Filter, FieldCondition, MatchValue, PointStruct

class TestQdrantQuery(unittest.TestCase):
    """
    Test cases for QdrantService querying capabilities
    """

    @patch('src.services.qdrant_service.QdrantClient')
    @patch('src.services.qdrant_service.config')
    def setUp(self, mock_config, mock_qdrant_client):
        # Setup Mock Config
        mock_config.QDRANT_URL = "http://mock-qdrant:6333"
        mock_config.QDRANT_API_KEY = "mock-key"
        mock_config.QDRANT_COLLECTION = "apartments_test"
        
        # Initialize Service (will use mocked QdrantClient)
        self.service = QdrantService()
        self.mock_client_instance = self.service.client
        self.collection_name = "apartments_test"

    def test_query_points_basic(self):
        """Test basic query_points call"""
        # Setup mock response
        mock_result = MagicMock()
        mock_result.points = [
            PointStruct(id="1", vector=[0.1]*768, payload={"ma_can": "A01", "gia": 2000}),
            PointStruct(id="2", vector=[0.1]*768, payload={"ma_can": "B02", "gia": 3000})
        ]
        self.mock_client_instance.query_points.return_value = mock_result

        # Execute
        query_vector = [0.1] * 768
        results = self.service.query_points(
            collection_name=self.collection_name, 
            query=query_vector, 
            limit=5
        )

        # Assert
        self.mock_client_instance.query_points.assert_called_once_with(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=None,
            limit=5,
            with_payload=True
        )
        self.assertEqual(len(results.points), 2)
        self.assertEqual(results.points[0].payload["ma_can"], "A01")

    def test_query_with_filter(self):
        """Test query_points with a filter (e.g., 2 bedrooms)"""
        # Create a filter
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="so_phong_ngu",
                    match=MatchValue(value=2)
                )
            ]
        )
        
        # Execute
        query_vector = [0.5] * 768
        self.service.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter
        )

        # Assert
        self.mock_client_instance.query_points.assert_called_with(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=10, # default
            with_payload=True
        )

    def test_query_integration_simulation(self):
        """
        Simulate a higher-level query flow where we find "luxury" apartments
        """
        # Mock empty return implies no matches
        mock_empty = MagicMock()
        mock_empty.points = []
        self.mock_client_instance.query_points.return_value = mock_empty

        # Execute
        results = self.service.query_points(
            collection_name=self.collection_name,
            query=[0.9] * 768
        )
        
        self.assertEqual(results.points, [])
        print("Validated empty result handling correctly.")

if __name__ == '__main__':
    unittest.main()
