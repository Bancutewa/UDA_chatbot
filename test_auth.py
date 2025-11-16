#!/usr/bin/env python3
"""
Test authentication system
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.auth_service import auth_service
from src.schemas.user import UserCreate

def test_user_registration():
    """Test user registration"""
    print("📝 Testing user registration...")

    try:
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            password="password123",
            role="user"
        )

        user = auth_service.register_user(user_data)
        print(f"✅ User registered: {user.username} ({user.role})")
        return True

    except Exception as e:
        print(f"❌ Registration failed: {e}")
        return False

def test_user_authentication():
    """Test user authentication"""
    print("🔐 Testing user authentication...")

    try:
        from src.schemas.user import LoginRequest
        login_data = LoginRequest(username="testuser", password="password123")

        token_response = auth_service.authenticate_user(login_data)
        print(f"✅ User authenticated: {token_response.user.username}")
        print(f"   Token: {token_response.access_token[:50]}...")

        # Test token validation
        user_session = auth_service.get_current_user(token_response.access_token)
        print(f"✅ Token validated: {user_session.username} ({user_session.role})")

        return True

    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

def test_admin_registration():
    """Test admin registration (first user)"""
    print("👑 Testing admin registration...")

    try:
        user_data = UserCreate(
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            password="admin123",
            role="user"  # Will be auto-promoted to admin
        )

        user = auth_service.register_user(user_data)
        print(f"✅ Admin registered: {user.username} ({user.role})")
        return user.role == "admin"

    except Exception as e:
        print(f"❌ Admin registration failed: {e}")
        return False

def main():
    print("🚀 Starting authentication tests...\n")

    # Test admin registration (should be first user)
    admin_ok = test_admin_registration()
    print()

    # Test user registration
    user_ok = test_user_registration()
    print()

    # Test authentication
    auth_ok = test_user_authentication()
    print()

    if admin_ok and user_ok and auth_ok:
        print("🎉 All authentication tests passed!")
        return 0
    else:
        print("❌ Some authentication tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())
