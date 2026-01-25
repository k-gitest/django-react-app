"""
Analytics Service Layer - dlt pipeline execution logic

このファイルは subprocess を使わず、同一プロセス内で dlt を実行します。
CLI特有のコード（self.stdout等）は含まず、純粋なビジネスロジックのみ。
"""

import dlt
from dlt.sources.sql_database import sql_database
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from apps.common.exceptions import AnalyticsError
import logging
import os

logger = logging.getLogger(__name__)


class DltPipelineService:
    """PostgreSQL → MotherDuck 同期サービス"""
    
    # 排他制御用の設定
    LOCK_KEY = "dlt_pipeline:lock"
    LOCK_TIMEOUT = 600  # 10分（dltの最大実行時間）
    
    @staticmethod
    def execute_postgres_to_motherduck(dry_run: bool = False) -> dict:
        """
        dltパイプラインを実行（subprocessなし、排他制御付き）
        
        Args:
            dry_run: Trueの場合、実行せずに同期対象を返す
            
        Returns:
            dict: 実行結果
                - status: "success" | "dry_run"
                - tables: 同期したテーブルのリスト
                - source: 接続先情報（dry_runの場合のみ）
                - info: dltの実行情報（successの場合のみ）
                
        Raises:
            AnalyticsError: パイプライン実行エラー、または二重実行検知時
        """
        # 1. DB設定の構築
        db_conf = settings.DATABASES['default']
        
        pg_credentials = {
            "drivername": "postgresql",
            "host": db_conf.get('HOST') or os.getenv("PGHOST"),
            "port": int(db_conf.get('PORT') or os.getenv("PGPORT", 5432)),
            "database": db_conf.get('NAME') or os.getenv("PGDATABASE"),
            "username": db_conf.get('USER') or os.getenv("PGUSER"),
            "password": db_conf.get('PASSWORD') or os.getenv("PGPASSWORD"),
        }
        
        # テスト環境対応（SQLiteなど）
        if not pg_credentials["host"] and not dry_run:
            pg_credentials.update({
                "host": "localhost",
                "database": "dummy_db",
                "username": "dummy_user",
                "password": "dummy_password",
            })
        
        # 2. 同期対象テーブルの取得
        from apps.todos.models import Todo
        User = get_user_model()
        table_names = [User._meta.db_table, Todo._meta.db_table]
        
        # 3. Dry run モード
        if dry_run:
            logger.info(f"🔍 Dry run - would sync tables: {table_names}")
            return {
                "status": "dry_run",
                "tables": table_names,
                "source": f"{pg_credentials['host']}/{pg_credentials['database']}"
            }
        
        # 4. 排他制御（Redisベース）
        # cache.add は「キーが存在しない場合のみ追加」なので、二重実行を防げる
        if not cache.add(DltPipelineService.LOCK_KEY, "locked", DltPipelineService.LOCK_TIMEOUT):
            logger.warning("⚠️ Pipeline already running, skipping this execution")
            raise AnalyticsError(
                message="Pipeline is already running",
                context={"lock_key": DltPipelineService.LOCK_KEY}
            )
        
        try:
            # 5. dlt実行
            logger.info(f"⏳ Starting dlt pipeline for tables: {table_names}")
            
            source = sql_database(
                credentials=pg_credentials,
                schema="public",
                table_names=table_names,
            )
            
            pipeline = dlt.pipeline(
                pipeline_name="postgres_to_motherduck",
                destination="motherduck",
                dataset_name="django_react_app_dwh",
            )
            
            info = pipeline.run(source, write_disposition="merge")
            
            # 6. 結果の整形
            synced_tables = list(info.load_packages[0].schema.tables.keys())
            user_tables = [t for t in synced_tables if not t.startswith('_dlt_')]
            
            logger.info(f"✅ Pipeline completed - synced tables: {user_tables}")
            
            return {
                "status": "success",
                "tables": user_tables,
                "info": info,
            }
            
        except AnalyticsError:
            # 既に適切な例外なので再送出
            raise
            
        except Exception as e:
            # dlt実行時の予期しないエラー
            logger.exception("❌ dlt pipeline execution failed")
            raise AnalyticsError(
                message=f"Pipeline execution failed: {str(e)}",
                context={
                    "error_type": type(e).__name__,
                    "tables": table_names,
                }
            )
            
        finally:
            # 7. ロック解放（成功・失敗を問わず）
            cache.delete(DltPipelineService.LOCK_KEY)