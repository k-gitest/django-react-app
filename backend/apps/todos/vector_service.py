import logging

from apps.common.services.base_vector import BaseVectorService
from apps.common.error_decorators import service_error_handler
from .embedding_service import TodoEmbeddingService


logger = logging.getLogger(__name__)


class VectorService(BaseVectorService):
    """
    Todoのベクトル検索サービス
    
    BaseVectorServiceを継承し、Todo固有のロジックを提供
    """

    def __init__(self):
        super().__init__()

    @service_error_handler
    def add_todo(self, todo):
        """
        Todoをベクトルインデックスに追加
        
        Raises:
            VectorError: ベクトルDB操作エラー時（Baseが投げる）
            EmbeddingError: ベクトル化エラー時
        """
        # テキスト準備
        text = TodoEmbeddingService.prepare_text(todo)
        
        # ベクトル化
        embedding = TodoEmbeddingService.embed_text(
            text, 
            task_type="retrieval_document"
        )
        
        # メタデータを含めて保存（Baseに委譲）
        vectors = [(
            str(todo.id),
            embedding,
            {
                "title": todo.todo_title,
                "user_id": todo.user.id,
                "priority": todo.priority,
                "progress": todo.progress,
                "created_at": todo.created_at.isoformat(),
            }
        )]
        
        self._safe_upsert(vectors, operation=f"add_todo_{todo.id}")

    @service_error_handler
    def update_todo(self, todo):
        """Todoをベクトルインデックスで更新"""
        self.delete_todo(todo.id)
        self.add_todo(todo)

    @service_error_handler
    def delete_todo(self, todo_id: int):
        """Todoをベクトルインデックスから削除"""
        self._safe_delete([str(todo_id)])

    @service_error_handler
    def search_similar(
        self, 
        query: str, 
        user_id: int, 
        top_k: int = 5, 
        min_score: float = 0.5
    ):
        """類似Todoをセマンティック検索"""
        # クエリをベクトル化
        query_embedding = TodoEmbeddingService.embed_text(
            query,
            task_type="retrieval_query"
        )
        
        # 検索（Baseに委譲）
        results = self._safe_query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=f"user_id = {user_id}"
        )
        
        # スコアでフィルタリング
        return [
            {
                "id": int(r.id),
                "score": r.score,
                "title": r.metadata["title"],
                "priority": r.metadata["priority"],
                "progress": r.metadata["progress"]
            }
            for r in results
            if r.score >= min_score
        ]

    @service_error_handler
    def add_todos_batch(self, todos):
        """複数のTodoを一括追加"""
        # テキストを一括準備
        texts = [TodoEmbeddingService.prepare_text(todo) for todo in todos]
        
        # バッチでベクトル化
        embeddings = TodoEmbeddingService.embed_batch(texts)
        
        # ベクトルデータ作成
        vectors = [
            (
                str(todo.id),
                embedding,
                {
                    "title": todo.todo_title,
                    "user_id": todo.user.id,
                    "priority": todo.priority,
                    "progress": todo.progress,
                    "created_at": todo.created_at.isoformat(),
                }
            )
            for todo, embedding in zip(todos, embeddings)
        ]
        
        # バッチ保存（Baseに委譲）
        self._safe_upsert(vectors, operation="batch_add")