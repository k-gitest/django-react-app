# MotherDuck Analytics 詳細ガイド

## 目次

- [概要](#概要)
- [アーキテクチャ選定の経緯](#アーキテクチャ選定の経緯)
- [ハイブリッドアプローチ](#ハイブリッドアプローチ)
- [イベントログ（Realtime Logging）](#イベントログrealtime-logging)
- [DB状態同期（Batch ETL）](#db状態同期batch-etl)
- [dlt実装](#dlt実装)
- [QStash Schedules設定](#qstash-schedules設定)
- [MotherDuckスキーマ](#motherduckスキーマ)
- [分析クエリ例](#分析クエリ例)
- [運用とモニタリング](#運用とモニタリング)
- [トラブルシューティング](#トラブルシューティング)
- [ベストプラクティス](#ベストプラクティス)

---

## 概要

**MotherDuck**（クラウドDWH）を使用して、アプリケーションのイベントログとDB状態を分析可能にしています。

**データ分析の目的**:
- ✅ **イベントログ**: ユーザー行動のリアルタイム記録
- ✅ **DB状態同期**: データの最終状態を定期的に記録
- ✅ **分析基盤**: ユーザー行動とデータ状態を包括的に分析

---

## アーキテクチャ選定の経緯

### CDC（論理レプリケーション）を検討したが見送り

当初、PostgreSQLのCDC（Change Data Capture）による完全なリアルタイム同期を検討しました。

**CDC方式**:
```
PostgreSQL (Neon)
    ↓ wal_level = logical
Write-Ahead Log (WAL)
    ↓ 論理レプリケーション
Debezium / Materialize
    ↓ ストリーム処理
MotherDuck
```

**メリット**:
- ⭐⭐⭐⭐⭐ 完全なリアルタイム性
- ⭐⭐⭐⭐⭐ すべてのDB変更を自動キャプチャ

**デメリット（見送り理由）**:
- ❌ **wal_level変更が不可逆**: NeonはPLAN変更でwal_levelを設定変更できるが、一度変更すると元に戻せない
- ❌ **WAL肥大化リスク**: レプリケーションスロットが消費されない場合、WALが肥大化
- ❌ **常駐プロセス必要**: Renderの無料枠ではスリープするため不向き
- ❌ **複雑度が高い**: Debezium/Materializeの運用コスト
- ❌ **コスト**: $40-50/月（Materialize等のサービス利用）

---

### 採用: ハイブリッドアプローチ

**Webhook（同期的なイベント記録） + dlt バッチETL（非同期的なDB状態同期）**

```
┌─────────────────────────────────────────────────────────────┐
│         MotherDuck Analytics Pipeline                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  【同期的なイベント記録】（10-50ms）                         │
│    ├─ logs.auth_events                                      │
│    │   - ログイン・ログアウト・登録イベント                  │
│    │   - リアルタイムで記録                                 │
│    │                                                        │
│    └─ logs.todo_events                                      │
│        - Todo作成・更新・削除・完了イベント                 │
│        - リアルタイムで記録                                 │
│                                                             │
│  【非同期的なDB状態同期】（15分ごと）                        │
│    ├─ dwh.custom_user                                       │
│    │   - 全ユーザーの最終状態                               │
│    │   - dlt（Data Load Tool）による増分同期               │
│    │                                                        │
│    └─ dwh.todos_todo                                        │
│        - 全Todoの最終状態                                   │
│        - dlt（Data Load Tool）による増分同期               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ハイブリッドアプローチ

### 技術選定の比較

| 手法 | リアルタイム性 | 複雑度 | コスト | 可逆性 | 採用 |
|------|--------------|--------|--------|--------|------|
| **CDC（論理レプリケーション）** | ⭐⭐⭐⭐⭐ | 非常に複雑 | $40-50/月 | ❌ 不可逆 | ❌ |
| **Webhook方式** | ⭐⭐⭐⭐⭐ | 中程度 | $0 | ✅ 容易 | ✅ |
| **dlt バッチETL** | ⭐⭐⭐☆☆ | シンプル | $0 | ✅ 容易 | ✅ |
| **Render Cron** | ⭐⭐⭐☆☆ | シンプル | $0 | ✅ 容易 | ❌ スリープ問題 |
| **QStash Schedules** | ⭐⭐⭐⭐☆ | シンプル | $0 | ✅ 容易 | ✅ |

**採用理由**:
- ✅ wal_level変更不要（不可逆な設定変更を回避）
- ✅ 常駐プロセス不要（Renderスリープ対応）
- ✅ WAL肥大化リスクなし
- ✅ 簡単にロールバック可能
- ✅ $0/月で運用可能

---

## イベントログ（Realtime Logging）

### 目的

ユーザーの行動（認証、Todo操作）をリアルタイムで記録し、行動履歴を分析可能にする。

### 記録するイベント

| テーブル | イベント種別 | 記録タイミング |
|---------|------------|--------------|
| `logs.auth_events` | login, logout, register, login_failed | 認証時に即座に記録 |
| `logs.todo_events` | create, update, delete, complete | CRUD操作時に即座に記録 |

### 実装

#### auth_events の記録

```python
# backend/users/services/auth_service.py
class UserAuthService:
    @staticmethod
    def handle_login_success(user, request):
        """ログイン成功時の処理"""
        # 1. 最終ログイン時刻を更新
        user.last_login = now()
        user.save(update_fields=["last_login"])
        
        # 2. ログインイベントをMotherDuckに記録
        if not settings.TESTING:
            AnalyticsService.log_auth_event(
                user=user,
                event_type="login",
                request=request,
                success=True
            )
```

#### todo_events の記録

```python
# backend/todos/service.py
class TodoService:
    @staticmethod
    def create_todo(user, validated_data):
        todo = Todo.objects.create(user=user, **validated_data)
        
        # Todoイベントを記録
        if not settings.TESTING:
            AnalyticsService.log_todo_event(
                user=user,
                event_type="create",
                todo_id=todo.id
            )
        
        return todo
```

### AnalyticsService 実装

```python
# backend/common/services/analytics_service.py
import duckdb

class AnalyticsService:
    @staticmethod
    def log_auth_event(user, event_type: str, request, success: bool = True):
        """認証イベントをMotherDuckに記録"""
        try:
            con = duckdb.connect(f'md:{settings.MOTHERDUCK_TOKEN}')
            
            con.execute("""
                INSERT INTO my_db.logs.auth_events (
                    user_id, email, event_type, success,
                    ip_address, user_agent, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                user.id if user else None,
                user.email if user else None,
                event_type,
                success,
                get_client_ip(request),
                request.META.get('HTTP_USER_AGENT', ''),
                now()
            ])
            
            con.close()
        except Exception as e:
            logger.error(f"Failed to log auth event: {e}")
```

---

## DB状態同期（Batch ETL）

### 目的

PostgreSQLのデータの最終状態を定期的にMotherDuckに同期し、分析を可能にする。

### 同期対象テーブル

| テーブル | 同期方式 | 実行頻度 | 主キー |
|---------|---------|---------|--------|
| `dwh.custom_user` | 増分同期（merge） | 15分ごと | id |
| `dwh.todos_todo` | 増分同期（merge） | 15分ごと | id |

### なぜ増分同期か？

**フル同期（全件置き換え）**:
```python
# ❌ 毎回全レコードを削除して再挿入
DELETE FROM dwh.custom_user;
INSERT INTO dwh.custom_user SELECT * FROM source;
```

**問題点**:
- ❌ データ量が増えると遅い
- ❌ ネットワーク帯域を無駄に消費
- ❌ MotherDuckのストレージコストが増加

**増分同期（merge）**:
```python
# ✅ 更新されたレコードのみを同期
MERGE INTO dwh.custom_user AS target
USING source
ON target.id = source.id
WHEN MATCHED AND target.updated_at < source.updated_at
    THEN UPDATE SET ...
WHEN NOT MATCHED
    THEN INSERT ...
```

**メリット**:
- ✅ 高速（更新分のみ処理）
- ✅ ネットワーク効率的
- ✅ コスト削減

---

## dlt実装

### dltとは？

**dlt (Data Load Tool)** は、PythonでETLパイプラインを構築するためのオープンソースライブラリです。

**特徴**:
- ✅ PostgreSQL → MotherDuckの同期が簡単
- ✅ 増分同期（incremental loading）をサポート
- ✅ スキーマ自動検出
- ✅ メタデータ管理（同期履歴、パイプライン状態）

### ディレクトリ構成

```
backend/
├── dlt_worker/
│   ├── __init__.py
│   ├── pipeline.py          # dltパイプライン本体
│   └── requirements.txt     # dlt依存関係
│
└── webhooks/
    └── views.py             # Webhook エンドポイント
```

### pipeline.py 実装

```python
# backend/dlt_worker/pipeline.py
import os
import dlt
from dlt.sources.sql_database import sql_database

# 環境変数から接続情報を取得
PGHOST = os.getenv("PGHOST")
PGDATABASE = os.getenv("PGDATABASE")
PGUSER = os.getenv("PGUSER")
PGPASSWORD = os.getenv("PGPASSWORD")
PGPORT = os.getenv("PGPORT", "5432")
MOTHERDUCK_TOKEN = os.getenv("MOTHERDUCK_TOKEN")

def run_pipeline():
    """dltパイプラインを実行"""
    
    # 1. PostgreSQLからデータを取得
    source = sql_database(
        credentials={
            "drivername": "postgresql",
            "host": PGHOST,
            "port": PGPORT,
            "database": PGDATABASE,
            "username": PGUSER,
            "password": PGPASSWORD,
        },
        table_names=["custom_user", "todos_todo"],  # 同期対象テーブル
        # 増分同期: updated_at が前回同期時刻より新しいレコードのみ取得
        incremental=dlt.sources.incremental("updated_at"),
    )
    
    # 2. MotherDuckに同期
    pipeline = dlt.pipeline(
        pipeline_name="django_react_app",
        destination="motherduck",
        dataset_name="django_react_app_dwh"
    )
    
    # 3. 実行
    load_info = pipeline.run(
        source,
        credentials=f"md:{MOTHERDUCK_TOKEN}"
    )
    
    print(load_info)

if __name__ == "__main__":
    run_pipeline()
```

### Webhook エンドポイント

```python
# backend/webhooks/views.py
@api_view(["POST"])
@permission_classes([IsQStashAuthenticated])
@log_webhook_call(webhook_name="dlt_pipeline")
def dlt_pipeline_webhook(request):
    """
    QStash Schedulesから呼ばれるWebhook
    
    dltパイプラインを実行してDB状態をMotherDuckに同期
    """
    try:
        # dltパイプラインを実行
        import subprocess
        result = subprocess.run(
            ["python", "dlt_worker/pipeline.py"],
            capture_output=True,
            text=True,
            timeout=300  # 5分でタイムアウト
        )
        
        if result.returncode == 0:
            return Response({
                "message": "dlt pipeline executed successfully",
                "output": result.stdout
            })
        else:
            return Response({
                "message": "dlt pipeline failed",
                "error": result.stderr
            }, status=500)
            
    except subprocess.TimeoutExpired:
        return Response({
            "message": "dlt pipeline timeout"
        }, status=504)
```

### 手動実行

```bash
# dltパイプラインを手動実行
docker compose exec backend python dlt_worker/pipeline.py

# 出力例
Pipeline django_react_app load step completed in 2.45 seconds
1 load package(s) were loaded to destination motherduck and into dataset django_react_app_dwh
The motherduck destination used md:your_token location to store data
Load package 1234567890 is LOADED and contains no failed jobs
```

---

## QStash Schedules設定

### なぜQStash Schedulesか？

| 手法 | 問題点 | QStash Schedulesの利点 |
|------|--------|----------------------|
| **Render Cron** | Renderがスリープすると実行されない | 外部からHTTPリクエストでウェイクアップ |
| **Django Celery Beat** | 常駐プロセスが必要（Renderで不向き） | サーバーレスで実行可能 |
| **GitHub Actions** | リポジトリに依存、実行頻度の制限 | 柔軟なスケジュール設定 |

### 設定手順

#### 1. QStash Consoleにアクセス

```
https://console.upstash.com/qstash
```

#### 2. Schedules タブを開く

#### 3. Create Schedule

**設定項目**:
```
Name: dlt-pipeline-sync
Destination: https://your-app.onrender.com/api/v1/webhooks/dlt-pipeline
Cron: */15 * * * *  （15分ごと）
Method: POST
Headers:
  Content-Type: application/json
Body: {}
Retries: 3
Retry: 5000 * (retried + 1)  （5秒、10秒、15秒）
```

**Cron式の例**:
```
*/15 * * * *   # 15分ごと
0 * * * *      # 毎時0分
0 0 * * *      # 毎日0時
0 0 * * 0      # 毎週日曜0時
```

---

## MotherDuckスキーマ

### データベース構造

```
my_db/
├── logs/  # イベントログ（Webhook方式）
│   ├── auth_events
│   │   ├── id (BIGINT)
│   │   ├── user_id (INTEGER)
│   │   ├── email (VARCHAR)
│   │   ├── event_type (VARCHAR)  # login, logout, register, login_failed
│   │   ├── success (BOOLEAN)
│   │   ├── ip_address (VARCHAR)
│   │   ├── user_agent (VARCHAR)
│   │   └── timestamp (TIMESTAMP)
│   │
│   └── todo_events
│       ├── id (BIGINT)
│       ├── user_id (INTEGER)
│       ├── todo_id (INTEGER)
│       ├── event_type (VARCHAR)  # create, update, delete, complete
│       ├── ip_address (VARCHAR)
│       └── timestamp (TIMESTAMP)
│
└── django_react_app_dwh/  # DB状態同期（dlt方式）
    ├── custom_user
    │   ├── id (INTEGER)
    │   ├── email (VARCHAR)
    │   ├── first_name (VARCHAR)
    │   ├── last_name (VARCHAR)
    │   ├── date_joined (TIMESTAMP)
    │   ├── last_login (TIMESTAMP)
    │   ├── is_active (BOOLEAN)
    │   ├── created_at (TIMESTAMP)
    │   └── updated_at (TIMESTAMP)
    │
    ├── todos_todo
    │   ├── id (INTEGER)
    │   ├── user_id (INTEGER)
    │   ├── todo_title (VARCHAR)
    │   ├── priority (VARCHAR)
    │   ├── progress (INTEGER)
    │   ├── created_at (TIMESTAMP)
    │   └── updated_at (TIMESTAMP)
    │
    ├── _dlt_version  # dltメタデータ
    ├── _dlt_loads    # 同期履歴
    └── _dlt_pipeline_state  # パイプライン状態
```

### テーブル作成

#### auth_events

```sql
CREATE TABLE IF NOT EXISTS my_db.logs.auth_events (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER,
    email VARCHAR,
    event_type VARCHAR,
    success BOOLEAN,
    ip_address VARCHAR,
    user_agent VARCHAR,
    timestamp TIMESTAMP
);
```

#### todo_events

```sql
CREATE TABLE IF NOT EXISTS my_db.logs.todo_events (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER,
    todo_id INTEGER,
    event_type VARCHAR,
    ip_address VARCHAR,
    timestamp TIMESTAMP
);
```

---

## 分析クエリ例

### 1. イベントログの分析

#### 時間帯別のログイン数

```sql
SELECT 
    HOUR(timestamp) as hour,
    COUNT(*) as login_count
FROM my_db.logs.auth_events
WHERE event_type = 'login'
  AND DATE(timestamp) = CURRENT_DATE
GROUP BY hour
ORDER BY hour;
```

#### ユーザー登録後の行動分析

```sql
-- 登録から最初のTodo作成までの時間
SELECT 
    a.user_id,
    a.email,
    a.timestamp as registered_at,
    MIN(t.timestamp) as first_todo_at,
    TIMESTAMPDIFF(MINUTE, a.timestamp, MIN(t.timestamp)) as minutes_to_first_todo
FROM my_db.logs.auth_events a
LEFT JOIN my_db.logs.todo_events t 
    ON a.user_id = t.user_id 
    AND t.event_type = 'create'
WHERE a.event_type = 'register'
GROUP BY a.user_id, a.email, a.timestamp
ORDER BY registered_at DESC;
```

---

### 2. DB状態の分析

#### 現在のアクティブユーザー数

```sql
SELECT 
    COUNT(*) as active_users
FROM my_db.django_react_app_dwh.custom_user
WHERE is_active = true;
```

#### ユーザー別のTodo統計

```sql
SELECT 
    u.email,
    COUNT(t.id) as total_todos,
    SUM(CASE WHEN t.progress = 100 THEN 1 ELSE 0 END) as completed_todos,
    AVG(t.progress) as avg_progress
FROM my_db.django_react_app_dwh.custom_user u
LEFT JOIN my_db.django_react_app_dwh.todos_todo t 
    ON u.id = t.user_id
GROUP BY u.email
ORDER BY total_todos DESC;
```

---

### 3. イベントログとDB状態の結合

#### Todo完了までの時間分析

```sql
SELECT 
    u.email,
    t.todo_title,
    create_event.timestamp as created_at,
    complete_event.timestamp as completed_at,
    TIMESTAMPDIFF(HOUR, create_event.timestamp, complete_event.timestamp) as hours_to_complete
FROM my_db.django_react_app_dwh.todos_todo t
JOIN my_db.django_react_app_dwh.custom_user u ON t.user_id = u.id
JOIN my_db.logs.todo_events create_event 
    ON t.id = create_event.todo_id AND create_event.event_type = 'create'
LEFT JOIN my_db.logs.todo_events complete_event 
    ON t.id = complete_event.todo_id AND complete_event.event_type = 'complete'
WHERE t.progress = 100
ORDER BY hours_to_complete;
```

---

## 運用とモニタリング

### dlt同期履歴の確認

```sql
SELECT 
    load_id,
    schema_name,
    status,
    inserted_at
FROM my_db.django_react_app_dwh._dlt_loads
ORDER BY inserted_at DESC
LIMIT 10;
```

### QStash Dashboard

```
1. https://console.upstash.com/qstash にアクセス
2. "Schedules" タブで実行履歴を確認
3. 成功/失敗、リトライ回数を監視
```

### ログ確認

```bash
# dltパイプラインの実行ログ
docker compose logs -f backend | grep "dlt"

# 成功例
✅ Pipeline django_react_app load step completed in 2.45 seconds

# 失敗例
❌ dlt pipeline failed: Connection timeout
```

---

## トラブルシューティング

### エラー: dlt同期が実行されない

```bash
# 確認項目
1. QStash Schedule が有効か
   → QStash Dashboard で確認

2. Webhook署名検証が成功しているか
   → ログで "Invalid signature" を確認

3. 環境変数が正しく設定されているか
   → MOTHERDUCK_TOKEN
   → PostgreSQL接続情報（PGHOST, PGDATABASE等）
```

### エラー: MotherDuckに接続できない

```bash
# 原因: MOTHERDUCK_TOKEN が無効
解決策:
  1. https://app.motherduck.com/ にアクセス
  2. Settings → Access Tokens → Create Token
  3. 環境変数を更新
```

### エラー: 増分同期が動作しない

```bash
# 原因: updated_atカラムが存在しない
解決策:
  1. マイグレーションで updated_at を追加
  2. auto_now=True を設定

# モデル例
class CustomUser(AbstractUser):
    updated_at = models.DateTimeField(auto_now=True)
```

---

## ベストプラクティス

### 1. イベントログとDB状態の使い分け

| 分析内容 | 使用するデータ | 理由 |
|---------|-------------|------|
| **ユーザーの行動履歴** | logs.auth_events, logs.todo_events | イベントログは履歴が残る |
| **現在のユーザー数** | dwh.custom_user | DB状態は最新の状態を反映 |
| **Todo完了までの時間** | logs.todo_events | イベントログに作成・完了のタイムスタンプ |
| **現在の未完了Todo数** | dwh.todos_todo | DB状態は最新の進捗を反映 |
| **ユーザー登録後の行動分析** | 両方を結合 | 登録イベント + 現在のTodo状況 |

### 2. 同期頻度の調整

```
【リアルタイム性が高い】
5分ごと: */5 * * * *

【バランス型】（推奨）
15分ごと: */15 * * * *

【コスト重視】
1時間ごと: 0 * * * *
```

### 3. エラーハンドリング

```python
# イベントログの記録は失敗してもメインフローに影響を与えない
if not settings.TESTING:
    try:
        AnalyticsService.log_auth_event(...)
    except Exception as e:
        logger.error(f"Failed to log event: {e}")
        # メインフローは継続
```

### 4. テスト環境での無効化

```python
# settings/base.py
TESTING = False

# tests/conftest.py
@pytest.fixture(autouse=True)
def set_testing_flag(settings):
    settings.TESTING = True
```

---

## まとめ

| 項目 | 実装方法 |
|------|---------|
| **イベントログ** | Webhook方式（同期的） |
| **DB状態同期** | dlt バッチETL（非同期的） |
| **スケジュール** | QStash Schedules（15分ごと） |
| **DWH** | MotherDuck（DuckDB） |
| **コスト** | $0/月（無料枠のみ） |
| **リアルタイム性** | イベントログ: 即座、DB状態: 15分遅延 |

この設計により、以下を実現しています：

✅ **リアルタイムなイベント記録**: ユーザー行動を即座にキャプチャ  
✅ **定期的なDB状態同期**: 最新のデータ状態を分析  
✅ **低コスト**: $0/月で運用可能  
✅ **スケーラブル**: dltの増分同期で効率的  
✅ **保守性**: シンプルなアーキテクチャで運用容易  
✅ **可逆性**: wal_level変更不要、簡単にロールバック可能