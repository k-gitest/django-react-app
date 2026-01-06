from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, action
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from common.permissions import IsQStashAuthenticated
from .serializers import TodoSerializer
from .service import TodoService
from .models import Todo
from .vector_service import VectorService
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class TodoViewSet(viewsets.ModelViewSet):
    serializer_class = TodoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 認可：本人のタスクのみをService層から取得
        return TodoService.get_user_todos(self.request.user)

    def perform_create(self, serializer):
        # Service層を介して作成
        todo = TodoService.create_todo(self.request.user, serializer.validated_data)
        # serializerのinstanceを設定（レスポンスに含めるため）
        serializer.instance = todo

    def perform_update(self, serializer):
        # Service層を介して更新
        todo = TodoService.update_todo(self.get_object().id, self.request.user, serializer.validated_data)
        # serializerのinstanceを設定（レスポンスに含めるため）
        serializer.instance = todo

    def perform_destroy(self, instance):
        # Service層を介して削除
        TodoService.delete_todo(instance.id, self.request.user)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """統計データの取得: /api/v1/todos/stats/"""
        user = request.user
        stats = TodoService.get_priority_stats(user)
        return Response(stats)
    
    @action(detail=False, methods=['get'], url_path='progress-stats')
    def progress_stats(self, request):
        """進捗率別統計データの取得: /api/v1/todos/progress-stats/"""
        user = request.user
        stats = TodoService.get_progress_stats(user)
        return Response(stats)
    
    # ===== 🆕 ベクトル検索機能 =====
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        セマンティック検索: /api/v1/todos/search/?q=明日の会議
        
        クエリパラメータ:
            - q: 検索クエリ（必須）
            - top_k: 返す結果数（デフォルト: 5）
            - min_score: 最小類似度スコア（デフォルト: 0.5）
        
        レスポンス例:
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
        """
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response(
                {"error": "検索クエリ 'q' を指定してください"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            top_k = int(request.query_params.get('top_k', 5))
            min_score = float(request.query_params.get('min_score', 0.5))
        except ValueError:
            return Response(
                {"error": "top_k は整数、min_score は小数を指定してください"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # バリデーション
        if top_k < 1 or top_k > 100:
            return Response(
                {"error": "top_k は 1〜100 の範囲で指定してください"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not (0 <= min_score <= 1):
            return Response(
                {"error": "min_score は 0.0〜1.0 の範囲で指定してください"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Service層で検索
        results = TodoService.search_similar_todos(
            request.user,
            query,
            top_k=top_k,
            min_score=min_score
        )
        
        return Response({
            "query": query,
            "results": results,
            "count": len(results)
        })
    
    @action(detail=False, methods=['post'], url_path='bulk-index')
    def bulk_index(self, request):
        """
        全Todoをベクトルインデックスに一括追加: /api/v1/todos/bulk-index/
        
        非同期処理（QStash経由）でバックグラウンド実行
        初期データ投入やリインデックス時に使用
        
        レスポンス例:
        {
            "message": "インデックス処理をバックグラウンドで開始しました",
            "status": "queued"
        }
        """
        try:
            TodoService.bulk_index_todos(request.user)
            return Response({
                "message": "インデックス処理をバックグラウンドで開始しました",
                "status": "queued"
            })
        except Exception as e:
            logger.error(f"Failed to queue bulk indexing: {e}")
            return Response(
                {"error": f"インデックス処理のキューイングに失敗しました: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ===== 🆕 Webhook エンドポイント（QStash専用） =====

@api_view(['POST'])
@permission_classes([IsQStashAuthenticated])
def vector_indexing_webhook(request):
    """
    Todoのベクトルインデックス処理（QStashから呼ばれる）
    
    署名検証は IsQStashAuthenticated で自動処理
    
    Payload:
        - todo_id: TodoのID（必須）
        - operation: "upsert" or "delete"（デフォルト: "upsert"）
    
    レスポンス:
        - 200: 成功
        - 400: バリデーションエラー
        - 404: Todo not found
        - 500: 処理エラー（QStashが自動リトライ）
    """
    todo_id = request.data.get("todo_id")
    operation = request.data.get("operation", "upsert")
    
    # バリデーション
    if not todo_id:
        logger.warning("vector_indexing_webhook: missing todo_id")
        return Response(
            {"error": "todo_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if operation not in ["upsert", "delete"]:
        logger.warning(f"vector_indexing_webhook: invalid operation '{operation}'")
        return Response(
            {"error": "operation must be 'upsert' or 'delete'"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        vector_service = VectorService()
        
        if operation == "delete":
            # 削除処理
            vector_service.delete_todo(todo_id)
            logger.info(f"✅ Deleted todo {todo_id} from vector index (async)")
            
            return Response({
                "message": "Vector deleted successfully",
                "todo_id": todo_id,
                "operation": "delete"
            })
        else:
            # Upsert処理
            todo = get_object_or_404(Todo, id=todo_id)
            vector_service.add_todo(todo)
            logger.info(f"✅ Added/Updated todo {todo_id} to vector index (async)")
            
            return Response({
                "message": "Vector indexed successfully",
                "todo_id": todo_id,
                "operation": "upsert"
            })
    
    except Todo.DoesNotExist:
        logger.error(f"❌ Todo {todo_id} not found")
        return Response(
            {"error": f"Todo with id {todo_id} not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    except Exception as e:
        logger.error(f"❌ Vector indexing webhook error: {e}", exc_info=True)
        # 500エラーでQStashが自動リトライする
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsQStashAuthenticated])
def bulk_vector_indexing_webhook(request):
    """
    ユーザーの全Todoを一括インデックス（QStashから呼ばれる）
    
    署名検証は IsQStashAuthenticated で自動処理
    
    Payload:
        - user_id: ユーザーID（必須）
    
    レスポンス:
        - 200: 成功
        - 400: バリデーションエラー
        - 404: User not found
        - 500: 処理エラー（QStashが自動リトライ）
    """
    user_id = request.data.get("user_id")
    
    # バリデーション
    if not user_id:
        logger.warning("bulk_vector_indexing_webhook: missing user_id")
        return Response(
            {"error": "user_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = get_object_or_404(User, id=user_id)
        todos = list(Todo.objects.filter(user=user))
        
        if not todos:
            logger.info(f"ℹ️ No todos found for user {user_id}")
            return Response({
                "message": "No todos to index",
                "count": 0
            })
        
        # 一括インデックス
        vector_service = VectorService()
        vector_service.add_todos_batch(todos)
        
        logger.info(f"✅ Bulk indexed {len(todos)} todos for user {user_id} (async)")
        
        return Response({
            "message": "Bulk vector indexing completed",
            "user_id": user_id,
            "count": len(todos)
        })
    
    except User.DoesNotExist:
        logger.error(f"❌ User {user_id} not found")
        return Response(
            {"error": f"User with id {user_id} not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    except Exception as e:
        logger.error(f"❌ Bulk vector indexing webhook error: {e}", exc_info=True)
        # 500エラーでQStashが自動リトライする
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )