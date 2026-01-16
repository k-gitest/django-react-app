from apps.common.infrastructure.qstash_client import QStashClient as BaseQStashService
from apps.common.exceptions import QStashError
from apps.common.error_decorators import service_error_handler
import logging

logger = logging.getLogger(__name__)


class UserQStashService:
    """
    ユーザー関連の非同期タスク送信
    
    common.QStashServiceをラップし、Users固有のペイロードを構築
    """

    @staticmethod
    @service_error_handler
    def send_welcome_email_async(email: str, first_name: str) -> dict:
        """
        ウェルカムメール送信をQStash経由で非同期実行

        Args:
            email: 送信先メールアドレス
            first_name: ユーザーの名前

        Returns:
            dict: {"success": bool, "message_id": str or None, "error": str or None}
            
        Raises:
            QStashError: QStash送信失敗時
        """
        result = BaseQStashService.publish(
            endpoint_path="/api/v1/webhooks/send-welcome-email",
            payload={"email": email, "first_name": first_name},
        )
            
        # 失敗時は例外を投げる（デコレーターがログ処理）
        if not result.get("success", False):
            raise QStashError(
                message=result.get("error", "Unknown error"),
                endpoint="/api/v1/webhooks/send-welcome-email"
            )
            
        return result