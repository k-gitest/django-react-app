"""
Tests for run_pipeline management command (CLI層)

このテストは Command 層の「CLI としての責務」をテストします：
- コマンドライン引数の処理
- 標準出力への表示
- Service層の呼び出し
- エラー時のCommandError発生
"""
from io import StringIO
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from apps.analytics.services import DltPipelineService


class RunPipelineCommandTest(TestCase):
    """run_pipeline management command のテスト"""
    
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