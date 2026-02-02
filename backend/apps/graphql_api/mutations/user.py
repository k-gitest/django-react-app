"""
GraphQL User Mutation定義
認証（ログイン・ログアウト・登録）の実装
"""
import strawberry
from typing import Union
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.user_service import UserRegistrationService
from apps.users.models import CustomUser
from apps.graphql_api.types.user import (
    AuthPayload,
    RegisterInput,
    LoginInput,
    ChangePasswordInput,
    AuthResult,
    LogoutResult,
    ChangePasswordResult,
)
from apps.graphql_api.types.common import (
    ValidationError,
    ConflictError,
    AuthenticationError,
    Success,
)
from apps.graphql_api.validators import UserValidator
from apps.graphql_api.errors.handlers import graphql_error_handler
from apps.graphql_api.permissions import IsAuthenticated


@strawberry.type
class UserMutation:
    """
    User関連のMutation定義
    
    認証機能:
        - register: ユーザー登録
        - login: ログイン
        - logout: ログアウト
        - change_password: パスワード変更
    """
    
    @strawberry.mutation
    @graphql_error_handler
    def register(
        self,
        info: strawberry.Info,
        input: RegisterInput
    ) -> AuthResult:
        """
        ユーザー登録
        
        Mutation例:
        mutation {
          register(input: {
            email: "user@example.com"
            password: "securepass123"
            passwordConfirm: "securepass123"
            firstName: "太郎"
            lastName: "山田"
          }) {
            ... on AuthPayload {
              user {
                id
                email
                fullName
              }
              message
            }
            ... on ValidationError {
              field
              message
              code
            }
            ... on ConflictError {
              message
              conflictingField
            }
          }
        }
        
        Note:
            - JWT CookieはHTTPレスポンスに自動設定される
            - ウェルカムメールは非同期送信（UserRegistrationService内）
        
        Returns:
            AuthResult = AuthPayload | ValidationError | ConflictError | ...
        """
        # バリデーション
        validation_errors = UserValidator.validate_register(input)
        if validation_errors:
            return validation_errors[0]
        
        # ユーザー登録（Service層）
        registration_service = UserRegistrationService()
        user_data = {
            'email': input.email,
            'password': input.password,
            'first_name': input.first_name,
            'last_name': input.last_name,
        }
        
        user = registration_service.register_user(
            request=info.context.request,
            user_data=user_data
        )
        
        # JWT Cookie設定
        self._set_jwt_cookies(info.context.response, user)
        
        return AuthPayload(user=user, message="登録が完了しました")
    
    @strawberry.mutation
    @graphql_error_handler
    def login(
        self,
        info: strawberry.Info,
        input: LoginInput
    ) -> AuthResult:
        """
        ログイン
        
        Mutation例:
        mutation {
          login(input: {
            email: "user@example.com"
            password: "securepass123"
          }) {
            ... on AuthPayload {
              user {
                id
                email
              }
              message
            }
            ... on ValidationError {
              message
              field
            }
          }
        }
        
        Note:
            - JWT CookieはHTTPレスポンスに自動設定される
            - 分析ログは UserAuthService.handle_login_success で記録
        
        Returns:
            AuthResult = AuthPayload | ValidationError | ...
        """
        # バリデーション
        validation_errors = UserValidator.validate_login(input)
        if validation_errors:
            return validation_errors[0]
        
        # 認証
        user = authenticate(
            request=info.context.request,
            username=input.email,  # CustomUserはemailをusernameとして使用
            password=input.password
        )
        
        if not user:
            return ValidationError(
                message="メールアドレスまたはパスワードが正しくありません。",
                code="invalid_credentials"
            )
        
        # JWT Cookie設定
        self._set_jwt_cookies(info.context.response, user)
        
        # 分析ログ記録（非同期、失敗してもエラーを投げない）
        from apps.users.user_service import UserAuthService
        UserAuthService.handle_login_success(user, info.context.request)
        
        return AuthPayload(user=user, message="ログインしました")
    
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    @graphql_error_handler
    def logout(self, info: strawberry.Info) -> LogoutResult:
        """
        ログアウト
        
        Mutation例:
        mutation {
          logout {
            ... on Success {
              message
              success
            }
          }
        }
        
        Note:
            - JWT Cookieを削除
            - Refresh Tokenをブラックリスト化
        
        Returns:
            LogoutResult = Success | AuthenticationError | ...
        """
        user = info.context.request.user
        
        # Refresh Tokenをブラックリスト化
        try:
            refresh_token = info.context.request.COOKIES.get(
                settings.REST_AUTH.get("JWT_AUTH_REFRESH_COOKIE", "refresh-token")
            )
            
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            # ブラックリスト化失敗は無視（Cookie削除は実行）
            pass
        
        # Cookie削除
        self._clear_jwt_cookies(info.context.response)
        
        # 分析ログ記録（非同期、失敗してもエラーを投げない）
        from apps.users.user_service import UserAuthService
        UserAuthService.handle_logout(info.context.request)
        
        return Success(message="ログアウトしました")
    
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    @graphql_error_handler
    def change_password(
        self,
        info: strawberry.Info,
        input: ChangePasswordInput
    ) -> ChangePasswordResult:
        """
        パスワード変更
        
        Mutation例:
        mutation {
          changePassword(input: {
            oldPassword: "oldpass123"
            newPassword: "newpass456"
            newPasswordConfirm: "newpass456"
          }) {
            ... on Success {
              message
            }
            ... on ValidationError {
              field
              message
            }
          }
        }
        
        Returns:
            ChangePasswordResult = Success | ValidationError | ...
        """
        user = info.context.request.user
        
        # バリデーション
        validation_errors = UserValidator.validate_change_password(input, user)
        if validation_errors:
            return validation_errors[0]
        
        # パスワード変更
        from apps.users.user_service import UserCommandService
        UserCommandService.change_password(user, input.new_password)
        
        return Success(message="パスワードを変更しました")
    
    # ===== ヘルパーメソッド =====
    
    @staticmethod
    def _set_jwt_cookies(response, user: CustomUser):
        """
        JWT トークンをCookieに設定
        
        Args:
            response: DRF Response or GraphQL Response
            user: CustomUser インスタンス
        """
        # JWT トークン生成
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Cookie設定
        cookie_settings = {
            "httponly": settings.REST_AUTH.get("JWT_AUTH_HTTPONLY", True),
            "secure": settings.REST_AUTH.get("JWT_AUTH_SECURE", False),
            "samesite": settings.REST_AUTH.get("JWT_AUTH_SAMESITE", "Lax"),
            "path": "/",
        }
        
        response.set_cookie(
            key=settings.REST_AUTH.get("JWT_AUTH_COOKIE", "access-token"),
            value=access_token,
            max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
            **cookie_settings,
        )
        
        response.set_cookie(
            key=settings.REST_AUTH.get("JWT_AUTH_REFRESH_COOKIE", "refresh-token"),
            value=refresh_token,
            max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
            **cookie_settings,
        )
    
    @staticmethod
    def _clear_jwt_cookies(response):
        """
        JWT CookieをクリアV
        
        Args:
            response: DRF Response or GraphQL Response
        """
        response.delete_cookie(
            key=settings.REST_AUTH.get("JWT_AUTH_COOKIE", "access-token"),
            path="/"
        )
        
        response.delete_cookie(
            key=settings.REST_AUTH.get("JWT_AUTH_REFRESH_COOKIE", "refresh-token"),
            path="/"
        )