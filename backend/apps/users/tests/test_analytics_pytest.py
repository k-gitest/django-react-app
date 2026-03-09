"""
Usersアプリ - 分析サービステスト（pytest）
AnalyticsService（外部DB連携）のテスト
MotherDuckClient のシングルトンが他テストに干渉しないよう独立ファイルに分離
"""
import pytest
from unittest.mock import MagicMock
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from apps.users.analytics_service import AnalyticsService

User = get_user_model()


@pytest.mark.django_db
class TestAnalyticsService:
    """分析用サービス（外部DB連携）のテスト"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        AnalyticsService._client = None
        yield
        from apps.common.infrastructure.motherduck_client import MotherDuckClient
        AnalyticsService._client = None
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

    def test_log_auth_event_login(self, mocker):
        """【Service】ログインイベントのログ記録テスト"""
        mocker.patch(
            "apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema"
        )
        mock_connect = mocker.patch(
            "apps.common.infrastructure.motherduck_client.duckdb.connect"
        )
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        request = self.factory.post("/login")

        result = AnalyticsService.log_auth_event(
            user=self.user,
            event_type="login",
            request=request,
            success=True
        )

        assert result is None
        mock_conn.execute.assert_called_once()

    def test_log_auth_event_with_ip_address(self, mocker):
        """【Service】ログ記録時のIPアドレス抽出テスト"""
        mocker.patch(
            "apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema"
        )
        mock_connect = mocker.patch(
            "apps.common.infrastructure.motherduck_client.duckdb.connect"
        )
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        request = self.factory.post("/login", REMOTE_ADDR="192.168.1.1")

        AnalyticsService.log_auth_event(
            user=self.user,
            event_type="login",
            request=request,
            success=True
        )

        assert mock_conn.execute.call_args is not None

    def test_log_auth_event_with_x_forwarded_for(self, mocker):
        """【Service】プロキシ経由（X-Forwarded-For）のIPアドレス抽出テスト"""
        mocker.patch(
            "apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema"
        )
        mock_connect = mocker.patch(
            "apps.common.infrastructure.motherduck_client.duckdb.connect"
        )
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        request = self.factory.post(
            "/login",
            HTTP_X_FORWARDED_FOR="203.0.113.1, 198.51.100.1"
        )

        AnalyticsService.log_auth_event(
            user=self.user,
            event_type="login",
            request=request,
            success=True
        )

        mock_conn.execute.assert_called_once()