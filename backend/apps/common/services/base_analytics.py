from apps.common.infrastructure.motherduck_client import MotherDuckClient
from apps.common.exceptions import AnalyticsError

class BaseAnalyticsService:
    """
    分析ログ記録の共通基盤
    MotherDuckClient の例外を AnalyticsError に翻訳し、
    データ挿入のインターフェースを抽象化する
    """
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = MotherDuckClient()
        return cls._client

    @classmethod
    def _safe_insert_auth(cls, event_data: dict):
        """認証イベント挿入の共通ラッパー"""
        try:
            client = cls.get_client()
            client.insert_auth_event(event_data)
        except Exception as e:
            # MotherDuck固有のエラーや接続エラーを翻訳
            raise AnalyticsError(
                message=f"MotherDuck auth log failed: {str(e)}",
                context={"event_type": event_data.get("event_type")}
            ) from e

    @classmethod
    def _safe_insert_todo(cls, event_data: dict):
        """Todoイベント挿入の共通ラッパー"""
        try:
            client = cls.get_client()
            client.insert_todo_event(event_data)
        except Exception as e:
            raise AnalyticsError(
                message=f"MotherDuck todo log failed: {str(e)}",
                context={"event_type": event_data.get("event_type")}
            ) from e