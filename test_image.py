#!/usr/bin/env python3
"""
Test image generation
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.image_service import image_service

def test_image_generation():
    """Test image generation"""
    print("🖼️ Testing image generation...")

    try:
        result = image_service.generate_image("một con mèo xinh xắn")
        if "❌" in result:
            print(f"❌ Image generation failed: {result}")
            return False
        elif "🖼️ **Hình ảnh của bạn:**" in result and "pollinations.ai" in result:
            print(f"✅ Image generation success!")
            return True
        else:
            print(f"⚠️ Unexpected result: {result[:100]}...")
            return False
    except Exception as e:
        print(f"❌ Image generation exception: {e}")
        return False

if __name__ == "__main__":
    success = test_image_generation()
    print(f"Test result: {'PASS' if success else 'FAIL'}")
    exit(0 if success else 1)
