"""
Analytics Webhook Service - Webhook経路専用の分析イベント処理

ユーザー操作からの分析ログ（users/analytics_service.py, todos/analytics_service.py）とは別経路。
QStashから送られてきた既に整形済みのイベントデータをMotherDuckに記録する。
"""

import logging
from apps.common.services.base_analytics import BaseAnalyticsService
from apps.common.error_decorators import service_error_handler
from apps.common.exceptions import AnalyticsError

logger = logging.getLogger(__name__)


class AnalyticsWebhookService(BaseAnalyticsService):
    """
    Webhook経由の分析イベント記録サービス
    
    BaseAnalyticsServiceを継承し、Webhook固有のロジックを担当。
    ユーザー操作経路（users/analytics_service.py, todos/analytics_service.py）とは別。
    """

    @classmethod
    @service_error_handler
    def handle_webhook_event(cls, event_type: str, event_data: dict) -> None:
        """
        Webhookから受け取った分析イベントを処理
        
        Args:
            event_type: "auth_event" | "todo_event"
            event_data: 既に整形済みのイベントデータ
        
        Raises:
            AnalyticsError: サポートされていないイベントタイプ
        """
        if event_type == "auth_event":
            cls._safe_insert("auth", event_data)
        elif event_type == "todo_event":
            cls._safe_insert("todo", event_data)
        else:
            # この分岐は実際には来ない（Serializerでバリデーション済み）
            # 将来的に新しいイベントタイプが追加された場合のフォールバック
            raise AnalyticsError(
                message=f"Unsupported event_type: {event_type}",
                context={"event_type": event_type}
            )