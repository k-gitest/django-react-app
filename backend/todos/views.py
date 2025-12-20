from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import TodoSerializer
from .service import TodoService
from rest_framework.decorators import action
from django.db.models import Count

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
    def stats(self, request):  # ← request引数を追加
        """統計データの取得: /api/v1/todos/stats/"""
        user = request.user
        stats = TodoService.get_priority_stats(user)
        return Response(stats)
    
    @action(detail=False, methods=['get'], url_path='progress-stats')  # ← 新規追加
    def progress_stats(self, request):
        """進捗率別統計データの取得: /api/v1/todos/progress-stats/"""
        user = request.user
        stats = TodoService.get_progress_stats(user)
        return Response(stats)