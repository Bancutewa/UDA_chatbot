"""
Image Service - Handle image generation logic
"""
import re
from urllib.parse import quote
from typing import Optional

from ..agents.image_agent import image_agent
from ..core.logger import logger
from ..core.exceptions import ImageGenerationError

class ImageService:
    """Service for image generation operations"""

    def __init__(self):
        self.agent = image_agent

    def generate_image(self, description: str) -> str:
        """
        Generate image from description

        Args:
            description: Image description

        Returns:
            Markdown with image URL or error message
        """
        if not self.agent or not self.agent.is_available():
            return "❌ Tính năng tạo ảnh hiện không khả dụng."

        if not description.strip():
            return "❌ Vui lòng cung cấp mô tả cho ảnh bạn muốn tạo."

        try:
            # Gọi Image Agent để tạo prompt chi tiết
            image_response = self.agent.agent.run(description)
            response_text = image_response.content if hasattr(image_response, 'content') else str(image_response)

            detailed_prompt = self._extract_image_prompt(response_text)

            if not detailed_prompt:
                # Fallback nếu image_agent không trả về tag <prompt>
                detailed_prompt = description  # Dùng tạm mô tả gốc
                logger.warning(f"No prompt tag found, using original description: {description}")

            # Generate image URL using Pollinations
            image_url = self._generate_image_url(detailed_prompt)

            logger.info(f"Generated image URL for: {description[:50]}...")

            # Trả về Markdown hoàn chỉnh (giống code cũ)
            return f"🖼️ **Hình ảnh của bạn:**\n\n![{detailed_prompt[:50]}...]({image_url})"

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise ImageGenerationError(f"Image generation failed: {e}")

    def is_available(self) -> bool:
        """Check if image service is available"""
        # Pollinations is always available as it's a free web service
        return True

    def _extract_image_prompt(self, message: str) -> str:
        """Extract detailed prompt from <prompt:...> tag"""
        match = re.search(r"<prompt:(.*?)>", message, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def _generate_image_url(self, detailed_prompt: str) -> str:
        """
        Generate image URL using Pollinations API

        Args:
            detailed_prompt: Detailed image prompt

        Returns:
            Image URL
        """
        try:
            # Encode prompt for URL
            prompt_encoded = quote(detailed_prompt)
            image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}"
            return image_url

        except Exception as e:
            logger.error(f"Error generating image URL: {e}")
            raise ImageGenerationError(f"Failed to generate image URL: {e}")

# Global instance
image_service = ImageService()
