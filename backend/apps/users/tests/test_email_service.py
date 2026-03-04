"""
Usersアプリ - メール・キューサービステスト
UserEmailService, UserQStashService のテスト
"""
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings

from apps.users.email_service import UserEmailService
from apps.users.qstash_service import UserQStashService


class UserEmailServiceTestCase(TestCase):
    """メール送信サービスのテスト"""

    def setUp(self):
        UserEmailService._client = None

    def tearDown(self):
        UserEmailService._client = None

    @override_settings(
        RESEND_API_KEY="test_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://example.com"
    )
    @patch("apps.common.infrastructure.email_client.resend.Emails.send")
    def test_send_welcome_email_success(self, mock_send):
        """【Service】ウェルカムメール送信の実行確認"""
        mock_send.return_value = {"id": "email_123"}

        message_id = UserEmailService.send_welcome_email(
            "user@example.com",
            "John"
        )

        self.assertEqual(message_id, "email_123")
        mock_send.assert_called_once()

        call_args = mock_send.call_args[0][0]
        self.assertIn("John", call_args["subject"])
        self.assertIn("John", call_args["html"])
        self.assertIn("https://example.com/dashboard", call_args["html"])

    @override_settings(
        RESEND_API_KEY="test_key",
        DEFAULT_FROM_EMAIL="noreply@example.com",
        FRONTEND_URL="https://example.com"
    )
    @patch("apps.common.infrastructure.email_client.resend.Emails.send")
    def test_send_password_reset_email(self, mock_send):
        """【Service】パスワードリセットメール送信の実行確認"""
        mock_send.return_value = {"id": "email_456"}

        message_id = UserEmailService.send_password_reset_email(
            "user@example.com",
            "reset_token_123"
        )

        self.assertEqual(message_id, "email_456")

        call_args = mock_send.call_args[0][0]
        self.assertIn("reset_token_123", call_args["html"])
        self.assertIn("/auth/reset-password", call_args["html"])


class UserQStashServiceTestCase(TestCase):
    """QStash（非同期ジョブキュー）連携のテスト"""

    @override_settings(
        QSTASH_TOKEN="test_token",
        WEBHOOK_BASE_URL="https://example.com"
    )
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_send_welcome_email_async_success(self, mock_post):
        """【Service】ウェルカムメールの非同期キュー登録テスト"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_123"}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        message_id = UserQStashService.send_welcome_email_async(
            "user@example.com",
            "John"
        )

        self.assertEqual(message_id, "msg_123")
        mock_post.assert_called_once()

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        self.assertEqual(payload["email"], "user@example.com")
        self.assertEqual(payload["first_name"], "John")