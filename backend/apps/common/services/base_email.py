from apps.common.infrastructure.email_client import EmailClient
from apps.common.exceptions import EmailDeliveryError

class BaseEmailService:
    """
    メール送信の共通基盤
    Client層の例外をEmailDeliveryErrorに翻訳する責務を持つ
    """
    client = EmailClient()
    
    @classmethod
    def _safe_send(
        cls, 
        to_email: str, 
        subject: str, 
        html_content: str
    ) -> str:
        """
        共通の送信ロジック（エラー変換を担当）
        
        Returns:
            str: message_id
            
        Raises:
            EmailDeliveryError: 送信失敗時
        """
        try:
            return cls.client.send(to_email, subject, html_content)
        except Exception as e:
            if isinstance(e, EmailDeliveryError):
                raise
            raise EmailDeliveryError(
                message=f"Email delivery failed: {str(e)}",
                email=to_email
            ) from e