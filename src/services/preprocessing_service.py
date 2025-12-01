"""
Preprocessing Service
Responsible for normalizing user input before NLU processing.
"""
import re
from typing import Optional, Union, Dict, Any
from ..core import settings
from ..core.logger import logger

class PreprocessingService:
    """Service for text normalization and preprocessing"""

    def normalize_project(self, text: str) -> Optional[str]:
        """
        Normalize project name.
        Example: "q7 riverside" -> "Q7Riverside"
        """
        if not text:
            return None
            
        text_lower = text.lower().strip()
        
        # Check exact mappings first
        for key, value in settings.PROJECT_NAME_MAPPING.items():
            if key in text_lower:
                return value
                
        return None

    def normalize_direction(self, text: str) -> Optional[str]:
        """
        Normalize direction.
        Example: "đn" -> "Đông Nam"
        """
        if not text:
            return None
            
        text_lower = text.lower().strip()
        return settings.DIRECTION_SHORTCUTS.get(text_lower)

    def normalize_furniture(self, text: str) -> Optional[str]:
        """
        Normalize furniture status.
        Example: "full nội thất" -> "Full"
        """
        if not text:
            return None
            
        text_lower = text.lower().strip()
        
        for key, value in settings.FURNITURE_MAPPING.items():
            if key in text_lower:
                return value
                
        return None

    def normalize_price(self, text: str) -> Optional[int]:
        """
        Normalize price string to integer (VND).
        Example: "3 tỷ" -> 3000000000
        """
        if not text:
            return None
            
        text_lower = text.lower().strip()
        
        # Simple regex for number + unit
        # Matches: "3 tỷ", "3.5 ty", "800 trieu", "800tr"
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*(tỷ|ty|triệu|tr|nghìn|k)?", text_lower)
        
        if match:
            amount_str = match.group(1).replace(',', '.')
            unit = match.group(2)
            
            try:
                amount = float(amount_str)
                
                if unit in ["tỷ", "ty"]:
                    return int(amount * 1_000_000_000)
                elif unit in ["triệu", "tr"]:
                    return int(amount * 1_000_000)
                elif unit in ["nghìn", "k"]:
                    return int(amount * 1_000)
                else:
                    # No unit, assume full number if large, or maybe billions if small?
                    # For safety, if < 1000, assume billions? No, that's risky.
                    # If user types "3000", is it 3000 VND or 3000 USD or 3000 Ty?
                    # Let's assume raw number if no unit.
                    return int(amount)
            except ValueError:
                return None
                
        return None

    def normalize_area(self, text: str) -> Optional[float]:
        """
        Normalize area string to float.
        Example: "70m2" -> 70.0
        """
        if not text:
            return None
            
        text_lower = text.lower().strip()
        
        # Matches: "70m2", "70 m2", "70.5"
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*(m2|m vuông|mét vuông)?", text_lower)
        
        if match:
            amount_str = match.group(1).replace(',', '.')
            try:
                return float(amount_str)
            except ValueError:
                return None
                
        return None

    def normalize_text(self, text: str) -> str:
        """
        General text normalization.
        - Lowercase
        - Remove extra spaces
        """
        if not text:
            return ""
        return " ".join(text.strip().split()).lower()

# Singleton
preprocessing_service = PreprocessingService()
