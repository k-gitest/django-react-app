"""
Usersアプリ - シリアライザテスト
CustomUserSerializer, CustomRegisterSerializer, WelcomeEmailWebhookSerializer のテスト
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model

from apps.users.serializers import (
    CustomUserSerializer,
    CustomRegisterSerializer,
    WelcomeEmailWebhookSerializer,
)

User = get_user_model()


class CustomUserSerializerTestCase(TestCase):
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

        self.assertEqual(set(data.keys()), {'id', 'email', 'first_name', 'last_name', 'is_staff'})
        self.assertEqual(data['email'], "test@example.com")
        self.assertEqual(data['first_name'], "John")
        self.assertEqual(data['last_name'], "Doe")

    def test_read_only_fields(self):
        """【Serializer】idやemailが更新不可（Read Only）であることをテスト"""
        user = User.objects.create_user(email="test@example.com", password="pass123")

        serializer = CustomUserSerializer(user, data={
            'id': 999,
            'email': 'hacker@example.com',
            'is_staff': True,
            'first_name': 'Updated'
        })

        self.assertTrue(serializer.is_valid())
        serializer.save()

        user.refresh_from_db()
        self.assertNotEqual(user.email, 'hacker@example.com')
        self.assertFalse(user.is_staff)
        self.assertEqual(user.first_name, 'Updated')


class CustomRegisterSerializerTestCase(TestCase):
    """会員登録用シリアライザのバリデーションテスト"""

    def setUp(self):
        self.factory = RequestFactory()

    def test_valid_registration_data(self):
        """【Serializer】正しい登録データがバリデーションを通過するかテスト"""
        data = {
            'email': 'newuser@example.com',
            'password1': 'strongpass123',
            'password2': 'strongpass123',
            'first_name': 'John',
            'last_name': 'Doe'
        }

        serializer = CustomRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_password_mismatch(self):
        """【Serializer】パスワード（確認用含む）の不一致バリデーションテスト"""
        data = {
            'email': 'test@example.com',
            'password1': 'pass123',
            'password2': 'different',
        }

        serializer = CustomRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_invalid_email(self):
        """【Serializer】不正なメール形式のバリデーションテスト"""
        data = {
            'email': 'not-an-email',
            'password1': 'pass123',
            'password2': 'pass123',
        }

        serializer = CustomRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


class WelcomeEmailWebhookSerializerTestCase(TestCase):
    """ウェルカムメールWebhook用シリアライザのテスト"""

    def test_valid_webhook_payload(self):
        """【Serializer】Webhookの正しいペイロードが検証を通るかテスト"""
        data = {
            'email': 'user@example.com',
            'first_name': 'John'
        }

        serializer = WelcomeEmailWebhookSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['email'], 'user@example.com')
        self.assertEqual(serializer.validated_data['first_name'], 'John')

    def test_missing_email(self):
        """【Serializer】必須項目 email が欠落している場合のバリデーションテスト"""
        data = {'first_name': 'John'}

        serializer = WelcomeEmailWebhookSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
        self.assertEqual(serializer.errors['email'][0], 'email is required')

    def test_missing_first_name(self):
        """【Serializer】必須項目 first_name が欠落している場合のバリデーションテスト"""
        data = {'email': 'user@example.com'}

        serializer = WelcomeEmailWebhookSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('first_name', serializer.errors)

    def test_blank_first_name(self):
        """【Serializer】first_name が空文字（blank）の場合のバリデーションテスト"""
        data = {
            'email': 'user@example.com',
            'first_name': ''
        }

        serializer = WelcomeEmailWebhookSerializer(data=data)
        self.assertFalse(serializer.is_valid())