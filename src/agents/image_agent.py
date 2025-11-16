"""
Image Agent - Pollinations agent for image generation
"""

from .llm_agent import llm_agent
from ..core.settings import IMAGE_SYSTEM_PROMPT
from ..core.logger import logger
from ..core.exceptions import AgentInitializationError

class ImageAgent:
    """Image generation agent using Pollinations"""

    def __init__(self):
        try:
            # Create single agent for image prompt generation (giống code cũ)
            self.agent = llm_agent.create_agent(
                name="Image Prompt Generator",
                instructions=[IMAGE_SYSTEM_PROMPT],
                description="Generate detailed image prompts for Pollinations AI",
                markdown=False,
                debug_mode=False
            )

            logger.info("Image Agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Image Agent: {e}")
            self.agent = None

    def is_available(self) -> bool:
        """Check if image generation is available"""
        return self.agent is not None

# Global instance
image_agent = ImageAgent()
