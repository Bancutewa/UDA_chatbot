"""
Audio Service - Handle audio generation logic
"""
import os
import base64
from typing import Optional, Tuple

from ..agents.audio_agent import audio_agent
from ..core.config import config
from ..core.logger import logger
from ..core.exceptions import AudioGenerationError

class AudioService:
    """Service for audio generation operations"""

    def __init__(self):
        self.agent = audio_agent

    def generate_audio(self, description: str) -> Tuple[str, Optional[str]]:
        """
        Generate audio from description

        Args:
            description: Text or URL to convert to audio

        Returns:
            Tuple of (display_html, file_path)
        """
        if not self.agent.is_available():
            return "❌ Tính năng tạo audio hiện không khả dụng.", None

        try:
            # For now, create a simple HTML audio player
            # In real implementation, this would call ElevenLabs API

            # Create a placeholder audio file path
            import uuid
            audio_filename = f"{uuid.uuid4()}.mp3"
            audio_path = os.path.join(config.AUDIO_TARGET_DIR, audio_filename)

            # Create HTML audio player
            html_content = f"""
🎵 **Audio được tạo thành công!**

**📝 Nội dung:** {description[:100]}{'...' if len(description) > 100 else ''}

**🎤 Voice:** Nguyễn Ngân (Female, Vietnamese)

**📁 File:** {audio_filename}

*Audio player sẽ được hiển thị tại đây trong phiên bản đầy đủ.*
"""

            logger.info(f"Audio generation simulated for: {description[:50]}...")
            return html_content, audio_path

        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            raise AudioGenerationError(f"Audio generation failed: {e}")

    def is_available(self) -> bool:
        """Check if audio service is available"""
        return self.agent.is_available()

    def get_voice_options(self) -> dict:
        """Get available voice options"""
        return self.agent.get_voice_options() if self.agent else {}

# Global instance
audio_service = AudioService()
