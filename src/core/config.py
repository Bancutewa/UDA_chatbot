"""
Configuration management
"""
import os
from typing import Optional
from dotenv import load_dotenv

# MongoDB imports (optional)
try:
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
except ImportError:
    MongoClient = None
    MONGODB_AVAILABLE = False

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""

    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    ELEVEN_LABS_API_KEY: str = os.getenv("ELEVEN_LABS_API_KEY", "").strip()
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "").strip()

    # Email Configuration
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "").strip()
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "").strip()
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")

    # Model Configuration
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Embedding Configuration
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME","AITeamVN/Vietnamese_Embedding").strip()

    # Qdrant Configuration
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "real_estate_listings")
    
    # Application Base URL (for email links)
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8501")

    # Audio Configuration
    AUDIO_VOICE_ID: str = "Nguyễn Ngân (Female, Vietnamese)"
    AUDIO_MODEL: str = "eleven_turbo_v2_5"
    AUDIO_TARGET_DIR: str = "data/audio_generations"

    # Database Configuration
    MONGODB_URL: str = os.getenv("MONGODB_URL") or os.getenv("MONGODB_URI", "")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "real_estate_db")

    # Fallback to local JSON if MongoDB not configured
    USE_MONGODB: bool = bool(MONGODB_URL.strip())

    # File Paths (fallback for local storage)
    CHAT_SESSIONS_FILE: str = "chat_sessions.json"
    AUDIO_GENERATIONS_DIR: str = "data/audio_generations"
    VISIT_SCHEDULES_FILE: str = "data/visit_schedules.json"
    ADMIN_CALENDAR_FILE: str = "data/admin_calendar.json"

    # MongoDB Client (lazy loaded)
    _mongodb_client: Optional[MongoClient] = None

    @property
    def mongodb_client(self) -> MongoClient:
        """Get MongoDB client (lazy loaded)"""
        if not MONGODB_AVAILABLE:
            raise ImportError("pymongo not installed. Run: pip install pymongo")

        if not self.MONGODB_URL:
            raise ValueError("MONGODB_URL not configured")

        if self._mongodb_client is None:
            try:
                self._mongodb_client = MongoClient(self.MONGODB_URL, serverSelectionTimeoutMS=5000)
                # Test connection
                self._mongodb_client.admin.command('ping')
            except Exception as e:
                raise ValueError(f"Failed to connect to MongoDB: {e}")

        return self._mongodb_client

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required. Set it in environment or .env file")

        # Create directories if they don't exist
        os.makedirs(cls.AUDIO_TARGET_DIR, exist_ok=True)
        schedules_dir = os.path.dirname(cls.VISIT_SCHEDULES_FILE)
        if schedules_dir:
            os.makedirs(schedules_dir, exist_ok=True)
        calendar_dir = os.path.dirname(cls.ADMIN_CALENDAR_FILE)
        if calendar_dir:
            os.makedirs(calendar_dir, exist_ok=True)

        return True

# Global config instance
config = Config()
