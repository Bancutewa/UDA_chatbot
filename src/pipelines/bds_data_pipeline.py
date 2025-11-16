"""
BDS Data Pipeline - Process and prepare BDS data for RAG
"""
import os
import json
from typing import List, Dict, Any

from ..repositories.bds_repo import bds_repo
from ..core.logger import logger

class BDSDataPipeline:
    """Pipeline for processing BDS data"""

    def __init__(self):
        self.repo = bds_repo

    def process_raw_data(self, raw_data: Dict[str, Any], source_name: str) -> List[Dict[str, Any]]:
        """
        Process raw BDS data into structured format

        Args:
            raw_data: Raw scraped data
            source_name: Name of data source

        Returns:
            List of processed property records
        """
        try:
            processed_properties = []

            # Extract properties from raw data
            # This would depend on the actual data structure from scraping
            properties = raw_data.get("properties", [])

            for prop in properties:
                processed_prop = {
                    "title": prop.get("title", ""),
                    "price": prop.get("price", ""),
                    "area": prop.get("area", ""),
                    "location": prop.get("location", ""),
                    "description": prop.get("description", ""),
                    "property_type": prop.get("type", "unknown"),
                    "url": prop.get("url", ""),
                    "source": source_name,
                    "processed_at": "2025-01-01T00:00:00"  # Would use datetime.now()
                }
                processed_properties.append(processed_prop)

            logger.info(f"Processed {len(processed_properties)} properties from {source_name}")
            return processed_properties

        except Exception as e:
            logger.error(f"Failed to process BDS raw data: {e}")
            return []

    def save_processed_data(self, properties: List[Dict[str, Any]], filename: str):
        """Save processed BDS data"""
        try:
            self.repo.save_raw_data({"properties": properties}, f"processed_{filename}")
            logger.info(f"Saved processed BDS data: {filename}")
        except Exception as e:
            logger.error(f"Failed to save processed BDS data: {e}")

    def chunk_text_for_embedding(self, text: str, chunk_size: int = 500) -> List[str]:
        """
        Chunk text for embedding

        Args:
            text: Text to chunk
            chunk_size: Maximum chunk size

        Returns:
            List of text chunks
        """
        if not text:
            return []

        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)

        return chunks

    def prepare_for_vector_db(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare BDS data for vector database insertion

        Args:
            properties: List of property records

        Returns:
            List of records ready for vector DB
        """
        vector_records = []

        for prop in properties:
            # Create searchable text from property data
            searchable_text = f"""
            {prop.get('title', '')}
            {prop.get('description', '')}
            {prop.get('location', '')}
            {prop.get('property_type', '')}
            Giá: {prop.get('price', '')}
            Diện tích: {prop.get('area', '')}
            """.strip()

            # Chunk the text
            chunks = self.chunk_text_for_embedding(searchable_text)

            for chunk in chunks:
                record = {
                    "text": chunk,
                    "metadata": {
                        "property_id": prop.get("id", ""),
                        "title": prop.get("title", ""),
                        "price": prop.get("price", ""),
                        "location": prop.get("location", ""),
                        "source": prop.get("source", ""),
                        "url": prop.get("url", "")
                    }
                }
                vector_records.append(record)

        logger.info(f"Prepared {len(vector_records)} vector records")
        return vector_records

# Global instance
bds_data_pipeline = BDSDataPipeline()
