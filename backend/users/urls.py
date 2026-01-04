from django.urls import path
from . import views

urlpatterns = [
    # Webhook エンドポイント
    path('send-welcome-email', views.send_welcome_email_webhook, name='webhook-welcome-email'),

    # 将来の拡張例:
    # path('password-reset-notification', views.password_reset_webhook, name='webhook-password-reset'),
    # path('todo-reminder', views.todo_reminder_webhook, name='webhook-todo-reminder'),
]