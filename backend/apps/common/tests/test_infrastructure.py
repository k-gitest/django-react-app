from unittest.mock import MagicMock, patch
from django.test import TestCase, override_settings
from apps.common.infrastructure.email_client import EmailClient
from apps.common.infrastructure.motherduck_client import MotherDuckClient
from apps.common.infrastructure.qstash_client import QStashClient
from apps.common.infrastructure.vector_client import VectorClient


class QStashClientTestCase(TestCase):
    @override_settings(QSTASH_TOKEN="test_token", WEBHOOK_BASE_URL="https://test.com")
    @patch("apps.common.infrastructure.qstash_client.requests.post")
    def test_publish_success(self, mock_post):
        """
        [QStash] メッセージのパブリッシュが成功し、正しいメッセージIDが返ることを確認
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_123"}
        mock_post.return_value = mock_response
        
        message_id = QStashClient.publish("/api/test", {"key": "val"})
        self.assertEqual(message_id, "msg_123")

class EmailClientTestCase(TestCase):
    @override_settings(RESEND_API_KEY="test_key", DEFAULT_FROM_EMAIL="test@example.com")
    @patch("apps.common.infrastructure.email_client.resend.Emails.send")
    def test_send_email_success(self, mock_send):
        """
        [Resend] メールの送信が成功し、Resend側から返されたメールIDを正しく取得できることを確認
        """
        mock_send.return_value = {"id": "email_123"}
        client = EmailClient()
        message_id = client.send("user@example.com", "Subject", "<h1>Hi</h1>")
        self.assertEqual(message_id, "email_123")

class MotherDuckClientTestCase(TestCase):
    def tearDown(self):
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

    @override_settings(MOTHERDUCK_TOKEN="test_token")
    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch.object(MotherDuckClient, "_setup_schema")
    def test_insert_auth_event_success(self, mock_setup, mock_connect):
        """
        [MotherDuck] 認証イベントのログ挿入が正常に行われることを確認
        """
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        client = MotherDuckClient()
        result = client.insert_auth_event({"user_id": 1, "event_type": "login"})
        self.assertIsNone(result)

class VectorClientTestCase(TestCase):
    def tearDown(self):
        VectorClient._instance = None
        VectorClient._index = None

    @override_settings(UPSTASH_VECTOR_REST_URL="https://test.io", UPSTASH_VECTOR_REST_TOKEN="token")
    @patch("apps.common.infrastructure.vector_client.Index")
    def test_upsert_success(self, mock_index_class):
        """
        [Upstash Vector] ベクトルデータのアップサート（登録・更新）が正常に呼び出されることを確認
        """
        mock_index = MagicMock()
        mock_index_class.return_value = mock_index
        client = VectorClient()
        client.upsert([("id1", [0.1], {})])
        mock_index.upsert.assert_called_once()