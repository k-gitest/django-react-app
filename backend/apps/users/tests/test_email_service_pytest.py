"""
Usersアプリ - メール・キューサービステスト（pytest）
UserEmailService, UserQStashService のテスト
"""
import pytest
from unittest.mock import MagicMock
from django.test import override_settings

from apps.users.email_service import UserEmailService
from apps.users.qstash_service import UserQStashService


@pytest.mark.django_db
class TestUserEmailService:
    """メール送信サービスのテスト"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        UserEmailService._client = None
        yield
        UserEmailService._client = None

    @override_settings(
        RESEND_API_KEY="test_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://example.com"
    )
    def test_send_welcome_email_success(self, mocker):
        """【Service】ウェルカムメール送信の実行確認"""
        mock_send = mocker.patch("apps.common.infrastructure.email_client.resend.Emails.send")
        mock_send.return_value = {"id": "email_123"}

        message_id = UserEmailService.send_welcome_email("user@example.com", "John")

        assert message_id == "email_123"
        mock_send.assert_called_once()

        call_args = mock_send.call_args[0][0]
        assert "John" in call_args["subject"]
        assert "John" in call_args["html"]
        assert "https://example.com/dashboard" in call_args["html"]

    @override_settings(
        RESEND_API_KEY="test_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://example.com"
    )
    def test_send_password_reset_email(self, mocker):
        """【Service】パスワードリセットメール送信の実行確認"""
        mock_send = mocker.patch("apps.common.infrastructure.email_client.resend.Emails.send")
        mock_send.return_value = {"id": "email_456"}

        message_id = UserEmailService.send_password_reset_email(
            "user@example.com",
            "reset_token_123"
        )

        assert message_id == "email_456"

        call_args = mock_send.call_args[0][0]
        assert "reset_token_123" in call_args["html"]
        assert "/auth/reset-password" in call_args["html"]


@pytest.mark.django_db
class TestUserQStashService:
    """QStash（非同期ジョブキュー）連携のテスト"""

    @override_settings(
        QSTASH_TOKEN="test_token",
        WEBHOOK_BASE_URL="https://example.com"
    )
    def test_send_welcome_email_async_success(self, mocker):
        """【Service】ウェルカムメールの非同期キュー登録テスト"""
        mock_post = mocker.patch("apps.common.infrastructure.qstash_client.requests.post")
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        message_id = UserQStashService.send_welcome_email_async("user@example.com", "John")

        assert message_id == "msg_123"
        mock_post.assert_called_once()

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["email"] == "user@example.com"
        assert payload["first_name"] == "John"