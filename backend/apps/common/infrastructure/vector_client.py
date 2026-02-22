from upstash_vector import Index
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class VectorClient:
    """
    Upstash Vector操作の技術層
    
    Indexインスタンスの管理と基本的なCRUD操作を提供
    """
    _instance = None
    _index = None

    def __new__(cls):
        """シングルトンパターン"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Indexインスタンスを初期化（一度だけ）"""
        if self._index is None:
            self._index = Index(
                url=settings.UPSTASH_VECTOR_REST_URL,
                token=settings.UPSTASH_VECTOR_REST_TOKEN
            )

    @classmethod
    def reset_for_testing(cls):
        """
        テスト用のリセットメソッド
        
        """
        cls._instance = None
        cls._index = None
        logger.debug("VectorClient reset for testing")

    def upsert(self, vectors: list) -> None:
        """
        ベクトルを挿入/更新
        
        Args:
            vectors: [(id, embedding, metadata), ...]
            
        Raises:
            Exception: Upstash Vector APIエラー（そのまま投げる）
        """
        self._index.upsert(vectors=vectors)

    def delete(self, ids: list[str]) -> None:
        """
        ベクトルを削除
        
        Args:
            ids: 削除対象のIDリスト
            
        Raises:
            Exception: Upstash Vector APIエラー（そのまま投げる）
        """
        self._index.delete(ids=ids)

    def query(
        self, 
        vector: list[float], 
        top_k: int = 5,
        include_metadata: bool = True,
        filter: str = None
    ):
        """
        ベクトル検索
        
        Args:
            vector: クエリベクトル
            top_k: 返す結果の最大数
            include_metadata: メタデータを含めるか
            filter: フィルタ条件
            
        Returns:
            検索結果
            
        Raises:
            Exception: Upstash Vector APIエラー（そのまま投げる）
        """
        return self._index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=include_metadata,
            filter=filter
        )