
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.core.config import config
from src.agents.estate_agent import estate_agent
from langchain_core.messages import HumanMessage, AIMessage

def test_agent():
    print("--- TESTING ESTATE AGENT WITH MEMORY ---")
    
    # Test 1: Search Listings (Initial Query)
    print("\n--- Test 1: Search Listings ---")
    question1 = "Tìm giúp tôi căn hộ 2 phòng ngủ giá dưới 3 tỷ"
    print(f"User: {question1}")
    try:
        response1 = estate_agent.invoke(question1, thread_id="test_thread_001")
        print(f"Agent: {response1}\n")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: RAG / General Info (Independent Query)
    print("--- Test 2: RAG / General Info ---")
    question2 = "Dự án The Filmore có tiện ích gì?"
    print(f"User: {question2}")
    try:
        response2 = estate_agent.invoke(question2, thread_id="test_thread_001")
        print(f"Agent: {response2}\n")
    except Exception as e:
        print(f"Error: {e}")

    # Test 3: Short-term Memory (Context Recall)
    print("--- Test 3: Short-term Memory (Context) ---")
    question3 = "Những căn đó có nội thất gì đặc biệt không?" 
    # This refers back to the listings found in Test 1. "Những căn đó" implies context.
    print(f"User: {question3}")
    try:
        response3 = estate_agent.invoke(question3, thread_id="test_thread_001")
        print(f"Agent: {response3}\n")
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Test Completed ---")

if __name__ == "__main__":
    test_agent()
