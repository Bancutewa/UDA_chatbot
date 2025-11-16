"""
Intent Registry - Quản lý các intent handlers
"""
from typing import Dict, Type, Optional
from agno.agent import Agent
from .base_intent import BaseIntent
from .general_chat_intent import GeneralChatIntent
from .generate_image_intent import GenerateImageIntent
from .generate_audio_intent import GenerateAudioIntent
from .bds_intent import BDSIntent


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
        self.register_intent("estate_query", BDSIntent)

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

# Global registry instance
intent_registry = IntentRegistry()
