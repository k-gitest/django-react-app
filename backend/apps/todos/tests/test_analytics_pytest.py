"""
Todoアプリの分析サービステスト（pytest）
TodoAnalyticsService（外部DB連携）のテスト
MotherDuckClient のシングルトンが他テストに干渉しないよう独立ファイルに分離
"""
import pytest
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model

from apps.todos.analytics_service import TodoAnalyticsService
from apps.todos.models import Todo

User = get_user_model()


@pytest.mark.django_db
class TestTodoAnalyticsService:
    """TodoAnalyticsService のテスト"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        TodoAnalyticsService._client = None
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass123"
        )
        self.todo = Todo.objects.create(
            user=self.user,
            todo_title="Test Todo",
            priority=Todo.Priority.HIGH,
            progress=50
        )
        from apps.common.infrastructure.motherduck_client import MotherDuckClient
        MotherDuckClient.reset_for_testing()
        yield
        from apps.common.infrastructure.motherduck_client import MotherDuckClient
        TodoAnalyticsService._client = None
        MotherDuckClient._instance = None
        MotherDuckClient._conn = None

    def test_log_todo_create(self, mocker):
        """Todo作成イベントのログ"""
        mocker.patch(
            "apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema"
        )
        mock_connect = mocker.patch(
            "apps.common.infrastructure.motherduck_client.duckdb.connect"
        )
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        result = TodoAnalyticsService.log_todo_create(self.user, self.todo)

        assert result is None
        mock_conn.execute.assert_called_once()

    def test_log_todo_update(self, mocker):
        """Todo更新イベントのログ"""
        mocker.patch(
            "apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema"
        )
        mock_connect = mocker.patch(
            "apps.common.infrastructure.motherduck_client.duckdb.connect"
        )
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        result = TodoAnalyticsService.log_todo_update(
            self.user,
            self.todo,
            changed_fields={"progress": [0, 50]}
        )

        assert result is None
        mock_conn.execute.assert_called_once()

    def test_log_todo_complete(self, mocker):
        """Todo完了イベントのログ"""
        mocker.patch(
            "apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema"
        )
        mock_connect = mocker.patch(
            "apps.common.infrastructure.motherduck_client.duckdb.connect"
        )
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        self.todo.progress = 100
        result = TodoAnalyticsService.log_todo_complete(self.user, self.todo)

        assert result is None
        mock_conn.execute.assert_called_once()

    def test_log_todo_delete(self, mocker):
        """Todo削除イベントのログ"""
        mocker.patch(
            "apps.common.infrastructure.motherduck_client.MotherDuckClient._setup_schema"
        )
        mock_connect = mocker.patch(
            "apps.common.infrastructure.motherduck_client.duckdb.connect"
        )
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        result = TodoAnalyticsService.log_todo_delete(
            self.user,
            self.todo,
            deletion_reason="completed"
        )

        assert result is None
        mock_conn.execute.assert_called_once()