"""
Permission helper functions for role-based access control
"""
from typing import Optional
from ..schemas.user import UserSession, UserRole


def is_admin(user_session: Optional[UserSession]) -> bool:
    """Check if user is admin"""
    return user_session is not None and user_session.role == UserRole.ADMIN


def is_sale(user_session: Optional[UserSession]) -> bool:
    """Check if user is sale staff"""
    return user_session is not None and user_session.role == UserRole.SALE


def is_user(user_session: Optional[UserSession]) -> bool:
    """Check if user is regular user"""
    return user_session is not None and user_session.role == UserRole.USER


def can_manage_users(user_session: Optional[UserSession]) -> bool:
    """Check if user can manage other users (Admin only)"""
    return is_admin(user_session)


def can_manage_schedules(user_session: Optional[UserSession]) -> bool:
    """Check if user can manage schedules (Admin and Sale)"""
    return is_admin(user_session) or is_sale(user_session)


def can_manage_data(user_session: Optional[UserSession]) -> bool:
    """Check if user can manage system data (Admin only)"""
    return is_admin(user_session)


def can_view_all_schedules(user_session: Optional[UserSession]) -> bool:
    """Check if user can view all schedules (Admin and Sale)"""
    return is_admin(user_session) or is_sale(user_session)


def can_delete_schedule(user_session: Optional[UserSession]) -> bool:
    """Check if user can delete schedules (Admin only)"""
    return is_admin(user_session)


def can_edit_user_role(user_session: Optional[UserSession]) -> bool:
    """Check if user can edit other users' roles (Admin only)"""
    return is_admin(user_session)


def can_edit_user_status(user_session: Optional[UserSession]) -> bool:
    """Check if user can edit other users' status (Admin only)"""
    return is_admin(user_session)


def can_view_user_list(user_session: Optional[UserSession]) -> bool:
    """Check if user can view user list (Admin and Sale)"""
    return is_admin(user_session) or is_sale(user_session)

