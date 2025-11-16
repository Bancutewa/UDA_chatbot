#!/usr/bin/env python3
"""
Debug session retrieval
"""
import sys
sys.path.insert(0, 'src')

from src.services.auth_service import auth_service
from src.services.chat_service import chat_service
from src.schemas.user import LoginRequest

def debug_sessions():
    """Debug session retrieval and filtering"""
    print("🔍 Debugging session retrieval...")

    try:
        # Try to login with admin account
        login_data = LoginRequest(username="admin", password="admin123")
        token_response = auth_service.authenticate_user(login_data)

        user_session = {
            'user_id': token_response.user.id,
            'username': token_response.user.username,
            'role': token_response.user.role.value
        }

        print(f"✅ Logged in as: {user_session['username']} (ID: {user_session['user_id']})")

        # Get sessions for this user
        user_sessions = chat_service.get_all_sessions(user_session['user_id'])
        print(f"✅ User sessions found: {len(user_sessions)}")

        for session in user_sessions:
            print(f"  - {session.get('title', 'Untitled')} (ID: {session.get('id', 'N/A')})")
            print(f"    User ID: {session.get('user_id', 'N/A')}")
            print(f"    Messages: {len(session.get('messages', []))}")

        # Also check what happens when calling without user_id
        all_sessions = chat_service.get_all_sessions()
        print(f"✅ All sessions in DB: {len(all_sessions)}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_sessions()
