"""
Tests for TodoAnalyticsService
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model

from todos.models import Todo
from todos.analytics_service import TodoAnalyticsService

User = get_user_model()


class TodoAnalyticsServiceTestCase(TestCase):
    """Tests for TodoAnalyticsService"""

    def setUp(self):
        """各テストの前に実行される初期設定"""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        self.todo = Todo.objects.create(
            user=self.user,
            todo_title='Test Todo',
            priority=Todo.Priority.HIGH,
            progress=50
        )

    @patch('todos.analytics_service.MotherDuckClient')
    def test_log_todo_create_success(self, mock_motherduck_class):
        """log_todo_create: 作成イベントが正しく記録される"""
        # Arrange
        mock_client = MagicMock()
        mock_client.insert_todo_event.return_value = True
        mock_motherduck_class.return_value = mock_client
        
        # Act
        TodoAnalyticsService.log_todo_create(self.user, self.todo)
        
        # Assert
        mock_client.insert_todo_event.assert_called_once()
        call_args = mock_client.insert_todo_event.call_args[0][0]
        
        self.assertEqual(call_args["user_id"], self.user.id)
        self.assertEqual(call_args["todo_id"], self.todo.id)
        self.assertEqual(call_args["event_type"], "create")
        self.assertEqual(call_args["todo_title"], "Test Todo")
        self.assertEqual(call_args["priority"], "HIGH")
        self.assertEqual(call_args["progress"], 50)
        self.assertFalse(call_args["is_completed"])
        self.assertIsNone(call_args["changed_fields"])
        self.assertIsNone(call_args["deletion_reason"])

    @patch('todos.analytics_service.MotherDuckClient')
    def test_log_todo_update_success(self, mock_motherduck_class):
        """log_todo_update: 更新イベントが正しく記録される"""
        # Arrange
        mock_client = MagicMock()
        mock_client.insert_todo_event.return_value = True
        mock_motherduck_class.return_value = mock_client
        
        changed_fields = {
            "priority": ["MEDIUM", "HIGH"],
            "progress": [30, 50]
        }
        
        # Act
        TodoAnalyticsService.log_todo_update(self.user, self.todo, changed_fields)
        
        # Assert
        mock_client.insert_todo_event.assert_called_once()
        call_args = mock_client.insert_todo_event.call_args[0][0]
        
        self.assertEqual(call_args["event_type"], "update")
        self.assertIsNotNone(call_args["changed_fields"])
        # changed_fields は JSON 文字列
        import json
        parsed_fields = json.loads(call_args["changed_fields"])
        self.assertEqual(parsed_fields["priority"], ["MEDIUM", "HIGH"])

    @patch('todos.analytics_service.MotherDuckClient')
    def test_log_todo_delete_success(self, mock_motherduck_class):
        """log_todo_delete: 削除イベントが正しく記録される"""
        # Arrange
        mock_client = MagicMock()
        mock_client.insert_todo_event.return_value = True
        mock_motherduck_class.return_value = mock_client
        
        # Act
        TodoAnalyticsService.log_todo_delete(self.user, self.todo, deletion_reason="cancelled")
        
        # Assert
        mock_client.insert_todo_event.assert_called_once()
        call_args = mock_client.insert_todo_event.call_args[0][0]
        
        self.assertEqual(call_args["event_type"], "delete")
        self.assertEqual(call_args["deletion_reason"], "cancelled")

    @patch('todos.analytics_service.MotherDuckClient')
    def test_log_todo_complete_success(self, mock_motherduck_class):
        """log_todo_complete: 完了イベントが正しく記録される"""
        # Arrange
        mock_client = MagicMock()
        mock_client.insert_todo_event.return_value = True
        mock_motherduck_class.return_value = mock_client
        
        self.todo.progress = 100
        
        # Act
        TodoAnalyticsService.log_todo_complete(self.user, self.todo)
        
        # Assert
        mock_client.insert_todo_event.assert_called_once()
        call_args = mock_client.insert_todo_event.call_args[0][0]
        
        self.assertEqual(call_args["event_type"], "complete")
        self.assertEqual(call_args["progress"], 100)
        self.assertTrue(call_args["is_completed"])

    @patch('todos.analytics_service.MotherDuckClient')
    def test_log_todo_create_continues_on_error(self, mock_motherduck_class):
        """log_todo_create: MotherDuck接続エラーでも例外を発生させない"""
        # Arrange
        mock_motherduck_class.side_effect = Exception("Connection error")
        
        # Act - 例外が発生しないことを確認
        try:
            TodoAnalyticsService.log_todo_create(self.user, self.todo)
        except Exception as e:
            self.fail(f"log_todo_create should not raise exception, but got: {e}")

    @patch('todos.analytics_service.MotherDuckClient')
    def test_log_todo_update_continues_on_error(self, mock_motherduck_class):
        """log_todo_update: MotherDuck記録エラーでも例外を発生させない"""
        # Arrange
        mock_client = MagicMock()
        mock_client.insert_todo_event.side_effect = Exception("Insert error")
        mock_motherduck_class.return_value = mock_client
        
        # Act
        try:
            TodoAnalyticsService.log_todo_update(self.user, self.todo, {})
        except Exception as e:
            self.fail(f"log_todo_update should not raise exception, but got: {e}")