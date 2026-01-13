"""
Tests for AnalyticsService
"""

from unittest.mock import MagicMock, patch

from apps.users.analytics_service import AnalyticsService
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

User = get_user_model()


class AnalyticsServiceTestCase(TestCase):
    """Tests for AnalyticsService"""

    def setUp(self):
        """各テストの前に実行される初期設定"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    @patch("apps.users.analytics_service.MotherDuckClient")
    def test_log_auth_event_login_success(self, mock_motherduck_class):
        """log_auth_event: ログインイベントが正しく記録される"""
        # Arrange
        mock_client = MagicMock()
        mock_client.insert_auth_event.return_value = True
        mock_motherduck_class.return_value = mock_client

        request = self.factory.post("/api/v1/auth/login/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        request.META["HTTP_USER_AGENT"] = "Mozilla/5.0 (Test Browser)"

        # Act
        AnalyticsService.log_auth_event(
            user=self.user, event_type="login", request=request, success=True
        )

        # Assert
        mock_client.insert_auth_event.assert_called_once()
        call_args = mock_client.insert_auth_event.call_args[0][0]

        self.assertEqual(call_args["user_id"], self.user.id)
        self.assertEqual(call_args["email"], "test@example.com")
        self.assertEqual(call_args["event_type"], "login")
        self.assertEqual(call_args["ip_address"], "192.168.1.1")
        self.assertEqual(call_args["user_agent"], "Mozilla/5.0 (Test Browser)")
        self.assertTrue(call_args["success"])
        self.assertIsNone(call_args["error_message"])

    @patch("apps.users.analytics_service.MotherDuckClient")
    def test_log_auth_event_login_failed(self, mock_motherduck_class):
        """log_auth_event: ログイン失敗イベントが正しく記録される"""
        # Arrange
        mock_client = MagicMock()
        mock_client.insert_auth_event.return_value = True
        mock_motherduck_class.return_value = mock_client

        request = self.factory.post("/api/v1/auth/login/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        request.META["HTTP_USER_AGENT"] = "Test Agent"

        # Act - ユーザーなし（ログイン失敗）
        AnalyticsService.log_auth_event(
            user=None,
            event_type="login_failed",
            request=request,
            success=False,
            error_message="Invalid credentials",
        )

        # Assert
        mock_client.insert_auth_event.assert_called_once()
        call_args = mock_client.insert_auth_event.call_args[0][0]

        self.assertIsNone(call_args["user_id"])
        self.assertIsNone(call_args["email"])
        self.assertEqual(call_args["event_type"], "login_failed")
        self.assertFalse(call_args["success"])
        self.assertEqual(call_args["error_message"], "Invalid credentials")

    @patch("apps.users.analytics_service.MotherDuckClient")
    def test_log_auth_event_register(self, mock_motherduck_class):
        """log_auth_event: 登録イベントが正しく記録される"""
        # Arrange
        mock_client = MagicMock()
        mock_client.insert_auth_event.return_value = True
        mock_motherduck_class.return_value = mock_client

        request = self.factory.post("/api/v1/auth/register/")
        request.META["REMOTE_ADDR"] = "10.0.0.1"
        request.META["HTTP_USER_AGENT"] = "Chrome/120.0"

        # Act
        AnalyticsService.log_auth_event(
            user=self.user, event_type="register", request=request, success=True
        )

        # Assert
        call_args = mock_client.insert_auth_event.call_args[0][0]
        self.assertEqual(call_args["event_type"], "register")
        self.assertEqual(call_args["user_id"], self.user.id)

    @patch("apps.users.analytics_service.MotherDuckClient")
    def test_log_auth_event_logout(self, mock_motherduck_class):
        """log_auth_event: ログアウトイベントが正しく記録される"""
        # Arrange
        mock_client = MagicMock()
        mock_client.insert_auth_event.return_value = True
        mock_motherduck_class.return_value = mock_client

        request = self.factory.post("/api/v1/auth/logout/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"

        # Act
        AnalyticsService.log_auth_event(
            user=self.user, event_type="logout", request=request, success=True
        )

        # Assert
        call_args = mock_client.insert_auth_event.call_args[0][0]
        self.assertEqual(call_args["event_type"], "logout")

    @patch("apps.users.analytics_service.MotherDuckClient")
    def test_log_auth_event_with_x_forwarded_for(self, mock_motherduck_class):
        """log_auth_event: X-Forwarded-For ヘッダーからIPを取得"""
        # Arrange
        mock_client = MagicMock()
        mock_client.insert_auth_event.return_value = True
        mock_motherduck_class.return_value = mock_client

        request = self.factory.post("/api/v1/auth/login/")
        # プロキシ経由のリクエスト
        request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.1, 198.51.100.1, 192.0.2.1"
        request.META["REMOTE_ADDR"] = "192.0.2.1"  # プロキシのIP

        # Act
        AnalyticsService.log_auth_event(
            user=self.user, event_type="login", request=request, success=True
        )

        # Assert
        call_args = mock_client.insert_auth_event.call_args[0][0]
        # 最初のIP（クライアント）が使われる
        self.assertEqual(call_args["ip_address"], "203.0.113.1")

    @patch("apps.users.analytics_service.MotherDuckClient")
    def test_log_auth_event_long_user_agent(self, mock_motherduck_class):
        """log_auth_event: User-Agentが500文字に切り詰められる"""
        # Arrange
        mock_client = MagicMock()
        mock_client.insert_auth_event.return_value = True
        mock_motherduck_class.return_value = mock_client

        # 600文字のUser-Agent
        long_user_agent = "A" * 600

        request = self.factory.post("/api/v1/auth/login/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        request.META["HTTP_USER_AGENT"] = long_user_agent

        # Act
        AnalyticsService.log_auth_event(
            user=self.user, event_type="login", request=request, success=True
        )

        # Assert
        call_args = mock_client.insert_auth_event.call_args[0][0]
        # 500文字に切り詰められる
        self.assertEqual(len(call_args["user_agent"]), 500)
        self.assertEqual(call_args["user_agent"], "A" * 500)

    @patch("apps.users.analytics_service.MotherDuckClient")
    def test_log_auth_event_missing_user_agent(self, mock_motherduck_class):
        """log_auth_event: User-Agentがない場合は空文字"""
        # Arrange
        mock_client = MagicMock()
        mock_client.insert_auth_event.return_value = True
        mock_motherduck_class.return_value = mock_client

        request = self.factory.post("/api/v1/auth/login/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        # HTTP_USER_AGENT なし

        # Act
        AnalyticsService.log_auth_event(
            user=self.user, event_type="login", request=request, success=True
        )

        # Assert
        call_args = mock_client.insert_auth_event.call_args[0][0]
        self.assertEqual(call_args["user_agent"], "")

    @patch("apps.users.analytics_service.MotherDuckClient")
    def test_log_auth_event_missing_remote_addr(self, mock_motherduck_class):
        """log_auth_event: REMOTE_ADDRがない場合は空文字"""
        # Arrange
        mock_client = MagicMock()
        mock_client.insert_auth_event.return_value = True
        mock_motherduck_class.return_value = mock_client

        request = self.factory.post("/api/v1/auth/login/")
        # REMOTE_ADDR を削除
        if "REMOTE_ADDR" in request.META:
            del request.META["REMOTE_ADDR"]

        # Act
        AnalyticsService.log_auth_event(
            user=self.user, event_type="login", request=request, success=True
        )

        # Assert
        call_args = mock_client.insert_auth_event.call_args[0][0]
        self.assertEqual(call_args["ip_address"], "")

    @patch("apps.users.analytics_service.MotherDuckClient")
    def test_log_auth_event_continues_on_error(self, mock_motherduck_class):
        """log_auth_event: MotherDuck接続エラーでも例外を発生させない"""
        # Arrange
        mock_motherduck_class.side_effect = Exception("Connection error")

        request = self.factory.post("/api/v1/auth/login/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"

        # Act - 例外が発生しないことを確認
        try:
            AnalyticsService.log_auth_event(
                user=self.user, event_type="login", request=request, success=True
            )
        except Exception as e:
            self.fail(f"log_auth_event should not raise exception, but got: {e}")

    @patch("apps.users.analytics_service.MotherDuckClient")
    def test_log_auth_event_insert_error(self, mock_motherduck_class):
        """log_auth_event: insert_auth_event エラーでも例外を発生させない"""
        # Arrange
        mock_client = MagicMock()
        mock_client.insert_auth_event.side_effect = Exception("Insert error")
        mock_motherduck_class.return_value = mock_client

        request = self.factory.post("/api/v1/auth/login/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"

        # Act
        try:
            AnalyticsService.log_auth_event(
                user=self.user, event_type="login", request=request, success=True
            )
        except Exception as e:
            self.fail(f"log_auth_event should not raise exception, but got: {e}")

    def test_get_client_ip_direct_connection(self):
        """_get_client_ip: 直接接続の場合はREMOTE_ADDRを使用"""
        # Arrange
        request = self.factory.get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        # Act
        ip = AnalyticsService._get_client_ip(request)

        # Assert
        self.assertEqual(ip, "192.168.1.100")

    def test_get_client_ip_through_proxy(self):
        """_get_client_ip: プロキシ経由の場合はX-Forwarded-Forを使用"""
        # Arrange
        request = self.factory.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.5, 198.51.100.5"
        request.META["REMOTE_ADDR"] = "192.0.2.5"

        # Act
        ip = AnalyticsService._get_client_ip(request)

        # Assert
        # 最初のIPアドレス（クライアント）を返す
        self.assertEqual(ip, "203.0.113.5")

    def test_get_client_ip_with_spaces(self):
        """_get_client_ip: X-Forwarded-Forの空白を処理"""
        # Arrange
        request = self.factory.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = " 203.0.113.10 ,  198.51.100.10 "

        # Act
        ip = AnalyticsService._get_client_ip(request)

        # Assert
        # strip() で空白を除去
        self.assertEqual(ip, "203.0.113.10")

    def test_get_client_ip_no_ip_info(self):
        """_get_client_ip: IPアドレス情報がない場合は空文字"""
        # Arrange
        request = self.factory.get("/")
        # REMOTE_ADDR を削除
        if "REMOTE_ADDR" in request.META:
            del request.META["REMOTE_ADDR"]

        # Act
        ip = AnalyticsService._get_client_ip(request)

        # Assert
        self.assertEqual(ip, "")

    @patch("apps.users.analytics_service.MotherDuckClient")
    def test_log_auth_event_with_default_ip(self, mock_motherduck_class):
        """log_auth_event: デフォルトIP（127.0.0.1）が記録される"""
        # Arrange
        mock_client = MagicMock()
        mock_client.insert_auth_event.return_value = True
        mock_motherduck_class.return_value = mock_client

        request = self.factory.post("/api/v1/auth/login/")
        # RequestFactory はデフォルトで 127.0.0.1 を設定

        # Act
        AnalyticsService.log_auth_event(
            user=self.user, event_type="login", request=request, success=True
        )

        # Assert
        call_args = mock_client.insert_auth_event.call_args[0][0]
        self.assertEqual(call_args["ip_address"], "127.0.0.1")

    @patch("apps.users.analytics_service.MotherDuckClient")
    def test_log_auth_event_explicit_remote_addr(self, mock_motherduck_class):
        """log_auth_event: 明示的に設定したREMOTE_ADDRが使用される"""
        # Arrange
        mock_client = MagicMock()
        mock_client.insert_auth_event.return_value = True
        mock_motherduck_class.return_value = mock_client

        request = self.factory.post("/api/v1/auth/login/")
        # 明示的にIPを設定
        request.META["REMOTE_ADDR"] = "203.0.113.50"

        # Act
        AnalyticsService.log_auth_event(
            user=self.user, event_type="login", request=request, success=True
        )

        # Assert
        call_args = mock_client.insert_auth_event.call_args[0][0]
        self.assertEqual(call_args["ip_address"], "203.0.113.50")

    def test_get_client_ip_with_default(self):
        """_get_client_ip: デフォルトIP（127.0.0.1）を返す"""
        # Arrange
        request = self.factory.get("/")

        # Act
        ip = AnalyticsService._get_client_ip(request)

        # Assert
        self.assertEqual(ip, "127.0.0.1")

    def test_get_client_ip_with_explicit_ip(self):
        """_get_client_ip: 明示的に設定したIPを返す"""
        # Arrange
        request = self.factory.get("/")
        request.META["REMOTE_ADDR"] = "10.0.0.50"

        # Act
        ip = AnalyticsService._get_client_ip(request)

        # Assert
        self.assertEqual(ip, "10.0.0.50")
