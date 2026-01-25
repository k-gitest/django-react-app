import logging

from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request

from apps.common.permissions import IsQStashAuthenticated
from apps.common.error_decorators import log_webhook_call

from .serializers import (
    TodoSerializer,
    TodoSearchParamsSerializer,
    VectorIndexingWebhookSerializer,
    BulkVectorIndexingWebhookSerializer
)
from .service import TodoCommandService, TodoQueryService, TodoStatsService, TodoSearchService
from .webhook_service import TodoWebhookService

logger = logging.getLogger(__name__)
User = get_user_model()


class TodoViewSet(viewsets.ModelViewSet):
    """
    TodoのCRUD操作
    
    すべてのビジネスロジックはService層に委譲。
    View層は以下のみを担当：
    - HTTPリクエスト/レスポンス処理
    - 認証・認可
    - Serializerでのバリデーション
    
    エラーハンドリングは統一エラーハンドラー（error_handlers.py）に任せる。
    """
    
    serializer_class = TodoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        本人のタスクのみを取得（認可の担保）
        
        Service層から取得することで、ビジネスロジックを集約
        """
        return TodoQueryService.get_user_todos(self.request.user)

    def perform_create(self, serializer):
        """
        Todoの作成

        """
        todo = TodoCommandService.create_todo(
            self.request.user,
            serializer.validated_data
        )
        serializer.instance = todo

    def perform_update(self, serializer):
        """
        Todoの更新

        """
        todo = TodoCommandService.update_todo(
            self.get_object().id,
            self.request.user,
            serializer.validated_data
        )
        serializer.instance = todo

    def perform_destroy(self, instance):
        """
        Todoの削除
        
        """
        TodoCommandService.delete_todo(instance.id, self.request.user)

    # ===== 統計エンドポイント =====

    @action(detail=False, methods=["get"])
    def stats(self, request: Request) -> Response:
        """
        優先度別統計データの取得
        
        GET /api/v1/todos/stats/
        
        Returns:
            [
                {"priority": "HIGH", "count": 3},
                {"priority": "MEDIUM", "count": 5},
                {"priority": "LOW", "count": 2}
            ]
        """
        stats = TodoStatsService.get_priority_stats(request.user)
        return Response(stats)

    @action(detail=False, methods=["get"], url_path="progress-stats")
    def progress_stats(self, request: Request) -> Response:
        """
        進捗率別統計データの取得
        
        GET /api/v1/todos/progress-stats/
        
        Returns:
            {
                "range_0_20": 2,
                "range_21_40": 3,
                "range_41_60": 1,
                "range_61_80": 4,
                "range_81_100": 5
            }
        """
        stats = TodoStatsService.get_progress_stats(request.user)
        return Response(stats)

    # ===== ベクトル検索エンドポイント =====

    @action(detail=False, methods=["get"])
    def search(self, request: Request) -> Response:
        """
        セマンティック検索
        
        GET /api/v1/todos/search/?q=明日の会議&top_k=5&min_score=0.5
        
        クエリパラメータ:
            - q: 検索クエリ（必須）
            - top_k: 返す結果数（デフォルト: 5）
            - min_score: 最小類似度スコア（デフォルト: 0.5）
        
        Returns:
            {
                "query": "明日の会議",
                "results": [
                    {
                        "id": 15,
                        "score": 0.87,
                        "title": "会議資料の作成",
                        "priority": "HIGH",
                        "progress": 50
                    }
                ],
                "count": 1
            }
        
        Raises:
            ValidationError: クエリパラメータが不正な場合
            VectorError: ベクトル検索エラー
            EmbeddingError: Embedding生成エラー
        """
        # Serializerでバリデーション
        serializer = TodoSearchParamsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        params = serializer.validated_data
        
        # Service層で検索（エラーは統一エラーハンドラーが処理）
        results = TodoSearchService.search_similar_todos(
            request.user,
            params['q'],
            top_k=params['top_k'],
            min_score=params['min_score']
        )

        return Response({
            "query": params['q'],
            "results": results,
            "count": len(results)
        })

    @action(detail=False, methods=["post"], url_path="bulk-index")
    def bulk_index(self, request: Request) -> Response:
        """
        全Todoをベクトルインデックスに一括追加
        
        POST /api/v1/todos/bulk-index/
        
        非同期処理（QStash経由）でバックグラウンド実行。
        初期データ投入やリインデックス時に使用。
        
        Returns:
            {
                "message": "インデックス処理をバックグラウンドで開始しました",
                "status": "queued"
            }
        
        Raises:
            QStashError: QStashキューイングエラー
        """
        # Service層でキューイング（エラーは統一エラーハンドラーが処理）
        TodoSearchService.bulk_index_todos(request.user)
        
        return Response({
            "message": "インデックス処理をバックグラウンドで開始しました",
            "status": "queued"
        })


# ===== Webhook エンドポイント（QStash専用） =====


@api_view(["POST"])
@permission_classes([IsQStashAuthenticated])
@log_webhook_call("vector_indexing")
def vector_indexing_webhook(request: Request) -> Response:
    """
    Todoのベクトルインデックス処理（QStashから呼ばれる）
    
    POST /api/v1/webhooks/vector-indexing
    
    """
    serializer = VectorIndexingWebhookSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    result = TodoWebhookService.handle_vector_indexing(
        todo_id=serializer.validated_data['todo_id'],
        operation=serializer.validated_data['operation']
    )
    
    return Response(result)


@api_view(["POST"])
@permission_classes([IsQStashAuthenticated])
@log_webhook_call("bulk_vector_indexing")
def bulk_vector_indexing_webhook(request: Request) -> Response:
    """
    ユーザーの全Todoを一括インデックス（QStashから呼ばれる）
    
    POST /api/v1/webhooks/bulk-vector-indexing
    
    """
    serializer = BulkVectorIndexingWebhookSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    result = TodoWebhookService.handle_bulk_vector_indexing(
        user_id=serializer.validated_data['user_id']
    )
    
    return Response(result)