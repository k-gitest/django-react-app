import logging

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from drf_spectacular.utils import extend_schema

from apps.common.permissions import IsQStashAuthenticated
from apps.common.error_decorators import log_webhook_call
from apps.common.exceptions import EmailDeliveryError, AnalyticsError
from .services import DltPipelineService

logger = logging.getLogger(__name__)

@extend_schema(
    summary="[内部API] DLTパイプライン実行",
    description="QStashから呼ばれる内部エンドポイント",
    request=None,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'pipeline_result': {'type': 'object'},
            }
        },
    },
    tags=['Internal', 'Webhooks'],
    exclude=True
)
@api_view(["POST"])
@permission_classes([IsQStashAuthenticated])
@log_webhook_call(webhook_name="dlt_pipeline")
def dlt_pipeline_webhook(request):
    """
    dltパイプライン実行Webhook（QStashから呼ばれる）
    
    POST /api/v1/webhooks/dlt-pipeline
    
    署名検証は IsQStashAuthenticated で自動処理。
    15分ごとにQStashから呼ばれ、PostgreSQL → MotherDuck 同期を実行。
    
    **変更点**:
    - subprocessを削除
    - Service層を直接呼び出し（メモリ効率向上）
    - タイムアウトはQStash側で管理（5-10分に設定推奨）
    
    Returns:
        200: 成功
        500: 処理エラー（QStashが自動リトライ）
    
    Raises:
        AnalyticsError: パイプライン実行エラー（統一エラーハンドラーが処理）
    """
    result = DltPipelineService.execute_postgres_to_motherduck()
    
    return Response({
        "status": "success",
        "message": "Pipeline executed successfully",
        "synced_tables": result["tables"],
    })