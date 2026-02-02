from .models import Todo
from django.db.models import Count, Case, When
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.db import transaction
from django.conf import settings
from typing import Optional, Dict, List, Any
import logging

from apps.common.error_decorators import service_error_handler
from apps.common.exceptions import (
    QStashError,
    AnalyticsError,
    VectorError,
    EmbeddingError,
)
from apps.common.error_reporting import ErrorMonitor, ErrorProfiles

from .qstash_service import TodoQStashService
from .analytics_service import TodoAnalyticsService
from .vector_service import VectorService

logger = logging.getLogger(__name__)


class TodoQueryService:
    """
    Todo読み取り操作サービス
    """
    
    @staticmethod
    @service_error_handler
    def get_user_todos(user):
        """
        ユーザー自身のタスクのみを取得（認可の担保）
        
        Args:
            user: 対象ユーザー
            
        Returns:
            QuerySet[Todo]: ユーザーのTodoリスト
        """
        # ユーザーが認証されていない（AnonymousUser）場合は、空のリストを返す
        if not user or user.is_anonymous:
            return Todo.objects.none()
        
        return Todo.objects.filter(user=user)
    
    @staticmethod
    @service_error_handler
    def get_todo_by_id(todo_id: int, user) -> Optional[Todo]:
        """
        IDでTodoを取得（認可チェック付き）
        
        Args:
            todo_id: TodoのID
            user: リクエストユーザー
            
        Returns:
            Todo or None
        """
        return Todo.objects.filter(id=todo_id, user=user).first()
    
    @staticmethod
    @service_error_handler
    def get_todo_or_404(todo_id: int, user) -> Todo:
        """
        IDでTodoを取得、存在しない場合は404
        
        Args:
            todo_id: TodoのID
            user: リクエストユーザー
            
        Returns:
            Todo
            
        Raises:
            Http404: Todoが存在しないか、他ユーザーのもの
        """
        return get_object_or_404(Todo, id=todo_id, user=user)


class TodoStatsService:
    """
    Todo統計サービス（キャッシュ管理含む）
    """
    
    # キャッシュの有効期限（秒）
    CACHE_TIMEOUT = 900

    @staticmethod
    def _get_stats_cache_key(user_id: int, stats_type: str) -> str:
        """キャッシュキーの生成ロジックを一元管理"""
        return f"todo_stats:{user_id}:{stats_type}"
    
    @staticmethod
    @service_error_handler
    def get_progress_stats(user) -> Dict[str, int]:
        """
        進捗率の分布を集計（20%刻み）
        
        Args:
            user: 対象ユーザー
            
        Returns:
            dict: 進捗率別の件数
        """
        cache_key = TodoStatsService._get_stats_cache_key(user.id, "progress")
        stats = cache.get(cache_key)

        if stats is None:
            stats = Todo.objects.filter(user=user).aggregate(
                range_0_20=Count(Case(When(progress__lte=20, then=1))),
                range_21_40=Count(Case(When(progress__gt=20, progress__lte=40, then=1))),
                range_41_60=Count(Case(When(progress__gt=40, progress__lte=60, then=1))),
                range_61_80=Count(Case(When(progress__gt=60, progress__lte=80, then=1))),
                range_81_100=Count(Case(When(progress__gt=80, then=1))),
            )
            cache.set(cache_key, stats, TodoStatsService.CACHE_TIMEOUT)
        return stats

    @staticmethod
    @service_error_handler
    def get_priority_stats(user) -> List[Dict[str, Any]]:
        """
        優先度別の統計を取得
        
        Args:
            user: 対象ユーザー
            
        Returns:
            list[dict]: 優先度別の件数
        """
        cache_key = TodoStatsService._get_stats_cache_key(user.id, "priority")
        stats = cache.get(cache_key)

        if stats is None:
            stats = list(
                Todo.objects.filter(user=user)
                .values('priority')
                .annotate(count=Count('id'))
                .order_by('priority')
            )
            cache.set(cache_key, stats, TodoStatsService.CACHE_TIMEOUT)
        return stats
    
    @staticmethod
    def invalidate_stats_cache(user_id: int):
        """
        指定したユーザーの統計キャッシュをすべて削除
        
        Args:
            user_id: ユーザーID
        """
        cache.delete(TodoStatsService._get_stats_cache_key(user_id, "progress"))
        cache.delete(TodoStatsService._get_stats_cache_key(user_id, "priority"))


class TodoCommandService:
    """
    Todo作成・更新・削除サービス
    """
    
    @staticmethod
    @service_error_handler
    @transaction.atomic
    def create_todo(user, validated_data: Dict[str, Any]) -> Todo:
        """
        タスクの作成
        
        ベクトルインデックスは非同期で実行（QStash経由）
        分析ログをMotherDuckに記録
        
        Args:
            user: 作成者
            validated_data: Serializerで検証済みのデータ
            
        Returns:
            Todo: 作成されたTodoインスタンス
        """
        # Todo作成
        todo = Todo.objects.create(user=user, **validated_data)
        
        # キャッシュ無効化
        TodoStatsService.invalidate_stats_cache(user.id)
        
        # 外部サービス（QStash, Analytics）はon_commitで実行
        if not getattr(settings, "TESTING", False):
            transaction.on_commit(
                lambda: TodoCommandService._queue_vector_indexing_safely(todo.id, "upsert")
            )
            transaction.on_commit(
                lambda: TodoCommandService._log_todo_create_safely(user, todo)
            )
        
        return todo
    
    @staticmethod
    @service_error_handler
    @transaction.atomic
    def update_todo(todo_id: int, user, validated_data: Dict[str, Any]) -> Todo:
        """
        タスクの更新
        
        ベクトルインデックスは非同期で更新（QStash経由）
        分析ログをMotherDuckに記録
        
        Args:
            todo_id: 更新対象のID
            user: リクエストユーザー（認可チェック用）
            validated_data: Serializerで検証済みのデータ
            
        Returns:
            Todo: 更新されたTodoインスタンス
        """
        # 認可チェック: 存在確認 + 本人確認
        todo = get_object_or_404(Todo, id=todo_id, user=user)

        # 変更前の値を保存（分析用）
        old_values = {
            "todo_title": todo.todo_title,
            "priority": todo.priority,
            "progress": todo.progress,
        }
        
        # 更新
        for key, value in validated_data.items():
            setattr(todo, key, value)
        todo.save()

        # 変更されたフィールドを検出
        changed_fields = {}
        for key, old_value in old_values.items():
            new_value = getattr(todo, key)
            if old_value != new_value:
                changed_fields[key] = [old_value, new_value]
        
        # キャッシュ無効化
        TodoStatsService.invalidate_stats_cache(user.id)
        
        # 外部サービス（QStash, Analytics）はon_commitで実行
        if not getattr(settings, "TESTING", False):
            transaction.on_commit(
                lambda: TodoCommandService._queue_vector_indexing_safely(todo.id, "upsert")
            )
            
            # 完了イベントの検出
            if old_values["progress"] < 100 and todo.progress == 100:
                transaction.on_commit(
                    lambda: TodoCommandService._log_todo_complete_safely(user, todo)
                )
            elif changed_fields:
                transaction.on_commit(
                    lambda: TodoCommandService._log_todo_update_safely(user, todo, changed_fields)
                )
        
        return todo
    
    @staticmethod
    @service_error_handler
    @transaction.atomic
    def delete_todo(todo_id: int, user) -> None:
        """
        タスクの削除
        
        ベクトルインデックスは非同期で削除（QStash経由）
        分析ログをMotherDuckに記録
        
        Args:
            todo_id: 削除対象のID
            user: リクエストユーザー（認可チェック用）
        """
        # 認可チェック: 存在確認 + 本人確認
        todo = get_object_or_404(Todo, id=todo_id, user=user)
        
        # 削除理由を判定
        deletion_reason = "completed" if todo.progress == 100 else "cancelled"
        
        # 外部サービス（QStash, Analytics）はon_commitで実行
        if not getattr(settings, "TESTING", False):
            transaction.on_commit(
                lambda: TodoCommandService._queue_vector_deletion_safely(todo_id)
            )
            transaction.on_commit(
                lambda: TodoCommandService._log_todo_delete_safely(user, todo, deletion_reason)
            )
        
        # Todo削除
        todo.delete()
        
        # キャッシュ無効化
        TodoStatsService.invalidate_stats_cache(user.id)
    
    # ===== 安全な外部サービス呼び出し =====
    
    @staticmethod
    def _queue_vector_indexing_safely(todo_id: int, operation: str):
        """ベクトルインデックス登録を安全に実行（失敗してもエラーを投げない）"""
        with ErrorMonitor.capture_and_continue(
            component='qstash',
            operation='queue_vector_indexing',
            service='TodoCommandService',
            expected_errors=(QStashError,),
            profile=ErrorProfiles.INFRASTRUCTURE_MEDIUM,
            context={'todo_id': todo_id, 'operation': operation}
        ):
            result = TodoQStashService.queue_vector_indexing(todo_id, operation=operation)
            if not result["success"]:
                raise QStashError(
                    message=f"Failed to queue vector indexing: {result.get('error')}",
                    endpoint="vector_indexing"
                )
    
    @staticmethod
    def _queue_vector_deletion_safely(todo_id: int):
        """ベクトルインデックス削除を安全に実行（失敗してもエラーを投げない）"""
        with ErrorMonitor.capture_and_continue(
            component='qstash',
            operation='queue_vector_deletion',
            service='TodoCommandService',
            expected_errors=(QStashError,),
            profile=ErrorProfiles.INFRASTRUCTURE_MEDIUM,
            context={'todo_id': todo_id}
        ):
            result = TodoQStashService.queue_vector_indexing(todo_id, operation="delete")
            if not result["success"]:
                raise QStashError(
                    message=f"Failed to queue vector deletion: {result.get('error')}",
                    endpoint="vector_deletion"
                )
    
    @staticmethod
    def _log_todo_create_safely(user, todo: Todo):
        """Todo作成ログを安全に実行（失敗してもエラーを投げない）"""
        with ErrorMonitor.capture_and_continue(
            component='analytics',
            operation='log_todo_create',
            service='TodoCommandService',
            expected_errors=(AnalyticsError,),
            profile=ErrorProfiles.MONITORING_LOW,
            user=user,
            context={'todo_id': todo.id}
        ):
            TodoAnalyticsService.log_todo_create(user=user, todo=todo)
    
    @staticmethod
    def _log_todo_update_safely(user, todo: Todo, changed_fields: Dict):
        """Todo更新ログを安全に実行（失敗してもエラーを投げない）"""
        with ErrorMonitor.capture_and_continue(
            component='analytics',
            operation='log_todo_update',
            service='TodoCommandService',
            expected_errors=(AnalyticsError,),
            profile=ErrorProfiles.MONITORING_LOW,
            user=user,
            context={'todo_id': todo.id, 'changed_fields': list(changed_fields.keys())}
        ):
            TodoAnalyticsService.log_todo_update(
                user=user,
                todo=todo,
                changed_fields=changed_fields
            )
    
    @staticmethod
    def _log_todo_complete_safely(user, todo: Todo):
        """Todo完了ログを安全に実行（失敗してもエラーを投げない）"""
        with ErrorMonitor.capture_and_continue(
            component='analytics',
            operation='log_todo_complete',
            service='TodoCommandService',
            expected_errors=(AnalyticsError,),
            profile=ErrorProfiles.MONITORING_LOW,
            user=user,
            context={'todo_id': todo.id}
        ):
            TodoAnalyticsService.log_todo_complete(user=user, todo=todo)
    
    @staticmethod
    def _log_todo_delete_safely(user, todo: Todo, deletion_reason: str):
        """Todo削除ログを安全に実行（失敗してもエラーを投げない）"""
        with ErrorMonitor.capture_and_continue(
            component='analytics',
            operation='log_todo_delete',
            service='TodoCommandService',
            expected_errors=(AnalyticsError,),
            profile=ErrorProfiles.MONITORING_LOW,
            user=user,
            context={'todo_id': todo.id, 'deletion_reason': deletion_reason}
        ):
            TodoAnalyticsService.log_todo_delete(
                user=user,
                todo=todo,
                deletion_reason=deletion_reason
            )


class TodoSearchService:
    """
    Todoセマンティック検索サービス
    """
    
    @staticmethod
    @service_error_handler
    def search_similar_todos(
        user,
        query: str,
        top_k: int = 5,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        セマンティック検索（同期処理）
        
        検索は即座に結果を返す必要があるため同期処理
        
        Args:
            user: リクエストユーザー
            query: 検索クエリ（例: "明日の会議関連"）
            top_k: 返す結果の最大数
            min_score: 最小類似度スコア
        
        Returns:
            list[dict]: 検索結果
            
        Raises:
            VectorError: ベクトル検索エラー
            EmbeddingError: Embedding生成エラー
        """
        try:
            vector_service = VectorService()
            return vector_service.search_similar(query, user.id, top_k, min_score)
        except (VectorError, EmbeddingError):
            # 既に適切な例外なので再送出
            raise
        except Exception as e:
            # 予期しないエラー
            logger.exception("Unexpected error in search_similar_todos")
            # VectorError として送出（検索機能のエラーとして扱う）
            raise VectorError(
                message=f"検索中に予期しないエラーが発生しました: {str(e)}",
                operation="search_similar"
            )
    
    @staticmethod
    @service_error_handler
    def bulk_index_todos(user) -> bool:
        """
        ユーザーの全Todoを一括インデックス（非同期版）
        
        QStash経由でWebhookを呼び出し
        
        Args:
            user: 対象ユーザー
        
        Returns:
            bool: キューイング成功/失敗
            
        Raises:
            QStashError: QStashキューイングエラー
        """
        try:
            result = TodoQStashService.queue_bulk_vector_indexing(user.id)
            if result["success"]:
                logger.info(f"Queued bulk indexing for user {user.id}")
                return True
            else:
                raise QStashError(
                    message=f"Failed to queue bulk indexing: {result.get('error')}",
                    endpoint="bulk_vector_indexing"
                )
        except QStashError:
            # 既に適切な例外なので再送出
            raise
        except Exception as e:
            # 予期しないエラー
            logger.exception("Unexpected error in bulk_index_todos")
            raise QStashError(
                message=f"一括インデックス登録中に予期しないエラーが発生しました: {str(e)}",
                endpoint="bulk_vector_indexing"
            )