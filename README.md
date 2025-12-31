# django-react-app

Django/React モノレポベースのSPAアプリケーション

## 概要

拡張性と保守性を重視したフルスタックWebアプリケーションです。バックエンドにDjango REST Framework、フロントエンドにReact + TypeScriptを採用し、レイヤードアーキテクチャによる明確な責務分離を実現しています。

## 主な特徴

- 🏗️ **スケール可能なモノレポ構成**: フロントエンドとバックエンドを一元管理し、チーム全体での仕様変更への迅速な対応を可能にします。
- 🎯 **チーム開発に適したレイヤードアーキテクチャ**: 複数人での並行開発を想定し、View/Service/Modelの責務を分離。コードの衝突（コンフリクト）を最小限に抑え、テスタビリティを向上させています。
- 🔐 **JWT認証**: dj-rest-auth + simplejwtによる堅牢な認証システム
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
│   │   ├── urls.py            # ルートURLルーティング
│   │   ├── wsgi.py / asgi.py  # サーバーインターフェース
│   │   └── __init__.py
│   │
│   ├── users/                 # ユーザー管理アプリケーション
│   │   ├── models.py          # データモデル定義
│   │   ├── views.py           # APIビュー（薄いコントローラ）
│   │   ├── service.py         # ビジネスロジック層
│   │   ├── utils.py           # ユーティリティ関数
│   │   ├── urls.py            # アプリ固有のルーティング
│   │   ├── serializers.py     # DRFシリアライザ
│   │   ├── tests/             # テストコード
│   │   │   ├── test_models.py
│   │   │   └── test_services.py
│   │   ├── management/        # カスタムコマンド
│   │   │   └── commands/
│   │   │       └── seed_db.py
│   │   └── migrations/        # DBマイグレーション
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
│   │   └── backblaze/
│   │   └── github/
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

### 前提条件

- Docker & Docker Compose
- Node.js 18+ (ローカル開発の場合)
- Python 3.11+ (ローカル開発の場合)
- Visual Studio Code + Dev Containers拡張機能 (devcontainer使用の場合)

### 開発環境の選択肢

このプロジェクトは以下の開発環境をサポートしています：

1. **GitHub Codespaces**: クラウド上の開発環境
2. **Dev Container（ローカル）**: VS Codeでの自動セットアップ
3. **Docker Compose**: コンテナベースの開発環境
4. **ローカル環境**: 直接マシンにインストール

---

### 方法1: GitHub Codespaces を使用

クラウド上で即座に開発環境が構築されます。

```bash
# 1. GitHubリポジトリページから
#    "Code" → "Codespaces" → "Create codespace on main"

# 2. Codespace起動後、以下のコマンドを実行
docker compose up -d

# 3. フロントエンドの依存関係インストールと開発サーバー起動
cd frontend
npm install
npm run dev

# 4. バックエンドのマイグレーション
docker compose exec backend python manage.py migrate

# 5. スーパーユーザーの作成
docker compose exec backend python manage.py createsuperuser
```

**使用設定**: `.devcontainer/devcontainer.json`

**アクセス**:
- Codespacesが自動でポートフォワーディングを設定
- "PORTS"タブから各サービスにアクセス

---

### 方法2: Dev Container（ローカル）を使用

ローカルのVS Codeで開発環境をセットアップする方法です。

#### パターンA: Compose統合型（自動起動）

`.devcontainer/devcontainer-compose.json`を使用

```bash
# 1. リポジトリをクローン
git clone <repository-url>
cd django-react-app

# 2. 設定ファイルを切り替え（初回のみ）
mv .devcontainer/devcontainer.json .devcontainer/devcontainer.manual.json
mv .devcontainer/devcontainer-compose.json .devcontainer/devcontainer.json

# 3. VS Codeで開く
code .

# 4. コマンドパレット（Ctrl+Shift+P / Cmd+Shift+P）から
#    "Dev Containers: Reopen in Container" を選択
```

初回起動後、以下が**自動実行**されます：
- Docker Composeによる全サービス起動
- ルート・フロントエンドの依存パッケージインストール
- バックエンドの開発サーバー起動（Django）
- ポートフォワーディング設定（8000, 3000）

**注意**: フロントエンドの開発サーバー（`npm run dev`）は、postCreateCommandでバックグラウンド起動してもdevcontainer構築完了後に終了するため、手動起動が必要です。

```bash
# devcontainer起動後、フロントエンド開発サーバーを起動
cd frontend
npm run dev
```

**アクセス**:
- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8000/api/v1/
- Django Admin: http://localhost:8000/admin/

#### パターンB: 手動起動型

`.devcontainer/devcontainer.json`を使用（デフォルト設定）

```bash
# 1-3. パターンAと同じ（設定ファイル切り替えは不要）

# 4. devcontainer起動後、手動でCompose起動
docker compose up -d

# 5. フロントエンド開発サーバー起動
cd frontend
npm install
npm run dev
```

このパターンは、Composeの起動/停止を柔軟に制御したい場合に適しています。

**補足**: どちらのパターンでも、マイグレーションとスーパーユーザー作成は手動実行が必要です。
```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

---

### 方法3: Docker Compose を使用

devcontainerを使わず、直接Docker Composeで開発する場合。

1. **リポジトリのクローン**
   ```bash
   git clone <repository-url>
   cd django-react-app
   ```

2. **環境変数の設定**
   ```bash
   # バックエンド
   cp backend/.env.example backend/.env
   # 必要な環境変数を編集
   
   # フロントエンド
   cp frontend/.env.example frontend/.env
   # 必要な環境変数を編集
   ```

3. **コンテナの起動**
   ```bash
   docker compose up -d
   ```

4. **データベースのマイグレーション**
   ```bash
   docker compose exec backend python manage.py migrate
   ```

5. **スーパーユーザーの作成**
   ```bash
   docker compose exec backend python manage.py createsuperuser
   ```

6. **アクセス**
   - フロントエンド: http://localhost:3000
   - バックエンドAPI: http://localhost:8000/api/v1/
   - Django Admin: http://localhost:8000/admin/

---

### 方法4: ローカル環境（Docker なし）

<details>
<summary>詳細を表示</summary>

#### バックエンド

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

#### フロントエンド

```bash
cd frontend
npm install
npm run dev
```

</details>

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

## 認証システム

### 概要

**dj-rest-auth + djangorestframework-simplejwt**によるJWT Cookie認証を採用しています。

### 設計変更の経緯：djoserからdj-rest-authへの移行

当初はdjoserによるヘッダー認証（Bearer）を採用していましたが、以下の理由からdj-rest-authのCookie認証方式に移行しました。

#### 移行の理由

**1. XSS攻撃への対策を最優先**

旧方式（djoser）では、Access TokenをクライアントサイドのlocalStorageやsessionStorageに保存する必要がありました。この方法は、XSS（Cross-Site Scripting）攻撃によってトークンが漏洩するリスクが非常に高いと判断しました。

dj-rest-authのHttpOnly Cookie方式では、JavaScriptからのアクセスを完全に遮断できるため、Webアプリケーションのセキュリティを大幅に向上させることができます。

**2. 自作実装のリスク回避**

HttpOnly Cookie認証を自作で実装することも検討しましたが、以下の懸念から見送りました：

- **セキュリティリスク**: 認証という極めて重要な機能での実装ミスは致命的
- **保守コスト**: コード量の増加と、将来的なメンテナンス負担
- **開発時間**: 実績のあるライブラリを使えば、同等の時間で堅牢な実装が可能

**3. SPA認証に特化した設計思想**

Djangoの標準的なセッション認証は、クロスオリジン（SPA）環境での認証フローに適していません。dj-rest-authは、SPA用に最適化された設計思想を持つため、本プロジェクトの要件に最適と判断しました。

---

### 認証方式の比較

| 項目 | 旧設計（djoser） | 新設計（dj-rest-auth） |
|---|---|---|
| **方式** | JWT（Bearer認証） | JWT（Cookie認証） |
| **トークン格納先** | localStorage / sessionStorage | HttpOnly Cookie |
| **セキュリティ上の懸念** | XSS攻撃 | CSRF攻撃（Djangoミドルウェアで対応） |
| **設計判断の理由** | APIの利便性 | Web SPAにおけるXSSリスク回避を最優先 |
| **クライアント側の責務** | トークン管理が必要 | トークン管理不要（サーバー側に委譲） |

---

### カスタムユーザーモデル

`AbstractUser`と`BaseUserManager`を継承し、**emailベースの認証**を実装しています。

**設計判断の理由**:

| 要件 | 採用した手法 |
|---|---|
| Django標準の認証機能を活用 | `AbstractUser`を継承 |
| username → email に変更 | `username = None`で無効化 |
| メールアドレスの大文字小文字問題 | `get_by_natural_key()`で`__iexact`検索 |
| createsuperuser対応 | `BaseUserManager`を継承してオーバーライド |

### Simple JWT設定

```python
SIMPLE_JWT = {
    # アクセストークンは短命に設定
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    
    # リフレッシュトークンは1日間有効
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    
    # トークンローテーション: refresh使用時に新しいrefreshを発行
    "ROTATE_REFRESH_TOKENS": True,
    
    # ローテーション後、古いrefreshトークンをブラックリストに追加
    "BLACKLIST_AFTER_ROTATION": True,
    
    # 標準のBearer認証スキームを使用（RFC 6750準拠）
    "AUTH_HEADER_TYPES": ("Bearer",),
}
```

**重要な設定**:

| 設定 | 値 | 理由 |
|---|---|---|
| `ACCESS_TOKEN_LIFETIME` | 5分 | 短命にしてセキュリティリスクを低減 |
| `REFRESH_TOKEN_LIFETIME` | 1日 | ユーザビリティとセキュリティのバランス |
| `ROTATE_REFRESH_TOKENS` | True | refresh使用時に新しいrefreshを発行 |
| `BLACKLIST_AFTER_ROTATION` | True | 古いrefreshを無効化（リプレイ攻撃対策） |
| `AUTH_HEADER_TYPES` | Bearer | 業界標準（RFC 6750）に準拠 |

### dj-rest-auth Cookie設定

```python
REST_AUTH = {
    'USE_JWT': True,
    'SESSION_LOGIN': False,
    
    # Cookie設定
    'JWT_AUTH_COOKIE': 'access-token',
    'JWT_AUTH_REFRESH_COOKIE': 'refresh-token',
    'JWT_AUTH_HTTPONLY': True,  # XSS対策の要
    'JWT_AUTH_SAMESITE': 'None',
    'JWT_AUTH_SECURE': True,
    # 'JWT_AUTH_SAMESITE': 'Lax',  # 開発環境がhttpの場合
    # 'JWT_AUTH_SECURE': False,    # 開発環境がhttpの場合
}
```

**セキュリティ設定の詳細**:

| 設定 | 値 | セキュリティ上の意義 |
|---|---|---|
| `JWT_AUTH_HTTPONLY` | True | **JavaScriptからのアクセスを完全遮断**（XSS対策の核心） |
| `JWT_AUTH_SECURE` | True（本番） | HTTPS接続でのみCookie送信を許可 |
| `SESSION_LOGIN` | False | JWT認証に一元化し、アーキテクチャの一貫性を確保 |

---

### CSRF対策

Cookie認証では、CSRF（Cross-Site Request Forgery）攻撃への対策が必須です。

```python
CSRF_COOKIE_HTTPONLY = False  # フロントエンドがCSRFトークンを読み取り可能に
CSRF_COOKIE_SAMESITE = 'None'  # クロスオリジンリクエストの制御
CSRF_COOKIE_SECURE = True     # 開発環境がhttpの場合はFalse
CORS_ALLOW_CREDENTIALS = True  # Cookie送信を許可
```

**重要**: `CSRF_COOKIE_HTTPONLY = False`の理由は、React（SPA）がCSRFトークンを読み取り、リクエストヘッダーに含める必要があるためです。これはSPAとCookie認証を組み合わせる際の標準的な設定です。

### 認証フロー
```
1. 登録     → POST /api/v1/auth/registration/
              ↓ HttpOnly Cookieでaccess-token, refresh-token発行
              
2. ログイン  → POST /api/v1/auth/login/
              ↓ HttpOnly Cookieでaccess-token, refresh-token発行
              
3. API呼び出し → Cookie自動送信（フロントエンドでのトークン操作不要）

4. トークン更新 → POST /api/v1/auth/token/refresh/
                 ↓ refresh-token Cookieが自動送信される
                 ↓ 新しいaccess-tokenとrefresh-tokenを発行
                 
5. ログアウト  → POST /api/v1/auth/logout/
                ↓ refresh-tokenをブラックリスト化
                ↓ Cookieを削除
```

#### 🔧 新規登録プロセスの最適化（CustomRegisterView）
dj-rest-authの標準RegisterViewは、ユーザー作成後に自動でJWT Cookieを発行しません。本プロジェクトではCustomRegisterViewを実装し、登録成功時に即座にaccess-tokenを発行・Cookieへセットするように拡張しています。これにより、ユーザーは登録後にログイン操作をすることなく、シームレスにダッシュボードへ遷移可能です。

### APIエンドポイント

| 機能 | Method | エンドポイント | 認証 |
|---|---|---|---|
| **新規登録** | POST | `/api/v1/auth/registration/` | 不要 |
| **ログイン** | POST | `/api/v1/auth/login/` | 不要 |
| **ログアウト** | POST | `/api/v1/auth/logout/` | Cookie自動送信 |
| **ユーザー情報取得** | GET | `/api/v1/auth/user/` | Cookie自動送信 |
| **ユーザー情報更新** | PUT/PATCH | `/api/v1/auth/user/` | Cookie自動送信 |
| **トークンリフレッシュ** | POST | `/api/v1/auth/token/refresh/` | refresh-token Cookie |
| **パスワード変更** | POST | `/api/v1/auth/password/change/` | Cookie自動送信 |

### ⚠️ 重要な注意点

1. **トークンはHttpOnly Cookieで管理**
   - クライアントサイド（JavaScript）からトークンにアクセスできない
   - XSS攻撃からの防御を実現

2. **フロントエンドでのトークン管理は不要**
   - localStorage/sessionStorageへの保存は不要
   - ブラウザが自動的にCookieを送信
   - セキュリティリスクとコード量を同時に削減

3. **トークンの自動更新**
   - `ROTATE_REFRESH_TOKENS=True`により、refresh token使用時に新しいrefresh tokenが発行される
   - 古いrefresh tokenは自動的にブラックリストに追加され、再利用できなくなる（リプレイ攻撃対策）

4. **本番環境での設定変更**
  - 開発環境をhttpで行っていた場合、本番環境で設定の変更が必要です
   ```python
   # 本番環境では以下に変更
   CSRF_COOKIE_SECURE = True
   CSRF_COOKIE_SAMESITE = 'None'
   JWT_AUTH_SECURE = True
   JWT_AUTH_SAMESITE = 'None'
   ```

---

### フロントエンド実装の簡素化

Cookie認証への移行により、フロントエンド側のトークン管理が大幅に簡素化されました：

**不要になったコード:**
- localStorage/sessionStorageへのトークン保存
- Authorization ヘッダーの手動設定
- トークン期限の監視とリフレッシュロジック

**残った責務:**
- 認証エラー（401）の最終的なハンドリング
- ログインページへのリダイレクト

この設計により、セキュリティを向上させながら、コードの保守性と可読性も同時に向上させることができました。


#### ⚡ TanStack Query による認証状態の同期
認証状態の管理を従来のuseEffectからTanStack Query (useQuery)へ移行し、Zustandと組み合わせることで以下の課題を解決しました。

**競合状態（Race Condition）の解消**: ログイン直後のリダイレクトとfetchMeのタイミングをsetQueryDataによって明示的に同期。AuthGuardにおいて「認証済みにもかかわらず一瞬ログイン画面が表示される」というUX上のチラつきを完全に解消しました。

**キャッシュの一貫性と即時性**: queryClient.invalidateQueriesは非同期の再取得を伴うため、認証状態の反映にラグが生じる場合があります。本プロジェクトでは、APIレスポンスから得られたユーザー情報を直接StoreおよびQueryキャッシュに書き込むことで、通信を待たずに即座にガードを通過させる設計を採用しています。

**不要なネットワークリクエストの削減**: サーバー状態（認証情報）をキャッシュ管理することで、コンポーネントの再レンダリングに伴う重複した API 呼び出しを最小限に抑えています。

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

## データベース戦略

### 採用：Neon PostgreSQL

本プロジェクトでは、デプロイの移植性と開発効率を重視し、**Neon (PostgreSQL)** をデータベースとして採用しています。

**選定理由**:

| 理由 | メリット |
|---|---|
| **ブランチ機能** | 開発・ステージング・テスト環境ごとにDBの軽量なコピー（ブランチ）を無料で作成・破棄可能。テストの再現性と環境分離が容易 |
| **移植性** | 標準PostgreSQL準拠のため、将来的なDB移行が容易。ベンダーロックインのリスクが低い |
| **低レイテンシ** | Renderと同じリージョン配置でプライベートネットワーク経由の高速通信が可能 |

### デプロイ構成と速度最適化

**原則**: アプリケーション（Render）とDB（Neon）は**同じリージョン**に配置すること

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

### ワークフロー構成

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pull Request                                               │
│  └─ pr-check.yml                                           │
│     ├─ Commit message validation (Conventional Commits)    │
│     ├─ File size check (<5MB)                              │
│     └─ Secret scan                                         │
│                                                             │
│  Push to develop branch                                     │
│  ├─ backend-staging.yml                                    │
│  │  ├─ Lint & Format (Black, isort, Flake8)               │
│  │  ├─ Type check                                          │
│  │  ├─ Tests (Django TestCase, 60%+ coverage)             │
│  │  ├─ Security audit                                      │
│  │  └─ Deploy notification                                 │
│  │                                                          │
│  ├─ frontend-staging.yml                                   │
│  │  ├─ Lint & Format (ESLint, Prettier)                   │
│  │  ├─ Type check (TypeScript)                            │
│  │  ├─ Unit tests (Vitest, 60%+ coverage)                 │
│  │  ├─ Build                                               │
│  │  ├─ E2E tests (Playwright + MSW, Chromium only)        │
│  │  ├─ Security audit (npm audit)                         │
│  │  └─ Deploy notification                                 │
│  │                                                          │
│  └─ e2e-smoke-test-staging.yml (手動実行)                  │
│     └─ Smoke tests (実環境での疎通確認)                    │
│                                                             │
│  Push to main branch                                        │
│  ├─ backend-production.yml                                 │
│  │  ├─ Lint & Format (Black, isort, Flake8)               │
│  │  ├─ Type check                                          │
│  │  ├─ Tests (Django TestCase, 80%+ coverage)             │
│  │  ├─ Security audit                                      │
│  │  └─ Deploy notification                                 │
│  │                                                          │
│  ├─ frontend-production.yml                                │
│  │  ├─ Lint & Format (ESLint, Prettier)                   │
│  │  ├─ Type check (TypeScript)                            │
│  │  ├─ Unit tests (Vitest, 70%+ coverage)                 │
│  │  ├─ Build                                               │
│  │  ├─ E2E tests (Playwright + MSW, All browsers)         │
│  │  ├─ Security audit (npm audit)                         │
│  │  └─ Deploy notification                                 │
│  │                                                          │
│  └─ e2e-smoke-test-production.yml                          │
│     ├─ 手動実行可能                                         │
│     ├─ 定期実行 (6時間ごと、将来用)                         │
│     └─ Smoke tests (実環境での疎通確認)                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### ワークフローの詳細

#### 1. PR Quality Check (`pr-check.yml`)

**トリガー**: Pull Request作成・更新時

**実行内容**:

| チェック | 説明 |
|---------|------|
| **Commit Message** | Conventional Commits形式の検証 |
| **File Size** | 5MB以上のファイル検出（Git LFS推奨） |
| **Secret Scan** | 認証情報の誤コミット検出 |

**目的**: コード品質の最低基準を維持

---

#### 2. Backend CI/CD

**Staging** (`backend-staging.yml`)
- **トリガー**: `develop`ブランチへのプッシュ
- **カバレッジ**: 60%以上
- **デプロイ**: Render（自動）

**Production** (`backend-production.yml`)
- **トリガー**: `main`ブランチへのプッシュ
- **カバレッジ**: 80%以上
- **デプロイ**: Render（自動）

**テストステップ**:
```yaml
1. Lint & Format
   - Black (コードフォーマット)
   - isort (import整理)
   - Flake8 (静的解析)

2. Django Checks
   - python manage.py check --deploy (本番環境)
   - python manage.py check (ステージング環境)

3. Migration Check
   - makemigrations --check --dry-run

4. Tests
   - Django TestCase
   - Coverage報告

5. Security Audit
   - safety check (脆弱性スキャン)
```

---

#### 3. Frontend CI/CD

**Staging** (`frontend-staging.yml`)
- **トリガー**: `develop`ブランチへのプッシュ
- **カバレッジ**: 60%以上
- **E2E**: Chromiumのみ
- **デプロイ**: Cloudflare Pages（自動）

**Production** (`frontend-production.yml`)
- **トリガー**: `main`ブランチへのプッシュ
- **カバレッジ**: 70%以上
- **E2E**: 全ブラウザ（Chromium, Firefox, WebKit）
- **デプロイ**: Cloudflare Pages（自動）

**テストステップ**:
```yaml
1. Lint & Format
   - ESLint (静的解析)
   - Prettier (コードフォーマット)

2. Type Check
   - TypeScript compiler (tsc --noEmit)

3. Unit & Integration Tests
   - Vitest + Testing Library
   - MSW (APIモック)
   - Coverage報告

4. Build
   - Vite build
   - Build size確認

5. E2E Tests
   - Playwright + playwright-msw
   - 認証済み/未認証テスト分離

6. Security Audit
   - npm audit (脆弱性スキャン)
```

---

#### 4. Smoke Tests

**目的**: デプロイ後の実環境での疎通確認

**Staging** (`e2e-smoke-test-staging.yml`)
- **トリガー**: 手動実行のみ
- **環境**: Staging環境
- **ブラウザ**: Chromiumのみ

**Production** (`e2e-smoke-test-production.yml`)
- **トリガー**: 手動実行、定期実行（6時間ごと、将来用）
- **環境**: Production環境
- **ブラウザ**: Chromiumのみ

**実行内容**:
```yaml
1. サービス疎通確認
   - Frontend: curl チェック
   - Backend: /api/v1/health/ エンドポイント

2. Smoke Tests実行
   - 重要なユーザーフロー検証
   - @smoke タグ付きテストのみ実行

3. 結果レポート
   - GitHub Step Summary
   - 失敗時の通知
```

---

### 再利用可能なワークフロー

#### Backend Tests (`reusable-backend-test.yml`)

**パラメータ**:
```yaml
inputs:
  environment: staging | production
  debug-mode: 'True' | 'False'
  strict-mode: boolean (lintエラーで失敗するか)
  coverage-threshold: 0-100 (カバレッジ閾値)
```

#### Frontend Tests (`reusable-frontend-test.yml`)

**パラメータ**:
```yaml
inputs:
  environment: staging | production
  strict-mode: boolean (lintエラーで失敗するか)
  coverage-threshold: 0-100 (カバレッジ閾値)
```

---

### カスタムアクション

#### Setup Node.js (`setup-node/action.yml`)

**機能**:
- Node.js環境のセットアップ
- npm キャッシュ管理
- 依存関係のインストール

**使用例**:
```yaml
- uses: ./.github/actions/setup-node
  with:
    node-version: '20'
    working-directory: frontend
```

#### Setup Python (`setup-python/action.yml`)

**機能**:
- Python環境のセットアップ
- pip キャッシュ管理
- 依存関係のインストール
- Django バージョン検証

**使用例**:
```yaml
- uses: ./.github/actions/setup-python
  with:
    python-version: '3.12'
    requirements-path: backend/requirements.txt
```

---

### 環境変数管理

**GitHub Environment Variables** (Terraform管理)

| 環境 | 変数 | 用途 |
|------|------|------|
| **staging** | `VITE_BASE_API_URL` | バックエンドURL |
| | `FRONTEND_URL` | フロントエンドURL |
| | `VITE_STORAGE_URL` | ストレージURL |
| | `E2E_TEST_EMAIL` | E2Eテスト用メール |
| | `E2E_TEST_PASSWORD` | E2Eテスト用パスワード |
| **production** | 同上 | 同上 |

**設定方法**: Terraformで自動設定（`terraform/modules/github/`）

---

### デプロイフロー

```
1. コード変更
   ↓
2. Pull Request作成
   └─ pr-check.yml 実行
      ├─ Commit message検証
      ├─ File size検証
      └─ Secret scan
   ↓
3. developブランチにマージ
   └─ backend-staging.yml, frontend-staging.yml 実行
      ├─ Lint & Format
      ├─ Type check
      ├─ Tests (60%+ coverage)
      ├─ Build
      ├─ E2E tests (Chromium)
      └─ デプロイ通知
   ↓
4. Render & Cloudflare が自動デプロイ
   ↓
5. 手動でスモークテスト実行（オプション）
   └─ e2e-smoke-test-staging.yml
   ↓
6. mainブランチにマージ
   └─ backend-production.yml, frontend-production.yml 実行
      ├─ Lint & Format
      ├─ Type check
      ├─ Tests (70-80%+ coverage)
      ├─ Build
      ├─ E2E tests (全ブラウザ)
      └─ デプロイ通知
   ↓
7. Render & Cloudflare が自動デプロイ
   ↓
8. 定期スモークテスト（6時間ごと、将来用）
   └─ e2e-smoke-test-production.yml
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

### トラブルシューティング

#### ワークフローが失敗する

```yaml
# 確認項目
1. GitHub Environment Variablesが設定されているか
   - Repository → Settings → Environments

2. Secretsが正しく設定されているか
   - E2E_TEST_EMAIL
   - E2E_TEST_PASSWORD

3. テストが通るか
   - ローカルで npm run test 実行
   - ローカルで npm run test:e2e 実行
```

#### デプロイが自動で行われない

```yaml
# 確認項目
1. RenderとCloudflareでGitHub連携が完了しているか

2. ブランチ設定が正しいか
   - Staging: develop
   - Production: main

3. ビルドコマンドが正しいか
```

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
