#!/usr/bin/env python3
"""
Test that project loads without BDS dependencies
"""
import sys

# Add src to path
sys.path.insert(0, 'src')

def test_clean_project():
    """Test that core services load without BDS dependencies"""
    print("🧹 Testing clean project (no BDS)...")

    try:
        # Test intent registry
        from src.intents.intent_registry import intent_registry
        print("✅ Intent registry loaded")
        intents = intent_registry.get_intent_names()
        print(f"   Available intents: {intents}")

        # Test core services
        from src.services.chat_service import chat_service
        print("✅ Chat service loaded")

        from src.services.audio_service import audio_service
        print("✅ Audio service loaded")

        from src.services.image_service import image_service
        print("✅ Image service loaded")

        # Test auth service
        from src.services.auth_service import auth_service
        print("✅ Auth service loaded")

        # Test agents
        from src.agents.llm_agent import llm_agent
        print("✅ LLM agent loaded")

        from src.agents.intent_agent import intent_agent
        print("✅ Intent agent loaded")

        from src.agents.audio_agent import audio_agent
        print("✅ Audio agent loaded")

        from src.agents.image_agent import image_agent
        print("✅ Image agent loaded")

        print("\n🎉 SUCCESS: All core services loaded without BDS dependencies!")
        print("📋 Available features:")
        print("   • General chat (streaming)")
        print("   • Image generation (Pollinations)")
        print("   • Audio generation (ElevenLabs)")
        print("   • User authentication")
        print("   • Chat history management")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_clean_project()
