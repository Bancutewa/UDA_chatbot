"""
Slot Validation Service
Responsible for validating extracted slots against business rules and constraints.
"""
from typing import Dict, Any, List, Optional
from ..core import settings
from ..core.logger import logger

class SlotValidator:
    """Validator for NLU slots"""

    def validate_slots(self, slots: Dict[str, Any]) -> List[str]:
        """
        Validate all slots.
        Returns a list of error messages (empty if valid).
        """
        errors = []
        
        # Validate Price
        if slots.get("gia_ban"):
            price_error = self.validate_price(slots["gia_ban"])
            if price_error:
                errors.append(price_error)

        # Validate Bedrooms
        if slots.get("so_phong_ngu"):
            bedroom_error = self.validate_bedrooms(slots["so_phong_ngu"])
            if bedroom_error:
                errors.append(bedroom_error)

        # Validate Area
        if slots.get("dien_tich"):
            area_error = self.validate_area(slots["dien_tich"])
            if area_error:
                errors.append(area_error)

        return errors

    def validate_price(self, price: Any) -> Optional[str]:
        """Validate price range or value"""
        try:
            if isinstance(price, dict):
                min_p = price.get("min", 0)
                max_p = price.get("max", float("inf"))
                
                if min_p < 0 or max_p < 0:
                    return "Giá bán không thể là số âm."
                if min_p > max_p:
                    return "Giá tối thiểu không thể lớn hơn giá tối đa."
                
                # Check reasonable limits (e.g. < 100 million or > 100 billion)
                # But be careful with "thue" vs "ban". Assuming "ban" for now.
                if max_p < settings.MIN_VALID_PRICE and max_p != float("inf"):
                     return f"Giá bán có vẻ quá thấp (dưới {settings.MIN_VALID_PRICE/1_000_000} triệu)."
                
            elif isinstance(price, (int, float)):
                if price < 0:
                    return "Giá bán không thể là số âm."
                if price < settings.MIN_VALID_PRICE:
                    return f"Giá bán có vẻ quá thấp (dưới {settings.MIN_VALID_PRICE/1_000_000} triệu)."
                if price > settings.MAX_VALID_PRICE:
                    return f"Giá bán có vẻ quá cao (trên {settings.MAX_VALID_PRICE/1_000_000_000} tỷ)."
                    
        except Exception as e:
            logger.error(f"Error validating price: {e}")
            return "Giá bán không hợp lệ."
            
        return None

    def validate_bedrooms(self, bedrooms: Any) -> Optional[str]:
        """Validate number of bedrooms"""
        try:
            if isinstance(bedrooms, dict):
                min_b = bedrooms.get("min", 0)
                max_b = bedrooms.get("max", 10)
                if min_b < 0 or max_b < 0:
                    return "Số phòng ngủ không thể âm."
                if min_b > max_b:
                    return "Số phòng ngủ tối thiểu không thể lớn hơn tối đa."
            else:
                val = int(bedrooms)
                if val < settings.MIN_BEDROOMS:
                    return f"Số phòng ngủ tối thiểu là {settings.MIN_BEDROOMS}."
                if val > settings.MAX_BEDROOMS:
                    return f"Số phòng ngủ tối đa là {settings.MAX_BEDROOMS}."
        except ValueError:
            return "Số phòng ngủ phải là số."
        return None

    def validate_area(self, area: Any) -> Optional[str]:
        """Validate area"""
        try:
            if isinstance(area, dict):
                min_a = area.get("min", 0)
                max_a = area.get("max", float("inf"))
                if min_a < 0:
                    return "Diện tích không thể âm."
                if min_a > max_a:
                    return "Diện tích tối thiểu không thể lớn hơn tối đa."
            else:
                val = float(area)
                if val < settings.MIN_AREA:
                    return f"Diện tích có vẻ quá nhỏ (dưới {settings.MIN_AREA}m2)."
                if val > settings.MAX_AREA:
                    return f"Diện tích có vẻ quá lớn (trên {settings.MAX_AREA}m2)."
        except ValueError:
            return "Diện tích phải là số."
        return None

# Singleton
slot_validator = SlotValidator()
