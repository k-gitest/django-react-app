"""
[Security] QStash セキュリティ / パーミッション テスト（pytest）
"""
import pytest
from unittest.mock import MagicMock
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory

from apps.common.security import verify_qstash_signature
from apps.common.permissions import IsQStashAuthenticated


# =========================
# Security
# =========================
class TestQStashSecurity:

    @pytest.fixture
    def rf(self):
        return RequestFactory()

    @pytest.fixture(autouse=True)
    def setup_settings(self, settings):
        settings.QSTASH_CURRENT_SIGNING_KEY = "cur"
        settings.QSTASH_NEXT_SIGNING_KEY = "nxt"

    def test_verify_signature_success(self, mocker, rf):
        """
        [セキュリティ] QStash署名が正しい場合に検証をパスすること
        """
        mock_receiver = MagicMock()
        mock_receiver.verify.return_value = None  # 例外なし = 成功

        mocker.patch(
            "apps.common.security.Receiver",
            return_value=mock_receiver,
        )

        request = rf.post("/webhook", HTTP_UPSTASH_SIGNATURE="v1=valid")

        result = verify_qstash_signature(request)

        assert result is True


# =========================
# Permission
# =========================
class TestIsQStashAuthenticated:

    @pytest.fixture
    def api_rf(self):
        return APIRequestFactory()

    @pytest.fixture
    def permission(self):
        return IsQStashAuthenticated()

    def test_permission_granted(self, mocker, api_rf, permission):
        """
        [パーミッション] 署名検証成功時にアクセスが許可されること
        """
        mocker.patch(
            "apps.common.permissions.verify_qstash_signature",
            return_value=True,
        )

        request = api_rf.post("/webhook")

        assert permission.has_permission(request, None) is True