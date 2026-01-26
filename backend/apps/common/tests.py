"""
Tests for common infrastructure layer (QStashClient, EmailClient, Security, Permissions)
現在の実装に合わせて修正済み
"""

from unittest.mock import MagicMock, patch

from apps.common.infrastructure.email_client import EmailClient
from apps.common.infrastructure.motherduck_client import MotherDuckClient
from apps.common.infrastructure.qstash_client import QStashClient
from apps.common.infrastructure.vector_client import VectorClient
from apps.common.services.base_analytics import BaseAnalyticsService
from apps.common.services.base_email import BaseEmailService
from apps.common.services.base_embedding import BaseEmbeddingService
from apps.common.services.base_qstash import BaseQStashService
from apps.common.services.base_vector import BaseVectorService
from apps.common.permissions import IsQStashAuthenticated
from apps.common.security import verify_qstash_signature
from apps.common.exceptions import (
    EmailDeliveryError,
    QStashError,
    AnalyticsError,
    EmbeddingError,
    VectorError,
)
from django.conf import settings
from django.test import RequestFactory, TestCase, override_settings
from rest_framework.test import APIRequestFactory


# ================================
# Infrastructure Layer Tests
# ================================

class QStashClientTestCase(TestCase):
    """Tests for QStashClient - 返り値が str (message_id) に変更"""

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
        message_id = QStashClient.publish(endpoint_path, payload)

        # Assert
        self.assertEqual(message_id, "msg_123")
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
        message_id = QStashClient.publish(
            endpoint_path, payload, delay_seconds=delay_seconds
        )

        # Assert
        self.assertEqual(message_id, "msg_456")
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]["headers"]["Upstash-Delay"], "60s")

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_publish_network_error(self, mock_post):
        """Test QStash publish raises exception on network error"""
        # Arrange
        import requests

        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        endpoint_path = "/api/v1/webhooks/test"
        payload = {"test": "data"}

        # Act & Assert
        with self.assertRaises(requests.exceptions.RequestException) as context:
            QStashClient.publish(endpoint_path, payload)
        
        self.assertIn("Network error", str(context.exception))

    @override_settings(
        QSTASH_TOKEN="test_qstash_token",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_publish_http_error(self, mock_post):
        """Test QStash publish raises HTTPError on API error"""
        # Arrange
        import requests

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")
        mock_post.return_value = mock_response

        endpoint_path = "/api/v1/webhooks/test"
        payload = {"test": "data"}

        # Act & Assert
        with self.assertRaises(requests.exceptions.HTTPError):
            QStashClient.publish(endpoint_path, payload)


class EmailClientTestCase(TestCase):
    """Tests for EmailClient - 返り値が str (message_id) に変更"""

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
        message_id = client.send(to_email, subject, html_content)

        # Assert
        self.assertEqual(message_id, "email_123")
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
        message_id = client.send(to_email, subject, html_content, from_email=custom_from)

        # Assert
        self.assertEqual(message_id, "email_456")
        call_args = mock_send.call_args[0][0]
        self.assertEqual(call_args["from"], custom_from)

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="test@example.com",
    )
    @patch("apps.common.infrastructure.email_client.resend.Emails.send")
    def test_send_email_resend_error(self, mock_send):
        """Test email sending raises exception on Resend API error"""
        # Arrange
        mock_send.side_effect = Exception("Resend API error")

        to_email = "user@example.com"
        subject = "Test"
        html_content = "<p>Test</p>"

        client = EmailClient()

        # Act & Assert
        with self.assertRaises(Exception) as context:
            client.send(to_email, subject, html_content)
        
        self.assertIn("Resend API error", str(context.exception))

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="test@example.com",
    )
    @patch("apps.common.infrastructure.email_client.resend.Emails.send")
    def test_send_batch(self, mock_send):
        """Test batch email sending"""
        # Arrange
        mock_send.side_effect = [
            {"id": "email_1"},
            {"id": "email_2"},
            {"id": "email_3"}
        ]

        client = EmailClient()
        emails = [
            {"to": "user1@example.com", "subject": "Test 1", "html": "<p>Test 1</p>"},
            {"to": "user2@example.com", "subject": "Test 2", "html": "<p>Test 2</p>"},
            {"to": "user3@example.com", "subject": "Test 3", "html": "<p>Test 3</p>"},
        ]

        # Act
        message_ids = client.send_batch(emails)

        # Assert
        self.assertEqual(message_ids, ["email_1", "email_2", "email_3"])
        self.assertEqual(mock_send.call_count, 3)


class MotherDuckClientTestCase(TestCase):
    """Tests for MotherDuckClient - 返り値が None に変更（例外ベース）"""

    def tearDown(self):
        """テスト後にシングルトンをリセット"""
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

    @override_settings(MOTHERDUCK_TOKEN="test_motherduck_token")
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch.object(MotherDuckClient, "_setup_schema")
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
        self.assertIsNone(result)  # 成功時は None を返す
        self.assertEqual(mock_conn.execute.call_count, 1)
        call_args = mock_conn.execute.call_args[0][0]
        self.assertIn("INSERT INTO django_react_app.logs.auth_events", call_args)

    @override_settings(MOTHERDUCK_TOKEN="test_motherduck_token")
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
        self.assertIsNone(result)  # 成功時は None を返す
        self.assertEqual(mock_conn.execute.call_count, 1)
        call_args = mock_conn.execute.call_args[0][0]
        self.assertIn("INSERT INTO django_react_app.logs.todo_events", call_args)

    @override_settings(MOTHERDUCK_TOKEN="test_motherduck_token")
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch.object(MotherDuckClient, "_setup_schema")
    def test_insert_auth_event_execution_error(self, mock_setup_schema, mock_connect):
        """Test auth event insertion raises exception on SQL error"""
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

        # Act & Assert
        with self.assertRaises(Exception) as context:
            client.insert_auth_event(event_data)
        
        self.assertIn("SQL error", str(context.exception))

    @override_settings(MOTHERDUCK_TOKEN="")
    def test_insert_with_missing_token(self):
        """Test initialization raises ValueError with missing token"""
        # Arrange
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            client = MotherDuckClient()
        
        self.assertIn("MOTHERDUCK_TOKEN is not set", str(context.exception))

    @override_settings(MOTHERDUCK_TOKEN="test_motherduck_token")
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    def test_connection_string_format(self, mock_connect):
        """Test MotherDuck connection string format"""
        # Arrange
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

        # Act
        client = MotherDuckClient()

        # Assert
        mock_connect.assert_called_once()
        connection_string = mock_connect.call_args[0][0]
        self.assertEqual(
            connection_string, "md:?motherduck_token=test_motherduck_token"
        )


class VectorClientTestCase(TestCase):
    """Tests for VectorClient"""

    def tearDown(self):
        """テスト後にシングルトンをリセット"""
        VectorClient._instance = None
        VectorClient._index = None

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test-vector.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_vector_token"
    )
    @patch("apps.common.infrastructure.vector_client.Index")
    def test_upsert_success(self, mock_index_class):
        """Test successful vector upsert"""
        # Arrange
        mock_index = MagicMock()
        mock_index_class.return_value = mock_index

        VectorClient._instance = None
        VectorClient._index = None

        client = VectorClient()
        vectors = [
            ("id1", [0.1, 0.2, 0.3], {"text": "test1"}),
            ("id2", [0.4, 0.5, 0.6], {"text": "test2"})
        ]

        # Act
        result = client.upsert(vectors)

        # Assert
        self.assertIsNone(result)
        mock_index.upsert.assert_called_once_with(vectors=vectors)

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test-vector.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_vector_token"
    )
    @patch("apps.common.infrastructure.vector_client.Index")
    def test_delete_success(self, mock_index_class):
        """Test successful vector deletion"""
        # Arrange
        mock_index = MagicMock()
        mock_index_class.return_value = mock_index

        VectorClient._instance = None
        VectorClient._index = None

        client = VectorClient()
        ids = ["id1", "id2", "id3"]

        # Act
        result = client.delete(ids)

        # Assert
        self.assertIsNone(result)
        mock_index.delete.assert_called_once_with(ids=ids)

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test-vector.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_vector_token"
    )
    @patch("apps.common.infrastructure.vector_client.Index")
    def test_query_success(self, mock_index_class):
        """Test successful vector query"""
        # Arrange
        mock_index = MagicMock()
        mock_query_result = [
            {"id": "id1", "score": 0.95, "metadata": {"text": "result1"}},
            {"id": "id2", "score": 0.85, "metadata": {"text": "result2"}}
        ]
        mock_index.query.return_value = mock_query_result
        mock_index_class.return_value = mock_index

        VectorClient._instance = None
        VectorClient._index = None

        client = VectorClient()
        query_vector = [0.1, 0.2, 0.3]

        # Act
        result = client.query(query_vector, top_k=2)

        # Assert
        self.assertEqual(result, mock_query_result)
        mock_index.query.assert_called_once_with(
            vector=query_vector,
            top_k=2,
            include_metadata=True,
            filter=None
        )


# ================================
# Service Layer Tests
# ================================

class BaseEmailServiceTestCase(TestCase):
    """Tests for BaseEmailService"""

    def tearDown(self):
        """シングルトンをリセット"""
        BaseEmailService._client = None

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="test@example.com",
    )
    @patch("apps.common.infrastructure.email_client.resend.Emails.send")
    def test_safe_send_success(self, mock_send):
        """Test _safe_send returns message_id on success"""
        # Arrange
        mock_send.return_value = {"id": "email_safe_123"}

        # Act
        message_id = BaseEmailService._safe_send(
            "user@example.com",
            "Test Subject",
            "<p>Test</p>"
        )

        # Assert
        self.assertEqual(message_id, "email_safe_123")

    @override_settings(
        RESEND_API_KEY="test_resend_key",
        DEFAULT_FROM_EMAIL="test@example.com",
    )
    @patch("apps.common.infrastructure.email_client.resend.Emails.send")
    def test_safe_send_raises_email_delivery_error(self, mock_send):
        """Test _safe_send raises EmailDeliveryError on failure"""
        # Arrange
        mock_send.side_effect = Exception("API error")

        # Act & Assert
        with self.assertRaises(EmailDeliveryError) as context:
            BaseEmailService._safe_send(
                "user@example.com",
                "Test",
                "<p>Test</p>"
            )
        
        self.assertIn("Email delivery failed", str(context.exception))
        self.assertEqual(context.exception.data["email"], "user@example.com")


class BaseQStashServiceTestCase(TestCase):
    """Tests for BaseQStashService"""

    @override_settings(
        QSTASH_TOKEN="test_token",
        WEBHOOK_BASE_URL="https://test.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_safe_publish_success(self, mock_post):
        """Test _safe_publish returns message_id on success"""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "qstash_safe_123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        # Act
        message_id = BaseQStashService._safe_publish(
            "/api/v1/webhooks/test",
            {"data": "test"}
        )

        # Assert
        self.assertEqual(message_id, "qstash_safe_123")

    @override_settings(
        QSTASH_TOKEN="test_token",
        WEBHOOK_BASE_URL="https://test.example.com",
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_safe_publish_raises_qstash_error(self, mock_post):
        """Test _safe_publish raises QStashError on failure"""
        # Arrange
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        # Act & Assert
        with self.assertRaises(QStashError) as context:
            BaseQStashService._safe_publish(
                "/api/v1/webhooks/test",
                {"data": "test"}
            )
        
        self.assertIn("QStash operation failed", str(context.exception))


class BaseAnalyticsServiceTestCase(TestCase):
    """Tests for BaseAnalyticsService"""

    def tearDown(self):
        """シングルトンをリセット"""
        BaseAnalyticsService._client = None
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

    @override_settings(MOTHERDUCK_TOKEN="test_token")
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch.object(MotherDuckClient, "_setup_schema")
    def test_safe_insert_auth_event_success(self, mock_setup_schema, mock_connect):
        """Test _safe_insert for auth events"""
        # Arrange
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        event_data = {
            "user_id": 1,
            "email": "test@example.com",
            "event_type": "login",
            "success": True
        }

        # Act
        result = BaseAnalyticsService._safe_insert("auth", event_data)

        # Assert
        self.assertIsNone(result)
        mock_conn.execute.assert_called_once()

    @override_settings(MOTHERDUCK_TOKEN="test_token")
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch.object(MotherDuckClient, "_setup_schema")
    def test_safe_insert_raises_analytics_error(self, mock_setup_schema, mock_connect):
        """Test _safe_insert raises AnalyticsError on failure"""
        # Arrange
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("DB error")
        mock_connect.return_value = mock_conn

        event_data = {
            "user_id": 1,
            "event_type": "login"
        }

        # Act & Assert
        with self.assertRaises(AnalyticsError) as context:
            BaseAnalyticsService._safe_insert("auth", event_data)
        
        self.assertIn("MotherDuck auth log failed", str(context.exception))


class BaseVectorServiceTestCase(TestCase):
    """Tests for BaseVectorService"""

    def tearDown(self):
        """シングルトンをリセット"""
        BaseVectorService._client = None
        VectorClient._instance = None
        VectorClient._index = None

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_token"
    )
    @patch("apps.common.infrastructure.vector_client.Index")
    def test_safe_upsert_success(self, mock_index_class):
        """Test _safe_upsert succeeds"""
        # Arrange
        mock_index = MagicMock()
        mock_index_class.return_value = mock_index

        vectors = [("id1", [0.1, 0.2], {})]

        # Act
        result = BaseVectorService._safe_upsert(vectors)

        # Assert
        self.assertIsNone(result)
        mock_index.upsert.assert_called_once()

    @override_settings(
        UPSTASH_VECTOR_REST_URL="https://test.upstash.io",
        UPSTASH_VECTOR_REST_TOKEN="test_token"
    )
    @patch("apps.common.infrastructure.vector_client.Index")
    def test_safe_upsert_raises_vector_error(self, mock_index_class):
        """Test _safe_upsert raises VectorError on failure"""
        # Arrange
        mock_index = MagicMock()
        mock_index.upsert.side_effect = Exception("API error")
        mock_index_class.return_value = mock_index

        vectors = [("id1", [0.1, 0.2], {})]

        # Act & Assert
        with self.assertRaises(VectorError) as context:
            BaseVectorService._safe_upsert(vectors)
        
        self.assertIn("Failed to upsert vectors", str(context.exception))


class BaseEmbeddingServiceTestCase(TestCase):
    """Tests for BaseEmbeddingService"""

    @override_settings(GOOGLE_API_KEY="test_google_key")
    @patch("apps.common.services.base_embedding.genai.embed_content")
    def test_embed_text_success(self, mock_embed):
        """Test successful text embedding"""
        # Arrange
        mock_embed.return_value = {"embedding": [0.1, 0.2, 0.3]}
        service = BaseEmbeddingService()

        # Act
        result = service.embed_text("test text")

        # Assert
        self.assertEqual(result, [0.1, 0.2, 0.3])
        mock_embed.assert_called_once()

    @override_settings(GOOGLE_API_KEY="test_google_key")
    @patch("apps.common.services.base_embedding.genai.embed_content")
    def test_embed_text_raises_embedding_error(self, mock_embed):
        """Test embed_text raises EmbeddingError on failure"""
        # Arrange
        mock_embed.side_effect = Exception("API error")
        service = BaseEmbeddingService()

        # Act & Assert
        with self.assertRaises(EmbeddingError) as context:
            service.embed_text("test text")
        
        self.assertIn("Failed to embed text", str(context.exception))

    @override_settings(GOOGLE_API_KEY="test_google_key")
    @patch("apps.common.services.base_embedding.genai.embed_content")
    def test_embed_batch_success(self, mock_embed):
        """Test successful batch embedding"""
        # Arrange
        mock_embed.return_value = {
            "embedding": [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
        }
        service = BaseEmbeddingService()

        # Act
        result = service.embed_batch(["text1", "text2", "text3"])

        # Assert
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], [0.1, 0.2])
        self.assertEqual(result[1], [0.3, 0.4])


# ================================
# Security Tests
# ================================

class QStashSecurityTestCase(TestCase):
    """Tests for QStash signature verification"""

    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="sig_test_current",
        QSTASH_NEXT_SIGNING_KEY="sig_test_next",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.security.Receiver")
    def test_verify_signature_success(self, mock_receiver_class):
        """Test signature verification succeeds"""
        # Arrange
        mock_receiver = MagicMock()
        mock_receiver.verify.return_value = None
        mock_receiver_class.return_value = mock_receiver

        body = b'{"test": "data"}'
        request = self.factory.post(
            "/api/v1/webhooks/test",
            data=body,
            content_type="application/json",
            HTTP_UPSTASH_SIGNATURE="v1=valid_signature",
        )

        # Act
        result = verify_qstash_signature(request)

        # Assert
        self.assertTrue(result)
        mock_receiver.verify.assert_called_once()

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="sig_test_current",
        QSTASH_NEXT_SIGNING_KEY="sig_test_next",
        WEBHOOK_BASE_URL="https://test-backend.example.com",
    )
    @patch("apps.common.security.Receiver")
    def test_verify_signature_failure(self, mock_receiver_class):
        """Test signature verification fails"""
        # Arrange
        mock_receiver = MagicMock()
        mock_receiver.verify.side_effect = Exception("Invalid signature")
        mock_receiver_class.return_value = mock_receiver

        body = b'{"test": "data"}'
        request = self.factory.post(
            "/api/v1/webhooks/test",
            data=body,
            content_type="application/json",
            HTTP_UPSTASH_SIGNATURE="v1=invalid",
        )

        # Act
        result = verify_qstash_signature(request)

        # Assert
        self.assertFalse(result)

    def test_verify_signature_missing_header(self):
        """Test verification fails with missing signature"""
        # Arrange
        request = self.factory.post(
            "/api/v1/webhooks/test",
            data=b'{"test": "data"}',
            content_type="application/json"
        )

        # Act
        result = verify_qstash_signature(request)

        # Assert
        self.assertFalse(result)


class IsQStashAuthenticatedTestCase(TestCase):
    """Tests for IsQStashAuthenticated permission"""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsQStashAuthenticated()

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="sig_current",
        QSTASH_NEXT_SIGNING_KEY="sig_next",
        WEBHOOK_BASE_URL="https://test.example.com",
    )
    @patch("apps.common.permissions.verify_qstash_signature")
    def test_permission_granted(self, mock_verify):
        """Test permission granted with valid signature"""
        # Arrange
        mock_verify.return_value = True
        request = self.factory.post("/webhook", data={})

        # Act
        has_permission = self.permission.has_permission(request, None)

        # Assert
        self.assertTrue(has_permission)

    @override_settings(
        QSTASH_CURRENT_SIGNING_KEY="sig_current",
        QSTASH_NEXT_SIGNING_KEY="sig_next",
        WEBHOOK_BASE_URL="https://test.example.com",
    )
    @patch("apps.common.permissions.verify_qstash_signature")
    def test_permission_denied(self, mock_verify):
        """Test permission denied with invalid signature"""
        # Arrange
        mock_verify.return_value = False
        request = self.factory.post("/webhook", data={})

        # Act
        has_permission = self.permission.has_permission(request, None)

        # Assert
        self.assertFalse(has_permission)

    def test_permission_error_message(self):
        """Test custom error message"""
        self.assertEqual(self.permission.message, "Invalid QStash signature")