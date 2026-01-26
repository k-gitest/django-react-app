# モニタリング詳細ガイド

## 目次

- [概要](#概要)
- [Sentry：エラー監視](#sentryエラー監視)
- [New Relic：パフォーマンス監視](#new-relicパフォーマンス監視)
- [分散トレーシング](#分散トレーシング)
- [ダッシュボード構築](#ダッシュボード構築)
- [アラート設定](#アラート設定)
- [トラブルシューティング](#トラブルシューティング)

---

## 概要

### モニタリングアーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                     Monitoring Stack                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  【エラー監視】Sentry                                        │
│    ├─ Frontend (React)                                      │
│    │   └─ GlobalErrorBoundary → captureException           │
│    └─ Backend (Django)                                      │
│        └─ BaseAppError → auto capture                       │
│                                                             │
│  【パフォーマンス監視】New Relic                              │
│    ├─ Frontend (React)                                      │
│    │   └─ BrowserAgent → Core Web Vitals                   │
│    └─ Backend (Django)                                      │
│        └─ APM Agent → SQL, API, Transaction                │
│                                                             │
│  【アクセス解析】Google Analytics                             │
│    └─ Frontend (React)                                      │
│        └─ GA4 → Page View, User Behavior                   │
│                                                             │
│  【データ分析】MotherDuck                                     │
│    └─ Backend (Django)                                      │
│        └─ Event Logs, DB State                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 設計原則

1. **責務の分離**: エラーとパフォーマンスを別ツールで管理
2. **自動化**: コードを汚さず、設定のみで監視
3. **分散トレーシング**: フロントとバックを一本の線で繋ぐ
4. **コスト最適化**: 無料枠内で最大限の価値を引き出す

---

## Sentry：エラー監視

### フロントエンド（React）

#### 初期化

```typescript
// frontend/src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import * as Sentry from "@sentry/react";
import { SENTRY_DSN, SENTRY_RELEASE, IS_PRODUCTION } from "@/lib/constants";

// Sentryの初期化（本番環境のみ）
if (IS_PRODUCTION && SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    sendDefaultPii: true,  // ユーザー情報を送信
    environment: import.meta.env.MODE,
    release: SENTRY_RELEASE,  // production@{git-hash}
    
    // 分散トレーシング設定
    integrations: [
      Sentry.browserTracingIntegration(),
    ],
    
    // Django APIのドメインを指定（Trace IDを送信）
    tracePropagationTargets: [
      "localhost",
      /^https:\/\/.*\.onrender\.com\/api/,
    ],
    
    // サンプリングレート（10%）
    tracesSampleRate: 0.1,
  });

  // グローバルに公開
  window.Sentry = Sentry;
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <GlobalAsyncBoundary>
      <App />
    </GlobalAsyncBoundary>
  </React.StrictMode>,
);
```

#### ErrorBoundaryでのキャッチ

```typescript
// frontend/src/errors/error-boundary.tsx
public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
  const level = this.props.level || 'component';
  
  // 1. UI処理（Toast表示など）
  errorHandler(error);

  // 2. Sentryへ送信（本番環境のみ）
  if (import.meta.env.PROD && window.Sentry) {
    window.Sentry.captureException(error, {
      contexts: {
        react: {
          componentStack: errorInfo.componentStack,
        },
      },
      tags: {
        errorBoundary: level,
      },
      level: level === 'global' ? 'fatal' : 'error',
    });
  }
}
```

#### ユーザー情報の紐付け

```typescript
// frontend/src/hooks/use-session-store.ts
import { useAuthStore } from '@/hooks/use-session-store';

// ログイン成功時
const handleLoginSuccess = (user: User) => {
  // Zustand Storeを更新
  setUser(user);
  
  // Sentryにユーザー情報を設定
  if (window.Sentry) {
    window.Sentry.setUser({
      id: user.id,
      email: user.email,
      username: user.first_name || user.email,
    });
  }
};

// ログアウト時
const handleLogout = () => {
  setUser(null);
  
  // Sentryのユーザー情報をクリア
  if (window.Sentry) {
    window.Sentry.setUser(null);
  }
};
```

---

### バックエンド（Django）

#### 初期化

```python
# backend/config/settings/base.py
from decouple import config
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging

# リリース情報
SENTRY_RELEASE = config('RELEASE', default='development@local')
SENTRY_ENVIRONMENT = config('ENVIRONMENT', default='development')

# before_send フック（エラーの前処理）
def _before_send(event, hint):
    # 404エラーは記録しない
    if event.get('status_code') == 404:
        return None
    
    # 特定のエラーメッセージを無視
    if 'exception' in event:
        for exception in event['exception'].get('values', []):
            if 'ConnectionError' in exception.get('type', ''):
                # 外部API接続エラーは記録しない（頻発するため）
                return None
    
    return event

# Sentry設定
if not DEBUG or config('SENTRY_ENABLED', default=False, cast=bool):
    sentry_sdk.init(
        dsn=config('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            LoggingIntegration(
                level=logging.INFO,        # ログレベル INFO以上をSentryに送信
                event_level=logging.ERROR  # ERROR以上はイベントとして記録
            ),
        ],
        
        # 環境設定
        environment=SENTRY_ENVIRONMENT,
        release=SENTRY_RELEASE,
        
        # パフォーマンス監視
        traces_sample_rate=config('SENTRY_TRACES_SAMPLE_RATE', default=0.1, cast=float),
        profiles_sample_rate=config('SENTRY_PROFILES_SAMPLE_RATE', default=0.1, cast=float),
        
        # エラーサンプリング
        sample_rate=1.0,  # 100%のエラーを送信
        
        # 機密情報のフィルタリング
        send_default_pii=False,
        
        # パフォーマンス
        max_breadcrumbs=50,
        
        # エラーの前処理
        before_send=_before_send,
    )
```

#### CORS設定（重要）

```python
# backend/config/settings/base.py
from corsheaders.defaults import default_headers

# CORSで許可するカスタムヘッダー
CORS_ALLOW_HEADERS = list(default_headers) + [
    # Sentry 分散トレーシング用
    "sentry-trace",
    "baggage",
    
    # New Relic 分散トレーシング用
    "traceparent",
    "tracestate",
    "newrelic",
]
```

**これがないと**: ブラウザがCORSエラーを出してAPIリクエストが失敗します。

---

## New Relic：パフォーマンス監視

### フロントエンド（React）

#### 初期化

```typescript
// frontend/src/lib/newrelic.ts
import { BrowserAgent } from '@newrelic/browser-agent/loaders/browser-agent';

const options = {
  init: {
    distributed_tracing: { enabled: true },
    privacy: { cookies_enabled: true },
    ajax: { deny_list: ['bam.nr-data.net'] }
  },
  info: {
    beacon: 'bam.nr-data.net',
    errorBeacon: 'bam.nr-data.net',
    licenseKey: import.meta.env.VITE_NEW_RELIC_LICENSE_KEY,
    applicationID: import.meta.env.VITE_NEW_RELIC_APP_ID,
    sa: 1
  },
  loader_config: {
    accountID: import.meta.env.VITE_NEW_RELIC_ACCOUNT_ID,
    trustKey: import.meta.env.VITE_NEW_RELIC_TRUST_KEY,
    agentID: import.meta.env.VITE_NEW_RELIC_APP_ID,
    licenseKey: import.meta.env.VITE_NEW_RELIC_LICENSE_KEY,
    applicationID: import.meta.env.VITE_NEW_RELIC_APP_ID
  }
};

// Production環境のみ有効化
export const initNewRelic = () => {
  if (import.meta.env.PROD && import.meta.env.VITE_NEW_RELIC_LICENSE_KEY) {
    new BrowserAgent(options);
  }
};
```

```typescript
// frontend/src/main.tsx
import { initNewRelic } from './lib/newrelic';

// Sentry初期化の後に
initNewRelic();
```

#### 自動収集される情報

- **Core Web Vitals**:
  - LCP (Largest Contentful Paint): 最大コンテンツの描画時間
  - FID (First Input Delay): 初回入力遅延
  - CLS (Cumulative Layout Shift): レイアウトのずれ

- **Page View Events**:
  - ページロード時間
  - DOMContentLoaded時間
  - リソースロード時間

- **AJAX Requests**:
  - APIリクエストの応答時間
  - エラー率
  - スループット

---

### バックエンド（Django）

#### インストール

```bash
# backend/requirements.txt
newrelic==9.5.0
```

```bash
pip install newrelic
```

#### Dockerfileの修正

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# ... 既存の設定 ...

# New Relicエージェント起動
CMD ["sh", "-c", "python manage.py collectstatic --noinput && newrelic-admin run-program gunicorn config.wsgi:application --bind 0.0.0.0:8000"]
```

#### 環境変数

```bash
# Render環境変数
NEW_RELIC_LICENSE_KEY=your_license_key
NEW_RELIC_APP_NAME=django-react-app-backend-production
NEW_RELIC_ENVIRONMENT=production
NEW_RELIC_DISTRIBUTED_TRACING_ENABLED=true
NEW_RELIC_LOG=stdout
NEW_RELIC_LOG_LEVEL=info
```

#### settings.py（オプション）

```python
# backend/config/settings/base.py
from decouple import config
import newrelic.agent

# New Relic初期化（本番環境のみ）
NEW_RELIC_LICENSE_KEY = config('NEW_RELIC_LICENSE_KEY', default='')

if not DEBUG and NEW_RELIC_LICENSE_KEY:
    newrelic.agent.initialize()
```

#### 自動収集される情報

- **トランザクション**:
  - エンドポイント別レスポンスタイム
  - スループット（リクエスト数/分）
  - エラー率

- **データベース**:
  - SQLクエリ実行時間
  - 低速クエリの特定
  - N+1問題の検出

- **外部サービス**:
  - Gemini API呼び出し時間
  - Upstash Redis通信時間
  - MotherDuck接続時間

- **インフラ**:
  - CPU使用率
  - メモリ使用量
  - ガベージコレクション

---

## 分散トレーシング

### 仕組み

```
1. フロントエンド（React）
   ├─ ユーザーがボタンクリック
   ├─ Sentryが Trace ID を生成（例: abc123）
   ├─ New Relicも Trace ID を生成（例: xyz789）
   └─ APIリクエストにヘッダーを付与
       ├─ sentry-trace: abc123-def456-1
       ├─ baggage: sentry-trace_id=abc123
       ├─ traceparent: 00-xyz789-def456-01
       └─ tracestate: newrelic=...

2. Django側で受信
   ├─ Sentry SDK が sentry-trace を読み取り
   ├─ New Relic Agent が traceparent を読み取り
   └─ 両方とも同じリクエストを追跡

3. エラー発生
   ├─ Sentry: abc123 で記録
   └─ New Relic: xyz789 で記録

4. Sentry画面
   ├─ エラー詳細を開く
   ├─ "Trace" タブをクリック
   └─ フロント→バックの流れが可視化
       [Frontend] Button Click
           ↓
       [Backend] TodoListView.get()
           ↓
       [Backend] SELECT * FROM todos
           ↓
       [Backend] Error: DoesNotExist
```

### リリースバージョンの統一

**重要**: フロントとバックで同じ`release`値を使う必要があります。

```yaml
# .github/workflows/deploy-all.yml
env:
  SENTRY_RELEASE: production@${{ github.sha }}  # 統一

jobs:
  deploy-backend:
    steps:
      - name: Deploy Backend
        env:
          RELEASE: ${{ env.SENTRY_RELEASE }}  # バックエンド
        run: |
          # Render環境変数を更新
  
  deploy-frontend:
    steps:
      - name: Deploy Frontend
        env:
          VITE_SENTRY_RELEASE: ${{ env.SENTRY_RELEASE }}  # フロントエンド
        run: |
          # Cloudflare Pages デプロイ
```

### 動作確認

#### 1. ブラウザのDevToolsで確認

```javascript
// Network タブ → API リクエスト → Headers
Request Headers:
  sentry-trace: abc123-def456-1
  baggage: sentry-trace_id=abc123,...
  traceparent: 00-xyz789-def456-01
  tracestate: newrelic=...
  newrelic: eyJ...
```

#### 2. Sentry画面で確認

```
Issues → エラーを開く → Trace タブ

Timeline:
  [12:34:56.100] Frontend: Button Click (TodoList.tsx:45)
  [12:34:56.150] Backend: GET /api/v1/todos/ (views.py:23)
  [12:34:56.200] Backend: SQL Query (50ms)
  [12:34:56.250] Backend: Error: DoesNotExist
```

---

## ダッシュボード構築

### Sentry

#### カスタムダッシュボード

```
Dashboards → Create Dashboard

Widgets:
  1. Error Rate by Endpoint
     - Type: Line Chart
     - Query: event.type:error
     - Group By: transaction
  
  2. Top Errors
     - Type: Table
     - Columns: Error, Count, Affected Users
     - Sort: Count DESC
  
  3. Error by Browser
     - Type: Pie Chart
     - Query: event.type:error
     - Group By: browser.name
  
  4. Response Time
     - Type: Line Chart
     - Query: event.type:transaction
     - Field: transaction.duration
```

### New Relic

#### カスタムダッシュボード（NRQL）

```sql
-- ページロード時間の推移
SELECT average(duration) 
FROM PageView 
WHERE appName = 'django-react-app-frontend-production'
FACET pageUrl 
SINCE 1 day ago 
TIMESERIES

-- 低速SQLクエリ Top 10
SELECT average(duration), query 
FROM Sql 
WHERE appName = 'django-react-app-backend-production'
FACET query 
SINCE 1 day ago 
LIMIT 10

-- エンドポイント別エラー率
SELECT percentage(count(*), WHERE error IS true) as 'Error Rate'
FROM Transaction 
WHERE appName = 'django-react-app-backend-production'
FACET request.uri 
SINCE 1 day ago

-- MotherDuck通信時間
SELECT average(duration) 
FROM External 
WHERE appName = 'django-react-app-backend-production' 
  AND host LIKE '%motherduck%'
SINCE 1 day ago 
TIMESERIES
```

---

## アラート設定

### Sentry

#### 1. エラー率アラート

```
Alerts → Create Alert Rule

Conditions:
  - Metric: Error Count
  - Threshold: > 10 errors in 5 minutes
  - Filter: environment:production

Actions:
  - Send notification to: Slack #alerts
  - Email: dev-team@example.com
```

#### 2. 新規エラーアラート

```
Alert Rule:
  - When: New issue is created
  - Level: error or fatal
  - Environment: production

Actions:
  - Slack notification (immediate)
```

### New Relic

#### 1. Apdexスコアアラート

```sql
-- Apdex < 0.8 が5分間続く
SELECT apdex(duration, t:0.5) 
FROM Transaction 
WHERE appName = 'django-react-app-backend-production'
```

#### 2. 低速クエリアラート

```sql
-- 平均クエリ実行時間 > 1秒
SELECT average(duration) 
FROM Sql 
WHERE appName = 'django-react-app-backend-production'
```

---

## トラブルシューティング

### エラー: CORS policy

```
Access to fetch at 'https://your-backend.onrender.com/api/v1/todos/' 
from origin 'https://your-frontend.pages.dev' has been blocked by CORS policy: 
Request header field sentry-trace is not allowed
```

**原因**: `CORS_ALLOW_HEADERS`に`sentry-trace`が含まれていない

**解決**:
```python
# backend/config/settings/base.py
CORS_ALLOW_HEADERS = list(default_headers) + [
    "sentry-trace",
    "baggage",
    "traceparent",
    "tracestate",
    "newrelic",
]
```

---

### エラー: Trace が繋がらない

**症状**: Sentry画面で「Trace」タブが表示されない

**原因1**: フロントとバックで`release`値が異なる

```yaml
# ❌ 異なる値
VITE_SENTRY_RELEASE: frontend-v1.2.3
RELEASE: backend-v1.0.0

# ✅ 同じ値
VITE_SENTRY_RELEASE: production@abc1234
RELEASE: production@abc1234
```

**原因2**: `tracePropagationTargets`にバックエンドURLが含まれていない

```typescript
// ❌ 不足
tracePropagationTargets: ["localhost"]

// ✅ 正しい
tracePropagationTargets: [
  "localhost",
  /^https:\/\/.*\.onrender\.com\/api/,
]
```

---

### エラー: New Relic にデータが送信されない

**症状**: New Relic画面が空

**原因1**: 環境変数が設定されていない

```bash
# Render環境変数を確認
NEW_RELIC_LICENSE_KEY=xxx  # ← これが必要
```

**原因2**: 起動コマンドが正しくない

```dockerfile
# ❌ 間違い
CMD ["gunicorn", "config.wsgi:application"]

# ✅ 正しい
CMD ["sh", "-c", "python manage.py collectstatic --noinput && newrelic-admin run-program gunicorn config.wsgi:application --bind 0.0.0.0:8000"]
```

---

### エラー: Sentry に大量のエラーが送信される

**症状**: 無料枠をすぐに使い切る

**解決1**: サンプリングレートを下げる

```python
# 10%のみ記録
traces_sample_rate=0.1
```

**解決2**: 特定のエラーを無視

```python
def _before_send(event, hint):
    # 404エラーは記録しない
    if event.get('status_code') == 404:
        return None
    
    # 外部API接続エラーは記録しない
    if 'ConnectionError' in str(hint.get('exc_info', '')):
        return None
    
    return event
```

---
