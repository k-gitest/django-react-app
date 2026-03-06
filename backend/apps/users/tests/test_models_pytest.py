"""
Usersアプリ - モデルテスト（pytest）
CustomUser モデルの基本機能テスト
"""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


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