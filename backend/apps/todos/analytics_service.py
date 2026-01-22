import json
from apps.common.services.base_analytics import BaseAnalyticsService
from apps.common.error_decorators import service_error_handler
import logging

logger = logging.getLogger(__name__)


class TodoAnalyticsService(BaseAnalyticsService):
    """
    Todo分析イベント記録サービス
    
    BaseAnalyticsServiceを継承し、Todo固有のイベントデータ整形を担当
    """

    @classmethod
    @service_error_handler
    def log_todo_create(cls, user, todo):
        """Todo作成イベントを記録"""
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
        cls._safe_insert("todo", event_data)

    @classmethod
    @service_error_handler
    def log_todo_update(cls, user, todo, changed_fields: dict):
        """Todo更新イベントを記録"""
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
        cls._safe_insert("todo", event_data)

    @classmethod
    @service_error_handler
    def log_todo_delete(cls, user, todo, deletion_reason: str = "other"):
        """Todo削除イベントを記録"""
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
        cls._safe_insert("todo", event_data)

    @classmethod
    @service_error_handler
    def log_todo_complete(cls, user, todo):
        """Todo完了イベントを記録"""
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
        cls._safe_insert("todo", event_data)