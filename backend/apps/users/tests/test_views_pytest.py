"""
Usersアプリ - ビューテスト（pytest）
認証系APIビュー、ウェルカムメールWebhookビューのテスト
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestAuthenticationViews:
    """認証系APIビューのテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="John"
        )

    @override_settings(TESTING=True)
    def test_login_success(self, mocker):
        """【View】正常なログインとJWTトークンの返却テスト"""
        mock_handle_login = mocker.patch(
            "apps.users.views.UserAuthService.handle_login_success"
        )

        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "test@example.com", "password": "testpass123"},
            format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        mock_handle_login.assert_called_once()

    def test_login_invalid_credentials(self):
        """【View】誤った認証情報でのログイン失敗テスト"""
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "test@example.com", "password": "wrongpass"},
            format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

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

        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email="newuser@example.com").exists()

    @override_settings(TESTING=True)
    def test_register_duplicate_email(self):
        """【View】既存メールアドレスによる登録時の 409 Conflict 返却テスト"""
        response = self.client.post(
            "/api/v1/auth/registration/",
            {
                "email": "test@example.com",  # 既にsetupで作成済み
                "password1": "newpass123",
                "password2": "newpass123"
            },
            format="json"
        )

        assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.django_db
class TestWelcomeEmailWebhookView:
    """ウェルカムメール送信Webhookのセキュリティテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()

    def test_webhook_success(self, mocker):
        """【View】正しい署名を持つWebhookによるメール送信テスト"""
        mocker.patch(
            "apps.common.permissions.verify_qstash_signature", return_value=True
        )
        mock_send_email = mocker.patch(
            "apps.users.views.UserEmailService.send_welcome_email",
            return_value="email_123"
        )

        response = self.client.post(
            "/api/v1/webhooks/send-welcome-email",
            {"email": "user@example.com", "first_name": "John"},
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid_signature"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message_id"] == "email_123"
        mock_send_email.assert_called_once_with("user@example.com", "John")

    def test_webhook_invalid_signature(self, mocker):
        """【View】署名が不正な場合に 403 Forbidden が返るかテスト"""
        mocker.patch(
            "apps.common.permissions.verify_qstash_signature", return_value=False
        )

        response = self.client.post(
            "/api/v1/webhooks/send-welcome-email",
            {"email": "user@example.com", "first_name": "John"},
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=invalid"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_webhook_missing_fields(self, mocker):
        """【View】バリデーションエラー時に 400 Bad Request が返るかテスト"""
        mocker.patch(
            "apps.common.permissions.verify_qstash_signature", return_value=True
        )

        response = self.client.post(
            "/api/v1/webhooks/send-welcome-email",
            {"email": "user@example.com"},  # first_nameが不足
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST