"""
Usersアプリ - サービステスト
UserQueryService, UserCommandService, UserRegistrationService のテスト
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.test import override_settings

from apps.users.user_service import (
    UserQueryService,
    UserCommandService,
    UserRegistrationService,
)
from apps.common.exceptions import UserAlreadyExistsError

User = get_user_model()


class UserQueryServiceTestCase(TestCase):
    """UserQueryService（参照系）のテスト"""

    def setUp(self):
        self.service = UserQueryService()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )

    def test_get_user_by_email(self):
        """【Service】メールアドレス指定によるユーザー取得のテスト"""
        user = self.service.get_user_by_email("test@example.com")

        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")

    def test_get_user_by_email_case_insensitive(self):
        """【Service】メールアドレス取得が大文字小文字を区別しないことをテスト"""
        user = self.service.get_user_by_email("TEST@EXAMPLE.COM")

        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")

    def test_get_user_by_email_not_found(self):
        """【Service】存在しないメールアドレスでNoneが返るかテスト"""
        user = self.service.get_user_by_email("nonexistent@example.com")

        self.assertIsNone(user)

    def test_email_exists(self):
        """【Service】メールアドレスの存在確認関数のテスト"""
        self.assertTrue(self.service.email_exists("test@example.com"))
        self.assertFalse(self.service.email_exists("nonexistent@example.com"))

    def test_email_exists_case_insensitive(self):
        """【Service】存在確認が大文字小文字を区別しないことをテスト"""
        self.assertTrue(self.service.email_exists("TEST@EXAMPLE.COM"))

    def test_get_user_by_id(self):
        """【Service】ID指定によるユーザー取得のテスト"""
        user = self.service.get_user_by_id(self.user.id)

        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user.id)

    def test_get_user_by_id_not_found(self):
        """【Service】存在しないIDでNoneが返るかテスト"""
        user = self.service.get_user_by_id(99999)

        self.assertIsNone(user)


class UserCommandServiceTestCase(TestCase):
    """UserCommandService（更新系）のテスト"""

    def setUp(self):
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

        self.assertEqual(user.email, "newuser@example.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertTrue(user.check_password("pass123"))

    def test_create_user_with_adapter(self):
        """【Service】allauthアダプターを経由したユーザー作成テスト"""
        request = self.factory.post('/register')

        user = self.service.create_user_with_adapter(
            request=request,
            email="adapter@example.com",
            password="pass123",
            first_name="Jane",
            last_name="Smith"
        )

        self.assertEqual(user.email, "adapter@example.com")
        self.assertEqual(user.first_name, "Jane")

    def test_update_user(self):
        """【Service】ユーザー情報の更新テスト"""
        user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )

        updated = self.service.update_user(
            user,
            first_name="Updated",
            last_name="Name"
        )

        self.assertEqual(updated.first_name, "Updated")
        self.assertEqual(updated.last_name, "Name")

    def test_change_password(self):
        """【Service】パスワード変更処理のテスト"""
        user = User.objects.create_user(
            email="test@example.com",
            password="oldpass"
        )

        updated = self.service.change_password(user, "newpass")

        self.assertTrue(updated.check_password("newpass"))
        self.assertFalse(updated.check_password("oldpass"))

    def test_delete_user(self):
        """【Service】ユーザー削除処理のテスト"""
        user = User.objects.create_user(
            email="delete@example.com",
            password="pass123"
        )
        user_id = user.id

        self.service.delete_user(user)

        self.assertFalse(User.objects.filter(id=user_id).exists())


class UserRegistrationServiceTestCase(TestCase):
    """ユーザー登録用ファサードサービスのテスト"""

    def setUp(self):
        self.service = UserRegistrationService()
        self.factory = RequestFactory()

    @override_settings(TESTING=True)
    def test_register_user_success(self):
        """【Service】正常なユーザー登録フローのテスト"""
        request = self.factory.post('/register')
        user_data = {
            'email': 'newuser@example.com',
            'password': 'pass123',
            'first_name': 'John',
            'last_name': 'Doe'
        }

        user = self.service.register_user(request, user_data)

        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertTrue(user.check_password('pass123'))

    @override_settings(TESTING=True)
    def test_register_user_duplicate_email(self):
        """【Service】重複メールアドレス登録時のカスタム例外送出テスト"""
        User.objects.create_user(
            email="duplicate@example.com",
            password="pass123"
        )

        request = self.factory.post('/register')
        user_data = {
            'email': 'duplicate@example.com',
            'password': 'pass456'
        }

        with self.assertRaises(UserAlreadyExistsError) as context:
            self.service.register_user(request, user_data)

        self.assertEqual(str(context.exception), "このメールアドレスは既に登録されています")
        self.assertEqual(context.exception.data.get("field"), "email")

    @override_settings(TESTING=True)
    def test_register_user_case_insensitive_duplicate(self):
        """【Service】重複登録チェックが大文字小文字を区別しないことをテスト"""
        User.objects.create_user(
            email="case@example.com",
            password="pass123"
        )

        request = self.factory.post('/register')
        user_data = {
            'email': 'CASE@EXAMPLE.COM',
            'password': 'pass456'
        }

        with self.assertRaises(UserAlreadyExistsError):
            self.service.register_user(request, user_data)