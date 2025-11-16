"""
LLM Agent - Gemini API wrapper
"""
from typing import List, Optional, Any
from agno.agent import Agent
from agno.models.google import Gemini

from ..core.config import config
from ..core.logger import logger
from ..core.exceptions import AgentInitializationError

class LLMAgent:
    """Gemini LLM Agent wrapper"""

    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.model_id = config.GEMINI_MODEL_ID

        if not self.api_key:
            raise AgentInitializationError("GEMINI_API_KEY is required")

        try:
            self.model = Gemini(id=self.model_id, api_key=self.api_key)
            logger.info(f"LLM Agent initialized with model: {self.model_id}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM Agent: {e}")
            raise AgentInitializationError(f"LLM Agent initialization failed: {e}")

    def create_agent(self,
                    name: str,
                    instructions: List[str],
                    description: str = "",
                    markdown: bool = True,
                    debug_mode: bool = False) -> Agent:
        """Create an agent with the Gemini model"""

        return Agent(
            name=name,
            model=self.model,
            description=description,
            instructions=instructions,
            markdown=markdown,
            debug_mode=debug_mode
        )

    def run_prompt(self,
                   prompt: str,
                   instructions: Optional[List[str]] = None,
                   name: str = "LLM Agent") -> str:
        """Run a simple prompt"""

        agent = self.create_agent(
            name=name,
            instructions=instructions or ["You are a helpful AI assistant."],
            description=f"Agent for: {name}"
        )

        try:
            response = agent.run(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"LLM Agent run failed: {e}")
            raise AgentInitializationError(f"LLM run failed: {e}")

# Global instance
llm_agent = LLMAgent()
