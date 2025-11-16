"""
Intent handler cho generate audio
"""
from typing import Dict, Any, Optional, Tuple
from .base_intent import BaseIntent

from ..services.audio_service import audio_service


class GenerateAudioIntent(BaseIntent):
    """Intent handler cho việc tạo audio"""

    @property
    def intent_name(self) -> str:
        return "generate_audio"

    @property
    def system_prompt(self) -> str:
        return "Bạn là AI hỗ trợ tạo audio. Nhận text/URL và chuyển thành nội dung audio."

    def get_response(self, data: Dict[str, Any], context: Optional[str] = None) -> str:
        """
        Xử lý response cho generate audio

        Args:
            data: Chứa key "description" với text hoặc URL
            context: Không sử dụng cho intent này

        Returns:
            HTML audio player hoặc thông báo lỗi
        """
        description = data.get("description", "").strip()

        if not description:
            return "❌ Vui lòng cung cấp text hoặc URL để tạo audio."

        try:
            html_content, audio_path = audio_service.generate_audio(description)
            return html_content
        except Exception as e:
            return f"❌ Lỗi tạo audio: {str(e)}"
