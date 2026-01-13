from apps.common.infrastructure.qstash_client import QStashClient as BaseQStashService


class TodoQStashService:
    """
    Todo関連の非同期タスク送信

    common.QStashServiceをラップし、Todos固有のペイロードを構築
    """

    @staticmethod
    def queue_vector_indexing(todo_id: int, operation: str = "upsert") -> dict:
        """
        Todoのベクトルインデックス処理をキューに追加

        Args:
            todo_id: TodoのID
            operation: "upsert" or "delete"

        Returns:
            dict: {"success": bool, "message_id": str or None, "error": str or None}
        """
        return BaseQStashService.publish(
            endpoint_path="/api/v1/webhooks/vector-indexing",
            payload={"todo_id": todo_id, "operation": operation},
            delay_seconds=1,  # DB確定を待つため1秒遅延
        )

    @staticmethod
    def queue_bulk_vector_indexing(user_id: int) -> dict:
        """
        ユーザーの全Todoを一括インデックス（非同期）

        Args:
            user_id: ユーザーID

        Returns:
            dict: {"success": bool, "message_id": str or None, "error": str or None}
        """
        return BaseQStashService.publish(
            endpoint_path="/api/v1/webhooks/bulk-vector-indexing",
            payload={"user_id": user_id},
        )
