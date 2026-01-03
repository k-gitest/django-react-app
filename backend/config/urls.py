from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from users.views import CustomRegisterView

def health_check(request):
    # status=200 を明示的に返す（curl -f は 200番台を成功とみなすため）
    return JsonResponse({'status': 'healthy', 'service': 'backend'}, status=200)

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

    # TODOアプリエンドポイント
    # GET /api/v1/todos/: 一覧取得
    # POST /api/v1/todos/: 新規作成
    # PUT/PATCH /api/v1/todos/{id}/: 更新
    # DELETE /api/v1/todos/{id}/: 削除
    path('api/v1/todos/', include('todos.urls')),

    # CIでのhealth-checkエンドポイント
    path('api/v1/health/', health_check, name='health_check'),
]
