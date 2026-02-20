import logging

from apps.common.infrastructure.email_client import EmailClient
from apps.common.exceptions import EmailDeliveryError


logger = logging.getLogger(__name__)

class BaseEmailService:
    """
    メール送信の共通基盤
    Client層の例外をEmailDeliveryErrorに翻訳する責務を持つ
    """
    _client = None
    
    @classmethod
    def get_client(cls):
        """シングルトンパターンでクライアントを取得"""
        if cls._client is None:
            cls._client = EmailClient()
        return cls._client
    
    @classmethod
    def _safe_send(
        cls, 
        to_email: str, 
        subject: str, 
        html_content: str
    ) -> str:
        """
        共通の送信ロジック（エラー変換を担当）
        
        Args:
            to_email: 送信先メールアドレス
            subject: 件名
            html_content: HTML本文
        
        Returns:
            str: message_id
            
        Raises:
            EmailDeliveryError: 送信失敗時
        """
        try:
            client = cls.get_client()
            message_id = client.send(to_email, subject, html_content)
            logger.info(f"Email sent successfully: {message_id} to {to_email}")
            return message_id
            
        except EmailDeliveryError:
            raise
        except Exception as e:
            logger.error(f"Email delivery failed to {to_email}: {str(e)}")
            raise EmailDeliveryError(
                internal_details=str(e)
            ) from e