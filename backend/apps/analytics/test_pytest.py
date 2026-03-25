"""
[Analytics] serializer / service / view / command tests（pytest）
"""
import pytest
from unittest.mock import MagicMock
from django.core.management import call_command
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.analytics.serializers import AnalyticsEventWebhookSerializer
from apps.analytics.services import AnalyticsWebhookService
from apps.common.exceptions import AnalyticsError


# ================================
# Serializer
# ================================
class TestAnalyticsEventWebhookSerializer:

    def test_valid_auth_event(self):
        data = {
            "event_type": "auth_event",
            "event_data": {
                "user_id": 1,
                "event_type": "login",
                "timestamp": "2024-01-01T00:00:00Z",
                "ip_address": "127.0.0.1",
                "success": True,
            },
        }

        serializer = AnalyticsEventWebhookSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data["event_type"] == "auth_event"
        assert serializer.validated_data["event_data"]["user_id"] == 1

    @pytest.mark.parametrize(
        "data, error_field, error_msg",
        [
            (
                {"event_data": {}},
                "event_type",
                "event_type is required",
            ),
            (
                {"event_type": "unknown_event", "event_data": {}},
                "event_type",
                "invalid event_type",
            ),
            (
                {"event_type": "auth_event"},
                "event_data",
                "event_data is required",
            ),
        ],
    )
    def test_invalid_cases(self, data, error_field, error_msg):
        serializer = AnalyticsEventWebhookSerializer(data=data)

        assert not serializer.is_valid()
        assert error_field in serializer.errors
        assert serializer.errors[error_field][0] == error_msg

    def test_auth_event_missing_required_fields(self):
        data = {
            "event_type": "auth_event",
            "event_data": {"user_id": 1},
        }

        serializer = AnalyticsEventWebhookSerializer(data=data)

        assert not serializer.is_valid()
        error = str(serializer.errors["event_data"][0])
        assert "missing required fields" in error
        assert "event_type" in error
        assert "timestamp" in error

    def test_auth_event_with_all_fields(self):
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
                "error_message": None,
            },
        }

        serializer = AnalyticsEventWebhookSerializer(data=data)

        assert serializer.is_valid()


# ================================
# Service
# ================================
class TestAnalyticsWebhookService:

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        from apps.common.infrastructure.motherduck_client import MotherDuckClient
        AnalyticsWebhookService._client = None
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None
        yield
        AnalyticsWebhookService._client = None
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

    def test_handle_auth_event(self, mocker):
        mock_conn = MagicMock()

        mocker.patch(
            "apps.common.infrastructure.motherduck_client.duckdb.connect",
            return_value=mock_conn,
        )
        mocker.patch(
            "apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema"
        )

        result = AnalyticsWebhookService.handle_webhook_event(
            "auth_event",
            {
                "user_id": 1,
                "event_type": "login",
                "timestamp": "2024-01-01T00:00:00Z",
            },
        )

        assert result is None
        mock_conn.execute.assert_called_once()
        assert "auth_events" in mock_conn.execute.call_args[0][0]

    def test_handle_unsupported_type(self):
        with pytest.raises(AnalyticsError) as e:
            AnalyticsWebhookService.handle_webhook_event(
                "unsupported", {}
            )

        assert "Unsupported event_type" in str(e.value.internal_info)

    def test_database_error(self, mocker):
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mocker.patch(
            "apps.common.infrastructure.motherduck_client.duckdb.connect",
            return_value=mock_conn,
        )
        mocker.patch(
            "apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema"
        )

        with pytest.raises(AnalyticsError) as e:
            AnalyticsWebhookService.handle_webhook_event(
                "auth_event",
                {"user_id": 1, "event_type": "login", "timestamp": "2024-01-01T00:00:00Z"},
            )

        assert "DB error" in str(e.value.internal_info)


# ================================
# View
# ================================
@pytest.mark.django_db
class TestAnalyticsWebhookView:

    @pytest.fixture
    def client(self):
        return APIClient()

    def test_webhook_success(self, mocker, client):
        mocker.patch(
            "apps.common.permissions.verify_qstash_signature",
            return_value=True,
        )
        mock_handle = mocker.patch(
            "apps.analytics.views.AnalyticsWebhookService.handle_webhook_event",
            return_value=None,
        )

        payload = {
            "event_type": "auth_event",
            "event_data": {
                "user_id": 1,
                "event_type": "login",
                "timestamp": "2024-01-01T00:00:00Z",
            },
        }

        res = client.post(
            "/api/v1/webhooks/analytics-event",
            payload,
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid",
        )

        assert res.status_code == status.HTTP_200_OK
        assert res.data["event_type"] == "auth_event"
        mock_handle.assert_called_once()

    def test_webhook_invalid_signature(self, mocker, client):
        mocker.patch(
            "apps.common.permissions.verify_qstash_signature",
            return_value=False,
        )

        res = client.post("/api/v1/webhooks/analytics-event", {}, format="json")

        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_webhook_service_error(self, mocker, client):
        mocker.patch(
            "apps.common.permissions.verify_qstash_signature",
            return_value=True,
        )
        mocker.patch(
            "apps.analytics.views.AnalyticsWebhookService.handle_webhook_event",
            side_effect=AnalyticsError(internal_details="DB error"),
        )

        res = client.post(
            "/api/v1/webhooks/analytics-event",
            {"event_type": "auth_event", "event_data": {}},
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid",
        )

        assert res.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


# ================================
# Command
# ================================
@pytest.mark.django_db
class TestRunPipelineCommand:

    def test_model_table_names(self):
        from apps.todos.models import Todo
        User = get_user_model()

        assert User._meta.db_table == "custom_user"
        assert Todo._meta.db_table == "todos_todo"