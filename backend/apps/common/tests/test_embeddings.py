from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from apps.common.services.base_embedding import BaseEmbeddingService
from apps.common.exceptions import EmbeddingError

class BaseEmbeddingServiceTestCase(TestCase):
    @override_settings(GOOGLE_API_KEY="test_key")
    # クラスそのものをパッチする
    @patch("apps.common.services.base_embedding.genai.Client")
    def test_embed_text_success(self, mock_client_class):
        """
        [正常系] テキストのベクトル化が成功し、正しい次元のリストが返ること
        """
        # 1. クライアントのインスタンスを模倣
        mock_client = mock_client_class.return_value
        
        # 2. 戻り値の構造を新SDKのオブジェクト形式に合わせる
        # (result.embeddings[0].values の構造を作る)
        mock_response = MagicMock()
        mock_response.embeddings = [MagicMock(values=[0.1, 0.2])]
        mock_client.models.embed_content.return_value = mock_response

        service = BaseEmbeddingService()
        result = service.embed_text("test")
        
        self.assertEqual(result, [0.1, 0.2])

    @patch("apps.common.services.base_embedding.genai.Client")
    def test_embed_text_raises_embedding_error(self, mock_client_class):
        """
        [異常系] APIがエラーを返した際、独自のEmbeddingErrorが送出されること
        """
        # クライアントがエラーを投げるように設定
        mock_client = mock_client_class.return_value
        mock_client.models.embed_content.side_effect = Exception("API error")
        
        service = BaseEmbeddingService()
        with self.assertRaises(EmbeddingError):
            service.embed_text("test")