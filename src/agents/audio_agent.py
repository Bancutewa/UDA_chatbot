"""
Audio Agent - ElevenLabs agent for audio generation
"""
import os
from typing import Optional

try:
    from agno.tools.eleven_labs import ElevenLabsTools
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ElevenLabsTools = None
    ELEVENLABS_AVAILABLE = False

try:
    from agno.tools.firecrawl import FirecrawlTools
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FirecrawlTools = None
    FIRECRAWL_AVAILABLE = False

from .llm_agent import llm_agent
from ..core.config import config
from ..core.settings import AUDIO_VOICE_OPTIONS, DEFAULT_VOICE_ID, DEFAULT_AUDIO_MODEL
from ..core.logger import logger
from ..core.exceptions import AgentInitializationError

class AudioAgent:
    """Audio generation agent using ElevenLabs"""

    def __init__(self):
        if not ELEVENLABS_AVAILABLE:
            logger.warning("ElevenLabs dependencies not available. Audio generation will be disabled.")
            self.agent = None
            return

        try:
            elevenlabs_api_key = config.ELEVEN_LABS_API_KEY
            firecrawl_api_key = config.FIRECRAWL_API_KEY

            if not elevenlabs_api_key:
                logger.warning("ELEVEN_LABS_API_KEY not found. Audio generation will be disabled.")
                self.agent = None
                return

            tools = [
                ElevenLabsTools(
                    voice_id=DEFAULT_VOICE_ID,
                    model_id=DEFAULT_AUDIO_MODEL,
                    target_directory=config.AUDIO_TARGET_DIR,
                    api_key=elevenlabs_api_key,
                )
            ]

            if firecrawl_api_key and FIRECRAWL_AVAILABLE:
                tools.append(FirecrawlTools(api_key=firecrawl_api_key))

            self.agent = llm_agent.create_agent(
                name="Audio Generation Agent",
                instructions=[
                    "When the user provides text or a URL:",
                    "1. If it's a URL, use FirecrawlTools to scrape the content first",
                    "2. Create a concise summary of the content that is NO MORE than 3000 characters long",
                    "3. The summary should capture the main points while being engaging and conversational",
                    "4. Use the ElevenLabsTools to convert the text/summary to audio",
                    "5. Ensure the text is within the 3000 character limit to avoid ElevenLabs API limits",
                ],
                description="You are an AI agent that can generate audio using the ElevenLabs API.",
                markdown=True,
                debug_mode=False
            )

            # Add tools to agent
            self.agent.tools = tools

            logger.info("Audio Agent initialized")

        except Exception as e:
            logger.error(f"Failed to initialize Audio Agent: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.agent = None

    def is_available(self) -> bool:
        """Check if audio generation is available"""
        return self.agent is not None and ELEVENLABS_AVAILABLE

    def get_voice_options(self) -> dict:
        """Get available voice options"""
        return AUDIO_VOICE_OPTIONS

    def generate_audio(self, description: str):
        """
        Generate audio from description using the agent

        Args:
            description: Text or URL to convert to audio

        Returns:
            Agent response with audio generation result
        """
        if not self.is_available():
            raise AgentInitializationError("Audio agent is not available")

        try:
            response = self.agent.run(f"Convert this content to audio: {description}")
            return response
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            raise e

# Global instance
audio_agent = AudioAgent()
