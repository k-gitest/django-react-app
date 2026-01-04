from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import LoginView
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .email_service import EmailService
from .qstash_service import QStashService
import hmac
import hashlib


# テスト環境かどうかをチェック
def is_testing():
    """テスト環境かどうかを判定"""
    return getattr(settings, 'TESTING', False)


# レート制限デコレーター（テスト時は無効化）
def apply_ratelimit(**kwargs):
    """テスト環境ではレート制限をスキップ"""
    def decorator(func):
        if is_testing():
            return func
        return ratelimit(**kwargs)(func)
    return decorator


@method_decorator(apply_ratelimit(key='ip', rate='5/5m', method='POST', block=True), name='dispatch')
class CustomLoginView(LoginView):
    """ログイン試行を5分間に5回までに制限"""
    pass


@method_decorator(apply_ratelimit(key='ip', rate='3/1h', method='POST', block=True), name='dispatch')
class CustomRegisterView(RegisterView):
    """
    新規登録時にJWT CookieをSet-Cookieヘッダーに設定
    レート制限: 1時間に3回まで
    ウェルカムメール送信（QStash経由）
    """
    
    def perform_create(self, serializer):
        user = serializer.save(self.request)
        self.user = user

        refresh = RefreshToken.for_user(user)
        self.access_token = str(refresh.access_token)
        self.refresh_token = str(refresh)

        # テスト環境ではメール送信をスキップ
        if not is_testing():
            QStashService.send_welcome_email_async(
                email=user.email,
                first_name=user.first_name or "User"
            )

        return user
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        
        if hasattr(self, 'access_token') and hasattr(self, 'refresh_token'):
            self._set_jwt_cookies(response, self.access_token, self.refresh_token)
        
        return response
            
    def _set_jwt_cookies(self, response, access_token, refresh_token):
        """JWTトークンをCookieに設定"""
        cookie_settings = {
            'httponly': settings.REST_AUTH.get('JWT_AUTH_HTTPONLY', True),
            'secure': settings.REST_AUTH.get('JWT_AUTH_SECURE', False),
            'samesite': settings.REST_AUTH.get('JWT_AUTH_SAMESITE', 'Lax'),
            'path': '/',
        }
        
        response.set_cookie(
            key=settings.REST_AUTH.get('JWT_AUTH_COOKIE', 'access-token'),
            value=access_token,
            max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
            **cookie_settings
        )
        
        response.set_cookie(
            key=settings.REST_AUTH.get('JWT_AUTH_REFRESH_COOKIE', 'refresh-token'),
            value=refresh_token,
            max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
            **cookie_settings
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def send_welcome_email_webhook(request):
    """
    QStashから呼び出されるWebhook
    ウェルカムメールを実際に送信する
    """
    
    if not _verify_qstash_signature(request):
        return Response(
            {"error": "Invalid signature"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    email = request.data.get("email")
    first_name = request.data.get("first_name")
    
    if not email or not first_name:
        return Response(
            {"error": "Missing required fields"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    result = EmailService.send_welcome_email(email, first_name)
    
    if result["success"]:
        return Response(
            {"message": "Email sent successfully", "id": result["id"]},
            status=status.HTTP_200_OK
        )
    else:
        return Response(
            {"error": result["error"]},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _verify_qstash_signature(request):
    """QStashからのリクエストを署名検証"""
    signature = request.headers.get("Upstash-Signature")
    
    if not signature:
        return False
    
    parts = signature.split(",")
    signatures = {}
    for part in parts:
        key, value = part.split("=")
        signatures[key] = value
    
    body = request.body
    
    current_signature = hmac.new(
        settings.QSTASH_CURRENT_SIGNING_KEY.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    next_signature = hmac.new(
        settings.QSTASH_NEXT_SIGNING_KEY.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return (signatures.get("v1") == current_signature or 
            signatures.get("v1") == next_signature)