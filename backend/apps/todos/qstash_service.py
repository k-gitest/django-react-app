from typing import Final
from apps.common.services.base_qstash import BaseQStashService
from apps.common.error_decorators import service_error_handler


class TodoQStashService(BaseQStashService):
    """
    Todo関連の非同期タスク送信
    
    BaseQStashServiceを継承し、Todos固有のエンドポイントとペイロードを定義
    """
    
    # エンドポイントをクラス定数として定義
    ENDPOINT_VECTOR_INDEXING: Final = "/api/v1/webhooks/vector-indexing"
    ENDPOINT_BULK_INDEXING: Final = "/api/v1/webhooks/bulk-vector-indexing"

    @classmethod
    @service_error_handler
    def queue_vector_indexing(cls, todo_id: int, operation: str = "upsert") -> str:
        """
        Todoのベクトルインデックス処理をキューに追加

        Args:
            todo_id: TodoのID
            operation: "upsert" or "delete"

        Returns:
            str: message_id
            
        Raises:
            QStashError: QStash送信失敗時（Baseが投げる）
        """
        return cls._safe_publish(
            endpoint_path=cls.ENDPOINT_VECTOR_INDEXING,
            payload={"todo_id": todo_id, "operation": operation},
            delay_seconds=1  # DB確定を待つため1秒遅延
        )

    @classmethod
    @service_error_handler
    def queue_bulk_vector_indexing(cls, user_id: int) -> str:
        """
        ユーザーの全Todoを一括インデックス（非同期）

        Args:
            user_id: ユーザーID

        Returns:
            str: message_id
            
        Raises:
            QStashError: QStash送信失敗時（Baseが投げる）
        """
        return cls._safe_publish(
            endpoint_path=cls.ENDPOINT_BULK_INDEXING,
            payload={"user_id": user_id}
        )