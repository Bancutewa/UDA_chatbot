#!/usr/bin/env python3
"""
Test user registration without role selection
"""
import sys
sys.path.insert(0, 'src')

from src.services.auth_service import auth_service
from src.schemas.user import UserCreate

def test_user_registration():
    """Test that new users are automatically assigned USER role"""
    print("🧪 Testing user registration...")

    try:
        # Create user without specifying role
        user_data = UserCreate(
            username="testuser4",
            email="test4@example.com",
            full_name="Test User 4",
            password="password123"
        )

        # Register user
        user_response = auth_service.register_user(user_data)

        # Check that role is USER
        if user_response.role.value == "user":
            print("✅ User registered with correct role: USER")
            print(f"   Username: {user_response.username}")
            print(f"   Role: {user_response.role.value}")
            return True
        else:
            print(f"❌ Unexpected role: {user_response.role.value}")
            return False

    except Exception as e:
        print(f"❌ Registration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing user registration changes...\n")

    user_test = test_user_registration()
    print()

    if user_test:
        print("🎉 Test passed!")
        exit(0)
    else:
        print("❌ Test failed!")
        exit(1)
