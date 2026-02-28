"""
Usersアプリ - モデルテスト
CustomUser モデルの基本機能テスト
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class CustomUserModelTestCase(TestCase):
    """カスタムユーザーモデルの基本機能テスト"""

    def test_create_user_with_email(self):
        """【Model】メールアドレスによる通常ユーザー作成のテスト"""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )

        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """【Model】スーパーユーザー作成（is_staff, is_superuser）のテスト"""
        superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )

        self.assertEqual(superuser.email, "admin@example.com")
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_email_normalization(self):
        """【Model】ドメイン部分が小文字化（正規化）されるかテスト"""
        user = User.objects.create_user(
            email="Test@EXAMPLE.com",
            password="pass123"
        )

        self.assertEqual(user.email, "Test@example.com")

    def test_email_unique_constraint(self):
        """【Model】同一メールアドレスでの登録がDBレベルで阻止されるかテスト"""
        User.objects.create_user(
            email="unique@example.com",
            password="pass123"
        )

        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email="unique@example.com",
                password="pass456"
            )

    def test_get_by_natural_key_case_insensitive(self):
        """【Model】ログイン時のメールアドレス大文字小文字を区別せず検索できるかテスト"""
        User.objects.create_user(
            email="User@Example.com",
            password="pass123"
        )

        user = User.objects.get_by_natural_key("user@example.com")
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "User@example.com")

    def test_str_representation(self):
        """【Model】ユーザーオブジェクトの文字列表現（__str__）のテスト"""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )

        self.assertEqual(str(user), "test@example.com")