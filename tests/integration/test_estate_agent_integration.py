"""Lightweight integration test for EstateAgent using real Gemini model.

- Chạy end-to-end EstateAgent.invoke (không mock)
- Skip nếu chưa cấu hình GEMINI_API_KEY
"""
import os
import sys
import pytest

# Add src to path (2 levels up from tests/integration)
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.core.config import config
from src.agents.estate_agent import EstateAgent


@pytest.mark.integration
@pytest.mark.skipif(not config.GEMINI_API_KEY, reason="GEMINI_API_KEY is not configured")
def test_estate_agent_real_invoke_smoke():
    """Smoke test: gọi thật EstateAgent.invoke với Gemini.

    Mục tiêu:
    - Xác nhận code khởi tạo model/agent không crash
    - Nhận được một chuỗi trả lời không rỗng

    Lưu ý: test này phụ thuộc mạng & API Gemini nên chỉ nên chạy
    khi bạn đã cấu hình GEMINI_API_KEY và chấp nhận gọi API thật.
    """

    agent = EstateAgent()
    response = agent.invoke("Xin chào, em cần tư vấn mua căn hộ.", thread_id="pytest-smoke")

    assert isinstance(response, str)
    assert len(response.strip()) > 0
