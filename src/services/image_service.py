"""
Image Service - Handle image generation logic
"""
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
            Image URL or error message
        """
        if not self.agent.is_available():
            return "❌ Tính năng tạo ảnh hiện không khả dụng."

        try:
            # Generate detailed prompt
            detailed_prompt = self.agent.generate_image_prompt(description)
            logger.info(f"Generated image prompt: {detailed_prompt[:100]}...")

            # For now, return a placeholder response
            # In a real implementation, this would call the actual image generation API
            return f"🎨 **Ảnh được tạo thành công!**\n\n**Mô tả:** {description}\n\n**Prompt chi tiết:** {detailed_prompt}\n\n*Ảnh sẽ được hiển thị tại đây trong phiên bản đầy đủ.*"

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise ImageGenerationError(f"Image generation failed: {e}")

    def is_available(self) -> bool:
        """Check if image service is available"""
        return self.agent.is_available()

# Global instance
image_service = ImageService()
