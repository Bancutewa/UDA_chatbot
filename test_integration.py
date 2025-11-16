#!/usr/bin/env python3
"""
Test script for image and audio generation integration
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.image_service import image_service
from src.services.audio_service import audio_service

def test_image_generation():
    """Test image generation"""
    print("🖼️ Testing image generation...")

    try:
        result = image_service.generate_image("một con mèo xinh xắn")
        print(f"✅ Image generation result: {result[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        return False

def test_audio_generation():
    """Test audio generation (without API keys)"""
    print("🎵 Testing audio generation availability...")

    try:
        # Test availability
        available = audio_service.is_available()
        print(f"Audio service available: {available}")

        # Test with demo mode (should work without API keys)
        result, file_path = audio_service.generate_audio("demo")
        print(f"✅ Demo audio result: {result[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Audio generation failed: {e}")
        return False

def main():
    print("🚀 Starting integration tests...\n")

    # Test image generation
    image_ok = test_image_generation()
    print()

    # Test audio generation
    audio_ok = test_audio_generation()
    print()

    if image_ok and audio_ok:
        print("🎉 All integration tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())
