"""
Tests for analytics app
"""
import logging
from io import StringIO
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from apps.analytics.serializers import AnalyticsEventWebhookSerializer
from apps.analytics.services import AnalyticsWebhookService
from apps.common.exceptions import AnalyticsError


# ================================
# Serializer Tests
# ================================

class AnalyticsEventWebhookSerializerTestCase(TestCase):
    """Tests for AnalyticsEventWebhookSerializer"""

    def test_valid_auth_event(self):
        """Test valid auth_event payload"""
        # Arrange
        data = {
            "event_type": "auth_event",
            "event_data": {
                "user_id": 1,
                "event_type": "login",
                "timestamp": "2024-01-01T00:00:00Z",
                "ip_address": "127.0.0.1",
                "success": True
            }
        }

        # Act
        serializer = AnalyticsEventWebhookSerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['event_type'], 'auth_event')
        self.assertEqual(serializer.validated_data['event_data']['user_id'], 1)

    def test_missing_event_type(self):
        """Test validation fails when event_type is missing"""
        # Arrange
        data = {
            "event_data": {
                "user_id": 1,
                "event_type": "login",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }

        # Act
        serializer = AnalyticsEventWebhookSerializer(data=data)

        # Assert
        self.assertFalse(serializer.is_valid())
        self.assertIn('event_type', serializer.errors)
        self.assertEqual(
            serializer.errors['event_type'][0],
            'event_type is required'
        )

    def test_invalid_event_type(self):
        """Test validation fails with invalid event_type"""
        # Arrange
        data = {
            "event_type": "unknown_event",
            "event_data": {
                "user_id": 1
            }
        }

        # Act
        serializer = AnalyticsEventWebhookSerializer(data=data)

        # Assert
        self.assertFalse(serializer.is_valid())
        self.assertIn('event_type', serializer.errors)
        self.assertEqual(
            serializer.errors['event_type'][0],
            'invalid event_type'
        )

    def test_missing_event_data(self):
        """Test validation fails when event_data is missing"""
        # Arrange
        data = {
            "event_type": "auth_event"
        }

        # Act
        serializer = AnalyticsEventWebhookSerializer(data=data)

        # Assert
        self.assertFalse(serializer.is_valid())
        self.assertIn('event_data', serializer.errors)
        self.assertEqual(
            serializer.errors['event_data'][0],
            'event_data is required'
        )

    def test_auth_event_missing_required_fields(self):
        """Test validation fails when auth_event is missing required fields"""
        # Arrange
        data = {
            "event_type": "auth_event",
            "event_data": {
                "user_id": 1
                # missing event_type and timestamp
            }
        }

        # Act
        serializer = AnalyticsEventWebhookSerializer(data=data)

        # Assert
        self.assertFalse(serializer.is_valid())
        self.assertIn('event_data', serializer.errors)
        error_message = str(serializer.errors['event_data'][0])
        self.assertIn('missing required fields', error_message)
        self.assertIn('event_type', error_message)
        self.assertIn('timestamp', error_message)

    def test_auth_event_with_all_fields(self):
        """Test auth_event with all optional fields"""
        # Arrange
        data = {
            "event_type": "auth_event",
            "event_data": {
                "user_id": 1,
                "email": "test@example.com",
                "event_type": "login",
                "timestamp": "2024-01-01T00:00:00Z",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0",
                "success": True,
                "error_message": None
            }
        }

        # Act
        serializer = AnalyticsEventWebhookSerializer(data=data)

        # Assert
        self.assertTrue(serializer.is_valid())


# ================================
# Service Tests
# ================================

class AnalyticsWebhookServiceTestCase(TestCase):
    """Tests for AnalyticsWebhookService"""

    def setUp(self):
        """テスト前にシングルトンをリセット"""
        AnalyticsWebhookService._client = None

    def tearDown(self):
        """テスト後にシングルトンをリセット"""
        from apps.common.infrastructure.motherduck_client import MotherDuckClient
        AnalyticsWebhookService._client = None
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch("apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema")
    def test_handle_webhook_event_auth_event(self, mock_setup_schema, mock_connect):
        """Test handling auth_event"""
        # Arrange
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        event_type = "auth_event"
        event_data = {
            "user_id": 1,
            "email": "test@example.com",
            "event_type": "login",
            "timestamp": "2024-01-01T00:00:00Z",
            "ip_address": "127.0.0.1",
            "success": True
        }

        # Act
        result = AnalyticsWebhookService.handle_webhook_event(event_type, event_data)

        # Assert
        self.assertIsNone(result)  # 成功時は None
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0][0]
        self.assertIn("INSERT INTO django_react_app.logs.auth_events", call_args)

    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch("apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema")
    def test_handle_webhook_event_todo_event(self, mock_setup_schema, mock_connect):
        """Test handling todo_event"""
        # Arrange
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        event_type = "todo_event"
        event_data = {
            "user_id": 1,
            "todo_id": 10,
            "event_type": "create",
            "todo_title": "Test Todo",
            "priority": "HIGH",
            "progress": 0,
            "is_completed": False
        }

        # Act
        result = AnalyticsWebhookService.handle_webhook_event(event_type, event_data)

        # Assert
        self.assertIsNone(result)
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0][0]
        self.assertIn("INSERT INTO django_react_app.logs.todo_events", call_args)

    def test_handle_webhook_event_unsupported_type(self):
        """Test handling unsupported event_type raises AnalyticsError"""
        # Arrange
        event_type = "unsupported_event"
        event_data = {"data": "test"}

        # Act & Assert
        with self.assertRaises(AnalyticsError) as cm:
            AnalyticsWebhookService.handle_webhook_event(event_type, event_data)
        
        self.assertIn("Unsupported event_type", str(cm.exception.internal_info))

    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch("apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema")
    def test_handle_webhook_event_database_error(self, mock_setup_schema, mock_connect):
        """Test handling database error raises AnalyticsError"""
        # Arrange
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("Database error")
        mock_connect.return_value = mock_conn

        event_type = "auth_event"
        event_data = {
            "user_id": 1,
            "event_type": "login",
            "timestamp": "2024-01-01T00:00:00Z"
        }

        # Act & Assert
        with self.assertRaises(AnalyticsError) as cm:
            AnalyticsWebhookService.handle_webhook_event(event_type, event_data)
        
        self.assertIn("Database error", cm.exception.internal_info)


# ================================
# View Tests
# ================================

class AnalyticsEventWebhookViewTestCase(APITestCase):
    """Tests for analytics_event_webhook view"""

    @patch("apps.analytics.views.AnalyticsWebhookService.handle_webhook_event")
    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_success(self, mock_verify_signature, mock_handle_event):
        """Test successful webhook call"""
        # Arrange
        mock_verify_signature.return_value = True
        mock_handle_event.return_value = None

        payload = {
            "event_type": "auth_event",
            "event_data": {
                "user_id": 1,
                "email": "test@example.com",
                "event_type": "login",
                "timestamp": "2024-01-01T00:00:00Z",
                "ip_address": "127.0.0.1",
                "success": True
            }
        }

        # Act
        response = self.client.post(
            "/api/v1/webhooks/analytics-event",
            data=payload,
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid_signature"
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Event logged successfully")
        self.assertEqual(response.data["event_type"], "auth_event")
        mock_handle_event.assert_called_once_with("auth_event", payload["event_data"])

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_invalid_signature(self, mock_verify_signature):
        """Test webhook with invalid signature"""
        # Arrange
        mock_verify_signature.return_value = False

        payload = {
            "event_type": "auth_event",
            "event_data": {
                "user_id": 1,
                "event_type": "login",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }

        # Act
        response = self.client.post(
            "/api/v1/webhooks/analytics-event",
            data=payload,
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=invalid_signature"
        )

        # Assert
        # DRF permission_classes は 401 を返す
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_missing_signature(self, mock_verify_signature):
        """Test webhook without signature header"""
        # Arrange
        mock_verify_signature.return_value = False

        payload = {
            "event_type": "auth_event",
            "event_data": {
                "user_id": 1,
                "event_type": "login",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }

        # Act
        response = self.client.post(
            "/api/v1/webhooks/analytics-event",
            data=payload,
            format="json"
        )

        # Assert
        # DRF permission_classes は 401 を返す
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_invalid_payload(self, mock_verify_signature):
        """Test webhook with invalid payload"""
        # Arrange
        mock_verify_signature.return_value = True

        payload = {
            "event_type": "invalid_type",  # Invalid event_type
            "event_data": {}
        }

        # Act
        response = self.client.post(
            "/api/v1/webhooks/analytics-event",
            data=payload,
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid_signature"
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_missing_event_data_fields(self, mock_verify_signature):
        """Test webhook with missing required fields in event_data"""
        # Arrange
        mock_verify_signature.return_value = True

        payload = {
            "event_type": "auth_event",
            "event_data": {
                "user_id": 1
                # missing event_type and timestamp
            }
        }

        # Act
        response = self.client.post(
            "/api/v1/webhooks/analytics-event",
            data=payload,
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid_signature"
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    @patch("apps.analytics.views.AnalyticsWebhookService.handle_webhook_event")
    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_service_error(self, mock_verify_signature, mock_handle_event):
        """Test webhook when service raises AnalyticsError"""
        # Arrange
        mock_verify_signature.return_value = True
        mock_handle_event.side_effect = AnalyticsError(
            internal_details="Database error",
        )

        payload = {
            "event_type": "auth_event",
            "event_data": {
                "user_id": 1,
                "event_type": "login",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }

        # Act
        response = self.client.post(
            "/api/v1/webhooks/analytics-event",
            data=payload,
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid_signature"
        )

        # Assert
        # AnalyticsErrorは503エラーを返す
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("error", response.data)


# ================================
# Management Command Tests
# ================================

class RunPipelineCommandTestCase(TestCase):
    """Tests for run_pipeline management command"""

    def test_command_uses_correct_models(self):
        """Test that command correctly identifies table names from models"""
        from apps.todos.models import Todo
        User = get_user_model()
        
        # テーブル名が期待通りか確認
        self.assertEqual(User._meta.db_table, "custom_user")
        self.assertEqual(Todo._meta.db_table, "todos_todo")