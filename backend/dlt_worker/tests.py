"""
Tests for dlt_worker pipeline
"""
import os
from unittest.mock import patch, MagicMock
from django.test import TestCase

# dlt_worker/pipeline.py から関数をインポート
import sys
sys.path.insert(0, '/workspace/backend')

from dlt_worker.pipeline import get_table_list, run_pipeline


class PipelineTestCase(TestCase):
    """Tests for dlt pipeline functions"""

    def test_get_table_list_success(self):
        """Test successful table list retrieval"""
        # Act
        tables = get_table_list()
        
        # Assert
        self.assertIn("custom_user", tables)
        self.assertIn("todos_todo", tables)
        self.assertEqual(len(tables), 2)

    @patch("dlt_worker.pipeline.dlt.pipeline")
    @patch("dlt_worker.pipeline.sql_database")
    @patch.dict(os.environ, {
        "PGHOST": "test-host",
        "PGPORT": "5432",
        "PGDATABASE": "test-db",
        "PGUSER": "test-user",
        "PGPASSWORD": "test-password",
    })
    def test_run_pipeline_success(self, mock_sql_database, mock_dlt_pipeline):
        """Test successful pipeline execution"""
        # Arrange
        mock_source = MagicMock()
        mock_sql_database.return_value = mock_source
        
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.run.return_value = MagicMock(
            load_packages=[
                MagicMock(
                    schema=MagicMock(
                        tables={
                            "custom_user": MagicMock(),
                            "todos_todo": MagicMock(),
                            "_dlt_version": MagicMock(),
                        }
                    )
                )
            ]
        )
        mock_dlt_pipeline.return_value = mock_pipeline_instance
        
        # Act
        exit_code = run_pipeline()
        
        # Assert
        self.assertEqual(exit_code, 0)
        
        # Verify PostgreSQL source creation
        mock_sql_database.assert_called_once()
        call_kwargs = mock_sql_database.call_args[1]
        self.assertEqual(call_kwargs["credentials"]["host"], "test-host")
        self.assertEqual(call_kwargs["credentials"]["database"], "test-db")
        self.assertEqual(call_kwargs["schema"], "public")
        
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

    @patch("dlt_worker.pipeline.get_table_list")
    def test_run_pipeline_no_tables(self, mock_get_table_list):
        """Test pipeline execution with no tables to sync"""
        # Arrange
        mock_get_table_list.return_value = []
        
        # Act
        exit_code = run_pipeline()
        
        # Assert
        self.assertEqual(exit_code, 1)  # エラーコード

    @patch("dlt_worker.pipeline.dlt.pipeline")
    @patch("dlt_worker.pipeline.sql_database")
    @patch.dict(os.environ, {
        "PGHOST": "test-host",
        "PGPORT": "5432",
        "PGDATABASE": "test-db",
        "PGUSER": "test-user",
        "PGPASSWORD": "test-password",
    })
    def test_run_pipeline_connection_error(self, mock_sql_database, mock_dlt_pipeline):
        """Test pipeline execution with connection error"""
        # Arrange
        mock_sql_database.side_effect = Exception("Connection failed")
        
        # Act
        exit_code = run_pipeline()
        
        # Assert
        self.assertEqual(exit_code, 1)  # エラーコード

    @patch("dlt_worker.pipeline.dlt.pipeline")
    @patch("dlt_worker.pipeline.sql_database")
    @patch.dict(os.environ, {
        "PGHOST": "test-host",
        "PGPORT": "5432",
        "PGDATABASE": "test-db",
        "PGUSER": "test-user",
        "PGPASSWORD": "test-password",
    })
    def test_run_pipeline_execution_error(self, mock_sql_database, mock_dlt_pipeline):
        """Test pipeline execution with dlt execution error"""
        # Arrange
        mock_source = MagicMock()
        mock_sql_database.return_value = mock_source
        
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.run.side_effect = Exception("Pipeline execution failed")
        mock_dlt_pipeline.return_value = mock_pipeline_instance
        
        # Act
        exit_code = run_pipeline()
        
        # Assert
        self.assertEqual(exit_code, 1)  # エラーコード