"""
OIDC JWT検証（Auth0統合）

Auth0が発行したJWTトークンを検証し、ユーザーを取得または作成する
"""
from asyncio import exceptions
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError as DjangoIntegrityError
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from joserfc import jwt
from joserfc.errors import JoseError
import requests
from django.conf import settings
from django.core.cache import cache
import logging
from exceptions import IntegrityConstraintError, InvalidTokenError, TokenExpiredError


logger = logging.getLogger(__name__)
User = get_user_model()


class OIDCAuthentication(BaseAuthentication):
    """
    Auth0 OIDC JWT検証
    
    フロー:
    1. Authorization ヘッダーからトークン取得
    2. Auth0の公開鍵でJWT検証
    3. oidc_sub（Auth0のUser ID）からユーザー取得/作成
    4. requestにユーザーを設定
    """
    
    def __init__(self):
        self.jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
        self.audience = settings.AUTH0_AUDIENCE  # API Identifier
        self.issuer = f"https://{settings.AUTH0_DOMAIN}/"
        self.leeway = 60  # 時刻ズレ許容（秒）
    
    def get_jwks(self):
        """
        Auth0のJWKS取得（Django Cacheでキャッシュ）
        キャッシュ戦略:
        - Django Cache使用（Redis）
        - 24時間キャッシュ（Auth0設定）
        - マルチプロセス環境で共有
        """
        cache_key = 'auth0_jwks'
        jwks = cache.get(cache_key)
        
        if not jwks:
            try:
                response = requests.get(self.jwks_url, timeout=10)
                response.raise_for_status()
                jwks = response.json()
                # 24時間キャッシュ
                cache.set(cache_key, jwks, 60 * 60 * 24)
                logger.info('Auth0 JWKS fetched and cached')
            except requests.RequestException as e:
                logger.error(f'Failed to fetch Auth0 JWKS: {e}')
                raise AuthenticationFailed('Failed to fetch JWKS')
        
        return jwks
    
    def authenticate(self, request):
        """
        JWT検証してユーザーを返す
        
        Returns:
            (user, None): 認証成功
            None: Authorizationヘッダーなし（他の認証方式にフォールバック）
        
        Raises:
            AuthenticationFailed: JWT検証失敗
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None  # 他の認証方式にフォールバック
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = self._verify_token(token)
            user = self._get_or_create_user(payload)
            return (user, None)
        except JoseError as e:
            error_msg = str(e).lower()
            if 'expired' in error_msg or 'exp' in error_msg:
                logger.warning(f'Token expired: {e}')
                raise TokenExpiredError()
            else:
                logger.warning(f'JWT verification failed: {e}')
                raise InvalidTokenError(internal_reason=str(e))
        except Exception as e:
            logger.error(f'Authentication error: {e}', exc_info=True)
            raise AuthenticationFailed(f'Authentication error: {str(e)}')
    
    def _verify_token(self, token):
        """
        joserfcによる厳格なJWT検証
        
        検証内容:
        - 署名検証（RS256）
        - 有効期限（exp）
        - 発行元（iss）
        - オーディエンス（aud）
        - 時刻ズレ許容（leeway=60秒）
        
        Args:
            token: JWT文字列（Access Token）
        
        Returns:
            dict: 検証済みペイロード（辞書として扱える）
        
        Raises:
            JoseError: JWT検証失敗
        """
        jwks = self.get_jwks()
        
        try:
            # 1. デコードと署名検証 (RS256固定)
            # kidの照合は joserfc が内部で自動実行します
            claims = jwt.decode(token, jwks, algorithms=['RS256'])
            
            # 2. クレーム検証 (exp, iss, aud をまとめてチェック)
            # leeway=60で時刻ズレを許容（サーバー間の時刻差対策）
            claims.validate(
                issuer=self.issuer,
                audience=self.audience,
                leeway=self.leeway
            )

            # claims は辞書のように扱える
            # claims.get('sub'), claims['email'] 等が可能
            return claims
        except Exception as e:
            # 有効期限切れ、発行元不一致、署名不正などはすべてここでキャッチ
            error_msg = str(e).lower()
            if 'expired' in error_msg or 'exp' in error_msg:
                raise TokenExpiredError()
            raise InvalidTokenError(internal_reason=str(e))
    
    @transaction.atomic
    def _get_or_create_user(self, payload):
        """
        ペイロードからユーザーを取得または作成（トランザクション保護）
        
        フロー:
        1. oidc_subで検索 → Auth0ユーザー（情報更新）
        2. emailで検索 → 既存Djangoユーザー（OIDC連携追加）
        3. 新規作成 → 新規Auth0ユーザー
        
        トランザクション:
        - 同時リクエストによるIntegrityError対策
        - select_for_update()でロック
        
        Args:
            payload: JWT payload（Access Token）
                {
                    "sub": "auth0|507f1f77bcf86cd799439011",
                    "email": "user@example.com",
                    "email_verified": true,
                    "given_name": "John",
                    "family_name": "Doe",
                    "scope": "openid profile email"
                }
        
        Returns:
            CustomUser: ユーザーインスタンス
        
        Raises:
            AuthenticationFailed: 必須情報が不足
        """
        oidc_sub = payload.get('sub')
        email = payload.get('email')
        
        if not oidc_sub or not email:
            raise InvalidTokenError(internal_reason='Missing user info in token')
        
        # 1. oidc_subで検索
        user = User.objects.filter(oidc_sub=oidc_sub).first()
        
        try:
            # 1. oidc_subで検索（Auth0ユーザー）
            # select_for_update()で排他ロック（同時更新対策）
            user = User.objects.select_for_update().filter(oidc_sub=oidc_sub).first()
            
            if user:
                # メールアドレスや名前が変更されている可能性があるので更新
                updated = False
                
                if user.email != email:
                    user.email = email
                    updated = True
                
                given_name = payload.get('given_name', '')
                family_name = payload.get('family_name', '')
                
                if user.first_name != given_name:
                    user.first_name = given_name
                    updated = True
                
                if user.last_name != family_name:
                    user.last_name = family_name
                    updated = True
                
                if updated:
                    user.save(update_fields=['email', 'first_name', 'last_name'])
                    logger.info(f'Updated user info for oidc_sub={oidc_sub}')
                
                return user
            
            # 2. emailで検索（既存Djangoユーザー）
            # select_for_update()で排他ロック
            user = User.objects.select_for_update().filter(email=email).first()
            
            if user:
                # OIDC連携を追加
                user.oidc_sub = oidc_sub
                user.first_name = payload.get('given_name', '') or user.first_name
                user.last_name = payload.get('family_name', '') or user.last_name
                user.save(update_fields=['oidc_sub', 'first_name', 'last_name'])
                logger.info(f'Linked existing user to oidc_sub={oidc_sub}')
                return user
            
            # 3. 新規ユーザー作成
            user = User.objects.create(
                oidc_sub=oidc_sub,
                email=email,
                first_name=payload.get('given_name', ''),
                last_name=payload.get('family_name', ''),
            )
            logger.info(f'Created new user with oidc_sub={oidc_sub}')
            return user
            
        except DjangoIntegrityError as e:
            error_msg = str(e).lower()
            
            # メールアドレス重複
            if 'unique' in error_msg and 'email' in error_msg:
                user = User.objects.filter(email=email).first()
                if user:
                    user.oidc_sub = oidc_sub
                    user.save(update_fields=['oidc_sub'])
                    return user
                raise IntegrityConstraintError(
                    constraint_type='unique_email',
                    user_hint='このメールアドレスは既に使用されています',
                    internal_details=str(e)  # ← 修正
                )
            
            # oidc_sub重複
            if 'unique' in error_msg and 'oidc_sub' in error_msg:
                user = User.objects.filter(oidc_sub=oidc_sub).first()
                if user:
                    return user
                raise IntegrityConstraintError(
                    constraint_type='unique_oidc_sub',
                    user_hint='認証情報の重複エラーが発生しました',
                    internal_details=str(e)  # ← 修正
                )
            
            # その他のIntegrityError
            raise IntegrityConstraintError(
                constraint_type='unknown',
                user_hint='データの整合性エラーが発生しました',
                internal_details=str(e)  # ← 修正
            )