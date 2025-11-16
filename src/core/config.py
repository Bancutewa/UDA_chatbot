"""
Configuration management
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""

    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    ELEVEN_LABS_API_KEY: str = os.getenv("ELEVEN_LABS_API_KEY", "").strip()
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "").strip()

    # Model Configuration
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_MODEL_ID: str = "gemini-2.5-flash"

    # Audio Configuration
    AUDIO_VOICE_ID: str = "Nguyễn Ngân (Female, Vietnamese)"
    AUDIO_MODEL: str = "eleven_turbo_v2_5"
    AUDIO_TARGET_DIR: str = "data/audio_generations"

    # Database Configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL") or os.getenv("MONGODB_URI", "")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "chatbot_db")

    # Fallback to local JSON if MongoDB not configured
    USE_MONGODB: bool = bool(MONGODB_URL.strip())

    # Vector Database
    VECTOR_DIMENSION: int = 768  # For text-embedding-3-small

    # File Paths (fallback for local storage)
    CHAT_SESSIONS_FILE: str = "chat_sessions.json"
    BDS_RAW_DATA_DIR: str = "data/bds_raw_data"
    AUDIO_GENERATIONS_DIR: str = "data/audio_generations"

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required. Set it in environment or .env file")

        # Create directories if they don't exist
        os.makedirs(cls.AUDIO_TARGET_DIR, exist_ok=True)
        os.makedirs(cls.BDS_RAW_DATA_DIR, exist_ok=True)

        return True

# Global config instance
config = Config()
