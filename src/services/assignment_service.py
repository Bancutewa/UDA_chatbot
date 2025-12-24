"""
Assignment Service - Handle schedule assignment to Sale staff
"""
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional

from ..core.config import config
from ..core.logger import logger
from ..core.exceptions import ValidationError, AuthenticationError, DatabaseConnectionError
from ..repositories.schedule_repository import schedule_repository
from ..repositories.user_repository import UserRepository
from ..schemas.user import UserRole, UserSession
from ..services.email_service import email_service


class AssignmentService:
    """Service for schedule assignment operations"""

    def __init__(self):
        self.schedule_repo = schedule_repository
        self.user_repo = UserRepository()
        self.token_secret = config.JWT_SECRET_KEY or "assignment-secret-key"
        self.token_expiry_days = 7

    def _generate_assignment_token(self, schedule_id: str, sale_id: str) -> str:
        """Generate JWT token for assignment confirmation/rejection"""
        payload = {
            "schedule_id": schedule_id,
            "sale_id": sale_id,
            "exp": datetime.utcnow() + timedelta(days=self.token_expiry_days)
        }
        return jwt.encode(payload, self.token_secret, algorithm="HS256")

    def _verify_assignment_token(self, token: str) -> Dict:
        """Verify and decode assignment token"""
        try:
            payload = jwt.decode(token, self.token_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValidationError("Token đã hết hạn. Vui lòng liên hệ Admin.")
        except jwt.JWTError:
            raise ValidationError("Token không hợp lệ.")

    def assign_schedule_to_sale(
        self, 
        schedule_id: str, 
        sale_id: str, 
        admin_user: UserSession
    ) -> Dict:
        """Assign schedule to Sale (Admin only)"""
        # Verify admin permission
        if admin_user.role != UserRole.ADMIN:
            raise AuthenticationError("Chỉ quản trị viên mới có thể phân công lịch hẹn.")

        # Get schedule
        schedule = self.schedule_repo.get(schedule_id)
        if not schedule:
            raise ValidationError("Không tìm thấy lịch hẹn.")

        # Get Sale user
        sale_user = self.user_repo.get_user_by_id(sale_id)
        if not sale_user:
            raise ValidationError("Không tìm thấy nhân viên Sale.")

        if sale_user.role != UserRole.SALE:
            raise ValidationError("Người dùng được chọn không phải là Sale.")

        # Check if schedule is already assigned to another Sale
        if schedule.get("assigned_to_sale_id") and schedule.get("assigned_to_sale_id") != sale_id:
            if schedule.get("status") not in ["rejected", "cancelled"]:
                raise ValidationError("Lịch hẹn đã được phân công cho Sale khác.")

        # Generate assignment token
        assignment_token = self._generate_assignment_token(schedule_id, sale_id)

        # Update schedule with assignment info
        assignment_data = {
            "assigned_to_sale_id": sale_id,
            "assigned_to_sale_name": sale_user.full_name,
            "assigned_at": datetime.utcnow().isoformat(),
            "status": "assigned",
            "assignment_token": assignment_token,
            "sale_response": None,
            "sale_response_at": None,
        }

        updated_schedule = self.schedule_repo.update_assignment(schedule_id, assignment_data)
        if not updated_schedule:
            raise DatabaseConnectionError("Không thể cập nhật lịch hẹn.")

        # Send email to Sale
        base_url = config.BASE_URL
        confirm_url = f"{base_url}/?token={assignment_token}&action=confirm"
        reject_url = f"{base_url}/?token={assignment_token}&action=reject"

        email_sent = email_service.send_assignment_email_to_sale(
            sale_user.email,
            updated_schedule,
            confirm_url,
            reject_url
        )
        
        if not email_sent:
            logger.warning(
                f"Failed to send assignment email to Sale {sale_user.email}. "
                f"Assignment was still created successfully. Please check email configuration."
            )

        logger.info(f"Schedule {schedule_id} assigned to Sale {sale_id} by Admin {admin_user.user_id}")
        return updated_schedule

    def sale_confirm_assignment(self, token: str) -> bool:
        """Sale confirm assignment via email link"""
        # Verify token
        payload = self._verify_assignment_token(token)
        schedule_id = payload.get("schedule_id")
        sale_id = payload.get("sale_id")

        # Get schedule
        schedule = self.schedule_repo.get(schedule_id)
        if not schedule:
            raise ValidationError("Không tìm thấy lịch hẹn.")

        # Verify assignment
        if schedule.get("assigned_to_sale_id") != sale_id:
            raise ValidationError("Lịch hẹn không được phân công cho bạn.")

        if schedule.get("status") != "assigned":
            raise ValidationError(f"Lịch hẹn đã ở trạng thái {schedule.get('status')}, không thể xác nhận.")

        # Update schedule
        assignment_data = {
            "status": "confirmed",
            "sale_response": "confirmed",
            "sale_response_at": datetime.utcnow().isoformat(),
        }

        updated_schedule = self.schedule_repo.update_assignment(schedule_id, assignment_data)
        if not updated_schedule:
            raise DatabaseConnectionError("Không thể cập nhật lịch hẹn.")

        # Get Sale info for logging
        sale = self.user_repo.get_user_by_id(sale_id)
        
        # Lịch đã được confirm, sẽ tự động hiển thị trong calendar của user
        # Không cần gửi email nữa
        logger.info(
            f"Schedule {schedule_id} confirmed by Sale {sale_id}. "
            f"Lịch sẽ hiển thị trong calendar của user."
        )

        # Send notification to Admin (optional - get all admins)
        # For now, we'll skip admin notification on confirm

        logger.info(f"Sale {sale_id} confirmed schedule {schedule_id}")
        return True

    def sale_reject_assignment(self, token: str, reason: Optional[str] = None) -> bool:
        """Sale reject assignment via email link"""
        # Verify token
        payload = self._verify_assignment_token(token)
        schedule_id = payload.get("schedule_id")
        sale_id = payload.get("sale_id")

        # Get schedule
        schedule = self.schedule_repo.get(schedule_id)
        if not schedule:
            raise ValidationError("Không tìm thấy lịch hẹn.")

        # Verify assignment
        if schedule.get("assigned_to_sale_id") != sale_id:
            raise ValidationError("Lịch hẹn không được phân công cho bạn.")

        if schedule.get("status") != "assigned":
            raise ValidationError(f"Lịch hẹn đã ở trạng thái {schedule.get('status')}, không thể từ chối.")

        # Update schedule
        assignment_data = {
            "status": "rejected",
            "sale_response": "rejected",
            "sale_response_at": datetime.utcnow().isoformat(),
            "rejection_reason": reason,
        }

        updated_schedule = self.schedule_repo.update_assignment(schedule_id, assignment_data)
        if not updated_schedule:
            raise DatabaseConnectionError("Không thể cập nhật lịch hẹn.")

        # Get Sale info
        sale = self.user_repo.get_user_by_id(sale_id)

        # Send email to Admin
        admins = self.user_repo.get_users_by_role(UserRole.ADMIN.value)
        for admin in admins:
            email_service.send_rejection_notification_to_admin(
                admin.email,
                updated_schedule,
                {"name": sale.full_name, "email": sale.email} if sale else {},
                reason
            )

        logger.info(f"Sale {sale_id} rejected schedule {schedule_id}. Reason: {reason}")
        return True

    def user_cancel_schedule(
        self, 
        schedule_id: str, 
        user_id: str, 
        reason: Optional[str] = None
    ) -> bool:
        """User cancel their own schedule"""
        # Get schedule
        schedule = self.schedule_repo.get(schedule_id)
        if not schedule:
            raise ValidationError("Không tìm thấy lịch hẹn.")

        # Verify user owns this schedule
        if schedule.get("user_id") != user_id:
            raise AuthenticationError("Bạn chỉ có thể hủy lịch hẹn của chính mình.")

        # Check if already cancelled
        if schedule.get("status") == "cancelled":
            raise ValidationError("Lịch hẹn đã được hủy trước đó.")

        # Update schedule
        assignment_data = {
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat(),
            "cancelled_by": "user",
            "cancellation_reason": reason,
        }

        updated_schedule = self.schedule_repo.update_assignment(schedule_id, assignment_data)
        if not updated_schedule:
            raise DatabaseConnectionError("Không thể cập nhật lịch hẹn.")

        # Get user info
        user = self.user_repo.get_user_by_id(user_id)

        # If schedule was assigned to Sale, notify Sale
        assigned_sale_id = schedule.get("assigned_to_sale_id")
        if assigned_sale_id:
            sale = self.user_repo.get_user_by_id(assigned_sale_id)
            if sale:
                email_service.send_cancellation_email_to_sale(
                    sale.email,
                    updated_schedule,
                    {"name": user.full_name, "email": user.email} if user else {},
                    reason
                )

        # Send notification to Admin
        # TODO: Send email to all admins
        logger.warning(f"User {user_id} cancelled schedule {schedule_id}. Reason: {reason}")

        return True


# Global instance
assignment_service = AssignmentService()

