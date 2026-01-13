"""
Tests for common infrastructure layer (QStashClient, EmailClient, Security, Permissions)
"""

import hashlib
import hmac
from unittest.mock import MagicMock, patch

from apps.common.infrastructure.email_client import EmailClient
from apps.common.infrastructure.motherduck_client import MotherDuckClient
from apps.common.infrastructure.qstash_client import QStashClient
from apps.common.permissions import IsQStashAuthenticated
from apps.common.security import verify_qstash_signature
from django.conf import settings
from django.test import RequestFactory, TestCase, override_settings
from rest_framework.test import APIRequestFactory


class QStashClientTestCase(TestCase):
    """Tests for QStashClient"""

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_publish_success(self, mock_post):
        """Test successful QStash message publishing"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        endpoint_path = "/api/v1/webhooks/test"
        payload = {"test_key": "test_value"}

        # Act
        result = QStashClient.publish(endpoint_path, payload)

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["message_id"], "msg_123")
        self.assertIsNone(result["error"])
        mock_post.assert_called_once()

        # Verify request details
        call_args = mock_post.call_args
        self.assertIn("https://qstash.upstash.io/v2/publish/", call_args[0][0])
        self.assertIn("test-backend.example.com", call_args[0][0])
        self.assertEqual(
            call_args[1]["headers"]["Authorization"], "Bearer test_qstash_token"
        )
        self.assertEqual(call_args[1]["json"], payload)

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_publish_with_delay(self, mock_post):
        """Test QStash message publishing with delay"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_456"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        endpoint_path = "/api/v1/webhooks/delayed-task"
        payload = {"task": "delayed"}
        delay_seconds = 60

        # Act
        result = QStashClient.publish(
            endpoint_path, payload, delay_seconds=delay_seconds
        )

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["message_id"], "msg_456")
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]["headers"]["Upstash-Delay"], "60s")

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_publish_network_error(self, mock_post):
        """Test QStash publish handling network error"""
        # Arrange
        import requests

        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        endpoint_path = "/api/v1/webhooks/test"
        payload = {"test": "data"}

        # Act
        result = QStashClient.publish(endpoint_path, payload)

        # Assert
        self.assertFalse(result["success"])
        self.assertIsNone(result["message_id"])
        self.assertIn("Network error", result["error"])

    @override_settings(
        QSTASH_TOKEN="", WEBHOOK_BASE_URL="https://test-backend.example.com"
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_publish_missing_token(self, mock_post):
        """Test QStash publish with missing token"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_no_token"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        endpoint_path = "/api/v1/webhooks/test"
        payload = {"test": "data"}

        # Act
        result = QStashClient.publish(endpoint_path, payload)

        # Assert - Should still attempt to publish
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]["headers"]["Authorization"], "Bearer ")


class EmailClientTestCase(TestCase):
    """Tests for EmailClient"""

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="test@example.com",
    )
    @patch("apps.common.infrastructure.email_client.resend.Emails.send")
    def test_send_email_success(self, mock_send):
        """Test successful email sending"""
        # Arrange
        mock_send.return_value = {"id": "email_123"}

        to_email = "user@example.com"
        subject = "Test Subject"
        html_content = "<h1>Test Email</h1>"

        client = EmailClient()

        # Act
        result = client.send(to_email, subject, html_content)

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["id"], "email_123")
        self.assertIsNone(result["error"])
        mock_send.assert_called_once()

        # Verify email parameters
        call_args = mock_send.call_args[0][0]
        self.assertEqual(call_args["from"], "test@example.com")
        self.assertEqual(call_args["to"], [to_email])
        self.assertEqual(call_args["subject"], subject)
        self.assertEqual(call_args["html"], html_content)

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="default@example.com",
    )
    @patch("apps.common.infrastructure.email_client.resend.Emails.send")
    def test_send_email_custom_from(self, mock_send):
        """Test email sending with custom from address"""
        # Arrange
        mock_send.return_value = {"id": "email_456"}

        to_email = "user@example.com"
        subject = "Test"
        html_content = "<p>Test</p>"
        custom_from = "custom@example.com"

        client = EmailClient()

        # Act
        result = client.send(to_email, subject, html_content, from_email=custom_from)

        # Assert
        self.assertTrue(result["success"])
        call_args = mock_send.call_args[0][0]
        self.assertEqual(call_args["from"], custom_from)

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="test@example.com",
    )
    @patch("apps.common.infrastructure.email_client.resend.Emails.send")
    def test_send_email_resend_error(self, mock_send):
        """Test email sending with Resend API error"""
        # Arrange
        mock_send.side_effect = Exception("Resend API error")

        to_email = "user@example.com"
        subject = "Test"
        html_content = "<p>Test</p>"

        client = EmailClient()

        # Act
        result = client.send(to_email, subject, html_content)

        # Assert
        self.assertFalse(result["success"])
        self.assertIsNone(result["id"])
        self.assertIn("Resend API error", result["error"])

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="test@example.com",
    )
    @patch("apps.common.infrastructure.email_client.resend.Emails.send")
    def test_send_email_empty_content(self, mock_send):
        """Test email sending with empty content"""
        # Arrange
        mock_send.return_value = {"id": "email_789"}

        to_email = "user@example.com"
        subject = ""
        html_content = ""

        client = EmailClient()

        # Act
        result = client.send(to_email, subject, html_content)

        # Assert
        self.assertTrue(result["success"])
        call_args = mock_send.call_args[0][0]
        self.assertEqual(call_args["subject"], "")
        self.assertEqual(call_args["html"], "")

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="test@example.com",
    )
    @patch("apps.common.infrastructure.email_client.resend.Emails.send")
    def test_send_email_multiple_recipients(self, mock_send):
        """Test that send method expects single recipient"""
        # Arrange
        mock_send.return_value = {"id": "email_999"}

        # Note: Current implementation only supports single recipient
        to_email = "user@example.com"
        subject = "Test"
        html_content = "<p>Test</p>"

        client = EmailClient()

        # Act
        result = client.send(to_email, subject, html_content)

        # Assert
        self.assertTrue(result["success"])
        call_args = mock_send.call_args[0][0]
        # Verify it's wrapped in a list
        self.assertEqual(call_args["to"], [to_email])
        self.assertEqual(len(call_args["to"]), 1)


class InfrastructureIntegrationTestCase(TestCase):
    """Integration tests for infrastructure components"""

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    @patch("apps.common.infrastructure.email_client.resend.Emails.send")
    def test_qstash_email_workflow(self, mock_email_send, mock_qstash_post):
        """Test typical workflow: QStash triggers email sending"""
        # Arrange
        mock_qstash_response = MagicMock()
        mock_qstash_response.json.return_value = {"messageId": "msg_integration"}
        mock_qstash_response.raise_for_status = MagicMock()
        mock_qstash_post.return_value = mock_qstash_response
        mock_email_send.return_value = {"id": "email_integration"}

        email_client = EmailClient()

        # Act - Simulate QStash message for email sending
        qstash_result = QStashClient.publish(
            "/api/v1/webhooks/send-welcome-email",
            {"email": "newuser@example.com", "first_name": "John"},
        )

        # Simulate webhook receiving the message and sending email
        email_result = email_client.send(
            "newuser@example.com", "Welcome, John!", "<h1>Welcome to our app!</h1>"
        )

        # Assert
        self.assertTrue(qstash_result["success"])
        self.assertEqual(qstash_result["message_id"], "msg_integration")
        self.assertTrue(email_result["success"])
        self.assertEqual(email_result["id"], "email_integration")

        # Verify both services were called
        mock_qstash_post.assert_called_once()
        mock_email_send.assert_called_once()

    @override_settings(
        MOTHERDUCK_TOKEN="test_motherduck_token",
    )
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch.object(MotherDuckClient, "_setup_schema")
    def test_auth_event_logging_workflow(self, mock_setup_schema, mock_connect):
        """Test typical workflow: Auth event is logged to MotherDuck"""
        # Arrange
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

        motherduck_client = MotherDuckClient()

        # Act
        result = motherduck_client.insert_auth_event(
            {
                "user_id": 1,
                "email": "test@example.com",
                "event_type": "login",
                "ip_address": "192.168.1.1",
                "user_agent": "Chrome/120.0",
                "success": True,
            }
        )

        # Assert
        self.assertTrue(result)
        self.assertEqual(mock_conn.execute.call_count, 1)  # INSERT文のみ

        call_args = mock_conn.execute.call_args[0][0]
        self.assertIn("INSERT INTO django_react_app.logs.auth_events", call_args)

    @override_settings(
        MOTHERDUCK_TOKEN="test_motherduck_token",
    )
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch.object(MotherDuckClient, "_setup_schema")
    def test_todo_event_logging_workflow(self, mock_setup_schema, mock_connect):
        """Test typical workflow: Todo event is logged to MotherDuck"""
        # Arrange
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

        motherduck_client = MotherDuckClient()

        # Act
        result = motherduck_client.insert_todo_event(
            {
                "user_id": 1,
                "todo_id": 5,
                "event_type": "create",
                "todo_title": "New Task",
                "priority": "MEDIUM",
                "progress": 0,
                "is_completed": False,
            }
        )

        # Assert
        self.assertTrue(result)
        self.assertEqual(mock_conn.execute.call_count, 1)  # INSERT文のみ

        call_args = mock_conn.execute.call_args[0][0]
        self.assertIn("INSERT INTO django_react_app.logs.todo_events", call_args)


class QStashSecurityTestCase(TestCase):
    """Tests for QStash signature verification using official Receiver"""

    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="sig_test_current",
        QSTASH_NEXT_SIGNING_KEY="sig_test_next",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.security.Receiver")
    def test_verify_signature_success(self, mock_receiver_class):
        """Test signature verification succeeds with valid signature"""
        # Arrange
        mock_receiver = MagicMock()
        mock_receiver.verify.return_value = None
        mock_receiver_class.return_value = mock_receiver

        body = b'{"test": "data"}'
        request = self.factory.post(
            "/api/v1/webhooks/test",
            data=body,
            content_type="application/json",
            HTTP_UPSTASH_SIGNATURE="v1=valid_signature_from_qstash",
        )

        # Act
        result = verify_qstash_signature(request)

        # Assert
        self.assertTrue(result)
        mock_receiver_class.assert_called_once_with(
            current_signing_key="sig_test_current",
            next_signing_key="sig_test_next",
        )
        mock_receiver.verify.assert_called_once()

        # Verify arguments
        call_kwargs = mock_receiver.verify.call_args[1]
        self.assertEqual(call_kwargs["body"], '{"test": "data"}')
        self.assertEqual(call_kwargs["signature"], "v1=valid_signature_from_qstash")
        # URLは環境依存なので、存在確認のみ
        self.assertIn("/api/v1/webhooks/test", call_kwargs["url"])

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="sig_test_current",
        QSTASH_NEXT_SIGNING_KEY="sig_test_next",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.security.Receiver")
    def test_verify_signature_failure(self, mock_receiver_class):
        """Test signature verification fails with invalid signature"""
        # Arrange
        mock_receiver = MagicMock()
        mock_receiver.verify.side_effect = Exception("Invalid signature")
        mock_receiver_class.return_value = mock_receiver

        body = b'{"test": "data"}'
        request = self.factory.post(
            "/api/v1/webhooks/test",
            data=body,
            content_type="application/json",
            HTTP_UPSTASH_SIGNATURE="v1=invalid_signature",
        )

        # Act
        result = verify_qstash_signature(request)

        # Assert
        self.assertFalse(result)

    def test_verify_signature_missing_header(self):
        """Test signature verification fails with missing signature header"""
        # Arrange
        body = b'{"test": "data"}'
        request = self.factory.post(
            "/api/v1/webhooks/test", data=body, content_type="application/json"
        )

        # Act
        result = verify_qstash_signature(request)

        # Assert
        self.assertFalse(result)

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="sig_test_current",
        QSTASH_NEXT_SIGNING_KEY="sig_test_next",
        WEBHOOK_BASE_URL="http://test.app.github.dev",
    )
    @patch("apps.common.security.Receiver")
    def test_verify_signature_url_normalization(self, mock_receiver_class):
        """Test URL normalization for GitHub Codespaces"""
        # Arrange
        mock_receiver = MagicMock()
        mock_receiver.verify.return_value = None
        mock_receiver_class.return_value = mock_receiver

        body = b'{"test": "data"}'
        request = self.factory.post(
            "/api/v1/webhooks/test",
            data=body,
            content_type="application/json",
            HTTP_UPSTASH_SIGNATURE="v1=valid",
        )

        # Act
        result = verify_qstash_signature(request)

        # Assert
        self.assertTrue(result)
        call_kwargs = mock_receiver.verify.call_args[1]
        # Codespaces環境ではhttpsに正規化される
        self.assertTrue(call_kwargs["url"].startswith("https://"))


class IsQStashAuthenticatedTestCase(TestCase):
    """Tests for IsQStashAuthenticated permission class"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsQStashAuthenticated()

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="sig_test_current",
        QSTASH_NEXT_SIGNING_KEY="sig_test_next",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch(
        "apps.common.permissions.verify_qstash_signature"
    )  # ← permissions内のimportをモック
    def test_permission_granted_valid_signature(self, mock_verify):
        """Test permission is granted with valid QStash signature"""
        # Arrange
        mock_verify.return_value = True

        body = b'{"test": "data"}'
        request = self.factory.post(
            "/webhook",
            data=body,
            content_type="application/json",
            HTTP_UPSTASH_SIGNATURE="v1=valid",
        )

        # Act
        has_permission = self.permission.has_permission(request, None)

        # Assert
        self.assertTrue(has_permission)
        mock_verify.assert_called_once_with(request)

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="sig_test_current",
        QSTASH_NEXT_SIGNING_KEY="sig_test_next",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.security.verify_qstash_signature")
    def test_permission_denied_invalid_signature(self, mock_verify):
        """Test permission is denied with invalid QStash signature"""
        # Arrange
        mock_verify.return_value = False

        body = b'{"test": "data"}'
        request = self.factory.post(
            "/webhook",
            data=body,
            content_type="application/json",
            HTTP_UPSTASH_SIGNATURE="v1=invalid",
        )

        # Act
        has_permission = self.permission.has_permission(request, None)

        # Assert
        self.assertFalse(has_permission)

    @patch("apps.common.security.verify_qstash_signature")
    def test_permission_denied_missing_signature(self, mock_verify):
        """Test permission is denied when signature is missing"""
        # Arrange
        mock_verify.return_value = False

        body = b'{"test": "data"}'
        request = self.factory.post(
            "/webhook", data=body, content_type="application/json"
        )

        # Act
        has_permission = self.permission.has_permission(request, None)

        # Assert
        self.assertFalse(has_permission)

    def test_permission_custom_error_message(self):
        """Test custom error message is set"""
        # Assert
        self.assertEqual(self.permission.message, "Invalid QStash signature")


class MotherDuckClientTestCase(TestCase):
    """Tests for MotherDuckClient"""

    @override_settings(
        MOTHERDUCK_TOKEN="test_motherduck_token",
    )
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch.object(MotherDuckClient, "_setup_schema")  # ← スキーマセットアップをスキップ
    def test_insert_auth_event_success(self, mock_setup_schema, mock_connect):
        """Test successful auth event insertion"""
        # Arrange
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

        client = MotherDuckClient()

        event_data = {
            "user_id": 1,
            "email": "test@example.com",
            "event_type": "login",
            "ip_address": "127.0.0.1",
            "user_agent": "Mozilla/5.0",
            "success": True,
        }

        # Act
        result = client.insert_auth_event(event_data)

        # Assert
        self.assertTrue(result)

        # Verify SQL call (INSERT文のみ)
        self.assertEqual(mock_conn.execute.call_count, 1)
        call_args = mock_conn.execute.call_args[0][0]
        self.assertIn("INSERT INTO django_react_app.logs.auth_events", call_args)

    @override_settings(
        MOTHERDUCK_TOKEN="test_motherduck_token",
    )
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch.object(MotherDuckClient, "_setup_schema")
    def test_insert_todo_event_success(self, mock_setup_schema, mock_connect):
        """Test successful todo event insertion"""
        # Arrange
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

        client = MotherDuckClient()

        event_data = {
            "user_id": 1,
            "todo_id": 10,
            "event_type": "create",
            "todo_title": "Test Todo",
            "priority": "HIGH",
            "progress": 0,
            "is_completed": False,
        }

        # Act
        result = client.insert_todo_event(event_data)

        # Assert
        self.assertTrue(result)

        self.assertEqual(mock_conn.execute.call_count, 1)
        call_args = mock_conn.execute.call_args[0][0]
        self.assertIn("INSERT INTO django_react_app.logs.todo_events", call_args)

    @override_settings(
        MOTHERDUCK_TOKEN="test_motherduck_token",
    )
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch.object(MotherDuckClient, "_setup_schema")
    def test_insert_auth_event_execution_error(self, mock_setup_schema, mock_connect):
        """Test auth event insertion with SQL execution error"""
        # Arrange
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("SQL error")
        mock_connect.return_value = mock_conn

        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

        client = MotherDuckClient()

        event_data = {
            "user_id": 1,
            "email": "test@example.com",
            "event_type": "login",
            "success": True,
        }

        # Act
        result = client.insert_auth_event(event_data)

        # Assert
        self.assertFalse(result)

    @override_settings(
        MOTHERDUCK_TOKEN="test_motherduck_token",
    )
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch.object(MotherDuckClient, "_setup_schema")
    def test_insert_todo_event_execution_error(self, mock_setup_schema, mock_connect):
        """Test todo event insertion with SQL execution error"""
        # Arrange
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("SQL error")
        mock_connect.return_value = mock_conn

        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

        client = MotherDuckClient()

        event_data = {
            "user_id": 1,
            "todo_id": 10,
            "event_type": "create",
            "todo_title": "Test",
            "priority": "HIGH",
            "progress": 0,
            "is_completed": False,
        }

        # Act
        result = client.insert_todo_event(event_data)

        # Assert
        self.assertFalse(result)

    @override_settings(MOTHERDUCK_TOKEN="")
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    def test_insert_with_missing_token(self, mock_connect):
        """Test insertion with missing MotherDuck token"""
        # Arrange
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

        # Act & Assert
        with self.assertRaises(ValueError):
            client = MotherDuckClient()

    @override_settings(
        MOTHERDUCK_TOKEN="test_motherduck_token",
    )
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    def test_connection_string_format(self, mock_connect):
        """Test MotherDuck connection string format"""
        # Arrange
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

        # Act
        # __init__ は _setup_schema を呼ぶが、それも検証の一部
        client = MotherDuckClient()

        # Assert
        mock_connect.assert_called_once()
        connection_string = mock_connect.call_args[0][0]
        self.assertEqual(
            connection_string, "md:?motherduck_token=test_motherduck_token"
        )

    def tearDown(self):
        """テスト後にシングルトンをリセット"""
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None
