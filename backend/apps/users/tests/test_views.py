"""
Usersアプリ - ビューテスト
認証系APIビュー、ウェルカムメールWebhookビューのテスト
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class AuthenticationViewsTestCase(APITestCase):
    """認証系APIビューのテスト"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="John"
        )

    @override_settings(TESTING=True)
    @patch("apps.users.views.UserAuthService.handle_login_success")
    def test_login_success(self, mock_handle_login):
        """【View】正常なログインとJWTトークンの返却テスト"""
        response = self.client.post(
            "/api/v1/auth/login/",
            {
                "email": "test@example.com",
                "password": "testpass123"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        mock_handle_login.assert_called_once()

    def test_login_invalid_credentials(self):
        """【View】誤った認証情報でのログイン失敗テスト"""
        response = self.client.post(
            "/api/v1/auth/login/",
            {
                "email": "test@example.com",
                "password": "wrongpass"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(TESTING=True)
    def test_register_success(self):
        """【View】新規会員登録APIの正常系テスト"""
        response = self.client.post(
            "/api/v1/auth/registration/",
            {
                "email": "newuser@example.com",
                "password1": "newpass123",
                "password2": "newpass123",
                "first_name": "Jane"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            User.objects.filter(email="newuser@example.com").exists()
        )

    @override_settings(TESTING=True)
    def test_register_duplicate_email(self):
        """【View】既存メールアドレスによる登録時の 409 Conflict 返却テスト"""
        response = self.client.post(
            "/api/v1/auth/registration/",
            {
                "email": "test@example.com",  # 既にsetUpで作成済み
                "password1": "newpass123",
                "password2": "newpass123"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)


class WelcomeEmailWebhookViewTestCase(APITestCase):
    """ウェルカムメール送信Webhookのセキュリティテスト"""

    @patch("apps.users.views.UserEmailService.send_welcome_email")
    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_success(self, mock_verify_signature, mock_send_email):
        """【View】正しい署名を持つWebhookによるメール送信テスト"""
        mock_verify_signature.return_value = True
        mock_send_email.return_value = "email_123"

        response = self.client.post(
            "/api/v1/webhooks/send-welcome-email",
            {
                "email": "user@example.com",
                "first_name": "John"
            },
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid_signature"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message_id"], "email_123")
        mock_send_email.assert_called_once_with("user@example.com", "John")

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_invalid_signature(self, mock_verify_signature):
        """【View】署名が不正な場合に 403 Forbidden が返るかテスト"""
        mock_verify_signature.return_value = False

        response = self.client.post(
            "/api/v1/webhooks/send-welcome-email",
            {
                "email": "user@example.com",
                "first_name": "John"
            },
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=invalid"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_missing_fields(self, mock_verify_signature):
        """【View】バリデーションエラー時に 400 Bad Request が返るかテスト"""
        mock_verify_signature.return_value = True

        response = self.client.post(
            "/api/v1/webhooks/send-welcome-email",
            {"email": "user@example.com"},  # first_nameが不足
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)