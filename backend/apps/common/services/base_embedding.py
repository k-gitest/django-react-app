"""
Embedding Service Base Layer - Gemini API直接統合

Gemini APIを使用したテキストのベクトル化サービス
text-embedding-004モデルを使用
- 次元数: 768
- 無料枠: 1,500リクエスト/日
"""

import logging
from google import genai
from django.conf import settings
from apps.common.exceptions import EmbeddingError


logger = logging.getLogger(__name__)


class BaseEmbeddingService:
    """
    Gemini API ベクトル化の共通基盤
    
    各ドメイン（todos, users 等）から継承して使用
    """
    
    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.model = "models/text-embedding-004"
    
    def embed_text(
        self, 
        text: str, 
        task_type: str = "retrieval_document"
    ) -> list[float]:
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
            EmbeddingError: API呼び出しエラー時
        """
        try:
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type=task_type
            )
            return result['embedding']
        except EmbeddingError:
            # 既に適切な例外なので再送出
            raise
        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise EmbeddingError(
                message=f"Failed to embed text: {str(e)}",
                text=text
            ) from e
    
    def embed_batch(
        self, 
        texts: list[str], 
        task_type: str = "retrieval_document"
    ) -> list[list[float]]:
        """
        複数テキストを一括ベクトル化
        
        Args:
            texts: テキストのリスト
            task_type: retrieval_document または retrieval_query
        
        Returns:
            list[list[float]]: ベクトルのリスト
        
        Raises:
            EmbeddingError: API呼び出しエラー時
        """
        try:
            result = genai.embed_content(
                model=self.model,
                content=texts,
                task_type=task_type
            )
            return [embedding for embedding in result['embedding']]
        except EmbeddingError:
            # 既に適切な例外なので再送出
            raise
        except Exception as e:
            logger.error(f"Failed to embed batch: {e}")
            raise EmbeddingError(
                message=f"Failed to embed batch: {str(e)}",
                text=f"{len(texts)} texts"
            ) from e