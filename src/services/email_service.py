"""
Email service for sending verification emails using Google App Password
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict
from datetime import datetime

from ..core.config import config
from ..core.logger import logger

class EmailService:
    """Service for sending emails"""

    def __init__(self):
        self.sender_email = config.EMAIL_SENDER
        self.password = config.EMAIL_PASSWORD
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT

    def is_configured(self) -> bool:
        """Check if email service is configured"""
        return bool(self.sender_email and self.password)

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send an email"""
        if not self.is_configured():
            logger.warning("Email service not configured. Skipping email sending.")
            return False

        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = to_email

            # Turn these into plain/html MIMEText objects
            part = MIMEText(html_content, "html")

            # Add HTML/plain-text parts to MIMEMultipart message
            message.attach(part)

            # Create secure connection with server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.password)
                server.sendmail(
                    self.sender_email, to_email, message.as_string()
                )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            error_msg = str(e)
            if "BadCredentials" in error_msg or "Username and Password not accepted" in error_msg:
                logger.error(
                    f"Email authentication failed. Please check:\n"
                    f"1. EMAIL_SENDER must be a valid Gmail address\n"
                    f"2. EMAIL_PASSWORD must be a Gmail App Password (not your regular password)\n"
                    f"   To create App Password: https://myaccount.google.com/apppasswords\n"
                    f"3. Enable 2-Step Verification if not already enabled\n"
                    f"Error details: {e}"
                )
            else:
                logger.error(f"SMTP authentication error: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error when sending email to {to_email}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}", exc_info=True)
            return False

    def send_verification_email(self, to_email: str, verification_code: str) -> bool:
        """Send verification email with OTP"""
        subject = "Xác thực tài khoản Chatbot Bất Động Sản"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                    <h2 style="color: #2c3e50; text-align: center;">Xác Thực Tài Khoản</h2>
                    <p>Xin chào,</p>
                    <p>Cảm ơn bạn đã đăng ký tài khoản tại Chatbot Bất Động Sản.</p>
                    <p>Mã xác thực của bạn là:</p>
                    <div style="background-color: #f8f9fa; padding: 15px; text-align: center; border-radius: 5px; margin: 20px 0;">
                        <h1 style="color: #0d6efd; margin: 0; letter-spacing: 5px;">{verification_code}</h1>
                    </div>
                    <p>Mã này sẽ hết hạn trong vòng 15 phút.</p>
                    <p>Nếu bạn không yêu cầu mã này, vui lòng bỏ qua email này.</p>
                    <br>
                    <p>Trân trọng,</p>
                    <p>Đội ngũ phát triển</p>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)

    def send_assignment_email_to_sale(
        self, 
        sale_email: str, 
        schedule: Dict, 
        confirm_url: str, 
        reject_url: str
    ) -> bool:
        """Send assignment email to Sale with confirm/reject links"""
        subject = "📅 Bạn được phân công lịch hẹn xem nhà mới"
        
        # Format schedule time
        requested_time = schedule.get("requested_time", "")
        try:
            if requested_time:
                dt = datetime.fromisoformat(requested_time.replace("Z", "+00:00"))
                time_display = dt.strftime("%H:%M, %d/%m/%Y")
            else:
                time_display = "Chưa xác định"
        except:
            time_display = requested_time

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                    <h2 style="color: #2c3e50; text-align: center;">📅 Phân Công Lịch Hẹn Mới</h2>
                    <p>Xin chào,</p>
                    <p>Bạn đã được phân công một lịch hẹn xem nhà mới:</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Khách hàng:</strong> {schedule.get('user_name', 'Không rõ')}</p>
                        <p><strong>Khu vực:</strong> {schedule.get('district', 'Chưa xác định')}</p>
                        <p><strong>Loại BĐS:</strong> {schedule.get('property_type', 'Bất động sản')}</p>
                        <p><strong>Thời gian:</strong> {time_display}</p>
                        {f"<p><strong>Ghi chú:</strong> {schedule.get('notes', '')}</p>" if schedule.get('notes') else ""}
                    </div>
                    
                    <p>Vui lòng xác nhận hoặc từ chối lịch hẹn này:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{confirm_url}" 
                           style="display: inline-block; background-color: #22c55e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 0 10px; font-weight: bold;">
                            ✅ Xác Nhận
                        </a>
                        <a href="{reject_url}" 
                           style="display: inline-block; background-color: #ef4444; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 0 10px; font-weight: bold;">
                            ❌ Từ Chối
                        </a>
                    </div>
                    
                    <p style="font-size: 12px; color: #666;">Link này sẽ hết hạn sau 7 ngày.</p>
                    <br>
                    <p>Trân trọng,</p>
                    <p>Đội ngũ quản lý</p>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(sale_email, subject, html_content)

    def send_confirmation_email_to_user(
        self, 
        user_email: str, 
        schedule: Dict, 
        sale_info: Dict
    ) -> bool:
        """Send notification email to User when Sale confirms their booking"""
        subject = "✅ Đặt lịch xem nhà thành công"
        
        # Format schedule time
        requested_time = schedule.get("requested_time", "")
        try:
            if requested_time:
                dt = datetime.fromisoformat(requested_time.replace("Z", "+00:00"))
                time_display = dt.strftime("%H:%M, %d/%m/%Y")
            else:
                time_display = "Chưa xác định"
        except:
            time_display = requested_time

        sale_name = sale_info.get("name", "Nhân viên tư vấn")
        sale_email = sale_info.get("email", "")

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                    <h2 style="color: #22c55e; text-align: center;">✅ Đặt Lịch Xem Nhà Thành Công</h2>
                    <p>Xin chào {schedule.get('user_name', 'Quý khách')},</p>
                    <p>Lịch hẹn xem nhà của bạn đã được xác nhận thành công! Nhân viên tư vấn sẽ liên hệ với bạn trước ngày hẹn.</p>
                    
                    <div style="background-color: #f0fdf4; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #22c55e;">
                        <p><strong>Khu vực:</strong> {schedule.get('district', 'Chưa xác định')}</p>
                        <p><strong>Loại BĐS:</strong> {schedule.get('property_type', 'Bất động sản')}</p>
                        <p><strong>Thời gian:</strong> {time_display}</p>
                        <p><strong>Nhân viên phụ trách:</strong> {sale_name}</p>
                        {f"<p><strong>Email liên hệ:</strong> {sale_email}</p>" if sale_email else ""}
                    </div>
                    
                    <p>Vui lòng có mặt đúng giờ tại địa điểm đã hẹn. Nếu có thay đổi, vui lòng liên hệ với nhân viên phụ trách.</p>
                    <br>
                    <p>Trân trọng,</p>
                    <p>Đội ngũ tư vấn</p>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)

    def send_rejection_notification_to_admin(
        self, 
        admin_email: str, 
        schedule: Dict, 
        sale_info: Dict, 
        reason: Optional[str] = None
    ) -> bool:
        """Send notification to Admin when Sale rejects"""
        subject = "⚠️ Sale từ chối lịch hẹn - Cần phân công lại"
        
        # Format schedule time
        requested_time = schedule.get("requested_time", "")
        try:
            if requested_time:
                dt = datetime.fromisoformat(requested_time.replace("Z", "+00:00"))
                time_display = dt.strftime("%H:%M, %d/%m/%Y")
            else:
                time_display = "Chưa xác định"
        except:
            time_display = requested_time

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                    <h2 style="color: #f59e0b; text-align: center;">⚠️ Sale Từ Chối Lịch Hẹn</h2>
                    <p>Xin chào Admin,</p>
                    <p>Sale <strong>{sale_info.get('name', 'Không rõ')}</strong> đã từ chối lịch hẹn sau:</p>
                    
                    <div style="background-color: #fef3c7; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                        <p><strong>Khách hàng:</strong> {schedule.get('user_name', 'Không rõ')}</p>
                        <p><strong>Khu vực:</strong> {schedule.get('district', 'Chưa xác định')}</p>
                        <p><strong>Thời gian:</strong> {time_display}</p>
                        {f"<p><strong>Lý do từ chối:</strong> {reason}</p>" if reason else ""}
                    </div>
                    
                    <p>Vui lòng đăng nhập vào hệ thống để phân công lại cho Sale khác.</p>
                    <br>
                    <p>Trân trọng,</p>
                    <p>Hệ thống</p>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(admin_email, subject, html_content)

    def send_cancellation_email_to_sale(
        self, 
        sale_email: str, 
        schedule: Dict, 
        user_info: Dict, 
        reason: Optional[str] = None
    ) -> bool:
        """Send email to Sale when User cancels schedule"""
        subject = "❌ Khách hàng đã hủy lịch hẹn"
        
        # Format schedule time
        requested_time = schedule.get("requested_time", "")
        try:
            if requested_time:
                dt = datetime.fromisoformat(requested_time.replace("Z", "+00:00"))
                time_display = dt.strftime("%H:%M, %d/%m/%Y")
            else:
                time_display = "Chưa xác định"
        except:
            time_display = requested_time

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                    <h2 style="color: #ef4444; text-align: center;">❌ Lịch Hẹn Đã Bị Hủy</h2>
                    <p>Xin chào,</p>
                    <p>Khách hàng <strong>{user_info.get('name', 'Không rõ')}</strong> đã hủy lịch hẹn sau:</p>
                    
                    <div style="background-color: #fee2e2; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ef4444;">
                        <p><strong>Khu vực:</strong> {schedule.get('district', 'Chưa xác định')}</p>
                        <p><strong>Thời gian:</strong> {time_display}</p>
                        {f"<p><strong>Lý do hủy:</strong> {reason}</p>" if reason else ""}
                    </div>
                    
                    <p>Lịch hẹn này đã được hủy và không cần xử lý nữa.</p>
                    <br>
                    <p>Trân trọng,</p>
                    <p>Hệ thống</p>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(sale_email, subject, html_content)

    def send_cancellation_notification_to_admin(
        self, 
        admin_email: str, 
        schedule: Dict, 
        user_info: Dict, 
        sale_info: Optional[Dict] = None,
        reason: Optional[str] = None
    ) -> bool:
        """Send notification to Admin when User cancels"""
        subject = "❌ Khách hàng đã hủy lịch hẹn"
        
        # Format schedule time
        requested_time = schedule.get("requested_time", "")
        try:
            if requested_time:
                dt = datetime.fromisoformat(requested_time.replace("Z", "+00:00"))
                time_display = dt.strftime("%H:%M, %d/%m/%Y")
            else:
                time_display = "Chưa xác định"
        except:
            time_display = requested_time

        sale_info_text = ""
        if sale_info:
            sale_info_text = f"<p><strong>Sale được phân công:</strong> {sale_info.get('name', 'Không rõ')}</p>"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                    <h2 style="color: #ef4444; text-align: center;">❌ Khách Hàng Hủy Lịch Hẹn</h2>
                    <p>Xin chào Admin,</p>
                    <p>Khách hàng <strong>{user_info.get('name', 'Không rõ')}</strong> đã hủy lịch hẹn sau:</p>
                    
                    <div style="background-color: #fee2e2; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ef4444;">
                        <p><strong>Khu vực:</strong> {schedule.get('district', 'Chưa xác định')}</p>
                        <p><strong>Thời gian:</strong> {time_display}</p>
                        {sale_info_text}
                        {f"<p><strong>Lý do hủy:</strong> {reason}</p>" if reason else ""}
                    </div>
                    
                    <p>Lịch hẹn này đã được hủy trong hệ thống.</p>
                    <br>
                    <p>Trân trọng,</p>
                    <p>Hệ thống</p>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(admin_email, subject, html_content)


# Global instance
email_service = EmailService()
