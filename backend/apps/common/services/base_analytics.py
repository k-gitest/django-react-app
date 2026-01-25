import logging
from typing import Literal
from apps.common.infrastructure.motherduck_client import MotherDuckClient
from apps.common.exceptions import AnalyticsError

logger = logging.getLogger(__name__)

EventType = Literal["auth", "todo"]

class BaseAnalyticsService:
    """
    分析ログ記録の共通基盤
    MotherDuckClient の例外を AnalyticsError に翻訳する
    """
    _client = None

    @classmethod
    def get_client(cls):
        """シングルトンパターンでクライアントを取得"""
        if cls._client is None:
            cls._client = MotherDuckClient()
        return cls._client

    @classmethod
    def _safe_insert(
        cls, 
        event_type: EventType,
        event_data: dict
    ):
        """
        イベント挿入の共通ラッパー
        
        Args:
            event_type: イベントの種類（"auth" or "todo"）
            event_data: イベントデータ
            
        Raises:
            AnalyticsError: MotherDuck挿入失敗時
        """
        try:
            client = cls.get_client()
            
            if event_type == "auth":
                client.insert_auth_event(event_data)
            elif event_type == "todo":
                client.insert_todo_event(event_data)
            else:
                raise ValueError(f"Unknown event_type: {event_type}")
            
            logger.debug(f"Analytics logged: {event_type} - {event_data.get('event_type')}")
            
        except AnalyticsError:
            raise
        except Exception as e:
            logger.warning(f"MotherDuck {event_type} log failed: {str(e)}")
            raise AnalyticsError(
                message=f"MotherDuck {event_type} log failed: {str(e)}",
                context={
                    "event_type": event_data.get("event_type"),
                    "category": event_type
                }
            ) from e