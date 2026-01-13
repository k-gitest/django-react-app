# backend/todos/vector_service.py
from upstash_vector import Index
from django.conf import settings
from .embedding_service import EmbeddingService
import logging

logger = logging.getLogger(__name__)


class VectorService:
    """
    Upstash Vectorを使用したベクトル検索サービス
    
    Todoのセマンティック検索機能を提供
    - 類似タスクの検索
    - 自然言語クエリでの検索
    """

    def __init__(self):
        self.index = Index(
            url=settings.UPSTASH_VECTOR_REST_URL,
            token=settings.UPSTASH_VECTOR_REST_TOKEN
        )
        self.embedding_service = EmbeddingService()
    
    def add_todo(self, todo):
        """
        Todoをベクトルインデックスに追加
        
        Args:
            todo: Todoモデルインスタンス
        
        Raises:
            Exception: ベクトルDB操作エラー時
        """
        try:
            # テキスト準備
            text = EmbeddingService.prepare_text(todo)
            
            # ベクトル化（document用）
            embedding = self.embedding_service.embed_text(
                text, 
                task_type="retrieval_document"
            )
            
            # メタデータを含めて保存
            self.index.upsert(
                vectors=[(
                    str(todo.id),  # IDは文字列として保存
                    embedding,
                    {
                        "title": todo.todo_title,
                        "user_id": todo.user.id,
                        "priority": todo.priority,
                        "progress": todo.progress,
                        "created_at": todo.created_at.isoformat(),
                    }
                )]
            )
            logger.info(f"Added todo {todo.id} to vector index")
        except Exception as e:
            logger.error(f"Failed to add todo to vector index: {e}")
            raise
    
    def update_todo(self, todo):
        """
        Todoをベクトルインデックスで更新
        
        既存のベクトルを削除してから再追加
        
        Args:
            todo: Todoモデルインスタンス
        """
        try:
            self.delete_todo(todo.id)
            self.add_todo(todo)
            logger.info(f"Updated todo {todo.id} in vector index")
        except Exception as e:
            logger.error(f"Failed to update todo in vector index: {e}")
            raise
    
    def delete_todo(self, todo_id: int):
        """
        Todoをベクトルインデックスから削除
        
        Args:
            todo_id: 削除対象のID
        """
        try:
            self.index.delete(ids=[str(todo_id)])
            logger.info(f"Deleted todo {todo_id} from vector index")
        except Exception as e:
            logger.error(f"Failed to delete todo from vector index: {e}")
            raise
    
    def search_similar(self, query: str, user_id: int, top_k: int = 5, min_score: float = 0.5):
        """
        類似Todoをセマンティック検索
        
        Args:
            query: 検索クエリ（自然言語）
            user_id: ユーザーID（認可用）
            top_k: 返す結果の最大数
            min_score: 最小類似度スコア（0-1）
        
        Returns:
            list[dict]: 検索結果
                - id: TodoのID
                - score: 類似度スコア
                - title: タイトル
                - priority: 優先度
                - progress: 進捗率
        """
        try:
            # クエリをベクトル化（query用）
            query_embedding = self.embedding_service.embed_text(
                query,
                task_type="retrieval_query"
            )
            
            # 検索（ユーザーでフィルタリング）
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=f"user_id = {user_id}"
            )
            
            # スコアでフィルタリング
            filtered_results = [
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
            
            return filtered_results
        except Exception as e:
            logger.error(f"Failed to search similar todos: {e}")
            raise
    
    def add_todos_batch(self, todos):
        """
        複数のTodoを一括追加
        
        初期データ投入や大量更新時に使用
        
        Args:
            todos: Todoモデルインスタンスのリスト
        """
        try:
            # テキストを一括準備
            texts = [EmbeddingService.prepare_text(todo) for todo in todos]
            
            # バッチでベクトル化
            embeddings = self.embedding_service.embed_batch(texts)
            
            # バッチで保存
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
            
            self.index.upsert(vectors=vectors)
            logger.info(f"Added {len(todos)} todos to vector index (batch)")
        except Exception as e:
            logger.error(f"Failed to add todos batch: {e}")
            raise