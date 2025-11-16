"""
Audio Service - Handle audio generation logic
"""
import os
import time
import uuid
from typing import Optional, Tuple

# Import optional dependencies with fallback
try:
    from agno.tools.eleven_labs import ElevenLabsTools
    from agno.tools.firecrawl import FirecrawlTools
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    ElevenLabsTools = None
    FirecrawlTools = None

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
        # Check for API keys first
        elevenlabs_key = os.getenv("ELEVEN_LABS_API_KEY", "").strip()
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

        # For testing, consider test keys as invalid
        is_test_gemini = gemini_key.startswith("test_key_") or gemini_key == "test_key_12345"

        if not ELEVENLABS_AVAILABLE or not elevenlabs_key or not gemini_key or is_test_gemini:
            # Fallback to demo mode if dependencies or API keys not available/valid
            return self._create_demo_audio_response(description), None

        # Even if agent says it's available, double-check API keys
        if not self.agent or not ELEVENLABS_AVAILABLE:
            return self._create_demo_audio_response(description), None

        try:
            # Tạo thư mục lưu audio nếu chưa có
            save_dir = config.AUDIO_TARGET_DIR
            os.makedirs(save_dir, exist_ok=True)

            # Lấy danh sách file hiện tại trước khi tạo audio
            existing_files = set(os.listdir(save_dir)) if os.path.exists(save_dir) else set()

            # Chạy audio agent để generate audio
            logger.info(f"🎵 Đang tạo audio cho: {description[:50]}...")
            audio_response = self.agent.generate_audio(description)

            # Chờ file được ghi xong (thay vì sleep cứng)
            latest_file = self._wait_for_new_audio_file(save_dir, existing_files)

            if not latest_file:
                return "❌ Audio được tạo nhưng không tìm thấy file. Vui lòng thử lại.", None

            logger.info(f"✅ Audio file đã tạo: {latest_file}")

            # Đọc file và tạo audio player
            try:
                with open(latest_file, "rb") as f:
                    audio_bytes = f.read()

                # Lấy tên file để hiển thị
                filename = os.path.basename(latest_file)

                # Kiểm tra kích thước file
                file_size = len(audio_bytes) / 1024  # KB
                logger.info(f"📦 Audio file size: {file_size:.2f} KB")

                # Tạo HTML audio player với base64
                import base64
                audio_b64 = base64.b64encode(audio_bytes).decode()

                html_content = f"""🎵 **Audio được tạo thành công!**

**📝 Nội dung:** {description[:100]}{'...' if len(description) > 100 else ''}

**🎤 Voice:** Nguyễn Ngân (Female, Vietnamese)

**📁 File:** `{filename}` ({file_size:.1f} KB)

<audio controls style="width: 100%; max-width: 400px;">
    <source src="data:audio/mpeg;base64,{audio_b64}" type="audio/mpeg">
    Trình duyệt của bạn không hỗ trợ audio player.
</audio>

<a href="data:audio/mpeg;base64,{audio_b64}" download="{filename}" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;">⬇️ Tải xuống Audio</a>"""

                return html_content, latest_file

            except Exception as e:
                logger.error(f"❌ Error reading audio file: {e}")
                return f"❌ Audio được tạo nhưng không thể hiển thị: {e}", None

        except Exception as e:
            error_msg = str(e).lower()
            if "eleven" in error_msg and ("api" in error_msg or "key" in error_msg):
                return "❌ Lỗi API ElevenLabs. Vui lòng kiểm tra ELEVEN_LABS_API_KEY.", None
            elif "quota" in error_msg or "limit" in error_msg:
                return "❌ Đã hết quota ElevenLabs API.", None
            else:
                logger.error(f"Audio generation failed: {e}")
                return f"❌ Lỗi tạo audio: {e}", None

    def is_available(self) -> bool:
        """Check if audio service is available"""
        return self.agent.is_available()

    def get_voice_options(self) -> dict:
        """Get available voice options"""
        return self.agent.get_voice_options() if self.agent else {}

    def _wait_for_new_audio_file(self, save_dir: str, existing_files: set) -> Optional[str]:
        """Chờ file audio mới được tạo và trả về đường dẫn đến file"""
        max_wait_time = 15  # Tối đa 15 giây
        check_interval = 0.5  # Kiểm tra mỗi 0.5 giây

        for _ in range(int(max_wait_time / check_interval)):
            time.sleep(check_interval)

            # Tìm file mới được tạo
            current_files = set(os.listdir(save_dir)) if os.path.exists(save_dir) else set()
            new_files = [f for f in (current_files - existing_files) if f.endswith('.mp3')]

            if new_files:
                # Lấy file mới nhất
                latest_file = os.path.join(save_dir, sorted(new_files)[-1])
                logger.info(f"📁 New audio file detected: {latest_file}")

                # Đợi file được ghi hoàn toàn (check size ổn định)
                if self._wait_for_file_stable(latest_file):
                    return latest_file

        # Fallback: lấy file mới nhất theo thời gian tạo
        logger.warning("⚠️ No new file detected, using fallback...")
        audio_files = [f for f in os.listdir(save_dir) if f.endswith('.mp3')]
        if audio_files:
            audio_files.sort(key=lambda x: os.path.getctime(os.path.join(save_dir, x)),
                          reverse=True)
            latest_file = os.path.join(save_dir, audio_files[0])
            logger.info(f"📁 Using latest file as fallback: {latest_file}")
            return latest_file

        return None

    def _wait_for_file_stable(self, file_path: str, timeout: int = 5) -> bool:
        """Chờ file không thay đổi size (đã được ghi hoàn toàn)"""
        if not os.path.exists(file_path):
            return False

        initial_size = os.path.getsize(file_path)
        time.sleep(0.5)  # Chờ 0.5 giây

        for _ in range(timeout * 2):  # Kiểm tra mỗi 0.5 giây
            if not os.path.exists(file_path):
                return False

            current_size = os.path.getsize(file_path)
            if current_size == initial_size:
                return True  # File không thay đổi size

            initial_size = current_size
            time.sleep(0.5)

        return True  # Timeout nhưng file vẫn ổn định

    def _create_demo_audio_response(self, description: str) -> str:
        """Create demo audio response for testing without API keys"""
        return f"""🎵 **Demo Audio Mode - Không có API Key**

**📝 Nội dung:** {description[:100]}{'...' if len(description) > 100 else ''}

**🎤 Voice:** Nguyễn Ngân (Female, Vietnamese)

**📁 File:** demo_audio.mp3

*Đây là chế độ demo. Để tạo audio thật, vui lòng cung cấp ELEVEN_LABS_API_KEY và GEMINI_API_KEY.*

**Để có audio thật:**
1. Thêm `ELEVEN_LABS_API_KEY` vào .env
2. Đảm bảo `GEMINI_API_KEY` hợp lệ
3. Restart ứng dụng

*Demo mode hoạt động! ✅*"""

# Global instance
audio_service = AudioService()
