"""
Tests for DltPipelineService (ビジネスロジック層)

このテストは Service 層の「核心的なロジック」をテストします：
- dlt の正しい設定
- テーブル名の取得
- エラーハンドリング
- 排他制御（二重実行防止）
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from apps.analytics.services import DltPipelineService
from apps.common.exceptions import AnalyticsError


class DltPipelineServiceTest(TestCase):
    """DltPipelineService のテスト"""
    
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
    
    @patch("apps.analytics.services.dlt.pipeline")
    @patch("apps.analytics.services.sql_database")
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
    
    @patch("apps.analytics.services.dlt.pipeline")
    @patch("apps.analytics.services.sql_database")
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
    
    @patch("apps.analytics.services.cache")
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
    
    @patch("apps.analytics.services.dlt.pipeline")
    @patch("apps.analytics.services.sql_database")
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