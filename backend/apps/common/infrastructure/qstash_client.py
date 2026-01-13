import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class QStashClient:
    """
    QStashを使った非同期タスク送信（汎用版）
    
    特定のビジネスロジック（User、Todo等）に依存しない、
    純粋な「運び屋」として機能する
    """
    
    BASE_URL = "https://qstash.upstash.io/v2"
    
    @staticmethod
    def publish(endpoint_path: str, payload: dict, delay_seconds: int = 0) -> dict:
        """
        QStashにメッセージを送信
        
        Args:
            endpoint_path: Webhook相対パス（例: "/api/v1/webhooks/send-welcome-email"）
            payload: 送信するデータ（JSON）
            delay_seconds: 遅延実行（秒）、デフォルト0（即座に実行）
        
        Returns:
            dict: {"success": bool, "message_id": str or None, "error": str or None}
        
        Raises:
            requests.RequestException: ネットワークエラー時
        """
        webhook_url = f"{settings.WEBHOOK_BASE_URL}{endpoint_path}"
        
        headers = {
            "Authorization": f"Bearer {settings.QSTASH_TOKEN}",
            "Content-Type": "application/json",
        }
        
        # 遅延実行の設定
        if delay_seconds > 0:
            headers["Upstash-Delay"] = f"{delay_seconds}s"
        
        try:
            response = requests.post(
                f"{QStashClient.BASE_URL}/publish/{webhook_url}",
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            message_id = response.json().get("messageId")
            logger.info(f"QStash message published to {endpoint_path}, ID: {message_id}")
            
            return {
                "success": True,
                "message_id": message_id,
                "error": None
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to publish QStash message: {e}")
            return {
                "success": False,
                "message_id": None,
                "error": str(e)
            }