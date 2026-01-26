"""
Management Command - dlt pipeline wrapper

このコマンドは Service 層の薄いラッパーです。
手動実行用に使用します：docker compose exec backend python manage.py run_pipeline

インフラ障害時の手動復旧: 万が一 QStash や Webhook の経路に問題が出た際、サーバーに SSH して直接コマンドを叩けば、強制的に同期を走らせることができます。

初期データ投入: 本番環境をセットアップした直後など、最初の1回だけ手動で同期したい時に便利です。
"""

from django.core.management.base import BaseCommand, CommandError
from apps.data_pipeline.services import DltPipelineService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run dlt pipeline from PostgreSQL to MotherDuck'
    
    def add_arguments(self, parser):
        """Add command arguments"""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without actually syncing',
        )
    
    def handle(self, *args, **options):
        """Execute the pipeline"""
        dry_run = options.get('dry_run', False)
        
        try:
            # Service層を直接呼び出し（subprocessなし）
            result = DltPipelineService.execute_postgres_to_motherduck(dry_run=dry_run)
            
            # 結果の表示
            if result["status"] == "dry_run":
                self.stdout.write(
                    self.style.WARNING(f'🔍 Dry run mode - would sync tables: {result["tables"]}')
                )
                self.stdout.write(
                    self.style.WARNING(f'   Source: {result["source"]}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Pipeline completed successfully!')
                )
                self.stdout.write(
                    self.style.SUCCESS(f'   Synced tables: {", ".join(result["tables"])}')
                )
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise CommandError(f'❌ Pipeline failed: {e}')