import json
import logging

from apps.common.infrastructure.motherduck_client import MotherDuckClient

logger = logging.getLogger(__name__)


class TodoAnalyticsService:
    """
    Todo分析イベント記録サービス

    MotherDuckにTodoイベントを送信
    """

    @staticmethod
    def log_todo_create(user, todo):
        """
        Todo作成イベントを記録

        Args:
            user: Userオブジェクト
            todo: Todoオブジェクト
        """
        event_data = {
            "user_id": user.id,
            "todo_id": todo.id,
            "event_type": "create",
            "todo_title": todo.todo_title,
            "priority": todo.priority,
            "progress": todo.progress,
            "is_completed": todo.progress == 100,
            "changed_fields": None,
            "deletion_reason": None,
        }

        try:
            client = MotherDuckClient()
            client.insert_todo_event(event_data)
        except Exception as e:
            logger.error(f"Failed to log todo create event: {e}")

    @staticmethod
    def log_todo_update(user, todo, changed_fields: dict):
        """
        Todo更新イベントを記録

        Args:
            user: Userオブジェクト
            todo: Todoオブジェクト（更新後）
            changed_fields: 変更されたフィールド
                例: {"priority": ["LOW", "HIGH"], "progress": [0, 50]}
        """
        event_data = {
            "user_id": user.id,
            "todo_id": todo.id,
            "event_type": "update",
            "todo_title": todo.todo_title,
            "priority": todo.priority,
            "progress": todo.progress,
            "is_completed": todo.progress == 100,
            "changed_fields": json.dumps(changed_fields) if changed_fields else None,
            "deletion_reason": None,
        }

        try:
            client = MotherDuckClient()
            client.insert_todo_event(event_data)
        except Exception as e:
            logger.error(f"Failed to log todo update event: {e}")

    @staticmethod
    def log_todo_delete(user, todo, deletion_reason: str = "other"):
        """
        Todo削除イベントを記録

        Args:
            user: Userオブジェクト
            todo: Todoオブジェクト（削除前）
            deletion_reason: 削除理由
                - 'completed': 完了したので削除
                - 'cancelled': キャンセル
                - 'duplicate': 重複
                - 'other': その他
        """
        event_data = {
            "user_id": user.id,
            "todo_id": todo.id,
            "event_type": "delete",
            "todo_title": todo.todo_title,
            "priority": todo.priority,
            "progress": todo.progress,
            "is_completed": todo.progress == 100,
            "changed_fields": None,
            "deletion_reason": deletion_reason,
        }

        try:
            client = MotherDuckClient()
            client.insert_todo_event(event_data)
        except Exception as e:
            logger.error(f"Failed to log todo delete event: {e}")

    @staticmethod
    def log_todo_complete(user, todo):
        """
        Todo完了イベントを記録

        Args:
            user: Userオブジェクト
            todo: Todoオブジェクト（完了後）
        """
        event_data = {
            "user_id": user.id,
            "todo_id": todo.id,
            "event_type": "complete",
            "todo_title": todo.todo_title,
            "priority": todo.priority,
            "progress": 100,
            "is_completed": True,
            "changed_fields": json.dumps({"progress": [todo.progress, 100]}),
            "deletion_reason": None,
        }

        try:
            client = MotherDuckClient()
            client.insert_todo_event(event_data)
        except Exception as e:
            logger.error(f"Failed to log todo complete event: {e}")
