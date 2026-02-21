from unittest.mock import MagicMock, patch
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.exceptions import AuthenticationFailed
from apps.common.auth.oidc import OIDCAuthentication
from apps.common.exceptions import TokenExpiredError, InvalidTokenError, IntegrityConstraintError

User = get_user_model()

class OIDCAuthenticationTestCase(TestCase):
    """
    [認証] Auth0 OIDC JWT認証クラスのテスト
    """

    def setUp(self):
        self.auth = OIDCAuthentication()
        self.factory_request = MagicMock()
        cache.clear()

        # ダミーのJWTペイロード
        self.payload = {
            "sub": "auth0|test_user_123",
            "email": "test@example.com",
            "given_name": "John",
            "family_name": "Doe",
        }

    @override_settings(AUTH0_DOMAIN="test.auth0.com", AUTH0_AUDIENCE="https://api.test.com")
    @patch("apps.common.auth.oidc.requests.get")
    def test_get_jwks_caching(self, mock_get):
        """[Auth] JWKSが正しく取得され、キャッシュされることを確認"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"keys": ["test_key"]}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # 1回目：ネットワーク経由で取得
        jwks1 = self.auth.get_jwks()
        self.assertEqual(jwks1["keys"], ["test_key"])
        self.assertEqual(mock_get.call_count, 1)

        # 2回目：キャッシュから取得（mock_getが呼ばれない）
        jwks2 = self.auth.get_jwks()
        self.assertEqual(jwks2["keys"], ["test_key"])
        self.assertEqual(mock_get.call_count, 1)

    @patch("apps.common.auth.oidc.OIDCAuthentication._verify_token")
    def test_authenticate_success_new_user(self, mock_verify):
        """[Auth] 有効なトークンの場合、新規ユーザーが作成され認証されることを確認"""
        mock_verify.return_value = self.payload
        self.factory_request.META = {"HTTP_AUTHORIZATION": "Bearer valid_token"}

        user, auth = self.auth.authenticate(self.factory_request)

        self.assertIsNotNone(user)
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.oidc_sub, "auth0|test_user_123")
        self.assertIsNone(auth)

    @patch("apps.common.auth.oidc.OIDCAuthentication._verify_token")
    def test_authenticate_link_existing_user(self, mock_verify):
        """[Auth] 既存のDjangoユーザー（email一致）にoidc_subが連携されることを確認"""
        existing_user = User.objects.create(email="test@example.com")
        mock_verify.return_value = self.payload
        self.factory_request.META = {"HTTP_AUTHORIZATION": "Bearer valid_token"}

        user, _ = self.auth.authenticate(self.factory_request)

        existing_user.refresh_from_db()
        self.assertEqual(user.id, existing_user.id)
        self.assertEqual(existing_user.oidc_sub, "auth0|test_user_123")

    @patch("apps.common.auth.oidc.jwt.decode")
    @patch("apps.common.auth.oidc.OIDCAuthentication.get_jwks")
    def test_verify_token_expired(self, mock_get_jwks, mock_decode):
        """[Auth] トークン期限切れ時に TokenExpiredError が送出されることを確認"""
        # 1. JWKS取得をモックして外部通信を遮断
        mock_get_jwks.return_value = {"keys": []}
        
        # 2. jwt.decodeが例外を投げるように設定
        # ロジック内で 'exp' という文字が含まれていると TokenExpiredError になる前提
        mock_decode.side_effect = Exception("Claim: exp has expired")
        
        with self.assertRaises(TokenExpiredError):
            self.auth._verify_token("expired_token")

    def test_authenticate_no_header(self):
        """[Auth] Authorizationヘッダーがない場合、Noneを返しフォールバックを許可することを確認"""
        self.factory_request.META = {}
        result = self.auth.authenticate(self.factory_request)
        self.assertIsNone(result)

    @patch("apps.common.auth.oidc.OIDCAuthentication._verify_token")
    def test_get_or_create_user_update_info(self, mock_verify):
        """[Auth] ユーザー名が変更された場合、既存レコードが更新されることを確認"""
        # すでにDBにいるユーザー
        user = User.objects.create(
            email="test@example.com", 
            oidc_sub="auth0|test_user_123",
            first_name="Old",
            last_name="Name"
        )
        
        # 新しい情報をペイロードに設定
        updated_payload = self.payload.copy()
        updated_payload["given_name"] = "New"

        updated_user = self.auth._get_or_create_user(updated_payload)
        
        self.assertEqual(updated_user.first_name, "New")
        self.assertEqual(updated_user.id, user.id)

    def test_get_or_create_user_missing_info(self):
        """[Auth] 必須情報(sub/email)が欠けている場合に InvalidTokenError を送出することを確認"""
        invalid_payload = {"sub": "only_sub"} # email欠落
        with self.assertRaises(InvalidTokenError):
            self.auth._get_or_create_user(invalid_payload)