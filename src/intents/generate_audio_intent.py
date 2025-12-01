"""
Intent handler cho generate audio
"""
import os
from typing import Dict, Any, Optional, Tuple
from .base_intent import BaseIntent

from ..services.audio_service import audio_service


class GenerateAudioIntent(BaseIntent):
    """Intent handler cho việc tạo audio"""

    def __init__(self, agent):
        super().__init__(agent)
        self._audio_display_response = None  # Response đầy đủ cho display
        self._audio_history_response = None  # Response rút gọn cho history

    @property
    def intent_name(self) -> str:
        return "generate_audio"

    @property
    def system_prompt(self) -> str:
        return "Bạn là AI hỗ trợ tạo audio. Nhận text/URL và chuyển thành nội dung audio."

    @property
    def description(self) -> str:
        return "Người dùng muốn tạo audio, podcast, đọc văn bản, tạo âm thanh, phát âm. Từ khóa: đọc, phát, audio, âm thanh, podcast."

    @property
    def keywords(self) -> list[str]:
        return ["đọc", "phát", "audio", "âm thanh", "podcast"]

    def get_response(self, data: Dict[str, Any], context: Optional[str] = None) -> str:
        """
        Xử lý response cho generate audio

        Args:
            data: Chứa key "description" với text hoặc URL
            context: Không sử dụng cho intent này

        Returns:
            Response rút gọn cho chat history
        """
        description = data.get("description", "").strip()

        if not description:
            return "❌ Vui lòng cung cấp text hoặc URL để tạo audio."

        try:
            html_content, audio_path = audio_service.generate_audio(description)

            # Tạo display response (đầy đủ với HTML player)
            self._audio_display_response = html_content

            # Tạo history response (rút gọn, không có base64)
            filename = audio_path.split(os.sep)[-1] if audio_path else "unknown.mp3"
            self._audio_history_response = f"🎵 Audio được tạo: {description[:50]}{'...' if len(description) > 50 else ''} ({filename})"

            # Trả về history response để lưu vào chat history
            return self._audio_history_response

        except Exception as e:
            return f"❌ Lỗi tạo audio: {str(e)}"

    def get_display_response(self) -> str:
        """Lấy response đầy đủ cho display (với HTML player)"""
        return self._audio_display_response or ""

    def get_history_response(self) -> str:
        """Lấy response rút gọn cho chat history"""
        return self._audio_history_response or ""
