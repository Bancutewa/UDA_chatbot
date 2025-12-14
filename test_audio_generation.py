#!/usr/bin/env python3
"""
Test Audio Generation Functionality (Updated for LangChain Tools)
"""
import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'chatbot', 'src'))
load_dotenv()

from src.tools.audio_tools import generate_audio_tool
from src.core.config import config

def test_audio_generation():
    """Test the audio generation functionality"""
    print("🎵 Testing Audio Generation Tool...")
    
    # Test environment variables
    print("\n1. Testing environment variables...")
    elevenlabs_key = config.ELEVEN_LABS_API_KEY
    
    print(f"ELEVEN_LABS_API_KEY: {'✅ Set' if elevenlabs_key else '❌ Not set'} (length: {len(elevenlabs_key) if elevenlabs_key else 0})")
    
    if not elevenlabs_key:
        print("⚠️ Warning: API Key missing. Audio generation will fail.")

    test_text = "Xin chào, đây là kiểm tra tạo âm thanh với công cụ mới."
    print(f"\n2. Generating audio for: '{test_text}'")
    
    try:
        # invoke the tool directly (it returns a string message)
        result = generate_audio_tool.invoke({"text": test_text})
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_audio_generation()
