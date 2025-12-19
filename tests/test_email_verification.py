
import sys
import os
import unittest
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.auth_service import AuthService
from src.services.email_service import EmailService
from src.schemas.user import UserCreate, UserStatus
from src.repositories.user_repository import UserRepository
import src.services.auth_service

# Mock EmailService to avoid sending real emails
class MockEmailService:
    def send_verification_email(self, to, otp):
        print(f"DTO SENT EMAIL: To={to}, OTP={otp}")
        return True

class TestEmailFlow(unittest.TestCase):
    def setUp(self):
        self.auth_service = AuthService()
        # Clean up test user if exists
        self.test_username = "test_verify_user"
        self.test_email = "test_verify@example.com"
        
        repo = UserRepository()
        u = repo.get_user_by_username(self.test_username)
        if u:
            repo.delete_user(u.id)

    def test_registration_and_verification(self):
        # 1. Register
        user_data = UserCreate(
            username=self.test_username,
            email=self.test_email,
            full_name="Test Verify User",
            password="password123"
        )
        
        # Monkey patch email service
        src.services.auth_service.email_service = MockEmailService()
        
        print("\n--- Registering User ---")
        user = self.auth_service.register_user(user_data)
        self.assertEqual(user.username, self.test_username)
        self.assertEqual(user.status, UserStatus.PENDING)
        print("Registration successful, status is PENDING.")

        # 2. Get OTP (from DB/Repo since we mocked email)
        repo = UserRepository()
        db_user = repo.get_user_by_username(self.test_username)
        otp = db_user.verification_code
        print(f"Retrieved OTP from DB: {otp}")
        self.assertIsNotNone(otp)
        self.assertEqual(len(otp), 6)

        # 3. Verify with WRONG OTP
        print("--- Verifying with WRONG OTP ---")
        with self.assertRaises(Exception) as cm:
            self.auth_service.verify_email(self.test_username, "000000")
        print(f"Caught expected error: {cm.exception}")

        # 4. Verify with CORRECT OTP
        print(f"--- Verifying with CORRECT OTP: {otp} ---")
        result = self.auth_service.verify_email(self.test_username, otp)
        self.assertTrue(result)
        
        # 5. Check Status
        db_user = repo.get_user_by_username(self.test_username)
        self.assertEqual(db_user.status, UserStatus.ACTIVE)
        print("User status is now ACTIVE.")

        # Cleanup
        repo.delete_user(db_user.id)

if __name__ == '__main__':
    unittest.main()
