import logging

from apps.common.infrastructure.motherduck_client import MotherDuckClient
from apps.common.exceptions import AnalyticsError
from apps.common.error_decorators import service_error_handler

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    分析イベント記録サービス
    
    MotherDuckに分析データを送信
    """

    @staticmethod
    @service_error_handler
    def log_auth_event(
        user,
        event_type: str,
        request,
        success: bool = True,
        error_message: str = None
    ) -> None:
        """
        認証イベントをMotherDuckに記録

        Args:
            user: Userオブジェクト（Noneの場合あり）
            event_type: "login", "logout", "register", "login_failed"
            request: HTTPリクエスト
            success: 成功/失敗
            error_message: エラーメッセージ（失敗時）
            
        Raises:
            AnalyticsError: MotherDuck接続エラー時
        """
        event_data = {
            "user_id": user.id if user else None,
            "email": user.email if user else None,
            "event_type": event_type,
            "ip_address": AnalyticsService._get_client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:500],
            "success": success,
            "error_message": error_message,
        }

        try:
            client = MotherDuckClient()
            client.insert_auth_event(event_data)
        except Exception as e:
            # AnalyticsErrorに変換して再送出
            raise AnalyticsError(message=f"Failed to insert auth event: {str(e)}")

    @staticmethod
    def _get_client_ip(request):
        """
        クライアントIPアドレスを取得
        
        プロキシ経由の場合は X-Forwarded-For から取得
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # X-Forwarded-For: client, proxy1, proxy2
            # → 最初のIPがクライアント
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")