"""
Usersアプリ - 分析サービステスト
AnalyticsService（外部DB連携）のテスト
MotherDuckClient のシングルトンが他テストに干渉しないよう独立ファイルに分離
"""
from unittest.mock import patch, MagicMock

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model

from apps.users.analytics_service import AnalyticsService

User = get_user_model()


class AnalyticsServiceTestCase(TestCase):
    """分析用サービス（外部DB連携）のテスト"""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        AnalyticsService._client = None

    def tearDown(self):
        from apps.common.infrastructure.motherduck_client import MotherDuckClient
        AnalyticsService._client = None
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch("apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema")
    def test_log_auth_event_login(self, mock_setup_schema, mock_connect):
        """【Service】ログインイベントのログ記録テスト"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        request = self.factory.post('/login')

        result = AnalyticsService.log_auth_event(
            user=self.user,
            event_type="login",
            request=request,
            success=True
        )

        self.assertIsNone(result)
        mock_conn.execute.assert_called_once()

    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch("apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema")
    def test_log_auth_event_with_ip_address(self, mock_setup_schema, mock_connect):
        """【Service】ログ記録時のIPアドレス抽出テスト"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        request = self.factory.post('/login', REMOTE_ADDR="192.168.1.1")

        AnalyticsService.log_auth_event(
            user=self.user,
            event_type="login",
            request=request,
            success=True
        )

        call_args = mock_conn.execute.call_args
        self.assertIsNotNone(call_args)

    @patch("apps.common.infrastructure.motherduck_client.duckdb.connect")
    @patch("apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema")
    def test_log_auth_event_with_x_forwarded_for(self, mock_setup_schema, mock_connect):
        """【Service】プロキシ経由（X-Forwarded-For）のIPアドレス抽出テスト"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        request = self.factory.post(
            '/login',
            HTTP_X_FORWARDED_FOR="203.0.113.1, 198.51.100.1"
        )

        AnalyticsService.log_auth_event(
            user=self.user,
            event_type="login",
            request=request,
            success=True
        )

        mock_conn.execute.assert_called_once()