"""
Tests for todos views
ViewSet と Webhook のテストを網羅
"""
from unittest.mock import patch
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.test import override_settings

from apps.todos.models import Todo

User = get_user_model()


# ================================
# TodoViewSet Tests
# ================================

class TodoViewSetTestCase(APITestCase):
    """TodoViewSet のテスト"""
    
    def setUp(self):
        """各テストの前に実行"""
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
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    @override_settings(TESTING=True)
    def test_create_todo(self):
        """Todo作成"""
        data = {
            'todo_title': 'New Todo',
            'priority': 'HIGH',
            'progress': 0
        }
        
        response = self.client.post(
            "/api/v1/todos/",
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['todo_title'], 'New Todo')
        self.assertTrue(Todo.objects.filter(todo_title='New Todo').exists())
    
    @override_settings(TESTING=True)
    def test_update_todo(self):
        """Todo更新"""
        todo = Todo.objects.create(
            user=self.user,
            todo_title="Original",
            progress=0
        )
        
        data = {'todo_title': 'Updated', 'progress': 50}
        response = self.client.patch(
            f"/api/v1/todos/{todo.id}/",
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['todo_title'], 'Updated')
        self.assertEqual(response.data['progress'], 50)
    
    @override_settings(TESTING=True)
    def test_delete_todo(self):
        """Todo削除"""
        todo = Todo.objects.create(user=self.user, todo_title="Delete Me")
        
        response = self.client.delete(f"/api/v1/todos/{todo.id}/")
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Todo.objects.filter(id=todo.id).exists())
    
    def test_get_stats(self):
        """優先度統計取得"""
        Todo.objects.create(
            user=self.user,
            todo_title="T1",
            priority=Todo.Priority.HIGH
        )
        Todo.objects.create(
            user=self.user,
            todo_title="T2",
            priority=Todo.Priority.HIGH
        )
        
        response = self.client.get("/api/v1/todos/stats/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_get_progress_stats(self):
        """進捗統計取得"""
        Todo.objects.create(user=self.user, todo_title="T1", progress=10)
        Todo.objects.create(user=self.user, todo_title="T2", progress=90)
        
        response = self.client.get("/api/v1/todos/progress-stats/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('range_0_20', response.data)
    
    def test_user_isolation(self):
        """ユーザーは自分のTodoのみアクセス可能"""
        other_user = User.objects.create_user(
            email="other@example.com",
            password="pass123"
        )
        other_todo = Todo.objects.create(
            user=other_user,
            todo_title="Other User Todo"
        )
        
        response = self.client.get(f"/api/v1/todos/{other_todo.id}/")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ================================
# TodoWebhook Tests
# ================================

class TodoWebhookViewsTestCase(APITestCase):
    """Todo Webhook ビューのテスト"""
    
    def setUp(self):
        """各テストの前に実行"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        self.todo = Todo.objects.create(
            user=self.user,
            todo_title="Test Todo"
        )
    
    @patch("apps.todos.views.TodoWebhookService.handle_vector_indexing")
    @patch("apps.common.permissions.verify_qstash_signature")
    def test_vector_indexing_webhook(self, mock_verify, mock_handle):
        """ベクトルインデックス化Webhook"""
        mock_verify.return_value = True
        mock_handle.return_value = {
            "message": "Vector indexed successfully",
            "todo_id": self.todo.id,
            "operation": "upsert"
        }
        
        response = self.client.post(
            "/api/v1/webhooks/vector-indexing",
            {
                'todo_id': self.todo.id,
                'operation': 'upsert'
            },
            format='json',
            HTTP_UPSTASH_SIGNATURE="v1=valid"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_handle.assert_called_once_with(
            todo_id=self.todo.id,
            operation='upsert'
        )
    
    @patch("apps.todos.views.TodoWebhookService.handle_bulk_vector_indexing")
    @patch("apps.common.permissions.verify_qstash_signature")
    def test_bulk_vector_indexing_webhook(self, mock_verify, mock_handle):
        """一括ベクトルインデックス化Webhook"""
        mock_verify.return_value = True
        mock_handle.return_value = {
            "message": "Bulk indexing completed",
            "user_id": self.user.id,
            "count": 1
        }
        
        response = self.client.post(
            "/api/v1/webhooks/bulk-vector-indexing",
            {'user_id': self.user.id},
            format='json',
            HTTP_UPSTASH_SIGNATURE="v1=valid"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_handle.assert_called_once_with(user_id=self.user.id)
    
    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_invalid_signature(self, mock_verify):
        """無効な署名でのWebhook"""
        mock_verify.return_value = False
        
        response = self.client.post(
            "/api/v1/webhooks/vector-indexing",
            {'todo_id': 1, 'operation': 'upsert'},
            format='json',
            HTTP_UPSTASH_SIGNATURE="v1=invalid"
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)