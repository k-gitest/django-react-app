from unittest.mock import MagicMock, patch
from django.test import TestCase
from apps.common.services.base_email import BaseEmailService
from apps.common.services.base_qstash import BaseQStashService
from apps.common.services.base_analytics import BaseAnalyticsService
from apps.common.services.base_vector import BaseVectorService
from apps.common.exceptions import EmailDeliveryError, QStashError, AnalyticsError, VectorError

class BaseEmailServiceTestCase(TestCase):
    @patch("apps.common.infrastructure.email_client.resend.Emails.send")
    def test_safe_send_raises_email_delivery_error(self, mock_send):
        """
        [異常系] EmailClientの例外がEmailDeliveryErrorに翻訳されることを確認
        """
        mock_send.side_effect = Exception("API error")
        with self.assertRaises(EmailDeliveryError):
            BaseEmailService._safe_send("u@ex.com", "T", "<p>H</p>")

class BaseQStashServiceTestCase(TestCase):
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_safe_publish_raises_qstash_error(self, mock_post):
        """
        [異常系] QStashClientの例外がQStashErrorに翻訳されることを確認
        """
        mock_post.side_effect = Exception("Net error")
        with self.assertRaises(QStashError):
            BaseQStashService._safe_publish("/path", {})

class BaseAnalyticsServiceTestCase(TestCase):
    def tearDown(self):
        # シングルトンのクリア（他テストへの影響防止）
        BaseAnalyticsService._client = None

    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    def test_safe_insert_raises_analytics_error(self, mock_conn):
        """
        [異常系] MotherDuckClientの例外がAnalyticsErrorに翻訳されることを確認
        """
        # クライアントの初期化または実行時にエラーを発生させる
        mock_conn.return_value.execute.side_effect = Exception("DB error")
        with self.assertRaises(AnalyticsError):
            BaseAnalyticsService._safe_insert("auth", {"data": 1})

class BaseVectorServiceTestCase(TestCase):
    @patch("apps.common.infrastructure.vector_client.Index")
    def test_safe_upsert_raises_vector_error(self, mock_index_class):
        """
        [異常系] VectorClientの例外がVectorErrorに翻訳されることを確認
        """
        mock_index = MagicMock()
        mock_index.upsert.side_effect = Exception("Vector DB error")
        mock_index_class.return_value = mock_index
        
        # BaseVectorServiceに _safe_upsert 等の翻訳メソッドがあると仮定
        # （クラス名やメソッド名は実際の実装に合わせて調整してください）
        with self.assertRaises(VectorError):
            # 実際のServiceメソッドを呼び出す
            BaseVectorService._safe_upsert([("id", [0.1], {})])