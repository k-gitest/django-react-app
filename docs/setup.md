# セットアップガイド

> **📖 このドキュメントについて**  
> このガイドでは、開発環境のセットアップ方法を詳しく解説します。  
> 概要については [README.md](../README.md#セットアップ) を参照してください。

## 目次

- [前提条件](#前提条件)
- [方法1: GitHub Codespaces を使用](#方法1-github-codespaces-を使用)
- [方法2: Dev Container（ローカル）を使用](#方法2-dev-containerローカルを使用)
  - [パターンA: Compose統合型（自動起動）](#パターンa-compose統合型自動起動)
  - [パターンB: 手動起動型](#パターンb-手動起動型)
- [方法3: Docker Compose を使用](#方法3-docker-compose-を使用)
- [方法4: ローカル環境（Docker なし）](#方法4-ローカル環境docker-なし)
- [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

開発環境ごとに必要なツールが異なります：

| 環境 | 必要なツール |
|------|------------|
| **GitHub Codespaces** | GitHubアカウントのみ |
| **Dev Container** | Docker Desktop、VS Code、Dev Containers拡張機能 |
| **Docker Compose** | Docker & Docker Compose |
| **ローカル環境** | Node.js 18+、Python 3.12+、PostgreSQL 17、Redis |

---

## 方法1: GitHub Codespaces を使用

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

**メリット**:
- ✅ ローカルマシンのリソースを消費しない
- ✅ 環境構築が不要
- ✅ どのマシンからでもアクセス可能

**デメリット**:
- ⚠️ インターネット接続が必須
- ⚠️ 無料枠に制限あり（月60時間）

---

## 方法2: Dev Container（ローカル）を使用

ローカルのVS Codeで開発環境をセットアップする方法です。

### パターンA: Compose統合型（自動起動）

**推奨**: 初回セットアップ後すぐに開発を始めたい場合

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

**メリット**:
- ✅ 自動セットアップで即座に開発開始
- ✅ VS Code拡張機能が自動インストール
- ✅ 統一された開発環境

**デメリット**:
- ⚠️ Docker Desktopが必要
- ⚠️ 初回ビルドに時間がかかる（5-10分）

---

### パターンB: 手動起動型

**推奨**: Composeの起動/停止を柔軟に制御したい場合

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

**メリット**:
- ✅ より細かい制御が可能
- ✅ リソース使用量を最適化できる

**デメリット**:
- ⚠️ 手動ステップが多い

---

## 方法3: Docker Compose を使用

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

**メリット**:
- ✅ VS Code不要
- ✅ 軽量で高速
- ✅ CI/CD環境に近い

**デメリット**:
- ⚠️ 環境変数を手動設定
- ⚠️ IDE統合なし

---

## 方法4: ローカル環境（Docker なし）

<details>
<summary>詳細を表示</summary>

### 前提条件
- Node.js 18+
- Python 3.12+
- PostgreSQL 17
- Redis

### バックエンド
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .env を編集してPostgreSQL/Redis接続情報を設定

# マイグレーション
python manage.py migrate

# サーバー起動
python manage.py runserver
```

### フロントエンド
```bash
cd frontend
npm install

# 環境変数設定
cp .env.example .env
# .env を編集してAPIエンドポイントを設定

# 開発サーバー起動
npm run dev
```

**メリット**:
- ✅ 完全な制御
- ✅ Docker不要

**デメリット**:
- ⚠️ 環境構築が複雑
- ⚠️ PostgreSQL/Redisのインストールが必要
- ⚠️ 環境差異が発生しやすい

</details>

---

## トラブルシューティング

### ポートが既に使用されている
```bash
# 使用中のポートを確認
lsof -i :3000  # フロントエンド
lsof -i :8000  # バックエンド

# プロセスを終了
kill -9 <PID>
```

### Docker Composeが起動しない
```bash
# コンテナとボリュームを完全削除
docker compose down -v

# 再起動
docker compose up -d
```

### devcontainerがビルドできない
```bash
# Dockerイメージを再ビルド
docker compose build --no-cache

# VS Codeを再起動
# コマンドパレット → "Dev Containers: Rebuild Container"
```

### データベースマイグレーションエラー
```bash
# データベースをリセット
docker compose down -v
docker compose up -d
docker compose exec backend python manage.py migrate
```

### フロントエンドが起動しない
```bash
# node_modules を削除して再インストール
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## 次のステップ

セットアップが完了したら、以下を確認してください：

1. **動作確認**
   - フロントエンド: http://localhost:3000
   - バックエンドAPI: http://localhost:8000/api/v1/
   - Django Admin: http://localhost:8000/admin/

2. **テストデータ投入**
```bash
   docker compose exec backend python manage.py seed_db
```
