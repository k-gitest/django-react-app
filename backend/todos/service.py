from .models import Todo
from django.db.models import Count, Case, When
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from .qstash_service import TodoQStashService
from .analytics_service import TodoAnalyticsService
import logging

logger = logging.getLogger(__name__)


class TodoService:
    """
    Todoのビジネスロジック層
    
    ベクトルインデックスは非同期処理（QStash経由）
    """

    # キャッシュの有効期限（秒）
    CACHE_TIMEOUT = 900

    @staticmethod
    def _get_stats_cache_key(user_id, stats_type):
        """キャッシュキーの生成ロジックを一元管理"""
        return f"todo_stats:{user_id}:{stats_type}"
    
    @staticmethod
    def get_user_todos(user):
        """ユーザー自身のタスクのみを取得（認可の担保）"""
        return Todo.objects.filter(user=user)

    @staticmethod
    def create_todo(user, validated_data):
        """
        タスクの作成
        
        ベクトルインデックスは非同期で実行（QStash経由）
        分析ログをMotherDuckに記録
        
        Args:
            user: 作成者
            validated_data: Serializerで検証済みのデータ
        """
        todo = Todo.objects.create(user=user, **validated_data)
        TodoService._invalidate_stats_cache(user.id)
        
        # 🔄 非同期でベクトルインデックスに追加
        try:
            result = TodoQStashService.queue_vector_indexing(todo.id, operation="upsert")
            if not result["success"]:
                logger.warning(f"QStash queue failed: {result['error']}")
        except Exception as e:
            # QStash送信失敗でもTodo作成は成功
            logger.error(f"Failed to queue vector indexing: {e}")

        TodoAnalyticsService.log_todo_create(user=user, todo=todo)
        
        return todo

    @staticmethod
    def update_todo(todo_id, user, validated_data):
        """
        タスクの更新
        
        ベクトルインデックスは非同期で更新（QStash経由）
        分析ログをMotherDuckに記録
        
        Args:
            todo_id: 更新対象のID
            user: リクエストユーザー（認可チェック用）
            validated_data: Serializerで検証済みのデータ
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
        
        TodoService._invalidate_stats_cache(user.id)
        
        # 🔄 非同期でベクトルインデックスを更新
        try:
            result = TodoQStashService.queue_vector_indexing(todo.id, operation="upsert")
            if not result["success"]:
                logger.warning(f"QStash queue failed: {result['error']}")
        except Exception as e:
            logger.error(f"Failed to queue vector indexing: {e}")
        
        # 完了イベントの検出
        if old_values["progress"] < 100 and todo.progress == 100:
            # 完了イベント
            TodoAnalyticsService.log_todo_complete(user=user, todo=todo)
        elif changed_fields:
            # 通常の更新イベント（変更がある場合のみ）
            TodoAnalyticsService.log_todo_update(user=user, todo=todo, changed_fields=changed_fields)
        
        return todo

    @staticmethod
    def delete_todo(todo_id, user):
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
        
        # 🔄 非同期でベクトルインデックスから削除
        try:
            result = TodoQStashService.queue_vector_indexing(todo_id, operation="delete")
            if not result["success"]:
                logger.warning(f"QStash queue failed: {result['error']}")
        except Exception as e:
            logger.error(f"Failed to queue vector deletion: {e}")

        # 削除理由を判定
        deletion_reason = "completed" if todo.progress == 100 else "cancelled"
        
        # 分析ログ記録（削除前に実行）
        TodoAnalyticsService.log_todo_delete(user=user, todo=todo, deletion_reason=deletion_reason)
        
        todo.delete()
        TodoService._invalidate_stats_cache(user.id)

    @staticmethod
    def get_progress_stats(user):
        cache_key = TodoService._get_stats_cache_key(user.id, "progress")
        stats = cache.get(cache_key)

        if stats is None:
            """進捗率の分布を集計（20%刻み）"""
            stats = Todo.objects.filter(user=user).aggregate(
                range_0_20=Count(Case(When(progress__lte=20, then=1))),
                range_21_40=Count(Case(When(progress__gt=20, progress__lte=40, then=1))),
                range_41_60=Count(Case(When(progress__gt=40, progress__lte=60, then=1))),
                range_61_80=Count(Case(When(progress__gt=60, progress__lte=80, then=1))),
                range_81_100=Count(Case(When(progress__gt=80, then=1))),
            )
            cache.set(cache_key, stats, TodoService.CACHE_TIMEOUT)
        return stats

    @staticmethod
    def get_priority_stats(user):
        cache_key = TodoService._get_stats_cache_key(user.id, "priority")
        stats = cache.get(cache_key)

        if stats is None:
            """優先度別の統計を取得"""
            stats = list(
                Todo.objects.filter(user=user)
                .values('priority')
                .annotate(count=Count('id'))
                .order_by('priority')
            )
            cache.set(cache_key, stats, TodoService.CACHE_TIMEOUT)
        return stats
    
    @staticmethod
    def _invalidate_stats_cache(user_id):
        """指定したユーザーの統計キャッシュをすべて削除"""
        cache.delete(TodoService._get_stats_cache_key(user_id, "progress"))
        cache.delete(TodoService._get_stats_cache_key(user_id, "priority"))
    
    # ===== ベクトル検索機能 =====
    
    @staticmethod
    def search_similar_todos(user, query: str, top_k: int = 5, min_score: float = 0.5):
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
        """
        from .vector_service import VectorService
        try:
            return VectorService().search_similar(query, user.id, top_k, min_score)
        except Exception as e:
            logger.error(f"Failed to search similar todos: {e}")
            # エラー時は空リストを返す
            return []
    
    @staticmethod
    def bulk_index_todos(user):
        """
        ユーザーの全Todoを一括インデックス（非同期版）
        
        QStash経由でWebhookを呼び出し
        
        Args:
            user: 対象ユーザー
        
        Returns:
            bool: キューイング成功/失敗
        """
        try:
            result = TodoQStashService.queue_bulk_vector_indexing(user.id)
            if result["success"]:
                logger.info(f"Queued bulk indexing for user {user.id}")
                return True
            else:
                logger.error(f"Failed to queue bulk indexing: {result['error']}")
                return False
        except Exception as e:
            logger.error(f"Failed to queue bulk indexing: {e}")
            raise