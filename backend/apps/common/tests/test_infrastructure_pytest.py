"""
[Infrastructure] クライアント系テスト（pytest）
"""
import pytest
from unittest.mock import MagicMock

from apps.common.infrastructure.email_client import EmailClient
from apps.common.infrastructure.motherduck_client import MotherDuckClient
from apps.common.infrastructure.qstash_client import QStashClient
from apps.common.infrastructure.vector_client import VectorClient


# =========================
# QStash
# =========================
@pytest.mark.django_db
class TestQStashClient:

    @pytest.fixture(autouse=True)
    def setup_settings(self, settings):
        settings.QSTASH_TOKEN = "test_token"
        settings.WEBHOOK_BASE_URL = "https://test.com"

    def test_publish_success(self, mocker):
        """
        [QStash] メッセージのパブリッシュが成功し、正しいメッセージIDが返ること
        """
        mock_response = MagicMock()
        mock_response.json.return_value = {"messageId": "msg_123"}

        mock_post = mocker.patch(
            "apps.common.infrastructure.qstash_client.requests.post",
            return_value=mock_response,
        )

        message_id = QStashClient.publish("/api/test", {"key": "val"})

        assert message_id == "msg_123"
        assert mock_post.called


# =========================
# Email (Resend)
# =========================
@pytest.mark.django_db
class TestEmailClient:

    @pytest.fixture(autouse=True)
    def setup_settings(self, settings):
        settings.RESEND_API_KEY = "test_key"
        settings.DEFAULT_FROM_EMAIL = "test@example.com"

    def test_send_email_success(self, mocker):
        """
        [Resend] メール送信が成功し、メールIDを取得できること
        """
        mock_send = mocker.patch(
            "apps.common.infrastructure.email_client.resend.Emails.send",
            return_value={"id": "email_123"},
        )

        client = EmailClient()
        message_id = client.send("user@example.com", "Subject", "<h1>Hi</h1>")

        assert message_id == "email_123"
        mock_send.assert_called_once()


# =========================
# MotherDuck
# =========================
@pytest.mark.django_db
class TestMotherDuckClient:

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """
        singletonの副作用を排除
        """
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None
        yield
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

    @pytest.fixture(autouse=True)
    def setup_settings(self, settings):
        settings.MOTHERDUCK_TOKEN = "test_token"

    def test_insert_auth_event_success(self, mocker):
        """
        [MotherDuck] 認証イベントのログ挿入が正常に行われること
        """
        mock_conn = MagicMock()

        mocker.patch(
            "apps.common.infrastructure.motherduck_client.duckdb.connect",
            return_value=mock_conn,
        )

        mocker.patch.object(MotherDuckClient, "_setup_schema")

        client = MotherDuckClient()
        result = client.insert_auth_event({"user_id": 1, "event_type": "login"})

        assert result is None


# =========================
# Vector (Upstash)
# =========================
@pytest.mark.django_db
class TestVectorClient:

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        VectorClient._instance = None
        VectorClient._index = None
        yield
        VectorClient._instance = None
        VectorClient._index = None

    @pytest.fixture(autouse=True)
    def setup_settings(self, settings):
        settings.UPSTASH_VECTOR_REST_URL = "https://test.io"
        settings.UPSTASH_VECTOR_REST_TOKEN = "token"

    def test_upsert_success(self, mocker):
        """
        [Upstash Vector] ベクトルのアップサートが呼ばれること
        """
        mock_index = MagicMock()

        mocker.patch(
            "apps.common.infrastructure.vector_client.Index",
            return_value=mock_index,
        )

        client = VectorClient()
        client.upsert([("id1", [0.1], {})])

        mock_index.upsert.assert_called_once()