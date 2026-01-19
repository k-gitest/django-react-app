from urllib import response
import resend
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class EmailClient:
    """
    Resend APIを使用したメール送信クライアント（技術層）
    
    ビジネスロジックに依存しない、純粋なメール送信機能を提供
    """
    
    def __init__(self):
        resend.api_key = settings.RESEND_API_KEY
    
    def send(self, to_email: str, subject: str, html_content: str, 
             from_email: str = None) -> str:
        """
        メールを送信
        
        Args:
            to_email: 送信先メールアドレス
            subject: 件名
            html_content: HTML本文
            from_email: 送信元（デフォルト: settings.DEFAULT_FROM_EMAIL）
        
        Returns:
            dict: {"success": bool, "id": str or None, "error": str or None}

        Raises:
            Exception: Resend APIのエラーがそのまま伝播
        """
        # try:

        params = {
            "from": from_email or settings.DEFAULT_FROM_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        # response = resend.Emails.send(params)
        # logger.info(f"Email sent to {to_email}, ID: {response['id']}")

        # try-exceptせず、エラーは上位に任せる
        response = resend.Emails.send(params)
        return response["id"]

        """
        return {
            "success": True,
            "id": response["id"],
            "error": None
        }
        """
        
        """
        except Exception as e:
            # logger.error(f"Failed to send email to {to_email}: {e}")
            return {
                "success": False,
                "id": None,
                "error": str(e)
            }
        """
    
    def send_batch(self, emails: list[dict]) -> list[str]:
        """
        複数のメールを一括送信
        
        Args:
            emails: [{"to": str, "subject": str, "html": str}, ...]
        
        Returns:
            list[dict]: 各メールの送信結果
        """
        message_ids = []
        for email_data in emails:
            message_id = self.send(
                to_email=email_data["to"],
                subject=email_data["subject"],
                html_content=email_data["html"]
            )
            message_ids.append(message_id)
        return message_ids