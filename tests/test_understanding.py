"""
Unit tests for EstateUnderstanding
"""
import unittest
import sys
import os
import logging
from unittest.mock import MagicMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Mock LLM agent BEFORE importing understanding
sys.modules['src.agents.llm_agent'] = MagicMock()

from src.intents.estate.understanding import EstateUnderstanding
from src.schemas.conversation_state import ConversationState

class TestEstateUnderstanding(unittest.TestCase):

    def setUp(self):
        self.understanding_layer = EstateUnderstanding()
        self.state = ConversationState()
        
        # Mock the agent inside the instance
        self.understanding_layer.agent = MagicMock()

    def test_process_search_intent(self):
        logger.info("Testing process_search_intent...")
        
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = '{"intent": "search_apartment", "confidence": 0.9, "slots": {"du_an": "Q7 Riverside", "so_phong_ngu": 2}}'
        self.understanding_layer.agent.run.return_value = mock_response
        
        message = "Tìm căn 2 phòng ngủ ở Q7 Riverside"
        updated_state, nlu_result = self.understanding_layer.process(message, self.state)
        
        logger.info(f"  Input: '{message}'")
        logger.info(f"  NLU Result: {nlu_result}")
        
        self.assertEqual(nlu_result["intent"], "search_apartment")
        self.assertEqual(nlu_result["slots"]["du_an"], "Q7Riverside") # Normalized
        self.assertEqual(nlu_result["slots"]["so_phong_ngu"], 2)
        
        # Verify state update
        self.assertEqual(updated_state.last_intent, "search_apartment")
        self.assertEqual(updated_state.slots["du_an"], "Q7Riverside")

    def test_process_negation(self):
        logger.info("Testing process_negation...")
        
        # Mock LLM response for negation
        mock_response = MagicMock()
        mock_response.content = '{"intent": "search_apartment", "confidence": 0.8, "slots": {"du_an": "CLEAR"}}'
        self.understanding_layer.agent.run.return_value = mock_response
        
        # Set initial state
        self.state.slots = {"du_an": "Q7Riverside"}
        
        message = "Không phải Q7 Riverside"
        updated_state, nlu_result = self.understanding_layer.process(message, self.state)
        
        logger.info(f"  Input: '{message}'")
        logger.info(f"  NLU Result: {nlu_result}")
        
        # Should be "CLEAR" in NLU result (indicating the intent to clear)
        self.assertEqual(nlu_result["slots"]["du_an"], "CLEAR")
        
        # Should be removed from state (set to None)
        self.assertIsNone(updated_state.slots["du_an"])

    def test_process_json_error(self):
        logger.info("Testing process_json_error...")
        
        # Mock invalid JSON response
        mock_response = MagicMock()
        mock_response.content = 'Invalid JSON'
        self.understanding_layer.agent.run.return_value = mock_response
        
        message = "Blah blah"
        updated_state, nlu_result = self.understanding_layer.process(message, self.state)
        
        logger.info(f"  NLU Result (Fallback): {nlu_result}")
        
        # Should fallback to default
        self.assertEqual(nlu_result["intent"], "search_apartment")
        self.assertEqual(nlu_result["confidence"], 1.0) # Default
        self.assertEqual(nlu_result["slots"], {})

if __name__ == '__main__':
    unittest.main()
