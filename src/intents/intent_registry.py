"""
Intent Registry - Quản lý các intent handlers
"""
from typing import Dict, Type, Optional, Any
from agno.agent import Agent
from .base_intent import BaseIntent
from .general_chat_intent import GeneralChatIntent
from .generate_image_intent import GenerateImageIntent
from .generate_audio_intent import GenerateAudioIntent
from .schedule_visit_intent import ScheduleVisitIntent
from .estate_query_intent import EstateQueryIntent


class IntentRegistry:
    """Registry để quản lý các intent handlers"""

    def __init__(self):
        self._intents: Dict[str, Type[BaseIntent]] = {}
        self._instances: Dict[str, BaseIntent] = {}
        self._register_builtin_intents()

    def _register_builtin_intents(self):
        """Đăng ký các intent có sẵn"""
        self.register_intent("general_chat", GeneralChatIntent)
        self.register_intent("generate_image", GenerateImageIntent)
        self.register_intent("generate_audio", GenerateAudioIntent)
        self.register_intent("schedule_visit", ScheduleVisitIntent)
        self.register_intent("estate_query", EstateQueryIntent)

    def register_intent(self, intent_name: str, intent_class: Type[BaseIntent]):
        """Đăng ký một intent mới"""
        self._intents[intent_name] = intent_class

    def get_intent_names(self) -> list[str]:
        """Lấy danh sách tên các intent đã đăng ký"""
        return list(self._intents.keys())

    def get_intent_instance(self, intent_name: str, agent: Optional[Agent] = None) -> Optional[BaseIntent]:
        """
        Lấy instance của intent với agent cụ thể
        Tạo mới nếu chưa có hoặc agent khác
        """
        if intent_name not in self._intents:
            return None

        # Tạo key unique cho intent + agent
        key = f"{intent_name}_{id(agent) if agent else 'no_agent'}"

        if key not in self._instances:
            intent_class = self._intents[intent_name]
            self._instances[key] = intent_class(agent)

        return self._instances[key]

    def generate_system_prompt(self) -> str:
        """Tạo system prompt động dựa trên các intent đã đăng ký"""
        prompt = """Bạn là một AI phân tích ý định (Intent Classification).
Nhiệm vụ: Phân tích câu hỏi của người dùng và trả về đúng intent trong danh sách dưới đây.

QUAN TRỌNG:
1. Chỉ trả về JSON thuần túy, không có markdown (```json ... ```).
2. Nếu câu hỏi liên quan đến Bất Động Sản (tìm nhà, hỏi giá, khu vực, dự án...), BẮT BUỘC chọn 'estate_query'.
3. Nếu không chắc chắn, hãy chọn 'general_chat'.

Danh sách intents:
"""
        for name, intent_cls in self._intents.items():
            try:
                instance = intent_cls(None)
                prompt += f"- '{name}': {instance.description}\n"
            except Exception as e:
                print(f"Error getting description for {name}: {e}")

        prompt += """
Ví dụ JSON output:
{"intent": "estate_query", "message": "Tìm căn hộ 2 phòng ngủ"}
HOẶC
{"intent": "general_chat", "message": "Chào bạn"}
"""
        return prompt

    def get_fallback_intent(self, message: str) -> Dict[str, Any]:
        """Tìm intent dựa trên keywords khi LLM fail"""
        message_lower = message.lower()
        
        for name, intent_cls in self._intents.items():
            try:
                instance = intent_cls(None)
                if any(k in message_lower for k in instance.keywords):
                    return {"intent": name, "message": message, "description": message}
            except Exception:
                continue
                
        return {"intent": "general_chat", "message": message}

# Global registry instance
intent_registry = IntentRegistry()
