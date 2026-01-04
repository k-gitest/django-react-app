import requests
from django.conf import settings


class QStashService:
    """QStashを使った非同期タスク送信"""
    
    @staticmethod
    def send_welcome_email_async(email: str, first_name: str):
        """ウェルカムメール送信をQStash経由で非同期実行"""
        webhook_url = f"{settings.WEBHOOK_BASE_URL}/api/v1/webhooks/send-welcome-email"
        
        payload = {
            "email": email,
            "first_name": first_name
        }
        
        try:
            response = requests.post(
                f"https://qstash.upstash.io/v2/publish/{webhook_url}",
                headers={
                    "Authorization": f"Bearer {settings.QSTASH_TOKEN}",
                    "Content-Type": "application/json",
                    "Upstash-Forward-Authorization": f"Bearer {settings.QSTASH_TOKEN}",  # Webhook認証用
                },
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return {"success": True, "message_id": response.json().get("messageId")}
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to send message to QStash: {str(e)}")
            return {"success": False, "error": str(e)}