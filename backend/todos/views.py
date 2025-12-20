from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import TodoSerializer
from .service import TodoService

class TodoViewSet(viewsets.ModelViewSet):
    serializer_class = TodoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 認可：本人のタスクのみをService層から取得
        return TodoService.get_user_todos(self.request.user)

    def perform_create(self, serializer):
        # Service層を介して作成
        TodoService.create_todo(self.request.user, serializer.validated_data)

    def perform_update(self, serializer):
        # Service層を介して更新
        TodoService.update_todo(self.get_object().id, self.request.user, serializer.validated_data)

    def perform_destroy(self, instance):
        # Service層を介して削除
        TodoService.delete_todo(instance.id, self.request.user)