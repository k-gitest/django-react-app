from apps.todos.views import bulk_vector_indexing_webhook, vector_indexing_webhook
from apps.users.views import (
    analytics_event_webhook,
    dlt_pipeline_webhook,
    send_welcome_email_webhook,
)
from django.urls import path

urlpatterns = [
    # Users Webhooks
    path(
        "send-welcome-email", send_welcome_email_webhook, name="webhook-welcome-email"
    ),
    path("analytics-event", analytics_event_webhook, name="webhook-analytics-event"),
    path("dlt-pipeline", dlt_pipeline_webhook, name="webhook-dlt-pipeline"),
    # Todos Webhooks
    path("vector-indexing", vector_indexing_webhook, name="webhook-vector-indexing"),
    path(
        "bulk-vector-indexing",
        bulk_vector_indexing_webhook,
        name="webhook-bulk-vector-indexing",
    ),
]
