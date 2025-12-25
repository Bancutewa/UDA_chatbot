"""
Utility functions for working with listing data.
"""
from typing import Optional, Dict
from ..core.logger import logger


def extract_district_from_listing(listing_details: Dict) -> Optional[str]:
    """
    Extract district/location from listing data payload.
    
    Checks multiple possible field names in priority order:
    1. khu_vuc (khu vực)
    2. quan (quận)
    3. district
    4. Extract from dia_chi (địa chỉ) if available
    
    Args:
        listing_details: Dictionary containing listing payload from Qdrant
        
    Returns:
        District string (e.g., "Quận 7") or None if not found
    """
    if not listing_details:
        return None
    
    # Priority 1: khu_vuc (most common field name)
    district = listing_details.get("khu_vuc")
    if district:
        return _normalize_district(district)
    
    # Priority 2: quan
    district = listing_details.get("quan")
    if district:
        return _normalize_district(district)
    
    # Priority 3: district (English field name)
    district = listing_details.get("district")
    if district:
        return _normalize_district(district)
    
    # Priority 4: Extract from dia_chi (địa chỉ)
    dia_chi = listing_details.get("dia_chi")
    if dia_chi:
        # Try to extract district from address
        # Format might be: "123 Đường ABC, Quận 7, TP.HCM"
        # or "Quận 7, TP.HCM"
        district = _extract_district_from_address(dia_chi)
        if district:
            return _normalize_district(district)
    
    logger.warning(f"Could not extract district from listing. Available fields: {list(listing_details.keys())}")
    return None


def _normalize_district(district: str) -> str:
    """
    Normalize district string to standard format.
    
    Examples:
    - "quận 7" -> "Quận 7"
    - "Q7" -> "Quận 7"
    - "Quận 7" -> "Quận 7"
    """
    if not district:
        return ""
    
    district = str(district).strip()
    
    # If already in "Quận X" format, return as is
    if district.startswith("Quận "):
        return district
    
    # Try to extract number from "Q7", "q7", "quận 7", etc.
    import re
    # Pattern: "Q7", "q7", "quận 7", "quan 7", etc.
    pattern = re.compile(r'(?:q|quan|quận)\s*(\d+)', flags=re.IGNORECASE | re.UNICODE)
    match = pattern.search(district)
    if match:
        return f"Quận {match.group(1)}"
    
    # If contains number, assume it's a district number
    numbers = re.findall(r'\d+', district)
    if numbers:
        return f"Quận {numbers[0]}"
    
    # Return as is if no pattern matches
    return district


def _extract_district_from_address(address: str) -> Optional[str]:
    """
    Extract district from address string.
    
    Examples:
    - "123 Đường ABC, Quận 7, TP.HCM" -> "Quận 7"
    - "Quận 7, TP.HCM" -> "Quận 7"
    """
    if not address:
        return None
    
    import re
    # Pattern to find "Quận X" or "quận X" in address
    pattern = re.compile(r'(?:quận|quan|q)\s*(\d+)', flags=re.IGNORECASE | re.UNICODE)
    match = pattern.search(address)
    if match:
        return f"Quận {match.group(1)}"
    
    return None

