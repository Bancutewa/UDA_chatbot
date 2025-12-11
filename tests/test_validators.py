"""
Unit tests for SlotValidator
"""
import unittest
import sys
import os

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.services.validators import slot_validator
from src.core import settings

class TestSlotValidator(unittest.TestCase):

    def test_validate_price(self):
        logger.info("Testing validate_price...")
        
        # Valid cases
        logger.info("  Testing valid price: 3 billion")
        self.assertIsNone(slot_validator.validate_price(3_000_000_000))
        logger.info("  Testing valid price range: 2-4 billion")
        self.assertIsNone(slot_validator.validate_price({"min": 2_000_000_000, "max": 4_000_000_000}))

        # Invalid cases
        logger.info("  Testing invalid price: -1")
        self.assertIsNotNone(slot_validator.validate_price(-1))
        logger.info("  Testing invalid price: 100 (too low)")
        self.assertIsNotNone(slot_validator.validate_price(100)) # Too low
        logger.info("  Testing invalid price: 200 billion (too high)")
        self.assertIsNotNone(slot_validator.validate_price(200_000_000_000)) # Too high
        logger.info("  Testing invalid range: min > max")
        self.assertIsNotNone(slot_validator.validate_price({"min": 5_000_000_000, "max": 3_000_000_000})) # Min > Max

    def test_validate_bedrooms(self):
        logger.info("Testing validate_bedrooms...")
        
        # Valid cases
        self.assertIsNone(slot_validator.validate_bedrooms(2))
        self.assertIsNone(slot_validator.validate_bedrooms({"min": 1, "max": 3}))

        # Invalid cases
        self.assertIsNotNone(slot_validator.validate_bedrooms(-1))
        self.assertIsNotNone(slot_validator.validate_bedrooms(20)) # Too many
        self.assertIsNotNone(slot_validator.validate_bedrooms({"min": 3, "max": 1})) # Min > Max

    def test_validate_area(self):
        logger.info("Testing validate_area...")
        
        # Valid cases
        self.assertIsNone(slot_validator.validate_area(70))
        self.assertIsNone(slot_validator.validate_area({"min": 50, "max": 100}))

        # Invalid cases
        self.assertIsNotNone(slot_validator.validate_area(-10))
        self.assertIsNotNone(slot_validator.validate_area(5)) # Too small
        self.assertIsNotNone(slot_validator.validate_area(20000)) # Too big

    def test_validate_slots(self):
        logger.info("Testing validate_slots (combined)...")
        
        # Mixed valid/invalid
        slots = {
            "gia_ban": 100, # Invalid
            "so_phong_ngu": 2 # Valid
        }
        errors = slot_validator.validate_slots(slots)
        logger.info(f"  Errors found: {errors}")
        self.assertEqual(len(errors), 1)
        self.assertIn("Giá bán", errors[0])

if __name__ == '__main__':
    unittest.main()
