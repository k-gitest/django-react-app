"""
[Service] Base系サービスの例外翻訳テスト（pytest）
"""
import pytest
from unittest.mock import MagicMock

from apps.common.services.base_email import BaseEmailService
from apps.common.services.base_qstash import BaseQStashService
from apps.common.services.base_analytics import BaseAnalyticsService
from apps.common.services.base_vector import BaseVectorService
from apps.common.exceptions import (
    EmailDeliveryError,
    QStashError,
    AnalyticsError,
    VectorError,
)


# =========================
# Email
# =========================
class TestBaseEmailService:

    def test_safe_send_raises_email_delivery_error(self, mocker):
        """
        [異常系] EmailClientの例外がEmailDeliveryErrorに翻訳されること
        """
        mocker.patch(
            "apps.common.infrastructure.email_client.resend.Emails.send",
            side_effect=Exception("API error"),
        )

        with pytest.raises(EmailDeliveryError):
            BaseEmailService._safe_send("u@ex.com", "T", "<p>H</p>")


# =========================
# QStash
# =========================
class TestBaseQStashService:

    def test_safe_publish_raises_qstash_error(self, mocker):
        """
        [異常系] QStashClientの例外がQStashErrorに翻訳されること
        """
        mocker.patch(
            "apps.common.infrastructure.qstash_client.requests.post",
            side_effect=Exception("Net error"),
        )

        with pytest.raises(QStashError):
            BaseQStashService._safe_publish("/path", {})


# =========================
# Analytics (MotherDuck)
# =========================
class TestBaseAnalyticsService:

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """
        シングルトンの副作用除去
        """
        BaseAnalyticsService._client = None
        yield
        BaseAnalyticsService._client = None

    def test_safe_insert_raises_analytics_error(self, mocker):
        """
        [異常系] MotherDuckClientの例外がAnalyticsErrorに翻訳されること
        """
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = Exception("DB error")

        mocker.patch(
            "apps.common.infrastructure.motherduck_client.duckdb.connect",
            return_value=mock_conn,
        )

        with pytest.raises(AnalyticsError):
            BaseAnalyticsService._safe_insert("auth", {"data": 1})


# =========================
# Vector
# =========================
class TestBaseVectorService:

    def test_safe_upsert_raises_vector_error(self, mocker):
        """
        [異常系] VectorClientの例外がVectorErrorに翻訳されること
        """
        mock_index = MagicMock()
        mock_index.upsert.side_effect = Exception("Vector DB error")

        mocker.patch(
            "apps.common.infrastructure.vector_client.Index",
            return_value=mock_index,
        )

        with pytest.raises(VectorError):
            BaseVectorService._safe_upsert([("id", [0.1], {})])