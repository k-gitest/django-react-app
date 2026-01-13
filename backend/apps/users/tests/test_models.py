from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

User = get_user_model()


class CustomUserModelTest(TestCase):
    """
    カスタムユーザーモデルのテスト
    """

    def test_create_user_with_email(self):
        """
        メールアドレスでユーザーを作成できることを確認
        """
        email = "test@example.com"
        password = "testpass123"
        user = User.objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_create_user_with_normalized_email(self):
        """
        メールアドレスが正規化されることを確認
        """
        email = "Test@EXAMPLE.com"
        user = User.objects.create_user(
            email=email,
            password="testpass123"
        )

        # ドメイン部分が小文字化される
        self.assertEqual(user.email, "Test@example.com")

    def test_create_superuser(self):
        """
        スーパーユーザーを作成できることを確認
        """
        email = "admin@example.com"
        password = "adminpass123"
        user = User.objects.create_superuser(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_create_user_without_email_raises_error(self):
        """
        メールアドレスなしでユーザーを作成しようとするとエラーが発生することを確認
        """
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email=None,
                password="testpass123"
            )

    def test_create_user_with_empty_email_raises_error(self):
        """
        空のメールアドレスでユーザーを作成しようとするとエラーが発生することを確認
        """
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="",
                password="testpass123"
            )

    def test_email_is_unique(self):
        """
        メールアドレスが一意であることを確認
        """
        email = "test@example.com"
        User.objects.create_user(email=email, password="pass1")

        with self.assertRaises(IntegrityError):
            User.objects.create_user(email=email, password="pass2")

    def test_get_by_natural_key_case_insensitive(self):
        """
        メールアドレスの大文字小文字を区別せずにユーザーを取得できることを確認
        """
        email = "Test@Example.com"
        user = User.objects.create_user(email=email, password="testpass123")

        # 小文字で検索
        found_user = User.objects.get_by_natural_key("test@example.com")
        self.assertEqual(found_user.id, user.id)

        # 大文字で検索
        found_user = User.objects.get_by_natural_key("TEST@EXAMPLE.COM")
        self.assertEqual(found_user.id, user.id)

    def test_user_string_representation(self):
        """
        ユーザーの文字列表現がメールアドレスであることを確認
        """
        email = "test@example.com"
        user = User.objects.create_user(email=email, password="testpass123")

        self.assertEqual(str(user), email)

    def test_create_user_with_first_and_last_name(self):
        """
        名前付きでユーザーを作成できることを確認
        """
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe"
        )

        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")