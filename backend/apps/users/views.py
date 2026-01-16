import logging
import subprocess

from apps.common.infrastructure.motherduck_client import MotherDuckClient
from apps.common.permissions import IsQStashAuthenticated
from apps.common.error_decorators import log_webhook_call
from apps.common.exceptions import EmailDeliveryError, AnalyticsError

from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import LoginView, LogoutView
from django.conf import settings
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .email_service import UserEmailService
from .user_service import UserAuthService

logger = logging.getLogger(__name__)


# レート制限デコレーター（テスト時は無効化）
def apply_ratelimit(**kwargs):
    """テスト環境ではレート制限をスキップ"""

    def decorator(func):
        if getattr(settings, "TESTING", False):
            return func
        return ratelimit(**kwargs)(func)

    return decorator


@method_decorator(
    apply_ratelimit(key="ip", rate="5/5m", method="POST", block=True), name="dispatch"
)
class CustomLoginView(LoginView):
    """
    カスタムログインビュー

    - レート制限（5回/5分）
    - JWT Cookie自動発行
    - 分析ログ記録（MotherDuck）
    """

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        # ログイン成功時のみ分析ログ記録
        if response.status_code == 200:
            # ユーザーオブジェクトを取得
            user = self._get_user_from_response(response)
            if user:
                UserAuthService.handle_login_success(user, request)

        return response

    def _get_user_from_response(self, response):
        # self.userがある場合
        if hasattr(self, "user") and self.user:
            return self.user

        # self.userが無い場合
        # レスポンスデータからPKを安全に抽出（初期値は空オブジェクト、欠損時はエラーではなくNoneにする）
        user_pk = response.data.get("user", {}).get("pk")
        # PKがあればDBから取得（filter().first() で安全に）
        if user_pk:
            from django.contrib.auth import get_user_model
            # pkなしでもnoneを返す
            return get_user_model().objects.filter(pk=user_pk).first()

        return None


@method_decorator(
    apply_ratelimit(key="ip", rate="3/1h", method="POST", block=True), name="dispatch"
)
class CustomRegisterView(RegisterView):
    """
    カスタム登録ビュー

    - レート制限（3回/1時間）
    - JWT Cookie自動発行
    - ウェルカムメール送信（QStash経由）
    - 分析ログ記録（MotherDuck）
    """

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)

        if hasattr(self, "access_token") and hasattr(self, "refresh_token"):
            self._set_jwt_cookies(response, self.access_token, self.refresh_token)

        return response
        
    def perform_create(self, serializer):
        user = serializer.save(self.request)
        self.user = user

        refresh = RefreshToken.for_user(user)
        self.access_token = str(refresh.access_token)
        self.refresh_token = str(refresh)

        return user

    def _set_jwt_cookies(self, response, access_token, refresh_token):
        """JWTトークンをCookieに設定"""
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
    def logout(self, request):
        # ログアウト前にユーザーを特定して記録
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            # 引数から use_async=True を削除して呼び出す
            UserAuthService.handle_logout(request)
        return super().logout(request)


# ============================================================================
# Webhook エンドポイント
# ============================================================================

@api_view(["POST"])
@permission_classes([IsQStashAuthenticated])
@log_webhook_call(webhook_name="send_welcome_email")
def send_welcome_email_webhook(request):
    """
    QStashから呼び出されるWebhook
    ウェルカムメールを実際に送信する
    """
    email = request.data.get("email")
    first_name = request.data.get("first_name")

    if not email or not first_name:
        return Response(
            {
                "error": "validation_error",
                "detail": "email と first_name は必須です"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        result = UserEmailService.send_welcome_email(email, first_name)
        
        if not result["success"]:
            raise EmailDeliveryError(
                message=result.get('error', 'Unknown error'),
                email=email
            )
        
        return Response(
            {"message": "Email sent successfully", "id": result["id"]},
            status=status.HTTP_200_OK
        )
        
    except EmailDeliveryError:
        # デコレーターがログ済み、DRFエラーハンドラーへ委譲
        raise


@api_view(["POST"])
@permission_classes([IsQStashAuthenticated])
@log_webhook_call(webhook_name="analytics_event")
def analytics_event_webhook(request):
    """
    QStashから呼ばれる分析イベントWebhook

    MotherDuckにイベントを記録
    """
    event_type = request.data.get("event_type")
    event_data = request.data.get("event_data")

    if not event_type or not event_data:
        return Response(
            {
                "error": "validation_error",
                "detail": "event_type と event_data は必須です"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        client = MotherDuckClient()

        if event_type == "auth_event":
            client.insert_auth_event(event_data)
        else:
            return Response(
                {
                    "error": "validation_error",
                    "detail": f"Unknown event_type: {event_type}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"message": "Event logged successfully", "event_type": event_type}
        )

    except Exception as e:
        raise AnalyticsError(message=str(e))


@api_view(["POST"])
@permission_classes([IsQStashAuthenticated])
@log_webhook_call(webhook_name="dlt_pipeline")
def dlt_pipeline_webhook(request):
    """
    QStashから呼ばれるdltパイプライン実行Webhook

    15分ごとにQStashから呼ばれ、PostgreSQL → MotherDuck 同期を実行
    """

    try:
        # dltパイプラインを実行
        result = subprocess.run(
            ["python", "manage.py", "run_pipeline"],
            capture_output=True,
            text=True,
            timeout=300,  # 5分タイムアウト
        )

        if result.returncode == 0:
            logger.info("dlt pipeline executed successfully")
            logger.info(f"Output: {result.stdout}")

            return Response(
                {
                    "status": "success",
                    "message": "Pipeline executed successfully",
                    "output": result.stdout[-500:],  # 最後の500文字のみ返す
                }
            )
        else:
            logger.error(f"dlt pipeline failed: {result.stderr}")

            return Response(
                {
                    "status": "error",
                    "message": "Pipeline execution failed",
                    "error": result.stderr[-500:],
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except subprocess.TimeoutExpired:
        logger.error("dlt pipeline timeout (5 minutes)")

        return Response(
            {"status": "error", "message": "Pipeline execution timeout (5 minutes)"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    except Exception as e:
        logger.exception("dlt pipeline error")
        raise
