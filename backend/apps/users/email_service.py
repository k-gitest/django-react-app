from email import message
import logging

from apps.common.infrastructure.email_client import EmailClient
from apps.common.exceptions import EmailDeliveryError
from apps.common.error_decorators import service_error_handler
from django.conf import settings

logger = logging.getLogger(__name__)


class UserEmailService:
    """
    ユーザー関連のメール送信サービス（ビジネス層）
    
    メールの「内容」を担当し、送信は EmailClient に委譲
    """

    def __init__(self):
        self.email_client = EmailClient()

    @service_error_handler
    def send_welcome_email(self, email: str, first_name: str) -> str:
        """
        ウェルカムメール送信

        Args:
            email: 送信先メールアドレス
            first_name: ユーザーの名前

        Returns:
            dict: {"success": bool, "id": str or None, "error": str or None}
            
        Raises:
            EmailDeliveryError: メール送信失敗時
        """
        subject = f"Welcome to Django React App, {first_name}!"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #4F46E5; padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0;">Welcome, {first_name}! 🎉</h1>
                </div>
                
                <div style="padding: 30px; background-color: #f9fafb;">
                    <h2 style="color: #1f2937;">Thank you for registering!</h2>
                    <p style="color: #4b5563; font-size: 16px; line-height: 1.6;">
                        We're excited to have you on board. Your account has been successfully created.
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{settings.FRONTEND_URL}/dashboard" 
                           style="background-color: #4F46E5; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 6px; display: inline-block;">
                            Get Started
                        </a>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 14px;">
                        If you have any questions, feel free to reply to this email.
                    </p>
                </div>
                
                <div style="padding: 20px; text-align: center; color: #9ca3af; font-size: 12px;">
                    <p>© 2025 Django React App. All rights reserved.</p>
                </div>
            </body>
        </html>
        """

        """
        result = self.email_client.send(
            to_email=email,
            subject=subject,
            html_content=html_content
        )

        # 失敗時は例外を投げる（デコレーターがログ処理）
        if not result["success"]:
            raise EmailDeliveryError(
                message=result.get('error', 'Unknown error'),
                email=email
            )

        logger.info(f"Welcome email sent to {email}")
        return result
        """
        try:
            message_id = self.email_client.send(
                to_email=email,
                subject=subject,
                html_content=html_content
            )
            logger.info(f"Welcome email sent to {email}, message_id={message_id}")
            return message_id
        except Exception as e:
            # インフラエラーをビジネス例外に変換
            raise EmailDeliveryError(
                message=f"Failed to send welcome email: {str(e)}",
                email=email
            ) from e

    @service_error_handler
    def send_password_reset_email(self, email: str, reset_token: str) -> dict:
        """
        パスワードリセットメール送信（将来用）

        Args:
            email: 送信先メールアドレス
            reset_token: リセットトークン

        Returns:
            dict: 送信結果
            
        Raises:
            EmailDeliveryError: メール送信失敗時
        """
        subject = "Password Reset Request"
        reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={reset_token}"

        html_content = f"""
        <html>
            <body>
                <h1>Password Reset Request</h1>
                <p>Click the link below to reset your password:</p>
                <a href="{reset_url}">Reset Password</a>
                <p>This link will expire in 24 hours.</p>
            </body>
        </html>
        """

        result = self.email_client.send(
            to_email=email,
            subject=subject,
            html_content=html_content
        )

        if not result["success"]:
            raise EmailDeliveryError(
                message=result.get('error', 'Unknown error'),
                email=email
            )

        return result