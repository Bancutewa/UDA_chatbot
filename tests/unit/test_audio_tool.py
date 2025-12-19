"""Smoke tests cho generate_audio_tool (ElevenLabs).

Mục tiêu:
- Kiểm tra hàm `generate_audio_tool` chạy được (không raise exception) khi có/không có API key.
- KHÔNG assert bắt buộc phải tạo file thành công (vì phụ thuộc quota, key, mạng...).
"""
import os
import pytest

# Thêm src vào path nếu cần
import sys
import os as _os
sys.path.append(_os.path.join(_os.path.dirname(__file__), "..", ".."))

from src.tools.audio_tools import generate_audio_tool


@pytest.mark.integration
def test_generate_audio_tool_smoke():
    """Gọi trực tiếp generate_audio_tool với câu text đơn giản.

    - Nếu không có ELEVEN_LABS_API_KEY: hàm nên trả về message lỗi thân thiện.
    - Nếu có key: hàm nên trả về string, thường chứa "Audio generated successfully" hoặc thông báo lỗi từ API.
    - Test này chỉ đảm bảo không ném exception và trả về chuỗi không rỗng.
    """

    text = "Đây là câu test audio đơn giản cho hệ thống chatbot."
    result = generate_audio_tool.invoke(text)

    assert isinstance(result, str)
    assert result.strip() != ""
