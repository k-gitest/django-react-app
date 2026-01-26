"""
Tests for data_pipeline app
DLT pipeline execution (views, services, management commands)
"""
from io import StringIO
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework import status

from apps.data_pipeline.services import DltPipelineService
from apps.common.exceptions import AnalyticsError


# ================================
# Service Tests
# ================================

class DltPipelineServiceTestCase(TestCase):
    """Tests for DltPipelineService (ビジネスロジック層)"""
    
    def tearDown(self):
        """各テスト後にRedisのロックをクリア"""
        cache.delete(DltPipelineService.LOCK_KEY)
    
    def test_dry_run_returns_correct_structure(self):
        """Dry-runモードが正しい構造を返すか"""
        # Act
        result = DltPipelineService.execute_postgres_to_motherduck(dry_run=True)
        
        # Assert
        self.assertEqual(result["status"], "dry_run")
        self.assertIn("tables", result)
        self.assertIn("source", result)
        
        # 期待されるテーブル名が含まれているか
        User = get_user_model()
        self.assertIn(User._meta.db_table, result["tables"])
        self.assertIn("todos_todo", result["tables"])
    
    @patch("apps.data_pipeline.services.dlt.pipeline")
    @patch("apps.data_pipeline.services.sql_database")
    def test_execute_success(self, mock_sql_database, mock_dlt_pipeline):
        """正常な実行が成功するか"""
        # Arrange
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
        self.assertEqual(result["status"], "success")
        self.assertIn("tables", result)
        self.assertIn("info", result)
        
        # _dlt_で始まるテーブルが除外されているか
        self.assertIn("custom_user", result["tables"])
        self.assertIn("todos_todo", result["tables"])
        self.assertNotIn("_dlt_version", result["tables"])
        
        # dltが正しく呼ばれているか
        mock_sql_database.assert_called_once()
        mock_dlt_pipeline.assert_called_once_with(
            pipeline_name="postgres_to_motherduck",
            destination="motherduck",
            dataset_name="django_react_app_dwh",
        )
        mock_pipeline_instance.run.assert_called_once()
    
    @patch("apps.data_pipeline.services.dlt.pipeline")
    @patch("apps.data_pipeline.services.sql_database")
    def test_execute_handles_dlt_error(self, mock_sql_database, mock_dlt_pipeline):
        """dlt実行エラーを適切に処理するか"""
        # Arrange
        mock_source = MagicMock()
        mock_sql_database.return_value = mock_source
        
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.run.side_effect = Exception("MotherDuck connection failed")
        mock_dlt_pipeline.return_value = mock_pipeline_instance
        
        # Act & Assert
        with self.assertRaises(AnalyticsError) as context:
            DltPipelineService.execute_postgres_to_motherduck()
        
        # エラーメッセージに元の例外が含まれているか
        self.assertIn("MotherDuck connection failed", str(context.exception))
        
        # ロックが解放されているか（finallyブロックの確認）
        self.assertIsNone(cache.get(DltPipelineService.LOCK_KEY))
    
    @patch("apps.data_pipeline.services.cache")
    def test_duplicate_execution_prevention(self, mock_cache):
        """二重実行が防止されるか"""
        # Arrange
        # cache.add が False を返す（既にロックが存在する状態）
        mock_cache.add.return_value = False
        
        # Act & Assert
        with self.assertRaises(AnalyticsError) as context:
            DltPipelineService.execute_postgres_to_motherduck()
        
        # エラーメッセージの確認
        self.assertIn("already running", str(context.exception))
        
        # cache.add が呼ばれたか
        mock_cache.add.assert_called_once_with(
            DltPipelineService.LOCK_KEY,
            "locked",
            DltPipelineService.LOCK_TIMEOUT
        )
        
        # ロックが取得できなかったので delete は呼ばれない
        mock_cache.delete.assert_not_called()
    
    @patch("apps.data_pipeline.services.dlt.pipeline")
    @patch("apps.data_pipeline.services.sql_database")
    def test_lock_released_on_success(self, mock_sql_database, mock_dlt_pipeline):
        """成功時にロックが解放されるか"""
        # Arrange
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
        # ロックが解放されているか
        self.assertIsNone(cache.get(DltPipelineService.LOCK_KEY))
    
    def test_table_names_are_correct(self):
        """使用されるテーブル名が正しいか"""
        # このテストは実際のモデルメタデータを検証
        from apps.todos.models import Todo
        User = get_user_model()
        
        # テーブル名が期待通りか確認
        self.assertEqual(User._meta.db_table, "custom_user")
        self.assertEqual(Todo._meta.db_table, "todos_todo")


# ================================
# Management Command Tests
# ================================

class RunPipelineCommandTestCase(TestCase):
    """Tests for run_pipeline management command (CLI層)"""
    
    @patch.object(DltPipelineService, 'execute_postgres_to_motherduck')
    def test_command_calls_service_without_dry_run(self, mock_execute):
        """コマンドがService層を正しく呼び出すか（通常実行）"""
        # Arrange
        mock_execute.return_value = {
            "status": "success",
            "tables": ["custom_user", "todos_todo"],
            "info": MagicMock(),
        }
        
        out = StringIO()
        
        # Act
        call_command('run_pipeline', stdout=out)
        
        # Assert
        # Service層が dry_run=False で呼ばれたか
        mock_execute.assert_called_once_with(dry_run=False)
        
        # 標準出力に成功メッセージが含まれているか
        output = out.getvalue()
        self.assertIn('Pipeline completed successfully', output)
        self.assertIn('custom_user', output)
        self.assertIn('todos_todo', output)
    
    @patch.object(DltPipelineService, 'execute_postgres_to_motherduck')
    def test_command_calls_service_with_dry_run(self, mock_execute):
        """コマンドがService層を正しく呼び出すか（Dry-run）"""
        # Arrange
        mock_execute.return_value = {
            "status": "dry_run",
            "tables": ["custom_user", "todos_todo"],
            "source": "localhost/test_db",
        }
        
        out = StringIO()
        
        # Act
        call_command('run_pipeline', '--dry-run', stdout=out)
        
        # Assert
        # Service層が dry_run=True で呼ばれたか
        mock_execute.assert_called_once_with(dry_run=True)
        
        # 標準出力にDry-runメッセージが含まれているか
        output = out.getvalue()
        self.assertIn('Dry run mode', output)
        self.assertIn('custom_user', output)
        self.assertIn('localhost/test_db', output)
    
    @patch.object(DltPipelineService, 'execute_postgres_to_motherduck')
    def test_command_handles_service_error(self, mock_execute):
        """Service層のエラーをCommandErrorに変換するか"""
        # Arrange
        mock_execute.side_effect = Exception("Pipeline execution failed")
        
        # Act & Assert
        with self.assertRaises(CommandError) as context:
            call_command('run_pipeline')
        
        # エラーメッセージが適切か
        self.assertIn("Pipeline failed", str(context.exception))
        self.assertIn("Pipeline execution failed", str(context.exception))
    
    @patch.object(DltPipelineService, 'execute_postgres_to_motherduck')
    def test_command_output_formatting(self, mock_execute):
        """標準出力のフォーマットが正しいか"""
        # Arrange
        mock_execute.return_value = {
            "status": "success",
            "tables": ["table1", "table2", "table3"],
            "info": MagicMock(),
        }
        
        out = StringIO()
        
        # Act
        call_command('run_pipeline', stdout=out)
        
        # Assert
        output = out.getvalue()
        
        # 1. 成功マーク（✅）が含まれているか
        self.assertIn('✅', output)
        
        # 2. テーブル名がカンマ区切りで表示されているか
        self.assertIn('table1, table2, table3', output)


# ================================
# View Tests
# ================================

class DltPipelineWebhookViewTestCase(APITestCase):
    """Tests for dlt_pipeline_webhook view"""

    @patch("apps.data_pipeline.views.DltPipelineService.execute_postgres_to_motherduck")
    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_success(self, mock_verify_signature, mock_execute):
        """Test successful webhook call"""
        # Arrange
        mock_verify_signature.return_value = True
        mock_execute.return_value = {
            "status": "success",
            "tables": ["custom_user", "todos_todo"],
            "info": MagicMock()
        }

        # Act
        response = self.client.post(
            "/api/v1/webhooks/dlt-pipeline",
            data={},
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid_signature"
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["message"], "Pipeline executed successfully")
        self.assertEqual(response.data["synced_tables"], ["custom_user", "todos_todo"])
        mock_execute.assert_called_once_with()

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_invalid_signature(self, mock_verify_signature):
        """Test webhook with invalid signature"""
        # Arrange
        mock_verify_signature.return_value = False

        # Act
        response = self.client.post(
            "/api/v1/webhooks/dlt-pipeline",
            data={},
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=invalid_signature"
        )

        # Assert
        # DRF permission_classes は 401 を返す
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_missing_signature(self, mock_verify_signature):
        """Test webhook without signature header"""
        # Arrange
        mock_verify_signature.return_value = False

        # Act
        response = self.client.post(
            "/api/v1/webhooks/dlt-pipeline",
            data={},
            format="json"
        )

        # Assert
        # DRF permission_classes は 401 を返す
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("apps.data_pipeline.views.DltPipelineService.execute_postgres_to_motherduck")
    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_service_error(self, mock_verify_signature, mock_execute):
        """Test webhook when service raises AnalyticsError"""
        # Arrange
        mock_verify_signature.return_value = True
        mock_execute.side_effect = AnalyticsError(
            message="MotherDuck connection failed",
            context={"error_type": "ConnectionError"}
        )

        # Act
        response = self.client.post(
            "/api/v1/webhooks/dlt-pipeline",
            data={},
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid_signature"
        )

        # Assert
        # AnalyticsErrorは503エラーを返す
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("error", response.data)

    @patch("apps.data_pipeline.views.DltPipelineService.execute_postgres_to_motherduck")
    @patch("apps.common.permissions.verify_qstash_signature")
    def test_webhook_duplicate_execution(self, mock_verify_signature, mock_execute):
        """Test webhook with duplicate execution error"""
        # Arrange
        mock_verify_signature.return_value = True
        mock_execute.side_effect = AnalyticsError(
            message="Pipeline is already running",
            context={"lock_key": "dlt_pipeline:lock"}
        )

        # Act
        response = self.client.post(
            "/api/v1/webhooks/dlt-pipeline",
            data={},
            format="json",
            HTTP_UPSTASH_SIGNATURE="v1=valid_signature"
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("error", response.data)
        self.assertIn("already running", response.data["detail"].lower())


# ================================
# Integration Tests
# ================================

class DltPipelineIntegrationTestCase(TestCase):
    """Integration tests for DLT pipeline workflow"""

    def tearDown(self):
        """各テスト後にロックをクリア"""
        cache.delete(DltPipelineService.LOCK_KEY)

    @patch("apps.data_pipeline.services.dlt.pipeline")
    @patch("apps.data_pipeline.services.sql_database")
    def test_full_pipeline_workflow(self, mock_sql_database, mock_dlt_pipeline):
        """Test complete pipeline workflow from service to command"""
        # Arrange
        mock_source = MagicMock()
        mock_sql_database.return_value = mock_source
        
        mock_pipeline_instance = MagicMock()
        mock_load_package = MagicMock()
        mock_load_package.schema.tables.keys.return_value = [
            "custom_user",
            "todos_todo",
            "_dlt_version"
        ]
        mock_pipeline_instance.run.return_value = MagicMock(
            load_packages=[mock_load_package]
        )
        mock_dlt_pipeline.return_value = mock_pipeline_instance
        
        out = StringIO()
        
        # Act
        call_command('run_pipeline', stdout=out)
        
        # Assert
        output = out.getvalue()
        self.assertIn('Pipeline completed successfully', output)
        self.assertIn('custom_user', output)
        self.assertIn('todos_todo', output)
        self.assertNotIn('_dlt_version', output)  # 内部テーブルは除外
        
        # ロックが解放されているか
        self.assertIsNone(cache.get(DltPipelineService.LOCK_KEY))

    def test_dry_run_workflow(self):
        """Test dry-run workflow"""
        # Arrange
        out = StringIO()
        
        # Act
        call_command('run_pipeline', '--dry-run', stdout=out)
        
        # Assert
        output = out.getvalue()
        self.assertIn('Dry run mode', output)
        self.assertIn('custom_user', output)
        self.assertIn('todos_todo', output)
        
        # 実際には実行されていないので、ロックもない
        self.assertIsNone(cache.get(DltPipelineService.LOCK_KEY))