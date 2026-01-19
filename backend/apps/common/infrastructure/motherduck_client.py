import duckdb
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MotherDuckClient:
    """
    MotherDuck接続クライアント（シングルトン）
    
    使用例:
        client = MotherDuckClient()
        client.insert_auth_event({
            "user_id": 1,
            "email": "user@example.com",
            "event_type": "login",
            # ...
        })
    """
    
    _instance = None
    _conn = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._conn is None:
            try:
                token = settings.MOTHERDUCK_TOKEN
                if not token:
                    raise ValueError("MOTHERDUCK_TOKEN is not set")
                
                # MotherDuckに接続
                self._conn = duckdb.connect(f"md:?motherduck_token={token}")
                self._setup_schema()
                logger.info("MotherDuck connection established")
            except Exception as e:
                # logger.error(f"Failed to connect to MotherDuck: {e}")
                raise
    
    def _setup_schema(self):
        """
        初回起動時にデータベース・スキーマ・テーブル作成
        
        既に存在する場合はスキップ（CREATE IF NOT EXISTS）
        """
        try:
            # 1. データベース作成
            self._conn.execute("""
                CREATE DATABASE IF NOT EXISTS django_react_app
            """)
            
            # 2. スキーマ作成
            self._conn.execute("""
                CREATE SCHEMA IF NOT EXISTS django_react_app.logs
            """)
            
            # 3. 認証イベントテーブル作成
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS django_react_app.logs.auth_events (
                    id UUID DEFAULT uuid() PRIMARY KEY,
                    user_id INTEGER,
                    email VARCHAR,
                    event_type VARCHAR,  -- 'login', 'logout', 'register', 'login_failed'
                    ip_address VARCHAR,
                    user_agent VARCHAR,
                    success BOOLEAN,
                    error_message VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- 分析用の計算カラム
                    date DATE GENERATED ALWAYS AS (CAST(created_at AS DATE)),
                    hour INTEGER GENERATED ALWAYS AS (EXTRACT(HOUR FROM created_at))
                )
            """)

            # 4. Todoイベントテーブル
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS django_react_app.logs.todo_events (
                    id UUID DEFAULT uuid() PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    todo_id INTEGER NOT NULL,
                    event_type VARCHAR NOT NULL,  -- 'create', 'update', 'delete', 'complete'
                    
                    -- Todoの内容（イベント発生時のスナップショット）
                    todo_title VARCHAR,
                    priority VARCHAR,  -- 'LOW', 'MEDIUM', 'HIGH'
                    progress INTEGER,  -- 0-100
                    is_completed BOOLEAN,
                    
                    -- 変更内容（updateイベントの場合）
                    changed_fields VARCHAR,  -- JSON文字列: {"priority": ["LOW", "HIGH"], "progress": [0, 50]}
                    
                    -- 削除理由（deleteイベントの場合）
                    deletion_reason VARCHAR,  -- 'completed', 'cancelled', 'duplicate', 'other'
                    
                    -- メタデータ
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- 分析用の計算カラム
                    date DATE GENERATED ALWAYS AS (CAST(created_at AS DATE)),
                    hour INTEGER GENERATED ALWAYS AS (EXTRACT(HOUR FROM created_at))
                )
            """)
            
            logger.info("MotherDuck schema initialized successfully")
        except Exception as e:
            # logger.error(f"Failed to setup MotherDuck schema: {e}")
            raise
    
    def insert_auth_event(self, event_data: dict) -> None:
        """
        認証イベントをMotherDuckに挿入
        
        Args:
            event_data: {
                "user_id": int,
                "email": str,
                "event_type": str,
                "ip_address": str,
                "user_agent": str,
                "success": bool,
                "error_message": str (optional)
            }
        
        Returns:
            bool: 成功/失敗
        """
        #try:

        self._conn.execute("""
            INSERT INTO django_react_app.logs.auth_events 
            (user_id, email, event_type, ip_address, user_agent, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            event_data.get("user_id"),
            event_data.get("email"),
            event_data.get("event_type"),
            event_data.get("ip_address"),
            event_data.get("user_agent", ""),
            event_data.get("success", True),
            event_data.get("error_message"),
        ])
            
        """
            logger.info(f"Auth event inserted: {event_data.get('event_type')} for user {event_data.get('user_id')}")
            return True
        except Exception as e:
            # logger.error(f"Failed to insert auth event: {e}")
            return False
        """

    def insert_todo_event(self, event_data: dict) -> None:
        """
        TodoイベントをMotherDuckに挿入
        
        Args:
            event_data: {
                "user_id": int,
                "todo_id": int,
                "event_type": str,  # 'create', 'update', 'delete', 'complete'
                "todo_title": str,
                "priority": str,
                "progress": int,
                "is_completed": bool,
                "changed_fields": str (optional),  # JSON文字列
                "deletion_reason": str (optional),
            }
        
        Returns:
            bool: 成功/失敗
        """
        # try:

        self._conn.execute("""
            INSERT INTO django_react_app.logs.todo_events 
            (user_id, todo_id, event_type, todo_title, 
            priority, progress, is_completed, changed_fields, deletion_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            event_data.get("user_id"),
            event_data.get("todo_id"),
            event_data.get("event_type"),
            event_data.get("todo_title"),
            event_data.get("priority"),
            event_data.get("progress"),
            event_data.get("is_completed"),
            event_data.get("changed_fields"),
            event_data.get("deletion_reason"),
        ])
            
        """
            logger.info(f"Todo event inserted: {event_data.get('event_type')} for todo {event_data.get('todo_id')}")
            return True
        except Exception as e:
            # logger.error(f"Failed to insert todo event: {e}")
            return False
        """
    
    def query(self, sql: str):
        """
        任意のSQLクエリを実行（テスト用）
        
        Args:
            sql: SQLクエリ文字列
        
        Returns:
            クエリ結果
        """
        try:
            result = self._conn.execute(sql).fetchall()
            return result
        except Exception as e:
            # logger.error(f"Query failed: {e}")
            return None
    
    def close(self):
        """接続を閉じる（アプリ終了時）"""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("MotherDuck connection closed")