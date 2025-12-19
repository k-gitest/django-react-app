from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import LoginView
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings


class CustomRegisterView(RegisterView):
    """
    新規登録時にJWT CookieをSet-Cookieヘッダーに設定
    """
    def perform_create(self, serializer):
        """
        ユーザー作成時に呼ばれるメソッド
        作成したユーザーをインスタンス変数に保存
        """
        user = serializer.save(self.request)
        self.user = user  # ここで保存

        # ここでトークンを生成し、Viewのインスタンスプロパティとして保持させる
        # dj-rest-authの内部でこれらを参照するロジックがあるため
        refresh = RefreshToken.for_user(user)
        self.access_token = str(refresh.access_token)
        self.refresh_token = str(refresh)

        return user
    
    def create(self, request, *args, **kwargs):
        # response = super().create(request, *args, **kwargs)
        response = super().create(request, *args, **kwargs)
        
        # トークンが存在する場合のみCookieをセット
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
        
        # Access Token
        response.set_cookie(
            key=settings.REST_AUTH.get('JWT_AUTH_COOKIE', 'access-token'),
            value=access_token,
            max_age=int(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()),
            **cookie_settings
        )
        
        # Refresh Token
        response.set_cookie(
            key=settings.REST_AUTH.get('JWT_AUTH_REFRESH_COOKIE', 'refresh-token'),
            value=refresh_token,
            max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
            **cookie_settings
        )