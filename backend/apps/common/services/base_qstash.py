from typing import Final
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
        
        Returns:
            str: message_id
            
        Raises:
            QStashError: 送信失敗時
        """
        try:
            result = QStashClient.publish(endpoint_path, payload, delay_seconds)
            
            # Clientが辞書を返す場合のエラー判定
            if isinstance(result, dict) and not result.get("success"):
                raise QStashError(
                    message=result.get("error", "Unknown error"),
                    endpoint=endpoint_path
                )
            
            # 成功時はIDを返す
            return result.get("messageId") if isinstance(result, dict) else result
            
        except Exception as e:
            # すでにQStashErrorならそのまま投げる
            if isinstance(e, QStashError):
                raise
            # 生の例外を from e で連結して翻訳
            raise QStashError(
                message=f"QStash operation failed: {str(e)}",
                endpoint=endpoint_path
            ) from e