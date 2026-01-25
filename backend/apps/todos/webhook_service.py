"""
Todo Webhook Service - Webhook経路専用のロジック

QStashから呼ばれるWebhook処理をService層で管理。
HTTP経路（TodoCommandService等）とは分離。
"""

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from apps.common.error_decorators import service_error_handler
import logging

from .models import Todo
from .vector_service import VectorService

logger = logging.getLogger(__name__)
User = get_user_model()


class TodoWebhookService:
    """
    Todo Webhook処理サービス
    
    Webhook経路からの処理をカプセル化。
    HTTP経路（TodoCommandService等）とは分離。
    """
    
    @staticmethod
    @service_error_handler
    def handle_vector_indexing(todo_id: int, operation: str) -> dict:
        """
        Todoのベクトルインデックス処理
        
        Args:
            todo_id: TodoのID
            operation: "upsert" | "delete"
        
        Returns:
            dict: 処理結果
                - message: 処理メッセージ
                - todo_id: TodoのID
                - operation: 実行した操作
        
        Raises:
            Http404: Todoが存在しない（upsertの場合）
            VectorError: ベクトル処理エラー
        """
        vector_service = VectorService()
        
        if operation == "delete":
            vector_service.delete_todo(todo_id)
            logger.info(f"✅ Deleted todo {todo_id} from vector index (webhook)")
            
            return {
                "message": "Vector deleted successfully",
                "todo_id": todo_id,
                "operation": "delete"
            }
        
        else:  # upsert
            # Todo取得（存在しない場合は404）
            todo = get_object_or_404(Todo, id=todo_id)
            
            # ベクトルインデックスに追加
            vector_service.add_todo(todo)
            logger.info(f"✅ Added/Updated todo {todo_id} to vector index (webhook)")
            
            return {
                "message": "Vector indexed successfully",
                "todo_id": todo_id,
                "operation": "upsert"
            }
    
    @staticmethod
    @service_error_handler
    def handle_bulk_vector_indexing(user_id: int) -> dict:
        """
        ユーザーの全Todoを一括インデックス
        
        Args:
            user_id: ユーザーID
        
        Returns:
            dict: 処理結果
                - message: 処理メッセージ
                - user_id: ユーザーID
                - count: インデックスした件数
        
        Raises:
            Http404: ユーザーが存在しない
            VectorError: ベクトル処理エラー
        """
        # ユーザー取得（存在しない場合は404）
        user = get_object_or_404(User, id=user_id)
        
        # Todoリスト取得
        todos = list(Todo.objects.filter(user=user))
        
        if not todos:
            logger.info(f"ℹ️ No todos found for user {user_id}")
            return {
                "message": "No todos to index",
                "user_id": user_id,
                "count": 0
            }
        
        # 一括インデックス
        vector_service = VectorService()
        vector_service.add_todos_batch(todos)
        
        logger.info(f"✅ Bulk indexed {len(todos)} todos for user {user_id} (webhook)")
        
        return {
            "message": "Bulk vector indexing completed",
            "user_id": user_id,
            "count": len(todos)
        }