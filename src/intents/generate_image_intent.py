"""
Intent handler cho generate image
"""
from typing import Dict, Any, Optional
from .base_intent import BaseIntent

from ..services.image_service import image_service


class GenerateImageIntent(BaseIntent):
    """Intent handler cho việc tạo ảnh"""

    @property
    def intent_name(self) -> str:
        return "generate_image"

    @property
    def system_prompt(self) -> str:
        return "Bạn là AI hỗ trợ tạo ảnh. Nhận description và chuyển thành prompt chi tiết."

    @property
    def description(self) -> str:
        return "Người dùng muốn tạo ảnh, vẽ, generate image, tạo hình ảnh. Từ khóa: vẽ, tạo ảnh, generate image, hình ảnh, bức ảnh."

    @property
    def keywords(self) -> list[str]:
        return ["vẽ", "tạo ảnh", "generate image", "hình ảnh", "bức ảnh"]

    def get_response(self, data: Dict[str, Any], context: Optional[str] = None) -> str:
        """
        Xử lý response cho generate image

        Args:
            data: Chứa key "description" với mô tả ảnh
            context: Không sử dụng cho intent này

        Returns:
            Response với thông tin ảnh được tạo
        """
        description = data.get("description", "").strip()

        if not description:
            return "❌ Vui lòng cung cấp mô tả cho ảnh bạn muốn tạo."

        try:
            result = image_service.generate_image(description)
            return result
        except Exception as e:
            return f"❌ Lỗi tạo ảnh: {str(e)}"
