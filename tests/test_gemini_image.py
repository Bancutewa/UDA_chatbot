
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.tools.image_tools import generate_image_tool
from src.core.config import config

def test_image_generation():
    print("Testing Gemini Image Generation...")
    
    if not config.GEMINI_API_KEY:
        print("Skipping test: GEMINI_API_KEY not found.")
        return

    prompt = "A futuristic city with flying cars, cyberpunk style"
    print(f"Prompt: {prompt}")
    
    # Langchain tool must be invoked
    try:
        result = generate_image_tool.invoke(prompt)
    except Exception as e:
        print(f"Direct invoke failed, trying to run: {e}")
        try:
           result = generate_image_tool.run(prompt)
        except Exception as e2:
           print(f"Run also failed: {e2}")
           return

    print(f"Result: {result}")
    
    if "data/generated_images" in result and "successfully" in result:
        # Extract path
        path = result.split(": ")[1].strip()
        if os.path.exists(path):
            print(f"✅ SUCCESS: Image created at {path}")
            print(f"File size: {os.path.getsize(path)} bytes")
        else:
            print(f"❌ FAILED: File path returned but file not found: {path}")
    else:
        print(f"❌ FAILED: Unexpected result format or error: {result}")

if __name__ == "__main__":
    test_image_generation()
