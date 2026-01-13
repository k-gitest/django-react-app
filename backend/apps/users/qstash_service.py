from apps.common.infrastructure.qstash_client import QStashClient as BaseQStashService


class UserQStashService:
    """
    ユーザー関連の非同期タスク送信

    common.QStashServiceをラップし、Users固有のペイロードを構築
    """

    @staticmethod
    def send_welcome_email_async(email: str, first_name: str) -> dict:
        """
        ウェルカムメール送信をQStash経由で非同期実行

        Args:
            email: 送信先メールアドレス
            first_name: ユーザーの名前

        Returns:
            dict: {"success": bool, "message_id": str or None, "error": str or None}
        """
        return BaseQStashService.publish(
            endpoint_path="/api/v1/webhooks/send-welcome-email",
            payload={"email": email, "first_name": first_name},
        )
