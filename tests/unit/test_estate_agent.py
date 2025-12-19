"""Tests for EstateAgent (new agent-based flow).

These tests focus on the Python wrapper logic in EstateAgent.invoke,
not on calling Gemini or LangGraph thật. Mọi dependency nặng đều được mock.
"""
import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import types as _types

# Add src to path (2 levels up: tests/unit -> project root)
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

# Stub external heavy dependencies so that importing estate_agent không yêu cầu cài langchain/langgraph thật
import sys as _sys

_sys.modules.setdefault(
    "langchain_google_genai",
    _types.SimpleNamespace(ChatGoogleGenerativeAI=MagicMock()),
)
_sys.modules.setdefault(
    "langchain.agents",
    _types.SimpleNamespace(create_agent=MagicMock()),
)
_sys.modules.setdefault(
    "langchain_core.messages",
    _types.SimpleNamespace(HumanMessage=MagicMock()),
)
_sys.modules.setdefault(
    "langgraph.checkpoint.mongodb",
    _types.SimpleNamespace(MongoDBSaver=MagicMock()),
)
_sys.modules.setdefault(
    "langchain.agents.middleware",
    _types.SimpleNamespace(SummarizationMiddleware=MagicMock()),
)
_sys.modules.setdefault(
    "langchain.tools",
    _types.SimpleNamespace(tool=MagicMock()),
)
_sys.modules.setdefault(
    "pymongo",
    _types.SimpleNamespace(MongoClient=MagicMock()),
)


def test_estate_agent_invoke_basic():
    """EstateAgent.invoke phải:
    - Gọi agent.invoke với thread_id được truyền vào config
    - Trả về chuỗi text cuối cùng từ messages[-1].content
    - Xử lý được cả content là string và content là list các block text
    """

    # Import module sau khi đã thêm src vào sys.path
    from src.agents import estate_agent as estate_agent_module

    # Patch dependencies ngay trên module đã import
    with patch.object(estate_agent_module, "ChatGoogleGenerativeAI"), patch.object(
        estate_agent_module, "create_agent"
    ) as mock_create_agent:
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent

        # Lần gọi đầu: content là string đơn giản
        first_response = {
            "messages": [
                SimpleNamespace(content="Xin chào, em là Realtor hỗ trợ anh/chị ạ."),
            ]
        }

        # Lần gọi thứ hai: content là list các block (giống cấu trúc rich content)
        second_response = {
            "messages": [
                SimpleNamespace(
                    content=[
                        {"type": "text", "text": "Dạ em tóm tắt giúp anh/chị:"},
                        {"type": "text", "text": "- Căn 2PN, diện tích 70m2."},
                    ]
                )
            ]
        }

        mock_agent.invoke.side_effect = [first_response, second_response]

        # Tạo instance EstateAgent với dependencies đã được patch
        agent = estate_agent_module.EstateAgent()

        # Gọi lần 1: content là string
        result1 = agent.invoke("Xin chào", thread_id="session-1")
        assert "Realtor" in result1

        # Đảm bảo agent.invoke được gọi với config thread_id đúng
        mock_agent.invoke.assert_any_call(
            {"messages": [{"role": "user", "content": "Xin chào"}]},
            config={"configurable": {"thread_id": "session-1"}},
        )

        # Gọi lần 2: content là list block text -> phải join bằng xuống dòng
        result2 = agent.invoke("Cho anh xem tóm tắt", thread_id="session-1")
        assert "tóm tắt" in result2
        assert "Căn 2PN" in result2
        assert "\n" in result2  # các block phải được nối bằng newline


def test_estate_agent_invoke_error_handling():
    """Khi agent.invoke ném exception, EstateAgent.invoke phải trả về
    thông báo lỗi user-friendly chứ không crash.
    """

    from src.agents import estate_agent as estate_agent_module

    with patch.object(estate_agent_module, "ChatGoogleGenerativeAI"), patch.object(
        estate_agent_module, "create_agent"
    ) as mock_create_agent:
        mock_agent = MagicMock()
        mock_create_agent.return_value = mock_agent
        mock_agent.invoke.side_effect = RuntimeError("fake error from agent")

        agent = estate_agent_module.EstateAgent()
        result = agent.invoke("Test lỗi", thread_id="session-err")

        assert "Xin lỗi" in result  # thông điệp fallback định nghĩa trong estate_agent
