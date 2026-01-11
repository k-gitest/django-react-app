import os
import sys
import django
from datetime import datetime
import logging

# Djangoの設定を読み込む
sys.path.insert(0, '/workspace/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import dlt
from dlt.sources.sql_database import sql_database

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_table_list():
    """Djangoモデルから同期対象のテーブル名を取得"""
    tables = []
    
    # Userテーブル
    from django.contrib.auth import get_user_model
    User = get_user_model()
    tables.append(User._meta.db_table)
    logger.info(f"Added table: {User._meta.db_table}")
    
    # Todoテーブル
    try:
        from todos.models import Todo
        tables.append(Todo._meta.db_table)
        logger.info(f"Added table: {Todo._meta.db_table}")
    except Exception as e:
        logger.warning(f"Todos table not available: {e}")
    
    return tables

def run_pipeline():
    """PostgreSQL → MotherDuck パイプラインを実行"""
    logger.info("=" * 60)
    logger.info("Starting dlt pipeline")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info("=" * 60)
    
    try:
        # 1. 同期対象のテーブルを取得
        table_names = get_table_list()
        logger.info(f"Tables to sync: {table_names}")
        
        if not table_names:
            logger.error("No tables to sync")
            return 1
        
        # 2. PostgreSQL接続設定
        pg_credentials = {
            "drivername": "postgresql",
            "host": os.getenv("PGHOST"),
            "port": int(os.getenv("PGPORT", 5432)),
            "database": os.getenv("PGDATABASE"),
            "username": os.getenv("PGUSER"),
            "password": os.getenv("PGPASSWORD"),
        }
        
        logger.info(f"Connecting to PostgreSQL: {pg_credentials['host']}/{pg_credentials['database']}")
        
        # 3. Sourceの作成
        source = sql_database(
            credentials=pg_credentials,
            schema="public",
            table_names=table_names,
            reflection_level="full",
        )
        
        # 4. Pipelineの作成（dataset名を正規化済みの形式に変更）
        pipeline = dlt.pipeline(
            pipeline_name="postgres_to_motherduck",
            destination="motherduck",
            dataset_name="django_react_app_dwh",  # ← アンダースコアに変更
        )
        
        logger.info("Connecting to MotherDuck...")
        
        # 5. 実行
        info = pipeline.run(
            source,
            write_disposition="merge",
        )
        
        # 6. 結果を出力
        logger.info("=" * 60)
        logger.info("Pipeline completed successfully!")
        logger.info(f"dlt version: {dlt.__version__}")
        logger.info(f"Tables synced: {list(info.load_packages[0].schema.tables.keys())}")
        
        # 各テーブルの同期結果
        for load_package in info.load_packages:
            for table_name, table in load_package.schema.tables.items():
                if not table_name.startswith('_dlt_'):
                    logger.info(f"  - {table_name}: synced")
        
        logger.info("=" * 60)
        
        return 0
    
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Pipeline failed: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()
        return 1

def main():
    """エントリーポイント"""
    exit_code = run_pipeline()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()