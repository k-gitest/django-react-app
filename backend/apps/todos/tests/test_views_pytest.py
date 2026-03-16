"""
Todoアプリのビューテスト（pytest）
TodoViewSet と Webhook ビューのテスト
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.todos.models import Todo

User = get_user_model()


# ================================
# TodoViewSet Tests
# ================================

@pytest.mark.django_db
class TestTodoViewSet:
    """TodoViewSet のテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    @override_settings(TESTING=True)
    def test_list_todos(self):
        """Todo一覧取得"""
        Todo.objects.create(user=self.user, todo_title="Todo 1")
        Todo.objects.create(user=self.user, todo_title="Todo 2")

        response = self.client.get("/api/v1/todos/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    @override_settings(TESTING=True)
    def test_create_todo(self):
        """Todo作成"""
        data = {
            "todo_title": "New Todo",
            "priority": "HIGH",
            "progress": 0
        }

        response = self.client.post("/api/v1/todos/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["todo_title"] == "New Todo"
        assert Todo.objects.filter(todo_title="New Todo").exists()

    @override_settings(TESTING=True)
    def test_update_todo(self):
        """Todo更新"""
        todo = Todo.objects.create(user=self.user, todo_title="Original", progress=0)

        response = self.client.patch(
            f"/api/v1/todos/{todo.id}/",
            {"todo_title": "Updated", "progress": 50},
            format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["todo_title"] == "Updated"
        assert response.data["progress"] == 50

    @override_settings(TESTING=True)
    def test_delete_todo(self):
        """Todo削除"""
        todo = Todo.objects.create(user=self.user, todo_title="Delete Me")

        response = self.client.delete(f"/api/v1/todos/{todo.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Todo.objects.filter(id=todo.id).exists()

    def test_get_stats(self):
        """優先度統計取得"""
        Todo.objects.create(user=self.user, todo_title="T1", priority=Todo.Priority.HIGH)
        Todo.objects.create(user=self.user, todo_title="T2", priority=Todo.Priority.HIGH)

        response = self.client.get("/api/v1/todos/stats/")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_get_progress_stats(self):
        """進捗統計取得"""
        Todo.objects.create(user=self.user, todo_title="T1", progress=10)
        Todo.objects.create(user=self.user, todo_title="T2", progress=90)

        response = self.client.get("/api/v1/todos/progress-stats/")

        assert response.status_code == status.HTTP_200_OK
        assert "range_0_20" in response.data

    def test_user_isolation(self):
        """ユーザーは自分のTodoのみアクセス可能"""
        other_user = User.objects.create_user(
            email="other@example.com",
            password="pass123"
        )
        other_todo = Todo.objects.create(user=other_user, todo_title="Other User Todo")

        response = self.client.get(f"/api/v1/todos/{other_todo.id}/")

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ================================
# TodoWebhook Tests
# ================================

@pytest.mark.django_db
class TestTodoWebhookViews:
    """Todo Webhook ビューのテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        self.todo = Todo.objects.create(user=self.user, todo_title="Test Todo")

    def test_vector_indexing_webhook(self, mocker):
        """ベクトルインデックス化Webhook"""
        mocker.patch(
            "apps.common.permissions.verify_qstash_signature", return_value=True
        )
        mock_handle = mocker.patch(
            "apps.todos.views.TodoWebhookService.handle_vector_indexing",
            return_value={
                "message": "Vector indexed successfully",
                "todo_id": self.todo.id,
                "operation": "upsert"
            }
        )

        response = self.client.post(
            "/api/v1/webhooks/vector-indexing",
            {"todo_id": self.todo.id, "operation": "upsert"},
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid"
        )

        assert response.status_code == status.HTTP_200_OK
        mock_handle.assert_called_once_with(todo_id=self.todo.id, operation="upsert")

    def test_bulk_vector_indexing_webhook(self, mocker):
        """一括ベクトルインデックス化Webhook"""
        mocker.patch(
            "apps.common.permissions.verify_qstash_signature", return_value=True
        )
        mock_handle = mocker.patch(
            "apps.todos.views.TodoWebhookService.handle_bulk_vector_indexing",
            return_value={
                "message": "Bulk indexing completed",
                "user_id": self.user.id,
                "count": 1
            }
        )

        response = self.client.post(
            "/api/v1/webhooks/bulk-vector-indexing",
            {"user_id": self.user.id},
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid"
        )

        assert response.status_code == status.HTTP_200_OK
        mock_handle.assert_called_once_with(user_id=self.user.id)

    def test_webhook_invalid_signature(self, mocker):
        """無効な署名でのWebhook"""
        mocker.patch(
            "apps.common.permissions.verify_qstash_signature", return_value=False
        )

        response = self.client.post(
            "/api/v1/webhooks/vector-indexing",
            {"todo_id": 1, "operation": "upsert"},
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=invalid"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN