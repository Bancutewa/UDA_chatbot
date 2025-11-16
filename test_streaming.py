#!/usr/bin/env python3
"""
Test streaming response for general chat
"""
import sys
sys.path.insert(0, 'src')

from src.intents.general_chat_intent import GeneralChatIntent

def test_streaming():
    """Test streaming response"""
    print("🎯 Testing streaming response for general chat...")

    # Create intent handler
    intent = GeneralChatIntent()

    # Test data
    test_data = {
        'message': 'Xin chào! Bạn có thể giúp gì cho tôi?'
    }

    print("User message:", test_data['message'])
    print("\nStreaming response:")

    # Collect all chunks
    chunks = []
    try:
        for chunk in intent.get_streaming_response(test_data):
            chunks.append(chunk)
            print(f"  📝 {chunk}")

        full_response = " ".join(chunks)
        print(f"\n✅ Full response: {full_response}")
        print(f"✅ Generated {len(chunks)} chunks")

        return True

    except Exception as e:
        print(f"❌ Streaming failed: {e}")
        return False

def test_chunking():
    """Test the chunking algorithm"""
    print("\n🔧 Testing chunking algorithm...")

    intent = GeneralChatIntent()

    test_text = "Xin chào! Tôi là một chatbot AI thông minh. Tôi có thể giúp bạn trả lời câu hỏi và thực hiện nhiều tác vụ hữu ích khác."

    print(f"Original text: {test_text}")
    print("Chunks:")

    chunks = list(intent._simulate_streaming(test_text))
    for i, chunk in enumerate(chunks, 1):
        print(f"  {i}: '{chunk}'")

    reconstructed = " ".join(chunks)
    print(f"\nReconstructed: {reconstructed}")
    print(f"Match: {test_text == reconstructed}")

    return len(chunks) > 1

if __name__ == "__main__":
    print("🚀 Testing streaming functionality...\n")

    streaming_test = test_streaming()
    chunking_test = test_chunking()

    print("\n📊 Test Results:")
    print(f"  Streaming: {'✅ PASS' if streaming_test else '❌ FAIL'}")
    print(f"  Chunking: {'✅ PASS' if chunking_test else '❌ FAIL'}")

    if streaming_test and chunking_test:
        print("\n🎉 All streaming tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)
