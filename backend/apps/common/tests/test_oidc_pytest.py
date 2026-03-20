"""
[認証] Auth0 OIDC JWT認証クラスのテスト（pytest）
"""
import pytest
from unittest.mock import MagicMock
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings

from apps.common.auth.oidc import OIDCAuthentication
from apps.common.exceptions import TokenExpiredError, InvalidTokenError

User = get_user_model()


@pytest.mark.django_db
class TestOIDCAuthentication:
    """[認証] Auth0 OIDC JWT認証クラスのテスト"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        self.auth = OIDCAuthentication()
        self.factory_request = MagicMock()
        cache.clear()
        self.payload = {
            "sub": "auth0|test_user_123",
            "email": "test@example.com",
            "given_name": "John",
            "family_name": "Doe",
        }
        yield
        cache.clear()

    @override_settings(AUTH0_DOMAIN="test.auth0.com", AUTH0_AUDIENCE="https://api.test.com")
    def test_get_jwks_caching(self, mocker):
        """[Auth] JWKSが正しく取得され、キャッシュされることを確認"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"keys": ["test_key"]}
        mock_response.raise_for_status = MagicMock()
        mock_get = mocker.patch("apps.common.auth.oidc.requests.get", return_value=mock_response)

        # 1回目：ネットワーク経由で取得
        jwks1 = self.auth.get_jwks()
        assert jwks1["keys"] == ["test_key"]
        assert mock_get.call_count == 1

        # 2回目：キャッシュから取得（mock_getが呼ばれない）
        jwks2 = self.auth.get_jwks()
        assert jwks2["keys"] == ["test_key"]
        assert mock_get.call_count == 1

    def test_authenticate_success_new_user(self, mocker):
        """[Auth] 有効なトークンの場合、新規ユーザーが作成され認証されることを確認"""
        mocker.patch.object(OIDCAuthentication, "_verify_token", return_value=self.payload)
        self.factory_request.META = {"HTTP_AUTHORIZATION": "Bearer valid_token"}

        user, auth = self.auth.authenticate(self.factory_request)

        assert user is not None
        assert user.email == "test@example.com"
        assert user.oidc_sub == "auth0|test_user_123"
        assert auth is None

    def test_authenticate_link_existing_user(self, mocker):
        """[Auth] 既存のDjangoユーザー（email一致）にoidc_subが連携されることを確認"""
        existing_user = User.objects.create(email="test@example.com")
        mocker.patch.object(OIDCAuthentication, "_verify_token", return_value=self.payload)
        self.factory_request.META = {"HTTP_AUTHORIZATION": "Bearer valid_token"}

        user, _ = self.auth.authenticate(self.factory_request)

        existing_user.refresh_from_db()
        assert user.id == existing_user.id
        assert existing_user.oidc_sub == "auth0|test_user_123"

    def test_verify_token_expired(self, mocker):
        """[Auth] トークン期限切れ時に TokenExpiredError が送出されることを確認"""
        mocker.patch.object(OIDCAuthentication, "get_jwks", return_value={"keys": []})
        mocker.patch(
            "apps.common.auth.oidc.jwt.decode",
            side_effect=Exception("Claim: exp has expired")
        )

        with pytest.raises(TokenExpiredError):
            self.auth._verify_token("expired_token")

    def test_authenticate_no_header(self):
        """[Auth] Authorizationヘッダーがない場合、Noneを返しフォールバックを許可することを確認"""
        self.factory_request.META = {}

        result = self.auth.authenticate(self.factory_request)

        assert result is None

    def test_get_or_create_user_update_info(self, mocker):
        """[Auth] ユーザー名が変更された場合、既存レコードが更新されることを確認"""
        user = User.objects.create(
            email="test@example.com",
            oidc_sub="auth0|test_user_123",
            first_name="Old",
            last_name="Name"
        )
        updated_payload = {**self.payload, "given_name": "New"}

        updated_user = self.auth._get_or_create_user(updated_payload)

        assert updated_user.first_name == "New"
        assert updated_user.id == user.id

    def test_get_or_create_user_missing_info(self):
        """[Auth] 必須情報(sub/email)が欠けている場合に InvalidTokenError を送出することを確認"""
        with pytest.raises(InvalidTokenError):
            self.auth._get_or_create_user({"sub": "only_sub"})  # email欠落