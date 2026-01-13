"""
Tests for UserQStashService
"""

from unittest.mock import MagicMock, patch

from apps.users.qstash_service import UserQStashService
from django.test import TestCase, override_settings


class UserQStashServiceTestCase(TestCase):
    """Tests for UserQStashService"""

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_send_welcome_email_async_success(self, mock_post):
        """Test successful async welcome email queueing"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_welcome_123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        email = "newuser@example.com"
        first_name = "John"

        # Act
        result = UserQStashService.send_welcome_email_async(email, first_name)

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["message_id"], "msg_welcome_123")
        self.assertIsNone(result["error"])
        mock_post.assert_called_once()

        # Verify request details
        call_args = mock_post.call_args
        self.assertIn("https://qstash.upstash.io/v2/publish/", call_args[0][0])
        self.assertIn("/api/v1/webhooks/send-welcome-email", call_args[0][0])
        self.assertEqual(
            call_args[1]["headers"]["Authorization"], "Bearer test_qstash_token"
        )

        # Verify payload
        payload = call_args[1]["json"]
        self.assertEqual(payload["email"], email)
        self.assertEqual(payload["first_name"], first_name)

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_send_welcome_email_async_with_special_characters(self, mock_post):
        """Test async welcome email queueing with special characters in name"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_456"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        email = "user@example.com"
        first_name = "François"

        # Act
        result = UserQStashService.send_welcome_email_async(email, first_name)

        # Assert
        self.assertTrue(result["success"])
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["first_name"], "François")

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_send_welcome_email_async_network_error(self, mock_post):
        """Test async welcome email queueing with network error"""
        # Arrange
        import requests

        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        email = "user@example.com"
        first_name = "Alice"

        # Act
        result = UserQStashService.send_welcome_email_async(email, first_name)

        # Assert
        self.assertFalse(result["success"])
        self.assertIsNone(result["message_id"])
        self.assertIn("Network error", result["error"])

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_send_welcome_email_async_qstash_api_error(self, mock_post):
        """Test async welcome email queueing with QStash API error"""
        # Arrange
        import requests

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "API Error"
        )
        mock_post.return_value = mock_response

        email = "user@example.com"
        first_name = "Bob"

        # Act
        result = UserQStashService.send_welcome_email_async(email, first_name)

        # Assert
        self.assertFalse(result["success"])
        self.assertIsNone(result["message_id"])
        self.assertIsNotNone(result["error"])

    @override_settings(
        QSTASH_TOKEN="",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_send_welcome_email_async_missing_token(self, mock_post):
        """Test async welcome email queueing with missing QStash token"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_no_token"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        email = "user@example.com"
        first_name = "Charlie"

        # Act
        result = UserQStashService.send_welcome_email_async(email, first_name)

        # Assert - Should still attempt to send
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]["headers"]["Authorization"], "Bearer ")

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_send_welcome_email_async_empty_name(self, mock_post):
        """Test async welcome email queueing with empty name"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_empty"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        email = "user@example.com"
        first_name = ""

        # Act
        result = UserQStashService.send_welcome_email_async(email, first_name)

        # Assert
        self.assertTrue(result["success"])
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["first_name"], "")

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_send_welcome_email_async_long_name(self, mock_post):
        """Test async welcome email queueing with very long name"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_long"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        email = "user@example.com"
        first_name = "A" * 100  # Very long name

        # Act
        result = UserQStashService.send_welcome_email_async(email, first_name)

        # Assert
        self.assertTrue(result["success"])
        payload = mock_post.call_args[1]["json"]
        self.assertEqual(payload["first_name"], first_name)
        self.assertEqual(len(payload["first_name"]), 100)

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_send_welcome_email_async_multiple_calls(self, mock_post):
        """Test multiple async welcome email queueing calls"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_multi"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        users = [
            ("user1@example.com", "Alice"),
            ("user2@example.com", "Bob"),
            ("user3@example.com", "Charlie"),
        ]

        # Act
        results = [
            UserQStashService.send_welcome_email_async(email, name)
            for email, name in users
        ]

        # Assert
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertTrue(result["success"])

        # Verify all calls were made
        self.assertEqual(mock_post.call_count, 3)

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_send_welcome_email_async_email_formats(self, mock_post):
        """Test async welcome email queueing with various email formats"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_format"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        test_cases = [
            "simple@example.com",
            "user+tag@example.com",
            "user.name@example.co.uk",
            "first.last@subdomain.example.com",
        ]

        for email in test_cases:
            with self.subTest(email=email):
                # Act
                result = UserQStashService.send_welcome_email_async(email, "Test")

                # Assert
                self.assertTrue(result["success"])
                payload = mock_post.call_args[1]["json"]
                self.assertEqual(payload["email"], email)

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_send_welcome_email_async_webhook_endpoint(self, mock_post):
        """Test that correct webhook endpoint is used"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_endpoint"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        email = "user@example.com"
        first_name = "Test"

        # Act
        result = UserQStashService.send_welcome_email_async(email, first_name)

        # Assert
        self.assertTrue(result["success"])
        call_args = mock_post.call_args
        url = call_args[0][0]

        # Verify webhook endpoint
        self.assertIn("/api/v1/webhooks/send-welcome-email", url)
        self.assertIn("test-backend.example.com", url)

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://production.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_send_welcome_email_async_uses_webhook_base_url_from_settings(
        self, mock_post
    ):
        """Test that UserQStashService uses WEBHOOK_BASE_URL from settings"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_prod"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        email = "user@example.com"
        first_name = "Test"

        # Act
        result = UserQStashService.send_welcome_email_async(email, first_name)

        # Assert
        self.assertTrue(result["success"])
        call_args = mock_post.call_args
        url = call_args[0][0]

        # Verify production URL is used
        self.assertIn("production.example.com", url)

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_send_welcome_email_async_timeout_handling(self, mock_post):
        """Test async welcome email queueing handles timeout"""
        # Arrange
        import requests

        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        email = "user@example.com"
        first_name = "Test"

        # Act
        result = UserQStashService.send_welcome_email_async(email, first_name)

        # Assert
        self.assertFalse(result["success"])
        self.assertIsNone(result["message_id"])
        self.assertIn("Request timeout", result["error"])
