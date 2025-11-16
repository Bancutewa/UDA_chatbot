"""
Image Agent - Pollinations agent for image generation
"""
from typing import Optional

try:
    from agno.tools.pollinations import PollinationsTools
    POLLINATIONS_AVAILABLE = True
except ImportError:
    PollinationsTools = None
    POLLINATIONS_AVAILABLE = False

from .llm_agent import llm_agent
from ..core.settings import IMAGE_SYSTEM_PROMPT
from ..core.logger import logger
from ..core.exceptions import AgentInitializationError

class ImageAgent:
    """Image generation agent using Pollinations"""

    def __init__(self):
        if not POLLINATIONS_AVAILABLE:
            logger.warning("Pollinations dependencies not available. Image generation will be disabled.")
            self.agent = None
            return

        try:
            # Create image prompt generator agent
            self.prompt_agent = llm_agent.create_agent(
                name="Image Prompt Generator",
                instructions=[IMAGE_SYSTEM_PROMPT],
                description="Generate detailed image prompts",
                markdown=False,
                debug_mode=False
            )

            # Note: Pollinations doesn't require API key, it's a free service
            self.agent = llm_agent.create_agent(
                name="Image Generation Agent",
                instructions=["You are an AI that can generate images using Pollinations AI."],
                description="Generate images from prompts",
                markdown=True,
                debug_mode=False
            )

            logger.info("Image Agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Image Agent: {e}")
            self.agent = None

    def generate_image_prompt(self, description: str) -> str:
        """Generate detailed image prompt from simple description"""

        if not self.prompt_agent:
            return description

        try:
            prompt = f"User description: {description}"
            response = self.prompt_agent.run(prompt)

            # Extract prompt from <prompt: ...> tag
            response_text = response.content if hasattr(response, 'content') else str(response)

            if '<prompt:' in response_text and '>' in response_text:
                start = response_text.find('<prompt:') + 8
                end = response_text.find('>', start)
                if end > start:
                    return response_text[start:end].strip()

            # Fallback to original description
            return description

        except Exception as e:
            logger.error(f"Image prompt generation failed: {e}")
            return description

    def is_available(self) -> bool:
        """Check if image generation is available"""
        return self.agent is not None and POLLINATIONS_AVAILABLE

# Global instance
image_agent = ImageAgent()
