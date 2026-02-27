"""
Usersアプリの統合テスト
Models, Serializers, Services, Views の網羅的テスト
"""
from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import RequestFactory, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from apps.common.exceptions import UserAlreadyExistsError
from apps.users.analytics_service import AnalyticsService
from apps.users.email_service import UserEmailService
from apps.users.qstash_service import UserQStashService
from apps.users.serializers import (
    CustomRegisterSerializer,
    CustomUserSerializer,
    WelcomeEmailWebhookSerializer,
)
from apps.users.user_service import (
    UserCommandService,
    UserQueryService,
    UserRegistrationService,
)

User = get_user_model()


# ================================
# Model Tests
# ================================

@pytest.mark.django_db
class TestCustomUserModel:
    """カスタムユーザーモデルの基本機能テスト"""

    def test_create_user_with_email(self):
        """【Model】メールアドレスによる通常ユーザー作成のテスト"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )

        assert user.email == "test@example.com"
        assert user.check_password("testpass123")
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        """【Model】スーパーユーザー作成（is_staff, is_superuser）のテスト"""
        superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )

        assert superuser.email == "admin@example.com"
        assert superuser.is_active
        assert superuser.is_staff
        assert superuser.is_superuser

    def test_email_normalization(self):
        """【Model】ドメイン部分が小文字化（正規化）されるかテスト"""
        user = User.objects.create_user(
            email="Test@EXAMPLE.com",
            password="pass123"
        )

        assert user.email == "Test@example.com"

    def test_email_unique_constraint(self):
        """【Model】同一メールアドレスでの登録がDBレベルで阻止されるかテスト"""
        User.objects.create_user(email="unique@example.com", password="pass123")

        with pytest.raises(IntegrityError):
            User.objects.create_user(email="unique@example.com", password="pass456")

    def test_get_by_natural_key_case_insensitive(self):
        """【Model】ログイン時のメールアドレス大文字小文字を区別せず検索できるかテスト"""
        User.objects.create_user(email="User@Example.com", password="pass123")

        user = User.objects.get_by_natural_key("user@example.com")
        assert user is not None
        assert user.email == "User@example.com"

    def test_str_representation(self):
        """【Model】ユーザーオブジェクトの文字列表現（__str__）のテスト"""
        user = User.objects.create_user(email="test@example.com", password="pass123")

        assert str(user) == "test@example.com"


# ================================
# Serializer Tests
# ================================

@pytest.mark.django_db
class TestCustomUserSerializer:
    """ユーザー情報シリアライザのテスト"""

    def test_serializer_fields(self):
        """【Serializer】必要なフィールドが全て含まれているかテスト"""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass123",
            first_name="John",
            last_name="Doe"
        )

        serializer = CustomUserSerializer(user)
        data = serializer.data

        assert set(data.keys()) == {"id", "email", "first_name", "last_name", "is_staff"}
        assert data["email"] == "test@example.com"
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"

    def test_read_only_fields(self):
        """【Serializer】idやemailが更新不可（Read Only）であることをテスト"""
        user = User.objects.create_user(email="test@example.com", password="pass123")

        serializer = CustomUserSerializer(user, data={
            "id": 999,
            "email": "hacker@example.com",
            "is_staff": True,
            "first_name": "Updated"
        })

        assert serializer.is_valid()
        serializer.save()

        user.refresh_from_db()
        assert user.email != "hacker@example.com"
        assert not user.is_staff
        assert user.first_name == "Updated"


@pytest.mark.django_db
class TestCustomRegisterSerializer:
    """会員登録用シリアライザのバリデーションテスト"""

    def test_valid_registration_data(self):
        """【Serializer】正しい登録データがバリデーションを通過するかテスト"""
        data = {
            "email": "newuser@example.com",
            "password1": "strongpass123",
            "password2": "strongpass123",
            "first_name": "John",
            "last_name": "Doe"
        }

        serializer = CustomRegisterSerializer(data=data)
        assert serializer.is_valid()

    def test_password_mismatch(self):
        """【Serializer】パスワード（確認用含む）の不一致バリデーションテスト"""
        data = {
            "email": "test@example.com",
            "password1": "pass123",
            "password2": "different",
        }

        serializer = CustomRegisterSerializer(data=data)
        assert not serializer.is_valid()

    def test_invalid_email(self):
        """【Serializer】不正なメール形式のバリデーションテスト"""
        data = {
            "email": "not-an-email",
            "password1": "pass123",
            "password2": "pass123",
        }

        serializer = CustomRegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors


@pytest.mark.django_db
class TestWelcomeEmailWebhookSerializer:
    """ウェルカムメールWebhook用シリアライザのテスト"""

    def test_valid_webhook_payload(self):
        """【Serializer】Webhookの正しいペイロードが検証を通るかテスト"""
        data = {"email": "user@example.com", "first_name": "John"}

        serializer = WelcomeEmailWebhookSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["email"] == "user@example.com"
        assert serializer.validated_data["first_name"] == "John"

    def test_missing_email(self):
        """【Serializer】必須項目 email が欠落している場合のバリデーションテスト"""
        serializer = WelcomeEmailWebhookSerializer(data={"first_name": "John"})

        assert not serializer.is_valid()
        assert "email" in serializer.errors
        assert serializer.errors["email"][0] == "email is required"

    def test_missing_first_name(self):
        """【Serializer】必須項目 first_name が欠落している場合のバリデーションテスト"""
        serializer = WelcomeEmailWebhookSerializer(data={"email": "user@example.com"})

        assert not serializer.is_valid()
        assert "first_name" in serializer.errors

    def test_blank_first_name(self):
        """【Serializer】first_name が空文字（blank）の場合のバリデーションテスト"""
        serializer = WelcomeEmailWebhookSerializer(data={
            "email": "user@example.com",
            "first_name": ""
        })

        assert not serializer.is_valid()


# ================================
# Service Tests - UserQueryService
# ================================

@pytest.mark.django_db
class TestUserQueryService:
    """UserQueryService（参照系）のテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = UserQueryService()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )

    def test_get_user_by_email(self):
        """【Service】メールアドレス指定によるユーザー取得のテスト"""
        user = self.service.get_user_by_email("test@example.com")

        assert user is not None
        assert user.email == "test@example.com"

    def test_get_user_by_email_case_insensitive(self):
        """【Service】メールアドレス取得が大文字小文字を区別しないことをテスト"""
        user = self.service.get_user_by_email("TEST@EXAMPLE.COM")

        assert user is not None
        assert user.email == "test@example.com"

    def test_get_user_by_email_not_found(self):
        """【Service】存在しないメールアドレスでNoneが返るかテスト"""
        user = self.service.get_user_by_email("nonexistent@example.com")

        assert user is None

    def test_email_exists(self):
        """【Service】メールアドレスの存在確認関数のテスト"""
        assert self.service.email_exists("test@example.com")
        assert not self.service.email_exists("nonexistent@example.com")

    def test_email_exists_case_insensitive(self):
        """【Service】存在確認が大文字小文字を区別しないことをテスト"""
        assert self.service.email_exists("TEST@EXAMPLE.COM")

    def test_get_user_by_id(self):
        """【Service】ID指定によるユーザー取得のテスト"""
        user = self.service.get_user_by_id(self.user.id)

        assert user is not None
        assert user.id == self.user.id

    def test_get_user_by_id_not_found(self):
        """【Service】存在しないIDでNoneが返るかテスト"""
        user = self.service.get_user_by_id(99999)

        assert user is None


# ================================
# Service Tests - UserCommandService
# ================================

@pytest.mark.django_db
class TestUserCommandService:
    """UserCommandService（更新系）のテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = UserCommandService()
        self.factory = RequestFactory()

    def test_create_user(self):
        """【Service】ユーザーの新規作成（保存）テスト"""
        user = self.service.create_user(
            email="newuser@example.com",
            password="pass123",
            first_name="John",
            last_name="Doe"
        )

        assert user.email == "newuser@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.check_password("pass123")

    def test_create_user_with_adapter(self):
        """【Service】allauthアダプターを経由したユーザー作成テスト"""
        request = self.factory.post("/register")

        user = self.service.create_user_with_adapter(
            request=request,
            email="adapter@example.com",
            password="pass123",
            first_name="Jane",
            last_name="Smith"
        )

        assert user.email == "adapter@example.com"
        assert user.first_name == "Jane"

    def test_update_user(self):
        """【Service】ユーザー情報の更新テスト"""
        user = User.objects.create_user(email="test@example.com", password="pass123")

        updated = self.service.update_user(user, first_name="Updated", last_name="Name")

        assert updated.first_name == "Updated"
        assert updated.last_name == "Name"

    def test_change_password(self):
        """【Service】パスワード変更処理のテスト"""
        user = User.objects.create_user(email="test@example.com", password="oldpass")

        updated = self.service.change_password(user, "newpass")

        assert updated.check_password("newpass")
        assert not updated.check_password("oldpass")

    def test_delete_user(self):
        """【Service】ユーザー削除処理のテスト"""
        user = User.objects.create_user(email="delete@example.com", password="pass123")
        user_id = user.id

        self.service.delete_user(user)

        assert not User.objects.filter(id=user_id).exists()


# ================================
# Service Tests - UserRegistrationService
# ================================

@pytest.mark.django_db
class TestUserRegistrationService:
    """ユーザー登録用ファサードサービスのテスト"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = UserRegistrationService()
        self.factory = RequestFactory()

    @override_settings(TESTING=True)
    def test_register_user_success(self):
        """【Service】正常なユーザー登録フローのテスト"""
        request = self.factory.post("/register")
        user_data = {
            "email": "newuser@example.com",
            "password": "pass123",
            "first_name": "John",
            "last_name": "Doe"
        }

        user = self.service.register_user(request, user_data)

        assert user.email == "newuser@example.com"
        assert user.first_name == "John"
        assert user.check_password("pass123")

    @override_settings(TESTING=True)
    def test_register_user_duplicate_email(self):
        """【Service】重複メールアドレス登録時のカスタム例外送出テスト"""
        User.objects.create_user(email="duplicate@example.com", password="pass123")

        request = self.factory.post("/register")
        user_data = {"email": "duplicate@example.com", "password": "pass456"}

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            self.service.register_user(request, user_data)

        assert str(exc_info.value) == "このメールアドレスは既に登録されています"
        assert exc_info.value.data.get("field") == "email"

    @override_settings(TESTING=True)
    def test_register_user_case_insensitive_duplicate(self):
        """【Service】重複登録チェックが大文字小文字を区別しないことをテスト"""
        User.objects.create_user(email="case@example.com", password="pass123")

        request = self.factory.post("/register")
        user_data = {"email": "CASE@EXAMPLE.COM", "password": "pass456"}

        with pytest.raises(UserAlreadyExistsError):
            self.service.register_user(request, user_data)


# ================================
# Service Tests - AnalyticsService
# ================================

@pytest.mark.django_db
class TestAnalyticsService:
    """分析用サービス（外部DB連携）のテスト"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        AnalyticsService._client = None
        yield
        from apps.common.infrastructure.motherduck_client import MotherDuckClient
        AnalyticsService._client = None
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

    def test_log_auth_event_login(self, mocker):
        """【Service】ログインイベントのログ記録テスト"""
        mocker.patch(
            "apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema"
        )
        mock_connect = mocker.patch(
            "apps.common.infrastructure.motherduck_client.duckdb.connect"
        )
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        request = self.factory.post("/login")

        result = AnalyticsService.log_auth_event(
            user=self.user,
            event_type="login",
            request=request,
            success=True
        )

        assert result is None
        mock_conn.execute.assert_called_once()

    def test_log_auth_event_with_ip_address(self, mocker):
        """【Service】ログ記録時のIPアドレス抽出テスト"""
        mocker.patch(
            "apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema"
        )
        mock_connect = mocker.patch(
            "apps.common.infrastructure.motherduck_client.duckdb.connect"
        )
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        request = self.factory.post("/login", REMOTE_ADDR="192.168.1.1")

        AnalyticsService.log_auth_event(
            user=self.user,
            event_type="login",
            request=request,
            success=True
        )

        assert mock_conn.execute.call_args is not None

    def test_log_auth_event_with_x_forwarded_for(self, mocker):
        """【Service】プロキシ経由（X-Forwarded-For）のIPアドレス抽出テスト"""
        mocker.patch(
            "apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema"
        )
        mock_connect = mocker.patch(
            "apps.common.infrastructure.motherduck_client.duckdb.connect"
        )
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        request = self.factory.post(
            "/login",
            HTTP_X_FORWARDED_FOR="203.0.113.1, 198.51.100.1"
        )

        AnalyticsService.log_auth_event(
            user=self.user,
            event_type="login",
            request=request,
            success=True
        )

        mock_conn.execute.assert_called_once()


# ================================
# Service Tests - UserEmailService
# ================================

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


# ================================
# Service Tests - UserQStashService
# ================================

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


# ================================
# View Tests
# ================================

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