from django.urls import path, include
from . import views
from .views import CustomLoginView, CustomRegisterView

urlpatterns = [
    # カスタムビュー
    path('login/', CustomLoginView.as_view(), name='rest_login'),
    path('registration/', CustomRegisterView.as_view(), name='rest_register'),

    # その他のdj_rest_authエンドポイント（logout, user, token/refreshなど）
    path('', include('dj_rest_auth.urls')),

    # Webhook エンドポイント
    path('send-welcome-email', views.send_welcome_email_webhook, name='webhook-welcome-email'),

    # 将来の拡張例:
    # path('password-reset-notification', views.password_reset_webhook, name='webhook-password-reset'),
    # path('todo-reminder', views.todo_reminder_webhook, name='webhook-todo-reminder'),
]