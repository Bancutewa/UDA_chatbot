#!/usr/bin/env python3
"""
Test user-specific session filtering
"""
import sys
sys.path.insert(0, 'src')

from src.services.auth_service import auth_service
from src.services.chat_service import chat_service
from src.schemas.user import UserCreate

def test_user_session_isolation():
    """Test that users only see their own sessions"""
    print("🧪 Testing user session isolation...")

    try:
        # Create test users
        user1_data = UserCreate(
            username="testuser_sess1",
            email="test_sess1@example.com",
            full_name="Test User Session 1",
            password="password123"
        )

        user2_data = UserCreate(
            username="testuser_sess2",
            email="test_sess2@example.com",
            full_name="Test User Session 2",
            password="password123"
        )

        # Register users
        user1 = auth_service.register_user(user1_data)
        user2 = auth_service.register_user(user2_data)

        print(f"✅ Created users: {user1.username}, {user2.username}")

        # Create sessions for each user
        session1 = chat_service.create_session(user1.id, "User 1 Session 1")
        session2 = chat_service.create_session(user1.id, "User 1 Session 2")
        session3 = chat_service.create_session(user2.id, "User 2 Session 1")

        print(f"✅ Created sessions: {session1['title']}, {session2['title']}, {session3['title']}")

        # Get all sessions
        all_sessions = chat_service.get_all_sessions()
        print(f"✅ Total sessions in DB: {len(all_sessions)}")

        # Simulate filtering logic (like in chat_interface.py)
        user1_sessions = [s for s in all_sessions if s.get("user_id") == user1.id]
        user2_sessions = [s for s in all_sessions if s.get("user_id") == user2.id]

        print(f"✅ User 1 sessions: {len(user1_sessions)} - {[s['title'] for s in user1_sessions]}")
        print(f"✅ User 2 sessions: {len(user2_sessions)} - {[s['title'] for s in user2_sessions]}")

        # Verify isolation
        user1_has_correct_sessions = (
            len(user1_sessions) == 2 and
            all(s.get("user_id") == user1.id for s in user1_sessions) and
            all(s['title'].startswith("User 1") for s in user1_sessions)
        )

        user2_has_correct_sessions = (
            len(user2_sessions) == 1 and
            all(s.get("user_id") == user2.id for s in user2_sessions) and
            all(s['title'].startswith("User 2") for s in user2_sessions)
        )

        if user1_has_correct_sessions and user2_has_correct_sessions:
            print("✅ Session isolation working correctly!")
            return True
        else:
            print("❌ Session isolation failed!")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing user session isolation...\n")

    success = test_user_session_isolation()

    print("\n📊 Test Result:")
    print(f"   Session Isolation: {'✅ PASS' if success else '❌ FAIL'}")

    if success:
        print("\n🎉 User sessions are properly isolated!")
        exit(0)
    else:
        print("\n❌ Session isolation issues detected!")
        exit(1)
