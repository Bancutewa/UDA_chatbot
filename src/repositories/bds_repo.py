"""
BDS Repository - Repository for real estate data
"""
import json
import os
from typing import List, Dict, Optional

from ..core.config import config
from ..core.logger import logger

class BDSRepository:
    """Repository for BDS (real estate) data"""

    def __init__(self):
        self.raw_data_dir = config.BDS_RAW_DATA_DIR
        os.makedirs(self.raw_data_dir, exist_ok=True)

    def save_raw_data(self, data: Dict[str, Any], filename: str):
        """Save raw BDS data to JSON file"""
        try:
            filepath = os.path.join(self.raw_data_dir, f"{filename}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved BDS raw data to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save BDS raw data: {e}")

    def load_raw_data(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load raw BDS data from JSON file"""
        try:
            filepath = os.path.join(self.raw_data_dir, f"{filename}.json")
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load BDS raw data: {e}")
        return None

    def list_raw_data_files(self) -> List[str]:
        """List all raw data files"""
        try:
            files = os.listdir(self.raw_data_dir)
            return [f for f in files if f.endswith('.json')]
        except Exception as e:
            logger.error(f"Failed to list raw data files: {e}")
            return []

    def get_bds_metadata(self) -> Dict[str, Any]:
        """Get BDS metadata summary"""
        files = self.list_raw_data_files()
        return {
            "total_files": len(files),
            "files": files,
            "raw_data_dir": self.raw_data_dir
        }

# Global instance
bds_repo = BDSRepository()
