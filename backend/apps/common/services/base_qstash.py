from typing import Final, Union
from apps.common.infrastructure.qstash_client import QStashClient
from apps.common.exceptions import QStashError

class BaseQStashService:
    """
    QStash操作の共通基盤
    Client層の例外をQStashErrorに翻訳する責務を持つ
    """
    
    @classmethod
    def _safe_publish(
        cls, 
        endpoint_path: str, 
        payload: dict, 
        delay_seconds: int = 0
    ) -> str:
        """
        共通の送信ロジック（エラー変換を担当）
        
        Args:
            endpoint_path: Webhook相対パス
            payload: 送信データ
            delay_seconds: 遅延実行（秒）
        
        Returns:
            str: message_id
            
        Raises:
            QStashError: 送信失敗時
        """
        try:
            message_id = QStashClient.publish(endpoint_path, payload, delay_seconds)
            
            # QStashClientは成功時に message_id (str) を返す設計
            if not message_id or not isinstance(message_id, str):
                raise QStashError(
                    message="Invalid response from QStash client",
                    endpoint=endpoint_path
                )
            
            return message_id
            
        except QStashError:
            raise
        except Exception as e:
            raise QStashError(
                message=f"QStash operation failed: {str(e)}",
                endpoint=endpoint_path
            ) from e