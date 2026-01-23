"""
Tests for analytics management commands
"""
import os
from io import StringIO
from unittest.mock import patch, MagicMock, call
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model
from apps.analytics.services import DltPipelineService


class RunPipelineCommandTestCase(TestCase):
    """Tests for run_pipeline management command"""

    @patch("apps.analytics.management.commands.run_pipeline.dlt.pipeline")
    @patch("apps.analytics.management.commands.run_pipeline.sql_database")
    def test_run_pipeline_success(self, mock_sql_database, mock_dlt_pipeline):
        """Test successful pipeline execution"""
        # Arrange
        mock_source = MagicMock()
        mock_sql_database.return_value = mock_source
        
        mock_pipeline_instance = MagicMock()
        mock_load_package = MagicMock()
        mock_load_package.schema.tables.keys.return_value = [
            "custom_user", 
            "todos_todo",
            "_dlt_version",
            "_dlt_loads",
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
        # 1. 成功メッセージが含まれているか
        self.assertIn('Pipeline completed successfully', output)
        
        # 2. 「Synced tables」という見出しが含まれているか
        self.assertIn('Synced tables', output)
        
        # 3. 具体的なテーブル名が含まれているか
        self.assertIn('custom_user', output)
        self.assertIn('todos_todo', output)
        
        # Verify PostgreSQL source creation
        mock_sql_database.assert_called_once()
        call_kwargs = mock_sql_database.call_args[1]
        
        # 辞書の構造に合わせてアクセス
        self.assertEqual(call_kwargs.get("schema"), "public")
        
        # credentials 辞書の中身を確認
        credentials = call_kwargs.get("credentials", {})
        self.assertEqual(credentials.get("drivername"), "postgresql")
        self.assertTrue(credentials.get("host"))
        self.assertTrue(credentials.get("database"))
        
        # テーブル名の検証
        User = get_user_model()
        expected_tables = [User._meta.db_table, "todos_todo"]
        self.assertEqual(call_kwargs["table_names"], expected_tables)
        
        # Verify pipeline creation
        mock_dlt_pipeline.assert_called_once_with(
            pipeline_name="postgres_to_motherduck",
            destination="motherduck",
            dataset_name="django_react_app_dwh",
        )
        
        # Verify pipeline execution
        mock_pipeline_instance.run.assert_called_once_with(
            mock_source,
            write_disposition="merge",
        )

    @patch("apps.analytics.management.commands.run_pipeline.dlt.pipeline")
    @patch("apps.analytics.management.commands.run_pipeline.sql_database")
    def test_run_pipeline_connection_error(self, mock_sql_database, mock_dlt_pipeline):
        """Test pipeline execution with connection error"""
        # Arrange
        mock_sql_database.side_effect = Exception("Connection failed")
        
        # Act & Assert
        with self.assertRaises(Exception) as context:
            call_command('run_pipeline')
        
        self.assertIn("Connection failed", str(context.exception))

    @patch("apps.analytics.management.commands.run_pipeline.dlt.pipeline")
    @patch("apps.analytics.management.commands.run_pipeline.sql_database")
    def test_run_pipeline_execution_error(self, mock_sql_database, mock_dlt_pipeline):
        """Test pipeline execution with dlt execution error"""
        # Arrange
        mock_source = MagicMock()
        mock_sql_database.return_value = mock_source
        
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.run.side_effect = Exception("Pipeline execution failed")
        mock_dlt_pipeline.return_value = mock_pipeline_instance
        
        # Act & Assert
        with self.assertRaises(Exception) as context:
            call_command('run_pipeline')
        
        self.assertIn("Pipeline execution failed", str(context.exception))

    def test_command_uses_correct_models(self):
        """Test that command correctly identifies table names from models"""
        # このテストは実際のモデルメタデータを検証
        from apps.todos.models import Todo
        User = get_user_model()
        
        # テーブル名が期待通りか確認
        self.assertEqual(User._meta.db_table, "custom_user")
        self.assertEqual(Todo._meta.db_table, "todos_todo")

class DltPipelineServiceTest(TestCase):
    def test_dry_run(self):
        result = DltPipelineService.execute_postgres_to_motherduck(dry_run=True)
        self.assertEqual(result["status"], "dry_run")
        self.assertIn("custom_user", result["tables"])