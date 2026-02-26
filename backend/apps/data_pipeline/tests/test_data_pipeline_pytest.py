"""
Tests for data_pipeline app
DLT pipeline execution (views, services, management commands)
"""
from io import StringIO
from unittest.mock import MagicMock

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework import status
from rest_framework.test import APIClient

from apps.common.exceptions import AnalyticsError
from apps.data_pipeline.services import DltPipelineService


# ================================
# Service Tests
# ================================

@pytest.mark.django_db
class TestDltPipelineService:
    """Tests for DltPipelineService (ビジネスロジック層)"""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """各テスト後にRedisのロックをクリア"""
        yield
        cache.delete(DltPipelineService.LOCK_KEY)

    def test_dry_run_returns_correct_structure(self):
        """Dry-runモードが正しい構造を返すか"""
        # Act
        result = DltPipelineService.execute_postgres_to_motherduck(dry_run=True)

        # Assert
        assert result["status"] == "dry_run"
        assert "tables" in result
        assert "source" in result

        # 期待されるテーブル名が含まれているか
        User = get_user_model()
        assert User._meta.db_table in result["tables"]
        assert "todos_todo" in result["tables"]

    def test_execute_success(self, mocker):
        """正常な実行が成功するか"""
        # Arrange
        mock_sql_database = mocker.patch("apps.data_pipeline.services.sql_database")
        mock_dlt_pipeline = mocker.patch("apps.data_pipeline.services.dlt.pipeline")

        mock_source = MagicMock()
        mock_sql_database.return_value = mock_source

        mock_pipeline_instance = MagicMock()
        mock_load_package = MagicMock()
        mock_load_package.schema.tables.keys.return_value = [
            "custom_user",
            "todos_todo",
            "_dlt_version",
        ]
        mock_pipeline_instance.run.return_value = MagicMock(
            load_packages=[mock_load_package]
        )
        mock_dlt_pipeline.return_value = mock_pipeline_instance

        # Act
        result = DltPipelineService.execute_postgres_to_motherduck()

        # Assert
        assert result["status"] == "success"
        assert "tables" in result
        assert "info" in result

        # _dlt_で始まるテーブルが除外されているか
        assert "custom_user" in result["tables"]
        assert "todos_todo" in result["tables"]
        assert "_dlt_version" not in result["tables"]

        # dltが正しく呼ばれているか
        mock_sql_database.assert_called_once()
        mock_dlt_pipeline.assert_called_once_with(
            pipeline_name="postgres_to_motherduck",
            destination="motherduck",
            dataset_name="django_react_app_dwh",
        )
        mock_pipeline_instance.run.assert_called_once()

    def test_execute_handles_dlt_error(self, mocker):
        """dlt実行エラーを適切に処理するか"""
        # Arrange
        mocker.patch("apps.data_pipeline.services.sql_database")
        mock_dlt_pipeline = mocker.patch("apps.data_pipeline.services.dlt.pipeline")

        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.run.side_effect = Exception("MotherDuck connection failed")
        mock_dlt_pipeline.return_value = mock_pipeline_instance

        # Act & Assert
        with pytest.raises(AnalyticsError) as exc_info:
            DltPipelineService.execute_postgres_to_motherduck()

        # エラーメッセージに元の例外が含まれているか
        assert "MotherDuck connection failed" in str(exc_info.value.internal_info)

        # ロックが解放されているか（finallyブロックの確認）
        assert cache.get(DltPipelineService.LOCK_KEY) is None

    def test_duplicate_execution_prevention(self, mocker):
        """二重実行が防止されるか"""
        # Arrange
        # cache.add が False を返す（既にロックが存在する状態）
        mock_cache = mocker.patch("apps.data_pipeline.services.cache")
        mock_cache.add.return_value = False

        # Act & Assert
        with pytest.raises(AnalyticsError) as exc_info:
            DltPipelineService.execute_postgres_to_motherduck()

        # エラーメッセージの確認
        assert "already running" in str(exc_info.value.internal_info)

        # cache.add が呼ばれたか
        mock_cache.add.assert_called_once_with(
            DltPipelineService.LOCK_KEY,
            "locked",
            DltPipelineService.LOCK_TIMEOUT,
        )

        # ロックが取得できなかったので delete は呼ばれない
        mock_cache.delete.assert_not_called()

    def test_lock_released_on_success(self, mocker):
        """成功時にロックが解放されるか"""
        # Arrange
        mock_sql_database = mocker.patch("apps.data_pipeline.services.sql_database")
        mock_dlt_pipeline = mocker.patch("apps.data_pipeline.services.dlt.pipeline")

        mock_source = MagicMock()
        mock_sql_database.return_value = mock_source

        mock_pipeline_instance = MagicMock()
        mock_load_package = MagicMock()
        mock_load_package.schema.tables.keys.return_value = ["custom_user"]
        mock_pipeline_instance.run.return_value = MagicMock(
            load_packages=[mock_load_package]
        )
        mock_dlt_pipeline.return_value = mock_pipeline_instance

        # Act
        DltPipelineService.execute_postgres_to_motherduck()

        # Assert
        assert cache.get(DltPipelineService.LOCK_KEY) is None

    def test_table_names_are_correct(self):
        """使用されるテーブル名が正しいか"""
        from apps.todos.models import Todo

        User = get_user_model()

        assert User._meta.db_table == "custom_user"
        assert Todo._meta.db_table == "todos_todo"


# ================================
# Management Command Tests
# ================================

@pytest.mark.django_db
class TestRunPipelineCommand:
    """Tests for run_pipeline management command (CLI層)"""

    def test_command_calls_service_without_dry_run(self, mocker):
        """コマンドがService層を正しく呼び出すか（通常実行）"""
        # Arrange
        mock_execute = mocker.patch.object(
            DltPipelineService, "execute_postgres_to_motherduck"
        )
        mock_execute.return_value = {
            "status": "success",
            "tables": ["custom_user", "todos_todo"],
            "info": MagicMock(),
        }

        out = StringIO()

        # Act
        call_command("run_pipeline", stdout=out)

        # Assert
        mock_execute.assert_called_once_with(dry_run=False)

        output = out.getvalue()
        assert "Pipeline completed successfully" in output
        assert "custom_user" in output
        assert "todos_todo" in output

    def test_command_calls_service_with_dry_run(self, mocker):
        """コマンドがService層を正しく呼び出すか（Dry-run）"""
        # Arrange
        mock_execute = mocker.patch.object(
            DltPipelineService, "execute_postgres_to_motherduck"
        )
        mock_execute.return_value = {
            "status": "dry_run",
            "tables": ["custom_user", "todos_todo"],
            "source": "localhost/test_db",
        }

        out = StringIO()

        # Act
        call_command("run_pipeline", "--dry-run", stdout=out)

        # Assert
        mock_execute.assert_called_once_with(dry_run=True)

        output = out.getvalue()
        assert "Dry run mode" in output
        assert "custom_user" in output
        assert "localhost/test_db" in output

    def test_command_handles_service_error(self, mocker):
        """Service層のエラーをCommandErrorに変換するか"""
        # Arrange
        mock_execute = mocker.patch.object(
            DltPipelineService, "execute_postgres_to_motherduck"
        )
        mock_execute.side_effect = Exception("Pipeline execution failed")

        # Act & Assert
        with pytest.raises(CommandError) as exc_info:
            call_command("run_pipeline")

        assert "Pipeline failed" in str(exc_info.value)
        assert "Pipeline execution failed" in str(exc_info.value)

    def test_command_output_formatting(self, mocker):
        """標準出力のフォーマットが正しいか"""
        # Arrange
        mock_execute = mocker.patch.object(
            DltPipelineService, "execute_postgres_to_motherduck"
        )
        mock_execute.return_value = {
            "status": "success",
            "tables": ["table1", "table2", "table3"],
            "info": MagicMock(),
        }

        out = StringIO()

        # Act
        call_command("run_pipeline", stdout=out)

        # Assert
        output = out.getvalue()

        # 1. 成功マーク（✅）が含まれているか
        assert "✅" in output

        # 2. テーブル名がカンマ区切りで表示されているか
        assert "table1, table2, table3" in output


# ================================
# View Tests
# ================================

@pytest.mark.django_db
class TestDltPipelineWebhookView:
    """Tests for dlt_pipeline_webhook view"""

    @pytest.fixture
    def api_client(self):
        return APIClient()

    def test_webhook_success(self, api_client, mocker):
        """Test successful webhook call"""
        # Arrange
        mocker.patch(
            "apps.common.permissions.verify_qstash_signature", return_value=True
        )
        mock_execute = mocker.patch(
            "apps.data_pipeline.views.DltPipelineService.execute_postgres_to_motherduck"
        )
        mock_execute.return_value = {
            "status": "success",
            "tables": ["custom_user", "todos_todo"],
            "info": MagicMock(),
        }

        # Act
        response = api_client.post(
            "/api/v1/webhooks/dlt-pipeline",
            data={},
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid_signature",
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "success"
        assert response.data["message"] == "Pipeline executed successfully"
        assert response.data["synced_tables"] == ["custom_user", "todos_todo"]
        mock_execute.assert_called_once_with()

    def test_webhook_invalid_signature(self, api_client, mocker):
        """Test webhook with invalid signature"""
        # Arrange
        mocker.patch(
            "apps.common.permissions.verify_qstash_signature", return_value=False
        )

        # Act
        response = api_client.post(
            "/api/v1/webhooks/dlt-pipeline",
            data={},
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=invalid_signature",
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_webhook_missing_signature(self, api_client, mocker):
        """Test webhook without signature header"""
        # Arrange
        mocker.patch(
            "apps.common.permissions.verify_qstash_signature", return_value=False
        )

        # Act
        response = api_client.post(
            "/api/v1/webhooks/dlt-pipeline",
            data={},
            format="json",
        )

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_webhook_service_error(self, api_client, mocker):
        """Test webhook when service raises AnalyticsError"""
        # Arrange
        mocker.patch(
            "apps.common.permissions.verify_qstash_signature", return_value=True
        )
        mock_execute = mocker.patch(
            "apps.data_pipeline.views.DltPipelineService.execute_postgres_to_motherduck"
        )
        mock_execute.side_effect = AnalyticsError(
            internal_details="MotherDuck connection failed"
        )

        # Act
        response = api_client.post(
            "/api/v1/webhooks/dlt-pipeline",
            data={},
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid_signature",
        )

        # Assert
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "error" in response.data

    def test_webhook_duplicate_execution(self, api_client, mocker):
        """Test webhook with duplicate execution error"""
        # Arrange
        mocker.patch(
            "apps.common.permissions.verify_qstash_signature", return_value=True
        )
        mock_execute = mocker.patch(
            "apps.data_pipeline.views.DltPipelineService.execute_postgres_to_motherduck"
        )
        mock_execute.side_effect = AnalyticsError(
            internal_details="Pipeline is already running",
        )

        # Act
        response = api_client.post(
            "/api/v1/webhooks/dlt-pipeline",
            data={},
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid_signature",
        )

        # Assert
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "error" in response.data
        assert "分析データの記録に失敗しました" in response.data["detail"].lower()


# ================================
# Integration Tests
# ================================

@pytest.mark.django_db
class TestDltPipelineIntegration:
    """Integration tests for DLT pipeline workflow"""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """各テスト後にロックをクリア"""
        yield
        cache.delete(DltPipelineService.LOCK_KEY)

    def test_full_pipeline_workflow(self, mocker):
        """Test complete pipeline workflow from service to command"""
        # Arrange
        mock_sql_database = mocker.patch("apps.data_pipeline.services.sql_database")
        mock_dlt_pipeline = mocker.patch("apps.data_pipeline.services.dlt.pipeline")

        mock_source = MagicMock()
        mock_sql_database.return_value = mock_source

        mock_pipeline_instance = MagicMock()
        mock_load_package = MagicMock()
        mock_load_package.schema.tables.keys.return_value = [
            "custom_user",
            "todos_todo",
            "_dlt_version",
        ]
        mock_pipeline_instance.run.return_value = MagicMock(
            load_packages=[mock_load_package]
        )
        mock_dlt_pipeline.return_value = mock_pipeline_instance

        out = StringIO()

        # Act
        call_command("run_pipeline", stdout=out)

        # Assert
        output = out.getvalue()
        assert "Pipeline completed successfully" in output
        assert "custom_user" in output
        assert "todos_todo" in output
        assert "_dlt_version" not in output  # 内部テーブルは除外

        # ロックが解放されているか
        assert cache.get(DltPipelineService.LOCK_KEY) is None

    def test_dry_run_workflow(self):
        """Test dry-run workflow"""
        # Arrange
        out = StringIO()

        # Act
        call_command("run_pipeline", "--dry-run", stdout=out)

        # Assert
        output = out.getvalue()
        assert "Dry run mode" in output
        assert "custom_user" in output
        assert "todos_todo" in output

        # 実際には実行されていないので、ロックもない
        assert cache.get(DltPipelineService.LOCK_KEY) is None