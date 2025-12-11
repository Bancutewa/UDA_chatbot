"""
Integration Tests for Estate Chatbot Pipeline
Simulates full conversation flows.
"""
import unittest
import sys
import os
import logging
from unittest.mock import MagicMock, patch

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_debug.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Mock services
sys.modules['src.agents.llm_agent'] = MagicMock()
sys.modules['src.services.qdrant_service'] = MagicMock()
sys.modules['src.services.embedding_service'] = MagicMock()
# chat_service will be patched in methods

from src.intents.estate_query_intent import EstateQueryIntent
from src.schemas.conversation_state import ConversationState, DialogState

class TestEstateIntegration(unittest.TestCase):

    def setUp(self):
        self.intent_handler = EstateQueryIntent()
        self.state = ConversationState()
        
        # Setup Mocks
        self.llm_mock = sys.modules['src.agents.llm_agent'].llm_agent
        self.qdrant_mock = sys.modules['src.services.qdrant_service'].qdrant_service
        self.embedding_mock = sys.modules['src.services.embedding_service'].embedding_service

    @patch('src.intents.estate_query_intent.chat_service')
    def test_full_search_flow(self, mock_chat_service):
        logger.info("Testing full_search_flow (Integration)...")
        
        # Configure Chat Service Mock
        mock_chat_service.get_state.return_value = self.state
        
        # 1. User: "Tìm căn 2 phòng ngủ ở Q7 Riverside"
        logger.info("Step 1: User asks for 2 bedroom apartment in Q7 Riverside")
        
        # Mock Understanding Layer (LLM)
        mock_nlu_response = MagicMock()
        mock_nlu_response.content = '{"intent": "search_apartment", "confidence": 0.95, "slots": {"du_an": "Q7 Riverside", "so_phong_ngu": 2}}'
        
        # Patch the agent on the singleton
        from src.intents.estate.understanding import estate_understanding
        estate_understanding.agent.run.return_value = mock_nlu_response

        # Mock Qdrant Response
        mock_point = MagicMock()
        mock_point.payload = {
            "du_an": "Q7Riverside", 
            "so_phong_ngu": 2, 
            "gia_ban": 2500000000,
            "ma_can": "A1.05",
            "tang": 5,
            "huong": "Đông Nam",
            "dien_tich": 70
        }
        mock_results = MagicMock()
        mock_results.points = [mock_point]
        self.qdrant_mock.query_points.return_value = mock_results
        self.embedding_mock.encode.return_value = [MagicMock()]

        # Execute
        data = {
            "message": "Tìm căn 2 phòng ngủ ở Q7 Riverside",
            "metadata": {"session_id": "test_session"}
        }
        response_text = self.intent_handler.get_response(data)
        
        # Verify Output
        logger.info(f"  Response Text: {response_text}")
        print(f"DEBUG: Response Text 1: {response_text}")
        self.assertIn("Q7Riverside", response_text)
        self.assertIn("PN: 2", response_text)
        
        # Verify State Update
        logger.info(f"  State Slots: {self.state.slots}")
        self.assertEqual(self.state.slots["du_an"], "Q7Riverside")
        self.assertEqual(self.state.slots["so_phong_ngu"], 2)
        self.assertEqual(self.state.dialog_state, DialogState.PRESENTING)

        # 2. User: "Tìm căn tầng cao hơn"
        logger.info("Step 2: User refines search 'Tìm căn tầng cao hơn'")
        
        # Mock NLU for refinement
        mock_nlu_response.content = '{"intent": "search_apartment", "confidence": 0.9, "slots": {"tang": {"min": 10, "max": 99}}}'
        estate_understanding.agent.run.return_value = mock_nlu_response
        
        # Execute
        data = {
            "message": "Tìm căn tầng cao hơn",
            "metadata": {"session_id": "test_session"}
        }
        response_text = self.intent_handler.get_response(data)
        
        # Verify State Merge
        logger.info(f"  State Slots: {self.state.slots}")
        self.assertEqual(self.state.slots["du_an"], "Q7Riverside") # Kept from previous
        self.assertEqual(self.state.slots["so_phong_ngu"], 2)      # Kept from previous

    @patch('src.intents.estate_query_intent.chat_service')
    def test_show_details_flow(self, mock_chat_service):
        logger.info("Testing show_details_flow (Integration)...")
        
        # Configure Chat Service Mock
        mock_chat_service.get_state.return_value = self.state
        
        # Setup State with context
        self.state.slots = {"du_an": "Q7Riverside"}
        
        # User: "Cho xem chi tiết căn A1.05"
        logger.info("Step 1: User asks for details of A1.05")
        
        # Mock NLU
        mock_nlu_response = MagicMock()
        mock_nlu_response.content = '{"intent": "show_details", "confidence": 0.98, "slots": {"ma_can_ho": "A1.05"}}'
        from src.intents.estate.understanding import estate_understanding
        estate_understanding.agent.run.return_value = mock_nlu_response
        
        # Mock Qdrant for Detail Search
        mock_point = MagicMock()
        mock_point.payload = {
            "du_an": "Q7Riverside",
            "ma_can": "A1.05",
            "gia_ban": 2500000000,
            "mo_ta": "Căn hộ view sông đẹp",
            "view": "Sông"
        }
        mock_results = MagicMock()
        mock_results.points = [mock_point]
        self.qdrant_mock.query_points.return_value = mock_results
        
        # Execute
        data = {
            "message": "Cho xem chi tiết căn A1.05",
            "metadata": {"session_id": "test_session"}
        }
        response_text = self.intent_handler.get_response(data)
        
        # Verify Output
        logger.info(f"  Response Text: {response_text}")
        print(f"DEBUG: Response Text 2: {response_text}")
        self.assertIn("A1.05", response_text)
        self.assertIn("2.500.000.000", response_text)
        
        self.assertEqual(self.state.last_intent, "show_details")

if __name__ == '__main__':
    unittest.main()
