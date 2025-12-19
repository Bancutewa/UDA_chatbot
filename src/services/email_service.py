"""
Email service for sending verification emails using Google App Password
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

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

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
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


# Global instance
email_service = EmailService()
