from typing import Final
from apps.common.services.base_qstash import BaseQStashService
from apps.common.error_decorators import service_error_handler


class UserQStashService(BaseQStashService):
    """ユーザー関連の非同期タスク送信"""
    
    ENDPOINT_WELCOME_EMAIL: Final = "/api/v1/webhooks/send-welcome-email"

    @classmethod
    @service_error_handler
    def send_welcome_email_async(cls, email: str, first_name: str) -> str:
        """ウェルカムメール送信をキューに追加"""
        return cls._safe_publish(
            cls.ENDPOINT_WELCOME_EMAIL,
            {"email": email, "first_name": first_name}
        )