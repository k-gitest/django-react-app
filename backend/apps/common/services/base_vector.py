import logging

from apps.common.infrastructure.vector_client import VectorClient
from apps.common.exceptions import VectorError


logger = logging.getLogger(__name__)


class BaseVectorService:
    """
    ベクトル操作の共通基盤
    VectorClient の例外を VectorError に翻訳する
    """
    _client = None

    @classmethod
    def get_client(cls):
        """シングルトンパターンでクライアントを取得"""
        if cls._client is None:
            cls._client = VectorClient()
        return cls._client

    @classmethod
    def _safe_upsert(cls, vectors: list, operation: str = "upsert"):
        """
        安全なベクトル挿入/更新
        
        Raises:
            VectorError: 操作失敗時
        """
        try:
            client = cls.get_client()
            client.upsert(vectors)
            logger.info(f"Vector {operation} successful: {len(vectors)} vectors")
        except VectorError:
            raise
        except Exception as e:
            logger.error(f"Vector {operation} failed: {e}")
            raise VectorError(
                internal_details=str(e)
            ) from e

    @classmethod
    def _safe_delete(cls, ids: list[str]):
        """
        安全なベクトル削除
        
        Raises:
            VectorError: 削除失敗時
        """
        try:
            client = cls.get_client()
            client.delete(ids)
            logger.info(f"Vector delete successful: {len(ids)} vectors")
        except VectorError:
            raise
        except Exception as e:
            logger.error(f"Vector delete failed: {e}")
            raise VectorError(
                internal_details=str(e)
            ) from e

    @classmethod
    def _safe_query(
        cls,
        vector: list[float],
        top_k: int = 5,
        include_metadata: bool = True,
        filter: str = None
    ):
        """
        安全なベクトル検索
        
        Raises:
            VectorError: 検索失敗時
        """
        try:
            client = cls.get_client()
            return client.query(
                vector=vector,
                top_k=top_k,
                include_metadata=include_metadata,
                filter=filter
            )
        except VectorError:
            raise
        except Exception as e:
            logger.error(f"Vector query failed: {e}")
            raise VectorError(
                internal_details=str(e)
            ) from e