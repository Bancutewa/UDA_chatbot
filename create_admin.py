#!/usr/bin/env python3
"""
Script to create the first admin user
"""
import sys
sys.path.insert(0, 'src')

from src.services.auth_service import auth_service
from src.schemas.user import UserCreate

def create_first_admin():
    """Create the first admin user"""
    print("👑 Creating first admin user...")

    try:
        # Create admin user
        admin_data = UserCreate(
            username="admin",
            email="admin@example.com",
            full_name="Administrator",
            password="admin123",
            role="admin"  # Force admin role for this script
        )

        # Temporarily modify register_user to allow admin creation
        original_method = auth_service.register_user

        def admin_register_user(user_data):
            # Override to allow admin role
            from src.schemas.user import UserRole
            user_data.role = UserRole.ADMIN

            # Hash password
            hashed_password = auth_service._hash_password(user_data.password)

            # Create user
            user = auth_service.user_repo.create_user(user_data, hashed_password)

            # Return user without password
            from src.schemas.user import UserResponse
            return UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )

        # Use modified method
        auth_service.register_user = admin_register_user

        user_response = auth_service.register_user(admin_data)

        # Restore original method
        auth_service.register_user = original_method

        print("✅ Admin user created successfully!")
        print(f"   Username: {user_response.username}")
        print(f"   Email: {user_response.email}")
        print(f"   Role: {user_response.role}")
        print(f"   Password: admin123")
        print("\n🔐 Please change the default password after first login!")

        return True

    except Exception as e:
        print(f"❌ Failed to create admin user: {e}")
        return False

if __name__ == "__main__":
    success = create_first_admin()
    if success:
        print("\n🚀 You can now start the chatbot and login with:")
        print("   Username: admin")
        print("   Password: admin123")
    exit(0 if success else 1)
