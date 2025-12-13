"""
Unit tests for EstateResponse
"""
import unittest
import sys
import os
from unittest.mock import MagicMock, patch

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Mock services BEFORE importing estate_response
sys.modules['src.services.qdrant_service'] = MagicMock()
sys.modules['src.services.embedding_service'] = MagicMock()
sys.modules['src.agents.llm_agent'] = MagicMock()

from src.intents.estate.response import EstateResponse
from src.schemas.conversation_state import ConversationState, DialogState

class TestEstateResponse(unittest.TestCase):

    def setUp(self):
        self.response_layer = EstateResponse()
        self.state = ConversationState()
        
        # Mock dependencies
        self.qdrant_mock = sys.modules['src.services.qdrant_service'].qdrant_service
        self.embedding_mock = sys.modules['src.services.embedding_service'].embedding_service

    def test_build_qdrant_filters(self):
        logger.info("Testing build_qdrant_filters...")
        filters = {
            "du_an": "Q7Riverside",
            "gia_ban": {"min": 2000000000, "max": 3000000000},
            "so_phong_ngu": 2
        }
        q_filter = self.response_layer._build_qdrant_filters(filters)
        
        # Verify structure (simplified check)
        self.assertIsNotNone(q_filter)
        logger.info(f"  Filter conditions count: {len(q_filter.must)}")
        self.assertEqual(len(q_filter.must), 3) # 3 conditions

    def test_construct_search_query_text(self):
        logger.info("Testing construct_search_query_text...")
        filters = {
            "du_an": "Q7Riverside",
            "so_phong_ngu": 2
        }
        text = self.response_layer._construct_search_query_text(filters)
        logger.info(f"  Generated query text: '{text}'")
        self.assertIn("dự án Q7Riverside", text)
        self.assertIn("2 phòng ngủ", text)

    def test_handle_search_success(self):
        logger.info("Testing handle_search_success...")
        # Setup mocks
        # We rely on the sys.modules mock from setUp
        
        mock_point = MagicMock()
        mock_point.payload = {"du_an": "Test Project", "gia_ban": 2000000000}
        mock_results = MagicMock()
        mock_results.points = [mock_point]
        
        self.qdrant_mock.query_points.return_value = mock_results
        self.embedding_mock.encode.return_value = [MagicMock()] # Dummy vector

        payload = {"filters": {"du_an": "Test"}}
        result = self.response_layer._handle_search(payload)
        
        logger.info(f"  Result apartments count: {len(result['apartments'])}")
        self.assertEqual(len(result["apartments"]), 1)
        self.assertIn("Test Project", result["apartments"][0]["du_an"])

    def test_update_stm(self):
        logger.info("Testing update_stm...")
        # Test SEARCH_LISTINGS update
        update = self.response_layer._update_stm("SEARCH_LISTINGS", {"apartments": [1, 2, 3]})
        logger.info(f"  SEARCH_LISTINGS -> DialogState: {update['dialog_state']}")
        self.assertEqual(update["dialog_state"], DialogState.PRESENTING)
        self.assertIn("3 căn hộ", update["episodic_summary"])

        # Test ASK_SLOT update
        update = self.response_layer._update_stm("ASK_SLOT", {})
        logger.info(f"  ASK_SLOT -> DialogState: {update['dialog_state']}")
        self.assertEqual(update["dialog_state"], DialogState.COLLECTING)

if __name__ == '__main__':
    unittest.main()
