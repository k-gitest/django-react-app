"""
[共通] BaseEmbeddingServiceのテスト（pytest）
"""
import pytest
from unittest.mock import MagicMock
from django.test import override_settings

from apps.common.services.base_embedding import BaseEmbeddingService
from apps.common.exceptions import EmbeddingError

class TestBaseEmbeddingService:
    """[共通] BaseEmbeddingServiceのテスト"""

    @override_settings(GOOGLE_API_KEY="test_key")
    def test_embed_text_success(self, mocker):
        """
        [正常系] テキストのベクトル化が成功し、正しい次元のリストが返ること
        """
        # 1. クライアントのクラスをパッチし、インスタンスを模倣
        # mock_client_class.return_value が service 内で生成される client インスタンスになる
        mock_client_class = mocker.patch("apps.common.services.base_embedding.genai.Client")
        mock_client = mock_client_class.return_value
        
        # 2. 戻り値の構造を新SDKのオブジェクト形式に合わせる
        # (result.embeddings[0].values の構造)
        mock_response = MagicMock()
        mock_response.embeddings = [MagicMock(values=[0.1, 0.2])]
        mock_client.models.embed_content.return_value = mock_response

        service = BaseEmbeddingService()
        result = service.embed_text("test")
        
        # 検証
        assert result == [0.1, 0.2]
        mock_client.models.embed_content.assert_called_once()

    def test_embed_text_raises_embedding_error(self, mocker):
        """
        [異常系] APIがエラーを返した際、独自のEmbeddingErrorが送出されること
        """
        # クライアントがエラーを投げるように設定
        mock_client_class = mocker.patch("apps.common.services.base_embedding.genai.Client")
        mock_client = mock_client_class.return_value
        mock_client.models.embed_content.side_effect = Exception("API error")
        
        service = BaseEmbeddingService()
        
        # 例外の検証
        with pytest.raises(EmbeddingError):
            service.embed_text("test")