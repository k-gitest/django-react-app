from django.urls import path
from users.views import send_welcome_email_webhook
from todos.views import vector_indexing_webhook, bulk_vector_indexing_webhook

urlpatterns = [
    # Users Webhooks
    path('send-welcome-email', send_welcome_email_webhook, name='webhook-welcome-email'),
    
    # Todos Webhooks
    path('vector-indexing', vector_indexing_webhook, name='webhook-vector-indexing'),
    path('bulk-vector-indexing', bulk_vector_indexing_webhook, name='webhook-bulk-vector-indexing'),
]