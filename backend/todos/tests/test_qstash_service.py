"""
Tests for TodoQStashService
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings

from todos.qstash_service import TodoQStashService


class TodoQStashServiceTestCase(TestCase):
    """Tests for TodoQStashService"""

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("common.infrastructure.qstash_client.requests.post")
    def test_queue_vector_indexing_upsert(self, mock_post):
        """Test queueing vector indexing with upsert operation"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        todo_id = 1

        # Act
        result = TodoQStashService.queue_vector_indexing(todo_id, operation="upsert")

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["message_id"], "msg_123")
        self.assertIsNone(result["error"])

        # Verify request details
        call_args = mock_post.call_args
        self.assertIn("/api/v1/webhooks/vector-indexing", call_args[0][0])
        self.assertEqual(call_args[1]["json"]["todo_id"], 1)
        self.assertEqual(call_args[1]["json"]["operation"], "upsert")
        self.assertEqual(call_args[1]["headers"]["Upstash-Delay"], "1s")

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("common.infrastructure.qstash_client.requests.post")
    def test_queue_vector_indexing_delete(self, mock_post):
        """Test queueing vector indexing with delete operation"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_456"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        todo_id = 5

        # Act
        result = TodoQStashService.queue_vector_indexing(todo_id, operation="delete")

        # Assert
        self.assertTrue(result["success"])
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]["json"]["operation"], "delete")

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("common.infrastructure.qstash_client.requests.post")
    def test_queue_vector_indexing_default_operation(self, mock_post):
        """Test queueing vector indexing with default operation (upsert)"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_789"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        todo_id = 10

        # Act
        result = TodoQStashService.queue_vector_indexing(todo_id)

        # Assert
        self.assertTrue(result["success"])
        call_args = mock_post.call_args
        # Default operation should be "upsert"
        self.assertEqual(call_args[1]["json"]["operation"], "upsert")

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("common.infrastructure.qstash_client.requests.post")
    def test_queue_vector_indexing_network_error(self, mock_post):
        """Test queueing vector indexing with network error"""
        # Arrange
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        todo_id = 1

        # Act
        result = TodoQStashService.queue_vector_indexing(todo_id)

        # Assert
        self.assertFalse(result["success"])
        self.assertIsNone(result["message_id"])
        self.assertIn("Network error", result["error"])

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("common.infrastructure.qstash_client.requests.post")
    def test_queue_bulk_vector_indexing_success(self, mock_post):
        """Test queueing bulk vector indexing"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_bulk_123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        user_id = 1

        # Act
        result = TodoQStashService.queue_bulk_vector_indexing(user_id)

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["message_id"], "msg_bulk_123")
        self.assertIsNone(result["error"])

        # Verify request details
        call_args = mock_post.call_args
        self.assertIn("/api/v1/webhooks/bulk-vector-indexing", call_args[0][0])
        self.assertEqual(call_args[1]["json"]["user_id"], 1)

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("common.infrastructure.qstash_client.requests.post")
    def test_queue_bulk_vector_indexing_network_error(self, mock_post):
        """Test queueing bulk vector indexing with network error"""
        # Arrange
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        user_id = 1

        # Act
        result = TodoQStashService.queue_bulk_vector_indexing(user_id)

        # Assert
        self.assertFalse(result["success"])
        self.assertIsNone(result["message_id"])
        self.assertIn("Network error", result["error"])

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("common.infrastructure.qstash_client.requests.post")
    def test_queue_vector_indexing_with_delay(self, mock_post):
        """Test that vector indexing queue has 1 second delay"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_delay"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Act
        TodoQStashService.queue_vector_indexing(1)

        # Assert
        call_args = mock_post.call_args
        # Verify 1 second delay is applied (for DB confirmation)
        self.assertEqual(call_args[1]["headers"]["Upstash-Delay"], "1s")

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("common.infrastructure.qstash_client.requests.post")
    def test_queue_vector_indexing_multiple_todos(self, mock_post):
        """Test queueing vector indexing for multiple todos"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_multi"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        todo_ids = [1, 2, 3, 4, 5]

        # Act
        results = [
            TodoQStashService.queue_vector_indexing(todo_id)
            for todo_id in todo_ids
        ]

        # Assert
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertTrue(result["success"])
        
        # Verify all were queued
        self.assertEqual(mock_post.call_count, 5)