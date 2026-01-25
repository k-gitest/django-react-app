import logging
import re
import google.generativeai as genai

from django.conf import settings
from apps.common.exceptions import EmbeddingError


logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Gemini APIを使用したテキストのベクトル化サービス
    
    text-embedding-004モデルを使用
    - 次元数: 768
    - 無料枠: 1,500リクエスト/日
    """

    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = "models/text-embedding-004"
    
    @staticmethod
    def prepare_text(todo) -> str:
        """
        検索用テキストを生成
        
        Todoのタイトル + メタデータを結合して検索精度を向上
        
        Args:
            todo: Todoモデルインスタンス
        
        Returns:
            str: 正規化されたテキスト
        """
        # タイトル + 優先度 + 進捗状態を結合
        text = (
            f"{todo.todo_title} "
            f"優先度:{todo.get_priority_display()} "
            f"進捗:{todo.progress}%"
        )
        
        # 正規化：複数の空白を1つに、前後の空白を削除
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def embed_text(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        """
        テキストをベクトル化
        
        Args:
            text: 埋め込むテキスト
            task_type: 
                - "retrieval_document": 保存用（デフォルト）
                - "retrieval_query": 検索クエリ用
        
        Returns:
            list[float]: 768次元のベクトル
        
        Raises:
            Exception: API呼び出しエラー時
        """
        try:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type=task_type
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise EmbeddingError(
                message=f"Failed to embed text: {str(e)}",
                text=text
            ) from e
    
    def embed_batch(self, texts: list[str], task_type: str = "retrieval_document") -> list[list[float]]:
        """
        複数テキストを一括ベクトル化
        
        Args:
            texts: テキストのリスト
            task_type: retrieval_document または retrieval_query
        
        Returns:
            list[list[float]]: ベクトルのリスト
        
        Raises:
            Exception: API呼び出しエラー時
        """
        try:
            result = genai.embed_content(
                model=self.model,
                content=texts,
                task_type=task_type
            )
            return [embedding for embedding in result['embedding']]
        except Exception as e:
            logger.error(f"Failed to embed batch: {e}")
            raise EmbeddingError(
                message=f"Failed to embed batch: {str(e)}",
                text=f"{len(texts)} texts"
            ) from e