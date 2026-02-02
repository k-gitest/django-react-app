import logging

from django.conf import settings
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import LoginView, LogoutView

from apps.common.permissions import IsQStashAuthenticated
from apps.common.error_decorators import log_webhook_call

from .email_service import UserEmailService
from .user_service import UserAuthService
from .serializers import WelcomeEmailWebhookSerializer
from .rest_schemas import AuthSchemas, UserWebhookSchemas

logger = logging.getLogger(__name__)


# ============================================================================
# レート制限ヘルパー
# ============================================================================
def apply_ratelimit(**kwargs):
    """
    テスト環境ではレート制限をスキップするデコレーター
    
    本番環境でのみレート制限を適用し、テスト時は無効化
    """
    def decorator(func):
        if getattr(settings, "TESTING", False):
            return func
        return ratelimit(**kwargs)(func)
    return decorator


# ============================================================================
# 認証ビュー
# ============================================================================
@method_decorator(
    apply_ratelimit(key="ip", rate="5/5m", method="POST", block=True),
    name="dispatch"
)
class CustomLoginView(LoginView):
    """
    カスタムログインビュー
    
    機能:
        - レート制限（5回/5分）
        - JWT Cookie自動発行
        - 分析ログ記録（MotherDuck）
    
    エラーハンドリング:
        - 認証エラー: dj-rest-authが処理
        - 分析ログエラー: ErrorMonitor.capture_and_continueで隔離（UserAuthService内）
    """

    @AuthSchemas.login
    def post(self, request, *args, **kwargs):
        """
        ログイン処理
        
        成功時に分析ログを記録。
        エラーは統一エラーハンドラーが処理。
        """
        response = super().post(request, *args, **kwargs)

        # ログイン成功時のみ分析ログ記録
        if response.status_code == 200:
            user = self._get_user_from_response(response)
            if user:
                # 分析ログのエラーは UserAuthService._log_analytics_safely で隔離
                UserAuthService.handle_login_success(user, request)

        return response

    def _get_user_from_response(self, response):
        """
        レスポンスからユーザーオブジェクトを安全に取得
        
        Args:
            response: DRFレスポンスオブジェクト
        
        Returns:
            CustomUser or None
        """
        # self.userがある場合（dj-rest-authが設定）
        if hasattr(self, "user") and self.user:
            return self.user

        # self.userが無い場合、レスポンスデータから取得
        user_pk = response.data.get("user", {}).get("pk")
        if user_pk:
            from django.contrib.auth import get_user_model
            return get_user_model().objects.filter(pk=user_pk).first()

        return None


@method_decorator(
    apply_ratelimit(key="ip", rate="3/1h", method="POST", block=True),
    name="dispatch"
)
class CustomRegisterView(RegisterView):
    """
    カスタム登録ビュー
    
    機能:
        - レート制限（3回/1時間）
        - JWT Cookie自動発行
        - ウェルカムメール送信（QStash経由、非同期）
        - 分析ログ記録（MotherDuck、非同期）
    
    エラーハンドリング:
        - メールアドレス重複: UserAlreadyExistsError → 統一エラーハンドラーが処理
        - ウェルカムメール送信エラー: ErrorMonitor.capture_and_continueで隔離
        - 分析ログエラー: ErrorMonitor.capture_and_continueで隔離
    """

    @AuthSchemas.register
    def create(self, request, *args, **kwargs):
        """
        ユーザー登録処理
        
        JWT Cookieを自動設定。
        エラーは統一エラーハンドラーが処理。
        """
        response = super().create(request, *args, **kwargs)

        # JWT Cookieを設定
        if hasattr(self, "access_token") and hasattr(self, "refresh_token"):
            self._set_jwt_cookies(response, self.access_token, self.refresh_token)

        return response
        
    def perform_create(self, serializer):
        """
        ユーザー作成の実行
        
        Serializerのsave()メソッドを呼び出し、
        JWT トークンを生成。
        
        エラーは統一エラーハンドラーが処理するため、try-catchは不要。
        """
        # Serializer.save() → UserRegistrationService.register_user()
        # エラーは統一エラーハンドラーへ伝播
        user = serializer.save(self.request)
        self.user = user

        # JWT トークン生成
        refresh = RefreshToken.for_user(user)
        self.access_token = str(refresh.access_token)
        self.refresh_token = str(refresh)

        return user

    def _set_jwt_cookies(self, response, access_token, refresh_token):
        """
        JWTトークンをCookieに設定
        
        Args:
            response: DRFレスポンスオブジェクト
            access_token: アクセストークン
            refresh_token: リフレッシュトークン
        """
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

class CustomLogoutView(LogoutView):
    """
    カスタムログアウトビュー
    
    機能:
        - 分析ログ記録（MotherDuck）
    
    エラーハンドリング:
        - 分析ログエラー: ErrorMonitor.capture_and_continueで隔離
    """

    serializer_class = serializers.Serializer
    
    @AuthSchemas.logout 
    def post(self, request, *args, **kwargs):
        """
        ログアウト処理
        
        ログアウト前にユーザーを特定して分析ログを記録。
        エラーは統一エラーハンドラーが処理。
        """

        # ログアウト前にユーザーを特定して記録
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            # 分析ログのエラーは UserAuthService._log_analytics_safely で隔離
            UserAuthService.handle_logout(request)
        
        return super().post(request, *args, **kwargs)


# ============================================================================
# Webhook エンドポイント
# ============================================================================

@UserWebhookSchemas.send_welcome_email
@api_view(["POST"])
@permission_classes([IsQStashAuthenticated])
@log_webhook_call(webhook_name="send_welcome_email")
def send_welcome_email_webhook(request):
    """
    ウェルカムメール送信Webhook（QStashから呼ばれる）
    
    POST /api/v1/webhooks/send-welcome-email
    
    署名検証は IsQStashAuthenticated で自動処理。
    
    Payload:
        {
            "email": "user@example.com",
            "first_name": "John"
        }
    
    Returns:
        200: 成功
        400: バリデーションエラー
        500: メール送信エラー（QStashが自動リトライ）
    
    Raises:
        ValidationError: バリデーションエラー（統一エラーハンドラーが処理）
        EmailDeliveryError: メール送信エラー（統一エラーハンドラーが処理）
    """
    # Serializerでバリデーション
    serializer = WelcomeEmailWebhookSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    first_name = serializer.validated_data['first_name']

    # メール送信（エラーは統一エラーハンドラーが処理）
    message_id = UserEmailService.send_welcome_email(email, first_name)

    return Response({
        "message": "Email sent successfully",
        "message_id": message_id
    })
