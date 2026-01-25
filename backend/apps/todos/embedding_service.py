"""
Todo Embedding Service - Todo固有のテキスト整形

BaseEmbeddingServiceを継承し、Todo固有のロジックを提供
"""

import re
import logging
from apps.common.services.base_embedding import BaseEmbeddingService


logger = logging.getLogger(__name__)


class TodoEmbeddingService(BaseEmbeddingService):
    """
    Todo用のEmbeddingサービス
    
    BaseEmbeddingServiceを継承し、Todo固有のテキスト整形を担当
    """
    
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