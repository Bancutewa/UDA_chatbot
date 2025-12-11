"""
Unit tests for EstateDecision
"""
import unittest
import sys
import os
from unittest.mock import MagicMock

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.intents.estate.decision import estate_decision
from src.schemas.conversation_state import ConversationState
from src.core import settings

class TestEstateDecision(unittest.TestCase):

    def setUp(self):
        self.state = ConversationState()

    def test_decide_low_confidence(self):
        logger.info("Testing decide_low_confidence...")
        nlu_result = {"intent": "search_apartment", "confidence": 0.5}
        result = estate_decision.decide(self.state, nlu_result)
        logger.info(f"  Result action: {result['action']}")
        self.assertEqual(result["action"], "ASK_REPHRASE")

    def test_decide_show_details_success(self):
        logger.info("Testing decide_show_details_success...")
        self.state.slots = {"ma_can_ho": "V2.31.02"}
        nlu_result = {"intent": "show_details", "confidence": 0.9}
        result = estate_decision.decide(self.state, nlu_result)
        logger.info(f"  Result action: {result['action']}")
        self.assertEqual(result["action"], "SHOW_DETAILS")
        self.assertEqual(result["payload"]["ma_can_ho"], "V2.31.02")

    def test_decide_book_appointment_success(self):
        logger.info("Testing decide_book_appointment_success...")
        self.state.slots = {
            "ma_can_ho": "V2.31.02",
            "sdt": "0909123456",
            "thoi_gian": "10:00 AM"
        }
        nlu_result = {"intent": "book_appointment", "confidence": 0.9}
        result = estate_decision.decide(self.state, nlu_result)
        logger.info(f"  Result action: {result['action']}")
        self.assertEqual(result["action"], "BOOK_APPOINTMENT")

    def test_decide_book_appointment_missing_info(self):
        logger.info("Testing decide_book_appointment_missing_info...")
        self.state.slots = {"ma_can_ho": "V2.31.02"} # Missing sdt, thoi_gian
        nlu_result = {"intent": "book_appointment", "confidence": 0.9}
        result = estate_decision.decide(self.state, nlu_result)
        logger.info(f"  Result action: {result['action']}")
        self.assertEqual(result["action"], "ASK_SLOT")
        # Should ask for sdt or thoi_gian
        self.assertIn(result["payload"]["slot"], ["sdt", "thoi_gian"])

    def test_decide_search_no_criteria(self):
        logger.info("Testing decide_search_no_criteria...")
        self.state.slots = {} # No slots
        nlu_result = {"intent": "search_apartment", "confidence": 0.9}
        result = estate_decision.decide(self.state, nlu_result)
        logger.info(f"  Result action: {result['action']}")
        self.assertEqual(result["action"], "ASK_SLOT")
        self.assertEqual(result["payload"]["slot"], "criteria")

    def test_decide_search_with_criteria(self):
        logger.info("Testing decide_search_with_criteria...")
        self.state.slots = {"du_an": "Q7Riverside"}
        nlu_result = {"intent": "search_apartment", "confidence": 0.9}
        result = estate_decision.decide(self.state, nlu_result)
        logger.info(f"  Result action: {result['action']}")
        self.assertEqual(result["action"], "SEARCH_LISTINGS")
        self.assertEqual(result["payload"]["filters"]["du_an"], "Q7Riverside")

    def test_decide_search_validation_error(self):
        logger.info("Testing decide_search_validation_error...")
        self.state.slots = {"gia_ban": -100} # Invalid price
        nlu_result = {"intent": "search_apartment", "confidence": 0.9}
        result = estate_decision.decide(self.state, nlu_result)
        logger.info(f"  Result action: {result['action']}")
        self.assertEqual(result["action"], "NO_RESULT")
        self.assertIn("message", result["payload"])

if __name__ == '__main__':
    unittest.main()
