"""
Usersアプリ - サービステスト（pytest）
UserQueryService, UserCommandService, UserRegistrationService のテスト
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings

from apps.common.exceptions import UserAlreadyExistsError
from apps.users.user_service import (
    UserCommandService,
    UserQueryService,
    UserRegistrationService,
)

User = get_user_model()


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