"""
Unit tests for PreprocessingService
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

from src.services.preprocessing_service import preprocessing_service

class TestPreprocessingService(unittest.TestCase):

    def test_normalize_project(self):
        logger.info("Testing normalize_project...")
        
        input_val = "Q7 Riverside"
        expected = "Q7Riverside"
        logger.info(f"  Input: '{input_val}' -> Expected: '{expected}'")
        self.assertEqual(preprocessing_service.normalize_project(input_val), expected)
        
        input_val = "riverside quận 7"
        logger.info(f"  Input: '{input_val}' -> Expected: '{expected}'")
        self.assertEqual(preprocessing_service.normalize_project(input_val), expected)
        
        input_val = "River Panorama"
        expected = "RiverPanorama"
        logger.info(f"  Input: '{input_val}' -> Expected: '{expected}'")
        self.assertEqual(preprocessing_service.normalize_project(input_val), expected)
        
        logger.info("  Input: 'Unknown Project' -> Expected: None")
        self.assertIsNone(preprocessing_service.normalize_project("Unknown Project"))

    def test_normalize_direction(self):
        logger.info("Testing normalize_direction...")
        self.assertEqual(preprocessing_service.normalize_direction("đn"), "Đông Nam")
        self.assertEqual(preprocessing_service.normalize_direction("Đông Nam"), "Đông Nam")
        self.assertEqual(preprocessing_service.normalize_direction("tây bắc"), "Tây Bắc")
        self.assertIsNone(preprocessing_service.normalize_direction("xyz"))

    def test_normalize_furniture(self):
        logger.info("Testing normalize_furniture...")
        self.assertEqual(preprocessing_service.normalize_furniture("full nội thất"), "Full")
        self.assertEqual(preprocessing_service.normalize_furniture("nhà trống"), "Trống")
        self.assertEqual(preprocessing_service.normalize_furniture("cơ bản"), "Cơ Bản")

    def test_normalize_price(self):
        logger.info("Testing normalize_price...")
        self.assertEqual(preprocessing_service.normalize_price("3 tỷ"), 3_000_000_000)
        self.assertEqual(preprocessing_service.normalize_price("3.5 tỷ"), 3_500_000_000)
        self.assertEqual(preprocessing_service.normalize_price("800 triệu"), 800_000_000)
        self.assertEqual(preprocessing_service.normalize_price("800tr"), 800_000_000)
        self.assertEqual(preprocessing_service.normalize_price("2 ty"), 2_000_000_000)

    def test_normalize_area(self):
        logger.info("Testing normalize_area...")
        self.assertEqual(preprocessing_service.normalize_area("70m2"), 70.0)
        self.assertEqual(preprocessing_service.normalize_area("70.5 m2"), 70.5)
        self.assertEqual(preprocessing_service.normalize_area("100 mét vuông"), 100.0)

if __name__ == '__main__':
    unittest.main()
