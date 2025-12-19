from django.contrib import admin
from django.urls import path, include
from users.views import CustomRegisterView

urlpatterns = [
    path("admin/", admin.site.urls),

    # dj-rest-auth認証エンドポイント
    # - POST /api/v1/auth/login/          → ログイン
    # - POST /api/v1/auth/logout/         → ログアウト
    # - POST /api/v1/auth/token/refresh/  → トークンリフレッシュ
    # - GET  /api/v1/auth/user/           → 現在のユーザー情報取得
    path('api/v1/auth/', include('dj_rest_auth.urls')),
    
    # ユーザー登録
    # - POST /api/v1/auth/registration/   → 新規登録
    # path('api/v1/auth/registration/', include('dj_rest_auth.registration.urls')),
    # dj-rest-auth標準の include では、登録成功時に JWT Cookie が Set-Cookie されないため、
    # 登録と同時にログイン状態を確立できるよう CustomRegisterView を使用する。
    path('api/v1/auth/registration/', CustomRegisterView.as_view(), name='rest_register'),
]
