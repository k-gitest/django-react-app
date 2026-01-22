from apps.common.services.base_email import BaseEmailService
from apps.common.error_decorators import service_error_handler
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class UserEmailService(BaseEmailService):
    """
    ユーザー関連のメール送信サービス（ビジネス層）
    
    メールの「内容（件名・HTML）」を担当し、
    送信とエラー変換は BaseEmailService に委譲
    """

    @classmethod
    @service_error_handler
    def send_welcome_email(cls, email: str, first_name: str) -> str:
        """
        ウェルカムメール送信

        Args:
            email: 送信先メールアドレス
            first_name: ユーザーの名前

        Returns:
            str: message_id
            
        Raises:
            EmailDeliveryError: メール送信失敗時（Baseが投げる）
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

        return cls._safe_send(email, subject, html_content)

    @classmethod
    @service_error_handler
    def send_password_reset_email(cls, email: str, reset_token: str) -> str:
        """
        パスワードリセットメール送信（将来用）

        Args:
            email: 送信先メールアドレス
            reset_token: リセットトークン

        Returns:
            str: message_id
            
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
        
        return cls._safe_send(email, subject, html_content)