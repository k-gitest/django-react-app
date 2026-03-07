"""
Usersアプリ - シリアライザテスト（pytest）
CustomUserSerializer, CustomRegisterSerializer, WelcomeEmailWebhookSerializer のテスト
"""
import pytest
from django.contrib.auth import get_user_model

from apps.users.serializers import (
    CustomRegisterSerializer,
    CustomUserSerializer,
    WelcomeEmailWebhookSerializer,
)

User = get_user_model()


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