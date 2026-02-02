import logging

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from drf_spectacular.utils import extend_schema

from apps.common.permissions import IsQStashAuthenticated
from apps.common.error_decorators import log_webhook_call

from .serializers import AnalyticsEventWebhookSerializer
from .services import AnalyticsWebhookService


logger = logging.getLogger(__name__)

@extend_schema(
    summary="[内部API] 分析イベント記録",
    description="QStashから呼ばれる内部エンドポイント",
    request={
        'type': 'object',
        'properties': {
            'event_type': {'type': 'string'},
            'user_id': {'type': 'integer'},
            'event_data': {'type': 'object'},
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
            }
        },
    },
    tags=['Internal', 'Webhooks'],
    exclude=True  # 公開ドキュメントから除外
)
@api_view(["POST"])
@permission_classes([IsQStashAuthenticated])
@log_webhook_call(webhook_name="analytics_event")
def analytics_event_webhook(request):
    """
    分析イベントWebhook（QStashから呼ばれる）
    
    POST /api/v1/webhooks/analytics-event
    
    署名検証は IsQStashAuthenticated で自動処理。
    MotherDuckにイベントを記録。
    
    Payload:
        {
            "event_type": "auth_event",
            "event_data": {
                "user_id": 123,
                "event_type": "login",
                "timestamp": "2024-01-01T00:00:00Z",
                ...
            }
        }
    
    Returns:
        200: 成功
        400: バリデーションエラー
        500: 処理エラー（QStashが自動リトライ）
    
    Raises:
        ValidationError: バリデーションエラー（統一エラーハンドラーが処理）
        AnalyticsError: 分析サービスエラー（統一エラーハンドラーが処理）
    """
    # Serializerでバリデーション
    serializer = AnalyticsEventWebhookSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    event_type = serializer.validated_data['event_type']
    event_data = serializer.validated_data['event_data']

    AnalyticsWebhookService.handle_webhook_event(event_type, event_data)

    return Response({
        "message": "Event logged successfully",
        "event_type": event_type
    })