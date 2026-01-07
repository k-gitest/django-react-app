"""
Tests for common infrastructure layer (QStashClient, EmailClient, Security, Permissions)
"""
from unittest.mock import patch, MagicMock
import hmac
import hashlib
from django.test import TestCase, override_settings, RequestFactory
from django.conf import settings
from rest_framework.test import APIRequestFactory

from common.infrastructure.qstash_client import QStashClient
from common.infrastructure.email_client import EmailClient
from common.security import verify_qstash_signature
from common.permissions import IsQStashAuthenticated


class QStashClientTestCase(TestCase):
    """Tests for QStashClient"""

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("common.infrastructure.qstash_client.requests.post")
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
        self.assertEqual(call_args[1]["headers"]["Authorization"], "Bearer test_qstash_token")
        self.assertEqual(call_args[1]["json"], payload)

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("common.infrastructure.qstash_client.requests.post")
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
        result = QStashClient.publish(endpoint_path, payload, delay_seconds=delay_seconds)

        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["message_id"], "msg_456")
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]["headers"]["Upstash-Delay"], "60s")

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("common.infrastructure.qstash_client.requests.post")
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

    @override_settings(QSTASH_TOKEN="", WEBHOOK_BASE_URL="https://test-backend.example.com")
    @patch("common.infrastructure.qstash_client.requests.post")
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
    @patch("common.infrastructure.email_client.resend.Emails.send")
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
    @patch("common.infrastructure.email_client.resend.Emails.send")
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
    @patch("common.infrastructure.email_client.resend.Emails.send")
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
    @patch("common.infrastructure.email_client.resend.Emails.send")
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
    @patch("common.infrastructure.email_client.resend.Emails.send")
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
    @patch("common.infrastructure.qstash_client.requests.post")
    @patch("common.infrastructure.email_client.resend.Emails.send")
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


class QStashSecurityTestCase(TestCase):
    """Tests for QStash signature verification"""

    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="current_secret_key",
        QSTASH_NEXT_SIGNING_KEY="next_secret_key",
    )
    def test_verify_signature_with_current_key(self):
        """Test signature verification with current signing key"""
        # Arrange
        body = b'{"test": "data"}'
        signature = hmac.new(
            b"current_secret_key", body, hashlib.sha256
        ).hexdigest()

        request = self.factory.post(
            "/webhook",
            data=body,
            content_type="application/json",
            HTTP_UPSTASH_SIGNATURE=f"v1={signature}",
        )

        # Act
        result = verify_qstash_signature(request)

        # Assert
        self.assertTrue(result)

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="current_secret_key",
        QSTASH_NEXT_SIGNING_KEY="next_secret_key",
    )
    def test_verify_signature_with_next_key(self):
        """Test signature verification with next signing key (key rotation)"""
        # Arrange
        body = b'{"test": "data"}'
        signature = hmac.new(
            b"next_secret_key", body, hashlib.sha256
        ).hexdigest()

        request = self.factory.post(
            "/webhook",
            data=body,
            content_type="application/json",
            HTTP_UPSTASH_SIGNATURE=f"v1={signature}",
        )

        # Act
        result = verify_qstash_signature(request)

        # Assert
        self.assertTrue(result)

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="current_secret_key",
        QSTASH_NEXT_SIGNING_KEY="next_secret_key",
    )
    def test_verify_signature_invalid(self):
        """Test signature verification with invalid signature"""
        # Arrange
        body = b'{"test": "data"}'
        invalid_signature = "invalid_signature_12345"

        request = self.factory.post(
            "/webhook",
            data=body,
            content_type="application/json",
            HTTP_UPSTASH_SIGNATURE=f"v1={invalid_signature}",
        )

        # Act
        result = verify_qstash_signature(request)

        # Assert
        self.assertFalse(result)

    def test_verify_signature_missing_header(self):
        """Test signature verification with missing signature header"""
        # Arrange
        body = b'{"test": "data"}'
        request = self.factory.post(
            "/webhook", data=body, content_type="application/json"
        )

        # Act
        result = verify_qstash_signature(request)

        # Assert
        self.assertFalse(result)

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="current_secret_key",
        QSTASH_NEXT_SIGNING_KEY="next_secret_key",
    )
    def test_verify_signature_malformed_format(self):
        """Test signature verification with malformed signature format"""
        # Arrange
        body = b'{"test": "data"}'
        request = self.factory.post(
            "/webhook",
            data=body,
            content_type="application/json",
            HTTP_UPSTASH_SIGNATURE="malformed_signature_no_equals",
        )

        # Act
        result = verify_qstash_signature(request)

        # Assert
        self.assertFalse(result)

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="current_secret_key",
        QSTASH_NEXT_SIGNING_KEY="next_secret_key",
    )
    def test_verify_signature_multiple_signatures(self):
        """Test signature verification with multiple signatures in header"""
        # Arrange
        body = b'{"test": "data"}'
        valid_signature = hmac.new(
            b"current_secret_key", body, hashlib.sha256
        ).hexdigest()
        invalid_signature = "invalid123"

        request = self.factory.post(
            "/webhook",
            data=body,
            content_type="application/json",
            HTTP_UPSTASH_SIGNATURE=f"v1={invalid_signature},v1={valid_signature}",
        )

        # Act
        result = verify_qstash_signature(request)

        # Assert
        self.assertTrue(result)  # Should succeed with valid signature

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="current_secret_key",
        QSTASH_NEXT_SIGNING_KEY="next_secret_key",
    )
    def test_verify_signature_empty_body(self):
        """Test signature verification with empty request body"""
        # Arrange
        body = b""
        signature = hmac.new(
            b"current_secret_key", body, hashlib.sha256
        ).hexdigest()

        request = self.factory.post(
            "/webhook",
            data=body,
            content_type="application/json",
            HTTP_UPSTASH_SIGNATURE=f"v1={signature}",
        )

        # Act
        result = verify_qstash_signature(request)

        # Assert
        self.assertTrue(result)


class IsQStashAuthenticatedTestCase(TestCase):
    """Tests for IsQStashAuthenticated permission class"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsQStashAuthenticated()

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="current_secret_key",
        QSTASH_NEXT_SIGNING_KEY="next_secret_key",
    )
    def test_permission_granted_valid_signature(self):
        """Test permission is granted with valid QStash signature"""
        # Arrange
        body = b'{"test": "data"}'
        signature = hmac.new(
            b"current_secret_key", body, hashlib.sha256
        ).hexdigest()

        request = self.factory.post(
            "/webhook",
            data=body,
            content_type="application/json",
            HTTP_UPSTASH_SIGNATURE=f"v1={signature}",
        )

        # Act
        has_permission = self.permission.has_permission(request, None)

        # Assert
        self.assertTrue(has_permission)

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="current_secret_key",
        QSTASH_NEXT_SIGNING_KEY="next_secret_key",
    )
    def test_permission_denied_invalid_signature(self):
        """Test permission is denied with invalid QStash signature"""
        # Arrange
        body = b'{"test": "data"}'
        request = self.factory.post(
            "/webhook",
            data=body,
            content_type="application/json",
            HTTP_UPSTASH_SIGNATURE="v1=invalid_signature",
        )

        # Act
        has_permission = self.permission.has_permission(request, None)

        # Assert
        self.assertFalse(has_permission)

    def test_permission_denied_missing_signature(self):
        """Test permission is denied when signature is missing"""
        # Arrange
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

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="current_secret_key",
        QSTASH_NEXT_SIGNING_KEY="next_secret_key",
    )
    def test_permission_with_key_rotation(self):
        """Test permission works during key rotation (next key)"""
        # Arrange
        body = b'{"test": "data"}'
        signature = hmac.new(
            b"next_secret_key", body, hashlib.sha256
        ).hexdigest()

        request = self.factory.post(
            "/webhook",
            data=body,
            content_type="application/json",
            HTTP_UPSTASH_SIGNATURE=f"v1={signature}",
        )

        # Act
        has_permission = self.permission.has_permission(request, None)

        # Assert
        self.assertTrue(has_permission)