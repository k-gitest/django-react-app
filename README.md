# django-react-app

Django/React モノレポベースのSPAアプリケーション

## 概要

拡張性と保守性を重視したフルスタックWebアプリケーションです。バックエンドにDjango REST Framework、フロントエンドにReact + TypeScriptを採用し、レイヤードアーキテクチャによる明確な責務分離を実現しています。

## 主な特徴

- 🏗️ **スケール可能なモノレポ構成**: フロントエンドとバックエンドを一元管理し、チーム全体での仕様変更への迅速な対応を可能にします。
- 🎯 **チーム開発に適したレイヤードアーキテクチャ**: 複数人での並行開発を想定し、View/Service/Modelの責務を分離。コードの衝突（コンフリクト）を最小限に抑え、テスタビリティを向上させています。
- 🔐 **JWT認証**: dj-rest-auth + simplejwtによる堅牢な認証システム
- 🔍 **AIセマンティック検索**: Google Gemini API + Upstash Vectorによる自然言語検索。「明日の会議関連」などの曖昧な検索が可能
- 📊 **データ分析基盤（MotherDuck Analytics）**: イベントログのリアルタイム記録とDB状態の定期同期により、ユーザー行動とデータ状態を包括的に分析可能
- 🐳 **フロントエンド独立開発 (MSW)**: APIの実装を待たずに開発・テストが可能なMSWを活用。バックエンドへの依存を減らし、開発スピードを最大化します。
- 🧪 **テスト充実**: Playwright(E2E)、Vitest(Unit)、Django TestCase
- ☁️ **オンボーディングの高速化**: DockerおよびGitHub Codespacesに完全対応。環境構築の手間を省き、新メンバーが即日コードを書ける環境を提供します。
- 🚀 **自動化されたCI/CD**: GitHub Actionsによる自動テスト・デプロイパイプライン

## 技術スタック

### バックエンド
- **フレームワーク**: Django 4.2.7
- **API**: Django REST Framework 3.14.0
- **認証**: dj-rest-auth 7.0.1, djangorestframework-simplejwt 5.5.1
- **データベース**: PostgreSQL 17 (psycopg2-binary 2.9.9)
- **データウェアハウス**: MotherDuck (DuckDB), dlt 1.20.0
- **キャッシュ/セッション**: Redis (Upstash), django-redis 5.4.0
- **レート制限**: django-ratelimit 4.1.0
- **メール送信**: Resend 0.8.0
- **非同期処理**: QStash (Upstash)
- **ベクトル検索**: Google Gemini API (text-embedding-004), Upstash Vector
- **HTTPクライアント**: requests 2.31.0
- **サーバー**: gunicorn 21.2.0
- **その他**: django-cors-headers, python-dotenv, python-decouple

### フロントエンド
- **フレームワーク**: React 19.2.0, TypeScript 5.9.3
- **ビルドツール**: Vite 7.2.4
- **ルーティング**: React Router DOM 7.10.1
- **状態管理**: Zustand 5.0.9, TanStack Query 5.90.12
- **フォーム**: React Hook Form 7.68.0, Zod 4.1.13
- **UI**: Tailwind CSS 4.1.17, shadcn/ui
- **HTTPクライアント**: Ky 1.14.1
- **テスト**: Playwright 1.57.0, Vitest 4.0.15, MSW 2.12.4, playwright-msw 3.0.1
- **Linter**: ESLint 9.39.1

### インフラ（Terraform管理）
- **Neon**: PostgreSQLデータベース
- **Backblaze B2**: オブジェクトストレージ（S3互換）
- **Cloudflare Pages**: フロントエンドホスティング
- **Render**: バックエンドホスティング
- **Terraform Cloud**: インフラ状態管理

## プロジェクト構成

```text
/
├── backend/                    # Djangoバックエンド
│   ├── config/                # プロジェクト設定
│   │   ├── settings.py        # 環境設定
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── local.py
│   │   │   ├── production.py
│   │   │   └── test.py
│   │   ├── urls.py            # ルートURLルーティング
│   │   ├── wsgi.py / asgi.py  # サーバーインターフェース
│   │   └── __init__.py
│   │
│   ├── apps/
│   │   ├── analytics/
│   │   │   ├── views.py
│   │   │   ├── serializers.py
│   │   │   ├── tests.py
│   │   │   └── services.py
│   │   │
│   │   ├── data_pipeline/
│   │   │   ├── managements/commands
│   │   │   │     └──commands/
│   │   │   │          └── run_pipeline.py
│   │   │   ├── tests.py
│   │   │   ├── views.py
│   │   │   └── services.py
│   │   │
│   │   ├── common/
│   │   │   ├── infrastructure/
│   │   │   │   ├── email_client.py
│   │   │   │   ├── qstash_client.py
│   │   │   │   ├── vector_client.py
│   │   │   │   └── motherduck_client.py
│   │   │   ├── services/
│   │   │   │   ├── base_email.py
│   │   │   │   ├── base_qstash.py
│   │   │   │   ├── base_vector.py
│   │   │   │   ├── base_embedding.py
│   │   │   │   └── base_analytics.py
│   │   │   ├── exceptions.py
│   │   │   ├── error_handlers.py
│   │   │   ├── error_decorators.py
│   │   │   ├── error_reporting.py
│   │   │   ├── security.py
│   │   │   └── permissions.py
│   │   │
│   │   ├── users/                 # ユーザー管理アプリケーション
│   │   │   ├── models.py          # データモデル定義
│   │   │   ├── views.py           # APIビュー（薄いコントローラ）
│   │   │   ├── user_service.py    # ビジネスロジック層
│   │   │   ├── utils.py           # ユーティリティ関数
│   │   │   ├── urls.py            # アプリ固有のルーティング
│   │   │   ├── serializers.py     # DRFシリアライザ
│   │   │   ├── email_service.py   
│   │   │   ├── qstash_service.py  
│   │   │   ├── analytics_service.py  
│   │   │   ├── tests/             # テストコード
│   │   │   │   ├── test_models.py
│   │   │   │   └── test_services.py
│   │   │   ├── management/        # カスタムコマンド
│   │   │   │   └── commands/
│   │   │   │       └── seed_db.py
│   │   │   └── migrations/        # DBマイグレーション
│   │   │
│   │   ├── todos/
│   │   │   ├── views.py 
│   │   │   ├── models.py                    
│   │   │   ├── service.py                  
│   │   │   ├── serializers.py                  
│   │   │   ├── qstash_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── vector_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── webhook_service.py
│   │   │   └── urls.py                     
│   │   │
│   │   └── webhooks/                     
│   │       ├── __init__.py
│   │       ├── apps.py
│   │       └── urls.py        
│   │
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .gitignore
│
├── frontend/                   # Reactフロントエンド
│   ├── src/
│   │   ├── features/          # 機能単位のディレクトリ（今後追加）
│   │   │   └── auth/         # 認証機能
│   │   │       ├── components/
│   │   │       ├── hooks/
│   │   │       ├── services/
│   │   │       └── types/
│   │   │
│   │   ├── components/        # 共通コンポーネント
│   │   │   ├── form/          # フォーム関連
│   │   │   ├── layout/        # レイアウト（header/footer等）
│   │   │   └── ui/            # shadcn/ui コンポーネント
│   │   │
│   │   ├── pages/             # ページコンポーネント
│   │   │   ├── Home/
│   │   │   ├── Auth/
│   │   │   ├── Dashboard/
│   │   │   └── ...
│   │   │
│   │   ├── routes/            # ルーティング設定
│   │   │   ├── router.tsx
│   │   │   ├── auth-guard.tsx
│   │   │   └── guest-guard.tsx
│   │   │
│   │   ├── hooks/             # 共通カスタムフック
│   │   ├── lib/               # ユーティリティ・クライアント
│   │   │   ├── api-client.ts  # Kyベースのクライアント
│   │   │   ├── auth-client.ts
│   │   │   └── queryClient.ts
│   │   ├── schemas/           # Zodスキーマ
│   │   ├── types/             # TypeScript型定義
│   │   ├── errors/            # エラーハンドリング
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── tests/                 # テスト構成
│   │   ├── e2e/               # E2Eテスト（Playwright専用）
│   │   ├── unit/              # ユニットテスト（Vitest）
│   │   ├── integration/       # 統合テスト（Vitest）
│   │   ├── setup/             # セットアップファイル
│   │   ├── mocks/             # MSW設定
│   │   └── test-utils/        # テストユーティリティ
│   │
│   ├── playwright.config.ts   # Playwright設定
│   ├── vitest.config.ts       # Vitest設定
│   ├── package.json
│   ├── Dockerfile
│   └── .gitignore
│
├── .devcontainer/             # Dev Container設定
│   ├── devcontainer.json      # Codespaces/ローカル手動起動型
│   └── devcontainer-compose.json  # ローカルCompose統合型（自動起動）
│
├── terraform/                 # terraform設定
│   ├── modules/               # 共通モジュール（部品）
│   │   ├── cloudflare/
│   │   │   ├── main.tf        # リソース
│   │   │   ├── outputs.tf
│   │   │   └── variables.tf
│   │   ├── neon/
│   │   ├── render/
│   │   ├── backblaze/
│   │   ├── github/
│   │   └── upstash/
│   └── envs/                  # 環境ごとの定義
│       ├── production/              # 本番環境
│       │   ├── main.tf        # 各moduleを呼び出し、本番用変数を渡す
│       │   ├── outputs.tf
│       │   └── variables.tf
│       └── staging/           # ステージング環境
│
├── cicd/                 
│   ├── actions/               # 再利用可能なカスタムアクション
│   │   ├── setup-node/
│   │   │   └── actions.yml
│   │   └── setup-python/
│   └── workflows/             # CI/CDワークフロー
│
├── docker-compose.yml         # Docker構成
├── .gitignore
├── package.json               # ルートパッケージ設定
└── README.md
```

## セットアップ

### クイックスタート

このプロジェクトは4つの開発環境をサポートしています：

| 環境 | 特徴 |
|------|------|
| **GitHub Codespaces** | クラウド上で即座に開発開始、設定不要 |
| **Dev Container** | ローカルで自動セットアップ、VS Code統合 |
| **Docker Compose** | 柔軟な制御、CLI中心の開発 |
| **ローカル環境** | 完全な制御、環境構築の手間あり |

### 最速で始める

#### GitHub Codespaces の場合
```bash
# 1. GitHubリポジトリページから "Code" → "Codespaces" → "Create codespace"
# 2. Codespace起動後
docker compose up -d
cd frontend && npm install && npm run dev
```

#### Dev Container の場合
```bash
git clone <repository-url>
cd django-react-app
code .  # VS Codeで開く
# → "Reopen in Container" を選択
# → 自動セットアップ完了後、フロントエンド開発サーバーを起動
cd frontend && npm run dev
```

### 詳細なセットアップ手順

各環境の詳細な手順、トラブルシューティング、環境変数の設定については、**[docs/setup.md](docs/setup.md)** を参照してください。

---

## アーキテクチャ設計

### 設計哲学

本プロジェクトは**個人開発でありながら将来的なチーム開発を視野に入れた構成**を採用しています。責務の分離（Separation of Concerns）を徹底し、長期的な保守性を優先します。

**チーム開発を支える「コントラクト（契約）優先」開発**: 本プロジェクトでは、フロントエンドとバックエンドの境界を明確にするためにMSWを採用しています。これにより、API仕様を「契約」として先に定義し、両チームが並行して実装を進めるワークフローを可能にしています。

### レイヤードアーキテクチャ

現在採用している**レイヤードアーキテクチャ**は、DjangoとReactのエコシステムを最大限活用しながら、ビジネスロジックとインフラストラクチャを適切に分離した実用的な設計です。

#### バックエンド（Django）

```
Request → View → Serializer → Service → Model → Database
                     ↓           ↓
                 Validation  Business Logic
```

**各層の責務**:

| 層 | ファイル | 責務 |
|---|---|---|
| **View** | `views.py` | HTTPリクエスト/レスポンスの薄い層<br>・リクエストの受付とレスポンス返却のみ |
| **Serializer** | `serializers.py` | データの検証とシリアライズ<br>・リクエストデータのバリデーション<br>・モデルとJSONの相互変換 |
| **Service** | `service.py` | ビジネスロジックの中核<br>・複数モデルを跨ぐ処理<br>・外部API連携<br>・トランザクション管理 |
| **Model** | `models.py` | データスキーマと永続化<br>・データベーススキーマ定義 |

#### フロントエンド（React）

```
User Interaction
    ↓
Page/Component (プレゼンテーション層)
    ↓
Custom Hook (データフェッチ・状態管理の抽象化)
    ↓
Service (API呼び出しロジック)
    ↓
Backend API

[横断的関心事]
- TanStack Query: サーバー状態のキャッシュ管理
- Zustand: グローバルなクライアント状態（認証情報等）
```

**Feature-Driven構造**（今後の拡張方針）:

今後の機能追加は、テーブル（エンティティ）単位で`features/`配下に実装します：

```
src/features/
├── auth/          # 認証機能（実装済み）
├── users/         # ユーザー管理
├── products/      # 商品管理
└── orders/        # 注文管理
    ├── components/
    ├── hooks/
    ├── services/
    └── types/
```

### 設計の位置づけ

| 項目 | 評価 |
|---|---|
| **導入コスト** | ✅ 低い：フレームワークの標準構成に自然に統合 |
| **保守性** | ✅ 高い：ビジネスロジックがService層に集約 |
| **テスト容易性** | ✅ 高い：各層を独立してテスト可能 |
| **適切な抽象化** | ✅ 実用性とのバランスを重視 |
| **発展性** | ✅ 将来的により厳密なアーキテクチャへの移行も可能 |


---

## エラーハンドリング戦略

### 概要

本プロジェクトでは、**責務の明確な分離**と**適切な例外の伝播**により、堅牢で保守性の高いエラーハンドリングを実現しています。

```
【設計原則】
✅ 各層で処理すべきエラーのみを扱う
✅ 例外を適切に翻訳・伝播させる
✅ ユーザーに分かりやすいエラーメッセージを返す
✅ 重要なエラーを確実にモニタリングする
```

---

### 4つのコンポーネント

エラーハンドリングは以下の4つのコンポーネントで構成されています。

| コンポーネント | ファイル | 役割 |
|--------------|---------|------|
| **1. 独自例外** | `exceptions.py` | エラーの「型」を定義（BaseAppError等） |
| **2. デコレーター** | `error_decorators.py` | Django例外の自動変換（@service_error_handler） |
| **3. 統一ハンドラー** | `error_handlers.py` | 最終的なJSON変換（custom_exception_handler） |
| **4. モニタリング** | `error_reporting.py` | ログサービスへの報告（ErrorMonitor） |

**処理の流れ**:
```
例外発生 → @service_error_handler → custom_exception_handler → ErrorMonitor → ログサービス
           (Django例外を変換)      (JSON形式で返却)        (重要度判定・報告)
```

---

### 使い分けガイド

| 層 | エラー処理 | 使用するコンポーネント |
|---|-----------|---------------------|
| **View** | 行わない（統一ハンドラーに委譲） | なし |
| **Serializer** | DRF標準バリデーションのみ | なし |
| **Service（親）** | ビジネスロジックの統合 | @service_error_handler + ErrorMonitor.capture_and_continue |
| **Service（子）** | ドメインロジック | @service_error_handler |
| **BaseService** | Client例外 → ドメイン例外に変換 | try-catch（手動） |
| **Client** | 行わない（例外をそのまま発生） | なし |

---

### 実装例

#### Service層（典型的なパターン）

```python
@service_error_handler  # Django例外を自動変換
@transaction.atomic
def register_user(self, request, user_data: Dict) -> CustomUser:
    # 1. メインフロー（絶対に成功させる）
    if self.email_exists(email):
        raise UserAlreadyExistsError(email)  # 独自例外を送出
    
    user = self.create_user(...)
    
    # 2. 副作用の隔離（失敗してもメインフローは成功）
    if not settings.TESTING:
        transaction.on_commit(lambda: self._send_welcome_email_safely(user))

@staticmethod
def _send_welcome_email_safely(user: CustomUser):
    """副作用を安全に実行（失敗してもエラーを投げない）"""
    with ErrorMonitor.capture_and_continue(
        component='qstash',
        operation='send_welcome_email',
        service='UserRegistrationService',
        expected_errors=(QStashError,),
        user=user
    ):
        UserQStashService.send_welcome_email_async(...)
```

#### View層（典型的なパターン）

```python
def post(self, request, *args, **kwargs):
    # エラー処理は書かない（統一ハンドラーに委譲）
    response = super().post(request, *args, **kwargs)
    
    if response.status_code == 200:
        user = self._get_user_from_response(response)
        if user:
            UserAuthService.handle_login_success(user, request)
    
    return response
```

---

### レスポンス形式

統一エラーハンドラーは、すべての例外を以下の形式で返却します。

```json
{
  "error": "user_already_exists",
  "detail": "メールアドレス user@example.com は既に登録されています",
  "data": {
    "field": "email"
  }
}
```

**フロントエンドでの処理**:
```typescript
try {
  await registerUser(data);
} catch (error) {
  if (error instanceof ApiError) {
    if (error.code === 'user_already_exists') {
      toast.error(error.serverMessage);
    }
  }
}
```

---

### 詳細ドキュメント

エラーハンドリングの詳細については、以下のドキュメントを参照してください。

- **[docs/error-handling.md](docs/error-handling.md)** - 全体の設計と実装ガイド
  - 階層構造の詳細
  - 各コンポーネントの詳細説明
  - BaseService層での例外変換パターン
  - エラープロファイルの使い方
  - フロントエンド連携の詳細
  - ベストプラクティス集

---

## 認証システム

### 概要

**dj-rest-auth + djangorestframework-simplejwt**によるJWT Cookie認証を採用しています。

```
【主な特徴】
✅ HttpOnly Cookie による XSS 対策
✅ JWT トークンローテーション（リプレイ攻撃対策）
✅ emailベース認証（username不要）
✅ 自動トークンリフレッシュ
```

---

### 認証方式の選定理由

| 項目 | djoser（旧）| dj-rest-auth（採用）|
|---|---|---|
| **方式** | JWT（Bearer認証） | JWT（Cookie認証） |
| **トークン格納先** | localStorage / sessionStorage | HttpOnly Cookie |
| **セキュリティ上の懸念** | XSS攻撃 | CSRF攻撃（Djangoで対応） |
| **クライアント側の責務** | トークン管理が必要 | トークン管理不要 |

**採用理由**: WebアプリケーションではXSS攻撃のリスクが高いため、JavaScriptからアクセスできないHttpOnly Cookie方式を採用しました。

---

### 認証フロー

```
1. 新規登録  → POST /api/v1/auth/registration/
              ↓ HttpOnly Cookieでaccess-token, refresh-token発行
              ↓ JWT自動設定により、ログイン不要でダッシュボードへ
              
2. ログイン  → POST /api/v1/auth/login/
              ↓ HttpOnly Cookieでaccess-token, refresh-token発行
              
3. API呼び出し → Cookie自動送信（フロントエンドでのトークン操作不要）

4. トークン更新 → POST /api/v1/auth/token/refresh/
                 ↓ refresh-token Cookieが自動送信
                 ↓ 新しいaccess-tokenとrefresh-tokenを発行
                 
5. ログアウト  → POST /api/v1/auth/logout/
                ↓ refresh-tokenをブラックリスト化
                ↓ Cookieを削除
```

---

### 主要APIエンドポイント

| 機能 | Method | エンドポイント | 認証 |
|---|---|---|---|
| **新規登録** | POST | `/api/v1/auth/registration/` | 不要 |
| **ログイン** | POST | `/api/v1/auth/login/` | 不要 |
| **ログアウト** | POST | `/api/v1/auth/logout/` | Cookie自動送信 |
| **ユーザー情報取得** | GET | `/api/v1/auth/user/` | Cookie自動送信 |
| **トークンリフレッシュ** | POST | `/api/v1/auth/token/refresh/` | refresh-token Cookie |
| **パスワード変更** | POST | `/api/v1/auth/password/change/` | Cookie自動送信 |

---

### フロントエンド実装の簡素化

Cookie認証により、フロントエンド側のトークン管理が大幅に簡素化されました：

**不要になったコード**:
- ❌ localStorage/sessionStorageへのトークン保存
- ❌ Authorization ヘッダーの手動設定
- ❌ トークン期限の監視とリフレッシュロジック

**残った責務**:
- ✅ 認証エラー（401）の最終的なハンドリング
- ✅ ログインページへのリダイレクト

---

### セキュリティ設定

#### JWT設定

```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),   # 短命で安全
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,                   # トークンローテーション
    "BLACKLIST_AFTER_ROTATION": True,                # リプレイ攻撃対策
}
```

#### Cookie設定

```python
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'access-token',
    'JWT_AUTH_REFRESH_COOKIE': 'refresh-token',
    'JWT_AUTH_HTTPONLY': True,      # XSS対策の要
    'JWT_AUTH_SECURE': True,         # HTTPS必須（本番）
    'JWT_AUTH_SAMESITE': 'None',     # クロスオリジン対応
}
```

---

### TanStack Query による認証状態の同期

認証状態の管理を従来のuseEffectからTanStack Query (useQuery)へ移行し、Zustandと組み合わせることで以下の課題を解決しました。

**解決した課題**:

| 課題 | 解決方法 |
|------|---------|
| **競合状態（Race Condition）** | setQueryDataによる明示的な同期 |
| **UXのチラつき** | キャッシュの即時更新でガード通過を高速化 |
| **不要なリクエスト** | サーバー状態のキャッシュ管理 |

```typescript
// ログイン成功時
const loginMutation = useMutation({
  mutationFn: authService.login,
  onSuccess: (userData) => {
    // 1. Zustand Storeを即座に更新
    setUser(userData);
    
    // 2. TanStack Query キャッシュも同期
    queryClient.setQueryData(['auth', 'me'], userData);
    
    // 3. リダイレクト（キャッシュがあるので即座にガード通過）
    navigate('/dashboard');
  }
});
```

---

### 詳細ドキュメント

認証システムの詳細については、以下のドキュメントを参照してください。

- **[docs/authentication.md](docs/authentication.md)** - 認証システム詳細ガイド
  - 設計変更の経緯（djoserからの移行理由）
  - カスタムユーザーモデルの実装
  - CustomRegisterViewの実装詳細
  - CSRF対策の詳細
  - 本番環境での設定変更
  - TanStack Query統合の詳細
  - トラブルシューティング

---

## Todo管理機能

### 概要

CRUD操作を含むタスク管理機能を実装。優先度設定、進捗管理、統計表示など、実用的なタスク管理に必要な機能を備えています。

### 主な機能

| 機能 | 説明 |
|---|---|
| **タスク作成** | タイトル、優先度、進捗を設定して新規タスクを作成 |
| **タスク一覧** | 優先度別、進捗別にタスクを表示 |
| **タスク編集** | タイトル、優先度、進捗をモーダルで編集 |
| **タスク削除** | 確認ダイアログ付きの安全な削除 |
| **進捗管理** | スライダーで0-100%の進捗を設定、チェックボックスで即座に完了切替 |
| **統計表示** | 優先度別の件数と進捗分布をグラフで可視化 |

### 技術的特徴

#### バックエンド（Django）

**実装構成**:
```
backend/todos/
├── models.py          # Todoモデル定義
├── serializers.py     # DRFシリアライザ
├── views.py          # ViewSet（CRUD API）
├── service.py        # ビジネスロジック層
├── urls.py           # APIエンドポイント
└── tests/            # テストコード
```

**データモデル**:
```python
class Todo(models.Model):
    user = ForeignKey(User)           # ユーザー紐付け
    todo_title = CharField(max_length=255)  # タスク名
    priority = CharField(choices=['HIGH', 'MEDIUM', 'LOW'])  # 優先度
    progress = IntegerField(0-100)    # 進捗率
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

**APIエンドポイント**:

| エンドポイント | Method | 説明 | 認証 |
|--------------|--------|-----|------|
| `/api/v1/todos/` | GET | タスク一覧取得 | 必須 |
| `/api/v1/todos/` | POST | タスク作成 | 必須 |
| `/api/v1/todos/{id}/` | GET | タスク詳細取得 | 必須 |
| `/api/v1/todos/{id}/` | PATCH | タスク更新 | 必須 |
| `/api/v1/todos/{id}/` | DELETE | タスク削除 | 必須 |
| `/api/v1/todos/stats/` | GET | 優先度別統計 | 必須 |
| `/api/v1/todos/progress-stats/` | GET | 進捗分布統計 | 必須 |

#### フロントエンド（React + TypeScript）

**実装構成**:
```
frontend/src/features/todo/
├── components/
│   ├── TodoList.tsx              # タスク一覧表示
│   ├── TodoItem.tsx              # 個別タスクカード
│   ├── TodoCreateForm.tsx        # 作成フォーム
│   ├── TodoEditModal.tsx         # 編集モーダル
│   ├── TodoForm.tsx              # 共通フォームロジック
│   ├── TodoStatsChart.tsx        # 優先度別統計グラフ
│   └── TodoProgressChart.tsx     # 進捗分布グラフ
│
├── hooks/
│   ├── useTodos.ts               # CRUD操作フック
│   ├── useTodoStats.ts           # 優先度統計フック
│   └── useProgressStats.ts       # 進捗統計フック
│
├── services/
│   └── todo-service.ts           # API呼び出しロジック
│
└── types/
    └── index.ts                  # 型定義
```

**状態管理とデータフェッチ**:

```typescript
// TanStack Query による楽観的更新
const { todos, createTodo, updateTodo, deleteTodo } = useTodos();

// 楽観的更新の実装例
const createMutation = useApiMutation({
  mutationFn: todoService.createTodo,
  onMutate: async (newTodo) => {
    // 1. 進行中のクエリをキャンセル
    await queryClient.cancelQueries({ queryKey: ['todos'] });
    
    // 2. 現在のキャッシュを保存（ロールバック用）
    const previousTodos = queryClient.getQueryData(['todos']);
    
    // 3. 楽観的更新: 仮IDで即座にUIに反映
    queryClient.setQueryData(['todos'], (old) => [...old, optimisticTodo]);
    
    return { previousTodos };
  },
  onError: (err, variables, context) => {
    // 4. エラー時: ロールバック
    queryClient.setQueryData(['todos'], context.previousTodos);
  },
  onSettled: () => {
    // 5. 最後に: サーバーと同期
    queryClient.invalidateQueries({ queryKey: ['todos'] });
  },
});
```

**UIコンポーネント**:
- **shadcn/ui**: Button, Card, Dialog, Select, Slider, Alert等
- **Radix UI**: アクセシブルなプリミティブコンポーネント
- **Recharts**: 統計グラフの描画

### 技術的な実装のポイント

#### 楽観的更新（Optimistic Update）

TanStack Queryの機能を活用し、サーバーの応答を待たずにUIを即座に更新します：

```typescript
const createMutation = useApiMutation({
  mutationFn: todoService.createTodo,
  onMutate: async (newTodo) => {
    // 1. 進行中のクエリをキャンセル
    await queryClient.cancelQueries({ queryKey: ['todos'] });
    
    // 2. 現在のキャッシュを保存（ロールバック用）
    const previousTodos = queryClient.getQueryData(['todos']);
    
    // 3. 楽観的更新: 仮IDで即座にUIに反映
    queryClient.setQueryData(['todos'], (old) => [...old, optimisticTodo]);
    
    return { previousTodos };
  },
  onError: (err, variables, context) => {
    // エラー時: ロールバック
    queryClient.setQueryData(['todos'], context.previousTodos);
  },
  onSettled: () => {
    // 最後に: サーバーと同期
    queryClient.invalidateQueries({ queryKey: ['todos'] });
  },
});
```

**効果**: タスクの追加・編集時に通信待機がなく、即座にUIに反映されるためUXが向上

#### データ集計の効率化

Django ORMの`aggregate`と`annotate`を使用し、データベース側で集計を実行：

```python
# 進捗率の分布を20%刻みで集計
Todo.objects.filter(user=user).aggregate(
    range_0_20=Count(Case(When(progress__lte=20, then=1))),
    range_21_40=Count(Case(When(progress__gt=20, progress__lte=40, then=1))),
    # ...
)
```

**効果**: Python側でループ処理せず、DBで一括計算することでパフォーマンスを最適化

#### 認可の徹底

Service層で必ず`filter(user=user)`を適用し、他人のデータへのアクセスを防止：

```python
@staticmethod
def get_user_todos(user):
    """ユーザー自身のタスクのみを取得（認可の担保）"""
    return Todo.objects.filter(user=user)
```

**効果**: View層に認可ロジックを書かず、Service層で一元管理することで保守性向上

---

---

## ベクトル検索機能（セマンティック検索）

### 概要

Google Gemini APIとUpstash Vectorを使用した**セマンティック検索**機能を実装。自然言語でTodoを検索できます。

**検索例**:
- "明日の会議関連のタスク" → 会議資料作成、プレゼン準備など
- "プログラミングの勉強" → Python学習、React練習など

---

### アーキテクチャ

```
Todo作成/更新
    ↓
QStash にメッセージ送信（即座にレスポンス）
    ↓
Webhook エンドポイント（/api/v1/webhooks/vector-indexing）
    ↓
Gemini API でベクトル化（768次元）
    ↓
Upstash Vector に保存
```

**非同期処理のメリット**:
- ⚡ Todo作成が高速（50-100ms、3-5倍高速化）
- 🔄 QStashの自動リトライ（最大3回）
- 🐳 Renderのスリープ対応

---

### 使用技術

| サービス | 用途 | 選定理由 |
|---------|------|---------|
| **Google Gemini API** | テキストのベクトル化 | 永久無料枠（1,500リクエスト/日）、高品質 |
| **Upstash Vector** | ベクトルデータベース | サーバーレス課金、既存Upstashアカウント統合 |
| **QStash** | 非同期処理キュー | 自動リトライ、Todo CRUD操作を高速化 |

**コスト**: $0/月（無料枠のみ使用）

---

### 主な機能

| 機能 | 説明 |
|------|------|
| **セマンティック検索** | 自然言語でTodoを検索 |
| **自動ベクトル化** | Todo作成・更新時に自動でベクトル化（非同期） |
| **高速レスポンス** | ベクトル化を待たずに即座にレスポンス（50-100ms） |
| **ユーザー分離** | 他人のTodoは検索されない（user_id フィルタ） |
| **一括インデックス** | 既存Todoを一括でベクトル化 |

---

### 使用例

#### セマンティック検索

```bash
# 基本的な検索
GET /api/v1/todos/search/?q=明日の会議関連
Authorization: Bearer <access-token>

# パラメータ指定
GET /api/v1/todos/search/?q=プログラミング&top_k=10&min_score=0.6

# レスポンス例
{
  "query": "明日の会議関連",
  "results": [
    {
      "id": 15,
      "score": 0.87,
      "title": "会議資料の作成",
      "priority": "HIGH",
      "progress": 50
    }
  ],
  "count": 1
}
```

#### 初期データのインデックス

```bash
# 既存のTodoをベクトルインデックスに追加
POST /api/v1/todos/bulk-index/
Authorization: Bearer <access-token>

# レスポンス
{
  "message": "インデックス処理をバックグラウンドで開始しました",
  "status": "queued"
}
```

---

### 環境変数

```bash
# backend/.env

# Google Gemini API (Embedding)
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXX

# Upstash Vector (Vector Database)
UPSTASH_VECTOR_REST_URL=https://xxx-xxx.upstash.io
UPSTASH_VECTOR_REST_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# QStash（既存）
QSTASH_TOKEN=your_qstash_token
QSTASH_CURRENT_SIGNING_KEY=sig_xxxxxxxxxxxxx
QSTASH_NEXT_SIGNING_KEY=sig_xxxxxxxxxxxxx
WEBHOOK_BASE_URL=https://your-backend.onrender.com
```

---

### パフォーマンス比較

| 処理 | 同期（変更前） | 非同期（変更後） | 改善 |
|------|--------------|----------------|------|
| **Todo作成** | 300-500ms | 50-100ms | **3-5倍高速** ⚡ |
| **Todo更新** | 300-500ms | 50-100ms | **3-5倍高速** ⚡ |
| **Todo削除** | 100-200ms | 50-100ms | **1-2倍高速** ⚡ |
| **検索** | 100-300ms | 100-300ms | 同じ（同期処理） |

---

### 詳細ドキュメント

ベクトル検索機能の詳細については、以下のドキュメントを参照してください。

- **[docs/vector-search.md](docs/vector-search.md)** - ベクトル検索詳細ガイド
  - 非同期処理の実装詳細
  - Gemini API設定
  - Upstash Vector設定
  - QStash Service実装
  - セキュリティ設定
  - 運用とモニタリング
  - トラブルシューティング
  - 将来の拡張計画（チャンク化、Pinecone移行等）

---

## MotherDuck Analytics（データ分析基盤）

### 概要

**MotherDuck**（クラウドDWH）を使用して、アプリケーションのイベントログとDB状態を分析可能にしています。

```
【データ分析の目的】
✅ イベントログ: ユーザー行動のリアルタイム記録
✅ DB状態同期: データの最終状態を定期的に記録
✅ 分析基盤: ユーザー行動とデータ状態を包括的に分析
```

---

### アーキテクチャ

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

### アーキテクチャ選定: ハイブリッドアプローチ

**Webhook + dlt バッチETL** を採用（CDC方式は見送り）

| 手法 | リアルタイム性 | 複雑度 | コスト | 採用 |
|------|--------------|--------|--------|------|
| **CDC（論理レプリケーション）** | ⭐⭐⭐⭐⭐ | 非常に複雑 | $40-50/月 | ❌ |
| **Webhook方式** | ⭐⭐⭐⭐⭐ | 中程度 | $0 | ✅ |
| **dlt バッチETL** | ⭐⭐⭐☆☆ | シンプル | $0 | ✅ |

**採用理由**:
- ✅ wal_level変更不要（不可逆な設定変更を回避）
- ✅ 常駐プロセス不要（Renderスリープ対応）
- ✅ WAL肥大化リスクなし
- ✅ 簡単にロールバック可能
- ✅ $0/月で運用可能

---

### データ収集方法

#### 1. 同期的なイベント記録（Realtime Logging）

**目的**: ユーザーの行動をリアルタイムで記録

| テーブル | イベント種別 | 記録タイミング |
|---------|------------|--------------|
| `logs.auth_events` | login, logout, register, login_failed | 認証時に即座に記録 |
| `logs.todo_events` | create, update, delete, complete | CRUD操作時に即座に記録 |

**実装例**:
```python
# ログインイベントの記録
AnalyticsService.log_auth_event(
    user=user,
    event_type="login",
    request=request,
    success=True
)
```

**分析クエリ例**:
```sql
-- 時間帯別のログイン数
SELECT 
    hour,
    COUNT(*) as login_count
FROM my_db.logs.auth_events
WHERE event_type = 'login'
GROUP BY hour
ORDER BY hour;
```

---

#### 2. 非同期的なDB状態同期（Batch ETL）

**目的**: DBの最終状態を定期的にDWHに同期して、分析を可能にする

| テーブル | 同期方式 | 実行頻度 |
|---------|---------|---------|
| `dwh.custom_user` | 増分同期（merge） | 15分ごと |
| `dwh.todos_todo` | 増分同期（merge） | 15分ごと |

**技術スタック**:
- **dlt** (Data Load Tool) - PostgreSQL → MotherDuck ETL
- **QStash** (Upstash) - スケジュール実行（Cron）
- **MotherDuck** - クラウドDWH

**実装**:
```python
# dlt_worker/pipeline.py
import dlt
from dlt.sources.sql_database import sql_database

source = sql_database(
    credentials={...},
    table_names=["custom_user", "todos_todo"],
    incremental=dlt.sources.incremental("updated_at"),
)

# MotherDuckに同期
pipeline = dlt.pipeline(
    pipeline_name="django_react_app",
    destination="motherduck",
    dataset_name="django_react_app_dwh"
)

pipeline.run(source)
```

**手動実行**:
```bash
# パイプラインを手動実行
docker compose exec backend python dlt_worker/pipeline.py
```

---

### イベントログとDB状態の使い分け

| 分析内容 | 使用するデータ | 理由 |
|---------|-------------|------|
| ユーザーの行動履歴 | `logs.auth_events`, `logs.todo_events` | イベントログは履歴が残る |
| 現在のユーザー数 | `dwh.custom_user` | DB状態は最新の状態を反映 |
| Todo完了までの時間 | `logs.todo_events` | イベントログに作成・完了のタイムスタンプがある |
| 現在の未完了Todo数 | `dwh.todos_todo` | DB状態は最新の進捗を反映 |
| ユーザー登録後の行動分析 | 両方を結合 | 登録イベント + 現在のTodo状況 |

---

### 環境変数

```bash
# PostgreSQL (Neon)
PGHOST=ep-xxx.aws.neon.tech
PGDATABASE=neondb
PGUSER=neondb_owner
PGPASSWORD=xxx
PGPORT=5432

# MotherDuck
MOTHERDUCK_TOKEN=your_motherduck_token

# QStash (スケジュール実行用)
QSTASH_TOKEN=qstash_xxx
QSTASH_CURRENT_SIGNING_KEY=sig_xxx
QSTASH_NEXT_SIGNING_KEY=sig_xxx
WEBHOOK_BASE_URL=https://your-app.onrender.com
```

---

### QStash Schedules 設定

**スケジュール名**: `dlt-pipeline-sync`

**Cron式**: `*/15 * * * *` （15分ごと）

**Destination**: `https://your-app.onrender.com/api/v1/webhooks/dlt-pipeline`

**Retry設定**:
- Retries: 3
- Retry Delay: `5000 * (retried + 1)` （5秒、10秒、15秒）

---

### MotherDuckでの確認方法

#### MotherDuck Web UIにアクセス
```
https://app.motherduck.com/
```

#### データベース構造
```
my_db/
├── logs/
│   ├── auth_events (認証イベントログ)
│   └── todo_events (Todoイベントログ)
│
└── django_react_app_dwh/
    ├── custom_user (ユーザー最終状態)
    ├── todos_todo (Todo最終状態)
    ├── _dlt_version (dltメタデータ)
    ├── _dlt_loads (同期履歴)
    └── _dlt_pipeline_state (パイプライン状態)
```

#### 同期履歴の確認
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

---

### 詳細ドキュメント

MotherDuck Analyticsの詳細については、以下のドキュメントを参照してください。

- **[docs/analytics.md](docs/analytics.md)** - データ分析基盤詳細ガイド
  - アーキテクチャ選定の経緯（CDC検討からdlt採用まで）
  - CDC（論理レプリケーション）を見送った理由
  - Webhook方式の実装詳細
  - dlt バッチETLの実装詳細
  - スケジュール実行方法の比較（Render Cron vs QStash）
  - 分析クエリ例
  - トラブルシューティング

---

## パフォーマンス最適化

### Redis による最適化

**Upstash Redis**を使用して、キャッシュ、セッション管理、レート制限を実装しています。

#### 1. 統計データのキャッシュ
```python
# backend/todos/service.py
CACHE_TIMEOUT = 900  # 15分

@staticmethod
def get_priority_stats(user):
    cache_key = f"todo_stats:{user.id}:priority"
    stats = cache.get(cache_key)
    
    if stats is None:
        stats = Todo.objects.filter(user=user) \
            .values('priority') \
            .annotate(count=Count('id'))
        cache.set(cache_key, stats, CACHE_TIMEOUT)
    
    return stats
```

- キャッシュがあればRedisから取得
- なければDBで集計してRedisに保存
- Todo作成・更新・削除時に`cache.delete()`で無効化

---

#### 2. レート制限
```python
# backend/users/views.py
from django_ratelimit.decorators import ratelimit

@method_decorator(ratelimit(key='ip', rate='5/5m', method='POST', block=True), 
                  name='dispatch')
class CustomLoginView(LoginView):
    """ログイン試行を5分間に5回までに制限"""
    pass

@method_decorator(ratelimit(key='ip', rate='3/1h', method='POST', block=True), 
                  name='dispatch')
class CustomRegisterView(RegisterView):
    """新規登録を1時間に3回までに制限"""
    pass
```

**エラーハンドリング**:
```python
# backend/users/exceptions.py
def custom_exception_handler(exc, context):
    if isinstance(exc, Ratelimited):
        return Response(
            {"detail": "リクエストが多すぎます。しばらく時間を置いてから再度お試しください。"},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    return exception_handler(exc, context)
```

**保護対象**:

| エンドポイント | 制限 |
|-------------|-----|
| `/api/v1/auth/login/` | 5回/5分 |
| `/api/v1/auth/registration/` | 3回/1時間 |

---

#### 3. セッション管理
```python
# backend/config/settings.py
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": getenv("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_KWARGS": {
                "ssl_cert_reqs": None,  # Upstash SSL対応
            },
        },
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_AGE = 1209600  # 2週間
```

- セッションデータをRedisに保存
- PostgreSQLの負荷を軽減

---

### 使用用途まとめ

| 用途 | 保持期間 | 無効化タイミング |
|-----|---------|---------------|
| **統計キャッシュ** | 15分 | Todo作成・更新・削除時 |
| **レート制限カウンター** | 5分〜1時間 | 自動（TTL切れ） |
| **セッション** | 2週間 | ログアウト時 |

---

### 環境変数
```bash
# backend/.env
REDIS_URL=rediss://default:password@region.upstash.io:6379
```

**重要**: `rediss://`（sが2つ）を使用してください。Upstash は TLS 必須です。

---

## メール送信機能（非同期処理）

### 概要

ユーザー登録時に**QStash + Resend**を使用してウェルカムメールを非同期送信します。

**アーキテクチャ**:
```
ユーザー登録
    ↓
QStash にメッセージ送信（即座にレスポンス）
    ↓
Webhook エンドポイント（/api/v1/webhooks/send-welcome-email）
    ↓
Resend でメール送信
```

---

### 使用技術

| サービス | 用途 | 選定理由 |
|---------|------|---------|
| **QStash** | 非同期タスクキュー | 自動リトライ、サーバーレス課金、メンテナンス不要 |
| **Resend** | メール送信 | 開発者フレンドリーなAPI、高い到達率 |

---

### メリット

- ⚡ **ユーザー登録が高速**: メール送信を待たずに即座にレスポンス
- 🔄 **自動リトライ**: QStashが失敗時に自動で再送（最大3回）
- 🐳 **Renderのスリープ対応**: サーバーがスリープしていても問題なし
- 🧪 **テストフレンドリー**: テスト環境では自動的に無効化

---

### 実装の流れ

```python
# 1. ユーザー登録時
@transaction.atomic
def register_user(self, request, user_data):
    # ユーザー作成
    user = self.command_service.create_user_with_adapter(...)
    
    # メール送信を予約（DB保存成功後に実行）
    if not settings.TESTING:
        transaction.on_commit(
            lambda: self._send_welcome_email_safely(user)
        )
    
    return user

# 2. メール送信を安全に実行（失敗してもエラーを投げない）
@staticmethod
def _send_welcome_email_safely(user):
    with ErrorMonitor.capture_and_continue(
        component='qstash',
        operation='send_welcome_email',
        service='UserRegistrationService',
        expected_errors=(QStashError,),
        user=user
    ):
        UserQStashService.send_welcome_email_async(
            email=user.email,
            first_name=user.first_name or "User"
        )
```

---

### 環境変数

```bash
# backend/.env
QSTASH_TOKEN=your_qstash_token
QSTASH_CURRENT_SIGNING_KEY=sig_xxx
QSTASH_NEXT_SIGNING_KEY=sig_xxx
RESEND_API_KEY=re_xxx
WEBHOOK_BASE_URL=https://your-backend.onrender.com
FRONT_URL=https://your-frontend.pages.dev
```

---

### セキュリティ

| 機能 | 実装 |
|-----|------|
| **署名検証** | QStashからのリクエストをHMAC-SHA256で検証 |
| **レート制限** | 登録エンドポイントを3回/時間に制限 |
| **テスト環境** | メール送信とレート制限を自動無効化 |

---

### 詳細ドキュメント

メール送信機能の詳細については、以下のドキュメントを参照してください。

- **[docs/email-sending.md](docs/email-sending.md)** - メール送信機能詳細ガイド
  - 実装ファイル構成
  - QStash Service実装
  - Resend設定
  - Webhook実装
  - 開発環境での動作確認
  - トラブルシューティング

---

## データベース戦略

### 採用：Neon PostgreSQL + Upstash Redis

本プロジェクトでは、永続化データに**Neon (PostgreSQL)**、揮発性データに**Upstash Redis**を採用しています。

**役割分担**:

| データ種別 | ストレージ | 用途 |
|----------|----------|-----|
| **永続データ** | PostgreSQL | ユーザー情報、Todo、認証情報 |
| **キャッシュ** | Redis | 統計集計結果、APIレスポンス |
| **レート制限** | Redis | IP制限カウンター |
| **セッション** | Redis | ユーザーセッション |

### Neon PostgreSQL
**選定理由**:

| 理由 | メリット |
|---|---|
| **ブランチ機能** | 開発・ステージング・テスト環境ごとにDBの軽量なコピー（ブランチ）を無料で作成・破棄可能。テストの再現性と環境分離が容易 |
| **移植性** | 標準PostgreSQL準拠のため、将来的なDB移行が容易。ベンダーロックインのリスクが低い |
| **低レイテンシ** | Renderと同じリージョン配置でプライベートネットワーク経由の高速通信が可能 |

### Upstash Redis
**選定理由**:

| 理由 | メリット |
|---|---|
| **サーバーレス課金** | 使用量ベースの従量課金 |
| **低レイテンシ** | Renderと同じリージョン配置可能 |
| **フルマネージド** | メンテナンス・スケーリング不要 |

### デプロイ構成と速度最適化

**原則**: アプリケーション（Render）とDB（Neon/Redis）は**同じリージョン**に配置すること

| 配置 | 速度 | 理由 |
|---|---|---|
| **同じリージョン** | ⚡ 最速（推奨） | Renderのプライベートネットワーク経由で通信。インターネットを経由せず、レイテンシ最小 |
| **異なるリージョン** | 🐢 低速 | 物理的な距離とネットワークホップが増加し、レイテンシが高くなる |

**推奨構成**:

```
本番環境:
  Render (us-west) 
    ↕️ プライベートネットワーク（低レイテンシ）
  Neon (us-west)

開発環境:
  Neon Branch: development
  Neon Branch: staging
  Neon Branch: feature/xxx (必要に応じて作成・削除)
```

### ベンダーロックイン対策

**方針**: 「付加価値機能（Neonのブランチ等）は活用しつつ、データの移植性は高く保つ」

Renderの提供する専用DBサービスを避けたのは、移植性の高いPostgreSQL標準を採用することで、将来的なデプロイ先の自由度を維持するためです。

**ポイント**:
- ✅ PostgreSQL標準準拠により他のPostgreSQLサービスへの移行が容易
- ✅ Neonの付加価値機能（ブランチ、オートスケール等）を活用しつつ、データ自体はポータブル
- ✅ 将来的なインフラ変更の柔軟性を確保
- ✅ ベンダー依存を最小限に抑えたアーキテクチャ

この構成により、高速なデータアクセスと環境の柔軟性を両立できます。


---

## HTTPクライアント戦略

### 採用：Ky

**選定経緯**:

当初、カスタム`FetchClient`を実装していましたが、以下の理由からライブラリ採用に方針転換：

> **核心的な気づき**: 「目的はアプリケーション開発であり、HTTPクライアント開発ではない」

**Ky採用の理由**:

| 項目 | Axios | **Ky（採用）** |
|---|---|---|
| バンドルサイズ | ~13KB | ~5KB ⭐ |
| API設計 | XMLHttpRequest風 | Fetch API風 ⭐ |
| リトライ | プラグイン必要 | 標準機能 ⭐ |
| 学習コスト | 低い | 低い（Fetch APIベース） ⭐ |

### 実装方針

Service層でラップすることで、プロジェクト全体への影響を最小化しています。

---

## テスト戦略

本プロジェクトでは、**テストの責務を明確に分離**し、テストが肥大化・形骸化しない構成を採用しています。

### テスト設計の基本方針

```
        /\
       /  \  E2Eテスト
      /----\  - ユーザー視点の統合テスト
     /      \ - CI/CDでの品質保証
    /--------\ 
   /          \ 統合テスト
  /------------\ - 機能単位の統合検証
 /--------------\ - APIモック使用
/________________\ 
    ユニットテスト
    - 単一責務の検証
    - 高速実行
```

### バックエンド（Django TestCase）

**テスト対象と方針**:

| 層 | テスト対象 | アプローチ |
|---|---|---|
| **Service層** | ビジネスロジック | 純粋関数としてテスト（ORMをモック） |
| **View層** | API疎通確認 | エラーハンドリングと基本的なレスポンスのみ |
| **Model層** | データ制約 | 必要最小限（Djangoの機能を信頼） |

**配置**: `backend/users/tests/`

---

### フロントエンド（React + TypeScript）

#### テスト構成

| テストレイヤー | 目的 | ツール | 対象 |
|--------------|------|-------|------|
| **Unit** | 単一責務の検証 | Vitest + Testing Library | hooks / utils / 単純なコンポーネント |
| **Integration** | 機能単位の統合検証 | Vitest + Testing Library + MSW | pages / features |
| **E2E** | ユーザー視点の統合テスト | Playwright + playwright-msw | 重要なユーザーフロー |

**配置**:
- ユニット/統合: `tests/unit/`, `tests/integration/`
- E2E: `tests/e2e/`
- モック: `tests/mocks/`
- セットアップ: `tests/setup/`

#### MSWの使用

**Node.js環境（Vitest）**: `tests/mocks/server.ts`
- ユニットテストと統合テストで使用
- `tests/setup/vitest.setup.ts` で自動セットアップ

**ブラウザ環境（Playwright）**: `tests/test-utils/playwright-msw.ts`
- E2Eテストでplaywright-mswを使用
- テストごとにハンドラーを上書き可能

#### E2Eテスト戦略

CI/CDでE2Eテストを実行する時点では、フロントエンドはビルド済み（`dist/`）だが、バックエンドAPIはまだデプロイされていないため、**MSWでAPIをモック**してテストを実行します。

**メリット**:
- デプロイ前に全機能とエッジケースを検証
- サーバー負荷を発生させない
- 高速で安定したテスト実行

#### 認証済み/未認証テストの分離

Playwrightでは、認証状態を保存・再利用することで、テストの高速化と保守性を向上：

| プロジェクト | 対象 | 認証状態 |
|------------|------|---------|
| `setup` | 認証セットアップ | - |
| `chromium` | 未認証テスト | なし |
| `auth_chromium` | 認証済みテスト | `playwright-results/.auth/user.json` |

**セットアップ**: `tests/setup/auth.setup.ts`
- ログイン処理を一度だけ実行
- 認証状態を `.auth/user.json` に保存
- 認証済みテストはこのファイルを読み込んで開始

#### E2Eテストにおけるリトライ制御

E2Eテスト環境では、React Queryのリトライ機能が無限ループを引き起こす可能性があるため、**windowオブジェクトを使った環境判定**でリトライを制御しています。

**実装方法**:

1. **queryClient.ts でE2E環境を検出**
```typescript
// frontend/src/lib/queryClient.ts
const isE2ETest = typeof window !== 'undefined' && window.__IS_E2E_TESTING__;

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: isE2ETest ? false : 3,  // E2E環境ではリトライ無効
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
    },
  },
});
```

2. **Playwright test-utils でフラグを設定**
```typescript
// tests/test-utils/playwright-msw.ts
import { test as base, expect } from '@playwright/test';
import { createWorkerFixture } from 'playwright-msw';
import { handlers } from '@tests/mocks';

const test = base.extend({
  worker: createWorkerFixture(handlers),
  http,
});

// すべてのE2Eテストで自動的にフラグを設定
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    (window as any).__IS_E2E_TESTING__ = true;
  });
});

export { expect, test };
```

**メリット**:
- ✅ ビルド済みアーティファクトに対してもテスト可能（`import.meta.env.MODE`に依存しない）
- ✅ リトライによる無限ループを防止し、テストが高速化
- ✅ エラーハンドリングのテストが確実に動作

---

### テスト実行コマンド

#### バックエンド

```bash
# テスト実行
docker compose exec backend python manage.py test

# 特定のテストのみ
docker compose exec backend python manage.py test users.tests.test_services

# カバレッジ
docker compose exec backend coverage run --source='.' manage.py test
docker compose exec backend coverage report
```

#### フロントエンド

```bash
# ユニット・統合テスト
npm run test                # 実行
npm run test:watch          # Watchモード
npm run test:coverage       # カバレッジ

# E2Eテスト
npm run test:e2e            # 実行
npm run test:e2e:ui         # UIモード

# 特定のプロジェクトのみ
npx playwright test --project=chromium        # 未認証
npx playwright test --project=auth_chromium   # 認証済み
```

---

### テスト戦略のまとめ

| テストタイプ | 本数 | API | 実行環境 | 所要時間 | 実行タイミング |
|------------|------|-----|---------|---------|--------------|
| **ユニット** | 多数 | - | Node.js (Vitest) | 数秒 | 毎コミット |
| **統合** | 中程度 | MSW | Node.js (Vitest) | 30秒-1分 | 毎コミット |
| **E2E** | 多数 | MSW | ブラウザ (Playwright) | 5-10分 | CI（デプロイ前） |

**テスト設計の原則**:

1. **責務の明確化**: 各レイヤーでテストする内容を明確に分離
2. **高速フィードバック**: ユニットテストは数秒で完了
3. **現実的なカバレッジ**: 100%を目指さず、重要な部分に集中
4. **保守性の確保**: テストコードも本番コードと同じ品質基準
5. **CI/CDとの統合**: デプロイ前に適切なテストを実行

この戦略により、開発速度とコード品質のバランスを保ちながら、長期的な保守性を確保しています。

---

## CI/CD パイプライン

### 概要

GitHub Actionsによる自動化されたCI/CDパイプラインを採用し、コード品質の維持とデプロイの自動化を実現しています。

---

### ワークフロー一覧

| トリガー | ワークフロー | 内容 |
|---------|------------|------|
| **Pull Request** | `pr-check.yml` | Commit message検証、ファイルサイズチェック、Secret scan |
| **Push to develop** | `backend-staging.yml` | Lint, Tests, Deploy（カバレッジ60%+） |
| | `frontend-staging.yml` | Lint, Tests, Build, E2E（カバレッジ60%+） |
| **Push to main** | `backend-production.yml` | Lint, Tests, Deploy（カバレッジ80%+） |
| | `frontend-production.yml` | Lint, Tests, Build, E2E（カバレッジ70%+、全ブラウザ） |
| **手動実行** | `e2e-smoke-test-*.yml` | 実環境での疎通確認 |

---

### デプロイフロー

```
1. コード変更
   ↓
2. Pull Request作成
   └─ pr-check.yml 実行
   ↓
3. developブランチにマージ
   └─ backend-staging.yml, frontend-staging.yml 実行
      ├─ Lint & Format
      ├─ Tests (60%+ coverage)
      ├─ Build
      ├─ E2E tests (Chromium)
      └─ デプロイ通知
   ↓
4. Render & Cloudflare が自動デプロイ
   ↓
5. mainブランチにマージ
   └─ backend-production.yml, frontend-production.yml 実行
      ├─ Lint & Format
      ├─ Tests (70-80%+ coverage)
      ├─ Build
      ├─ E2E tests (全ブラウザ)
      └─ デプロイ通知
   ↓
6. Render & Cloudflare が自動デプロイ
```

---

### テスト戦略の違い

| 環境 | カバレッジ | E2Eブラウザ | Strict Mode |
|------|-----------|------------|-------------|
| **Staging** | 60%+ | Chromiumのみ | false |
| **Production** | 70-80%+ | 全ブラウザ | true |

**理由**:
- Stagingは開発速度を優先し、基本的な品質を確保
- Productionは品質を最優先し、全環境で動作保証

---

### バックエンドCI/CD

**実行内容**:
```yaml
1. Lint & Format
   - Black (コードフォーマット)
   - isort (import整理)
   - Flake8 (静的解析)

2. Django Checks
   - python manage.py check

3. Migration Check
   - makemigrations --check --dry-run

4. Tests
   - Django TestCase
   - Coverage報告

5. Security Audit
   - safety check (脆弱性スキャン)
```

---

### フロントエンドCI/CD

**実行内容**:
```yaml
1. Lint & Format
   - ESLint (静的解析)
   - Prettier (コードフォーマット)

2. Type Check
   - TypeScript compiler

3. Unit & Integration Tests
   - Vitest + Testing Library
   - MSW (APIモック)

4. Build
   - Vite build

5. E2E Tests
   - Playwright + playwright-msw
   - 認証済み/未認証テスト分離

6. Security Audit
   - npm audit (脆弱性スキャン)
```

---

### 再利用可能なコンポーネント

#### カスタムアクション

| アクション | 用途 |
|-----------|------|
| `setup-node` | Node.js環境のセットアップ、npmキャッシュ管理 |
| `setup-python` | Python環境のセットアップ、pipキャッシュ管理 |

#### 再利用可能なワークフロー

| ワークフロー | パラメータ |
|------------|----------|
| `reusable-backend-test.yml` | environment, debug-mode, strict-mode, coverage-threshold |
| `reusable-frontend-test.yml` | environment, strict-mode, coverage-threshold |

---

### 環境変数管理

**GitHub Environment Variables** (Terraform管理)

| 環境 | 主な変数 |
|------|---------|
| **staging** | VITE_BASE_API_URL, FRONTEND_URL, E2E_TEST_EMAIL, E2E_TEST_PASSWORD |
| **production** | 同上 |

**設定方法**: Terraformで自動設定（`terraform/modules/github/`）

---

### 詳細ドキュメント

CI/CDパイプラインの詳細については、以下のドキュメントを参照してください。

- **[docs/cicd.md](docs/cicd.md)** - CI/CD詳細ガイド
  - 各ワークフローの詳細
  - 再利用可能なワークフロー
  - カスタムアクションの実装
  - 環境変数管理
  - Smoke Testsの実装
  - トラブルシューティング

---

## インフラ構成（Terraform）

### 概要

このプロジェクトのインフラは **Terraform** で管理されており、以下のクラウドサービスを自動構築します。
```
┌─────────────────────────────────────────────────────────────┐
│                     Infrastructure                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │    Neon      │  │  Backblaze   │  │  Cloudflare  │    │
│  │  PostgreSQL  │  │   B2 Storage │  │    Pages     │    │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘    │
│         │                  │                               │
│         └────────┬─────────┘                               │
│                  │                                         │
│         ┌────────▼────────┐                                │
│         │     Render      │                                │
│         │  Django Backend │                                │
│         └─────────────────┘                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### ディレクトリ構造
```
terraform/
├── modules/              # 再利用可能なモジュール
│   ├── neon/            # Neon PostgreSQL
│   ├── backblaze/       # Backblaze B2
│   ├── cloudflare/      # Cloudflare Pages
│   └── render/          # Render Web Service
└── envs/                # 環境ごとの構成
    ├── production/      # 本番環境
    │   ├── provider.tf
    │   ├── variables.tf
    │   ├── locals.tf
    │   ├── main.tf
    │   └── outputs.tf
    └── staging/         # ステージング環境
        └── ...
```

### インフラコンポーネント

| サービス | 用途 | リソース |
|---------|------|---------|
| **Neon** | PostgreSQLデータベース | プロジェクト、ブランチ、DB、ロール |
| **Upstash Redis** | Redisキャッシュ/セッション | Database、REST Token |
| **Upstash QStash** | 非同期タスクキュー | Endpoint |
| **Resend** | メール送信 | API Key |
| **Backblaze B2** | 静的アセットストレージ | バケット、Application Key |
| **Cloudflare Pages** | フロントエンドホスティング | Pagesプロジェクト |
| **Render** | バックエンドホスティング | Web Service（Docker） |

### Terraform Cloud設定

#### 必要な環境変数
```
Environment Variables（Terraform Cloud）:
  RENDER_API_KEY           # Render APIキー
  NEON_API_KEY             # Neon APIキー
  CLOUDFLARE_API_TOKEN     # Cloudflare APIトークン
  B2_APPLICATION_KEY_ID    # Backblaze Key ID
  B2_APPLICATION_KEY       # Backblaze Key Secret
```

#### Terraform Variables
```
Terraform Variables:
  render_owner_id          # Render Owner ID（usr-xxx）
  cloudflare_account_id    # Cloudflare Account ID
  github_repo_url          # GitHub リポジトリURL
```

### 初期セットアップ

#### 1. 前提条件

- Terraform Cloud アカウント
- 各サービスのアカウント作成
  - [Neon](https://neon.tech/)
  - [Backblaze](https://www.backblaze.com/b2/)
  - [Cloudflare](https://www.cloudflare.com/)
  - [Render](https://render.com/)

#### 2. Terraform Cloudの準備
```bash
# Terraform Cloudにログイン
terraform login

# Organization作成（ブラウザで）
# Organization名: django-react-app

# Workspaces作成
# - django-react-production
# - django-react-staging
```

#### 3. APIキーの取得

**Render**:
```
Dashboard → Account Settings → API Keys → Create API Key
→ RENDER_API_KEY
```

**Neon**:
```
Dashboard → Account → API keys → Generate new API key
→ NEON_API_KEY
```

**Cloudflare**:
```
Dashboard → My Profile → API Tokens → Create Token
→ Edit Cloudflare Workers → CLOUDFLARE_API_TOKEN
```

**Backblaze**:
```
Dashboard → App Keys → Add a New Application Key
→ B2_APPLICATION_KEY_ID / B2_APPLICATION_KEY
```

#### 4. GitHub連携

**Cloudflare Pages**:
```
1. Cloudflare Dashboard → Workers & Pages
2. Create application → Pages → Connect to Git
3. GitHubアカウントを連携
4. リポジトリへのアクセスを許可
```

**Render**:
```
1. Render Dashboard → Settings → GitHub Apps
2. GitHubアカウントを連携
3. リポジトリへのアクセスを許可
```

#### 5. Terraform実行
```bash
# 初期化
cd terraform/envs/production
terraform init

# 構成プレビュー
terraform plan

# インフラ作成
terraform apply

# 確認
terraform output
```

### デプロイ後の確認
```bash
# 出力値を確認
terraform output deployment_info

# 出力例:
# deployment_info = {
#   database = {
#     provider = "Neon"
#     host     = "ep-xxx.aws-ap-southeast-1.aws.neon.tech"
#   }
#   backend = {
#     provider = "Render"
#     url      = "https://django-react-app-backend-production.onrender.com"
#   }
#   frontend = {
#     provider = "Cloudflare Pages"
#     url      = "https://django-react-app-frontend-production.pages.dev"
#   }
#   storage = {
#     provider = "Backblaze B2"
#     bucket   = "django-react-app-assets-production"
#   }
# }
```

### リソース命名規則
```
形式: {project_name}-{component}-{environment}

例:
  - django-react-app-db-production
  - django-react-app-assets-production
  - django-react-app-frontend-production
  - django-react-app-backend-production
```

### インフラ更新
```bash
# 変更をプレビュー
terraform plan

# 変更を適用
terraform apply

# 特定のリソースのみ更新
terraform apply -target=module.render

# インフラ削除（注意）
terraform destroy
```

### トラブルシューティング

#### エラー: 認証失敗
```
解決策:
  1. Terraform Cloud Variables を確認
  2. APIキーが有効か確認
  3. 権限が正しく設定されているか確認
```

#### エラー: GitHub連携
```
解決策:
  1. Cloudflare/Render Dashboard で手動連携を完了
  2. リポジトリへのアクセス権を確認
```

#### エラー: リソース作成失敗
```
解決策:
  1. terraform state list でリソース一覧を確認
  2. 手動で作成されたリソースがあれば削除
  3. terraform apply を再実行
```

---

## Terraform + デプロイワークフロー

### 概要

**Terraform Cloud**によるインフラ管理と**GitHub Actions**による自動デプロイを組み合わせ、安全で再現性の高いデプロイフローを実現しています。

---

### フロー概要

```
1. terraform/** 変更 + PR作成
   └─ terraform-plan.yml（自動実行）
      └─ PRにPlan結果をコメント

2. PR マージ（develop または main）
   └─ 通常のCI/CDワークフロー実行

3. terraform-apply.yml（手動実行）
   ├─ Terraform Apply
   │  └─ GitHub Environment Variables 更新
   └─ デプロイ戦略の選択
      ├─ Staging: Parallel（高速）
      └─ Production: Sequential（安全）

4. アプリケーションデプロイ（自動トリガー）
   ├─ Backend Deployment（Render）
   └─ Frontend Deployment（Cloudflare Pages）
```

---

### Terraformワークフロー

| ワークフロー | トリガー | 用途 |
|------------|---------|------|
| `terraform-plan.yml` | PR作成・更新 | 変更内容のプレビュー |
| `terraform-apply.yml` | 手動実行 | インフラ構築・変更 |
| `terraform-fmt.yml` | PR作成・更新 | フォーマットチェック |
| `terraform-destroy.yml` | 手動実行（緊急時） | 環境削除 |

---

### デプロイ戦略

#### Parallel（並列実行）- Staging推奨

```
Terraform Apply 完了
  ↓
┌─────────────┬─────────────┐
│  Backend    │  Frontend   │ ← 同時実行
│  Deploy     │  Deploy     │
└─────────────┴─────────────┘
  ↓             ↓
完了（2-3分）
```

**特徴**:
- ⚡ 高速（2-3分で完了）
- ⚠️ Frontend が先に完成する可能性
- 💡 Staging では許容範囲

---

#### Sequential（順次実行）- Production推奨

```
Terraform Apply 完了
  ↓
Backend Deploy
  ↓
Health Check（最大5分）
  ↓ ✅ Healthy
Frontend Deploy
  ↓
完了（5-7分）
```

**特徴**:
- 🛡️ 安全（ゼロダウンタイム）
- ⏱️ 時間がかかる（5-7分）
- 💡 Production では必須

---

### 実際の運用フロー

#### シナリオ1: 新しい環境変数の追加

```bash
1. .env.example に環境変数を追加
2. Terraform に反映（terraform/modules/github/main.tf）
3. PR作成 → terraform-plan.yml が自動実行
4. レビュー & マージ（develop）
5. terraform-apply.yml を手動実行（Staging）
6. 自動デプロイ開始
7. 完了 🎉
```

#### シナリオ2: データベース設定の変更

```bash
1. Neon モジュールを編集
2. PR作成 → Staging/Production Plan 表示
3. レビュー & マージ（develop）
4. terraform-apply.yml を手動実行（Staging）
5. Staging で動作確認
6. main ブランチにマージ
7. terraform-apply.yml を手動実行（Production）
8. Production デプロイ完了 🎉
```

---

### GitHub Environment 設定

#### terraform-staging

```
Protection rules:
  ✅ Required reviewers: 0人
  ❌ Wait timer: なし
```

#### terraform-production

```
Protection rules:
  ✅ Required reviewers: 1人以上
  ⏱️ Wait timer: 0分（任意）
```

---

### GitHub Secrets

| Secret | 用途 |
|--------|------|
| `TF_API_TOKEN` | Terraform Cloud API Token |
| `GH_PAT` | Personal Access Token（repo + workflow権限） |

---

### 詳細ドキュメント

Terraform + デプロイワークフローの詳細については、以下のドキュメントを参照してください。

- **[docs/terraform-workflow.md](docs/terraform-workflow.md)** - Terraformワークフロー詳細ガイド
  - terraform-plan.ymlの詳細
  - terraform-apply.ymlの詳細
  - terraform-destroy.ymlの安全機能
  - Backend/Frontend Deployワークフロー
  - Health Checkの仕組み
  - トラブルシューティング
  - ベストプラクティス

---

## よく使うコマンド

### バックエンド

```bash
# マイグレーション
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate

# テストデータ投入
docker compose exec backend python manage.py seed_db

# テスト実行
docker compose exec backend python manage.py test
docker compose exec backend python manage.py test users.tests.test_services

# カバレッジ
docker compose exec backend coverage run --source='.' manage.py test
docker compose exec backend coverage report

# スーパーユーザー作成
docker compose exec backend python manage.py createsuperuser

# Djangoシェル
docker compose exec backend python manage.py shell
```

### フロントエンド

```bash
# 開発サーバー起動
npm run dev

# ビルド
npm run build
npm run preview  # ビルド結果をプレビュー

# テスト
npm run test              # ユニット・統合テスト
npm run test:watch        # Watchモード
npm run test:coverage     # カバレッジ付き
npm run test:e2e          # E2Eテスト
npm run test:e2e:ui       # E2E UIモード

# リンター・フォーマッター
npm run lint
npm run format

# 型チェック
npm run type-check
```

### Docker

```bash
# コンテナ起動
docker compose up -d

# ログ確認
docker compose logs -f backend
docker compose logs -f frontend

# コンテナ再起動
docker compose restart backend
docker compose restart frontend

# コンテナ停止
docker compose down

# ボリューム削除（DB初期化）
docker compose down -v
```

---

## デプロイ

### インフラ構成

| コンポーネント | サービス | 選定理由 |
|---|---|---|
| **バックエンド** | Render | Git連携による自動デプロイ、環境変数管理が容易 |
| **フロントエンド** | Cloudflare Pages | エッジ配信による高速化、無料プランで十分な性能 |
| **データベース** | Neon (PostgreSQL) | ブランチ機能、移植性の高さ、低レイテンシ |

---
