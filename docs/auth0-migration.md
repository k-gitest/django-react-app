# Auth0移行ガイド

## 目次

- [概要](#概要)
- [移行のメリット](#移行のメリット)
- [移行前の準備](#移行前の準備)
- [ステップ1: Auth0設定](#ステップ1-auth0設定)
- [ステップ2: バックエンド設定](#ステップ2-バックエンド設定)
- [ステップ3: フロントエンド実装](#ステップ3-フロントエンド実装)
- [ステップ4: デプロイと検証](#ステップ4-デプロイと検証)
- [ロールバック手順](#ロールバック手順)
- [既存ユーザーのマイグレーション](#既存ユーザーのマイグレーション)
- [ソーシャルログイン設定](#ソーシャルログイン設定)
- [MFA設定](#mfa設定)
- [トラブルシューティング](#トラブルシューティング)

---

## 概要

このガイドでは、**既存のJWT Cookie認証からAuth0 OIDC認証への移行**を段階的に実施する手順を説明します。

**所要時間**: 約1-2時間  
**難易度**: 中級  
**前提知識**: Django, React, 環境変数の設定

**注意**: バックエンドの`OIDCAuthentication`クラスは**既に実装済み**です。このガイドでは、Auth0の設定とフロントエンド実装に焦点を当てます。

---

## 移行のメリット

| 項目 | JWT Cookie | Auth0 |
|------|-----------|-------|
| **セキュリティ更新** | 自己責任 | Auth0が自動対応 |
| **ソーシャルログイン** | 自前実装（週単位） | 設定のみ（分単位） |
| **MFA** | 自前実装（週単位） | 設定のみ（分単位） |
| **パスワードリセット** | 自前実装 | 標準機能 |
| **ユーザー管理UI** | Django Admin | Auth0 Dashboard |
| **監査ログ** | 自前実装 | 標準機能 |
| **異常ログイン検知** | 自前実装 | 標準機能（Bot Detection等） |

---

## 移行前の準備

### 1. データベースバックアップ
```bash
# Neon Consoleからバックアップを作成
# または
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### 2. 現在の認証フローの確認
```bash
# ログインテスト
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

# ユーザー情報取得テスト
curl http://localhost:8000/api/v1/auth/user/ \
  --cookie "access-token=xxx"
```

### 3. 依存関係の確認
```bash
# フロントエンド
cd frontend
npm list @auth0/auth0-react || echo "未インストール"

# バックエンド（既に実装済み）
cd backend
pip show joserfc requests
```

---

## ステップ1: Auth0設定

### 1.1 Auth0アカウント作成
```
1. https://auth0.com/ にアクセス
2. "Sign Up" をクリック
3. メールアドレスとパスワードを入力
4. テナント名を設定（例: django-react-app-dev）
   - 地域: Asia Pacific (推奨: シンガポール)
   - 環境: Development
```

### 1.2 API作成
```
1. Auth0 Dashboard → Applications → APIs
2. "Create API" をクリック
3. 以下を入力：
   - Name: Django React App API
   - Identifier: https://api.your-domain.com
     （任意のURL、後で変更不可）
     （例: https://api.django-react-app.com）
   - Signing Algorithm: RS256
4. "Create" をクリック
5. Identifier をコピー → AUTH0_AUDIENCE

【重要】Identifierは実在するURLでなくても構いません。
これは単なる識別子として機能します。
```

### 1.3 Application作成
```
1. Auth0 Dashboard → Applications → Applications
2. "Create Application" をクリック
3. 以下を入力：
   - Name: Django React App Frontend
   - Type: Single Page Application (SPA)
4. "Create" をクリック
5. Settings タブを開く
6. 以下をコピー：
   - Domain → VITE_AUTH0_DOMAIN
   - Client ID → VITE_AUTH0_CLIENT_ID
```

### 1.4 Callback URL設定
```
Application Settings → Application URIs

Allowed Callback URLs:
  http://localhost:5173
  https://your-frontend-staging.pages.dev
  https://your-frontend.pages.dev

Allowed Logout URLs:
  http://localhost:5173
  https://your-frontend-staging.pages.dev
  https://your-frontend.pages.dev

Allowed Web Origins:
  http://localhost:5173
  https://your-frontend-staging.pages.dev
  https://your-frontend.pages.dev

"Save Changes" をクリック
```

### 1.5 スコープ設定
```
API Settings → Permissions

以下のスコープを追加（オプション）:
- read:profile
- write:profile
- read:todos
- write:todos

【注意】openid, profile, email は自動的に含まれます
```

---

## ステップ2: バックエンド設定

### 2.1 マイグレーション実行

**oidc_sub フィールドは既に実装済み**ですが、未実行の場合：
```bash
cd backend

# マイグレーションファイル確認
python manage.py showmigrations users

# 未適用の場合、実行
python manage.py migrate users

# 確認
python manage.py dbshell
# SELECT column_name FROM information_schema.columns 
# WHERE table_name='custom_user';
```

### 2.2 環境変数の設定

**backend/.env**:
```bash
# Auth0設定
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://api.your-domain.com
```

**backend/.env.example**（サンプル）:
```bash
# Auth0設定（オプション）
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://api.your-domain.com
```

### 2.3 settings.py の更新

**config/settings/base.py**:
```python
# Auth0設定
AUTH0_DOMAIN = config('AUTH0_DOMAIN', default='')
AUTH0_AUDIENCE = config('AUTH0_AUDIENCE', default='')

# REST Framework設定
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.common.auth.oidc.OIDCAuthentication',  # Auth0（優先）
        'rest_framework.authentication.SessionAuthentication',  # フォールバック
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

**重要**: 
- `OIDCAuthentication`を最初に配置
- `SessionAuthentication`をフォールバックとして残す
- これにより、既存のJWT Cookie認証も併用可能

### 2.4 動作確認
```bash
# サーバー起動
docker compose up -d backend

# ログ確認
docker compose logs -f backend

# エラーがないことを確認
# "AUTH0_DOMAIN is not set" などの警告は無視（環境変数設定前）
```

---

## ステップ3: フロントエンド実装

### 3.1 依存関係のインストール
```bash
cd frontend
npm install @auth0/auth0-react
```

### 3.2 Auth0 Provider設定

**src/main.tsx**:
```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { Auth0Provider } from '@auth0/auth0-react';
import App from './App';
import './index.css';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

// Auth0設定の存在確認
const auth0Domain = import.meta.env.VITE_AUTH0_DOMAIN;
const auth0ClientId = import.meta.env.VITE_AUTH0_CLIENT_ID;
const auth0Audience = import.meta.env.VITE_AUTH0_AUDIENCE;

const isAuth0Enabled = auth0Domain && auth0ClientId && auth0Audience;

root.render(
  <React.StrictMode>
    {isAuth0Enabled ? (
      <Auth0Provider
        domain={auth0Domain}
        clientId={auth0ClientId}
        authorizationParams={{
          redirect_uri: window.location.origin,
          audience: auth0Audience,
          scope: 'openid profile email',
        }}
        cacheLocation="localstorage"
        useRefreshTokens={true}
      >
        <App />
      </Auth0Provider>
    ) : (
      <App />
    )}
  </React.StrictMode>
);
```

**ポイント**:
- ✅ 環境変数の存在確認
- ✅ Auth0無効時も動作可能（既存認証を使用）
- ✅ `cacheLocation="localstorage"` でトークンを永続化
- ✅ `useRefreshTokens={true}` で自動リフレッシュ

### 3.3 認証フックの作成

**src/hooks/use-auth.ts**:
```typescript
import { useAuth0 } from '@auth0/auth0-react';

export const useAuth = () => {
  const {
    isAuthenticated,
    isLoading,
    user,
    loginWithRedirect,
    logout: auth0Logout,
    getAccessTokenSilently,
    error,
  } = useAuth0();

  const login = () => {
    loginWithRedirect({
      appState: {
        returnTo: window.location.pathname,
      },
    });
  };

  const logout = () => {
    auth0Logout({
      logoutParams: {
        returnTo: window.location.origin,
      },
    });
  };

  const getAccessToken = async () => {
    try {
      return await getAccessTokenSilently();
    } catch (error) {
      console.error('Failed to get access token:', error);
      throw error;
    }
  };

  return {
    isAuthenticated,
    isLoading,
    user,
    login,
    logout,
    getAccessToken,
    error,
  };
};
```

### 3.4 API Client の更新

**src/lib/api-client.ts**:
```typescript
import createClient, { type Middleware } from "openapi-fetch";
import type { paths } from "@/types/api";
import { ApiError } from "@/errors/api-error";

const BASE_API_URL = import.meta.env.VITE_BASE_API_URL || 'http://localhost:8000';

export const client = createClient<paths>({
  baseUrl: BASE_API_URL,
  credentials: "include",  // Cookie認証用
  headers: {
    "Content-Type": "application/json",
  },
});

// Auth0トークン自動付与Middleware
const auth0TokenMiddleware: Middleware = {
  async onRequest({ request }) {
    // Auth0が有効な場合のみトークンを取得
    if (window.auth0) {
      try {
        const token = await window.auth0.getAccessTokenSilently();
        request.headers.set('Authorization', `Bearer ${token}`);
      } catch (error) {
        console.warn('Failed to get Auth0 token:', error);
        // Cookie認証にフォールバック
      }
    }
    return request;
  },
};

// HTTPエラーハンドリング
const httpErrorMiddleware: Middleware = {
  async onResponse({ response }) {
    if (!response.ok) {
      const errorBody = await response.clone().json().catch(() => null);
      throw new ApiError(
        response.status,
        errorBody?.detail || errorBody?.message || response.statusText,
        errorBody,
        new Error(response.statusText)
      );
    }
    return response;
  },
};

client.use(auth0TokenMiddleware);
client.use(httpErrorMiddleware);
```

**重要**: 
- Auth0トークンが取得できない場合、Cookie認証にフォールバック
- 既存のCookie認証も並行して動作

### 3.5 Auth0インスタンスをグローバルに保存

**src/main.tsx**（追記）:
```typescript
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';

// Auth0インスタンスをグローバルに保存
function Auth0Wrapper({ children }: { children: React.ReactNode }) {
  const auth0 = useAuth0();
  
  React.useEffect(() => {
    window.auth0 = auth0;
  }, [auth0]);
  
  return <>{children}</>;
}

root.render(
  <React.StrictMode>
    {isAuth0Enabled ? (
      <Auth0Provider {...}>
        <Auth0Wrapper>
          <App />
        </Auth0Wrapper>
      </Auth0Provider>
    ) : (
      <App />
    )}
  </React.StrictMode>
);
```

**src/types/global.d.ts**:
```typescript
import { Auth0ContextInterface } from '@auth0/auth0-react';

declare global {
  interface Window {
    auth0?: Auth0ContextInterface;
  }
}

export {};
```

### 3.6 ログインページの更新

**src/pages/Auth/LoginPage.tsx**:
```typescript
import { useAuth } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';

export const LoginPage = () => {
  const { login, isLoading } = useAuth();

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold">ログイン</h1>
          <p className="mt-2 text-gray-600">
            Auth0アカウントでログインしてください
          </p>
        </div>
        
        <Button
          onClick={login}
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? 'ログイン中...' : 'Auth0でログイン'}
        </Button>
      </div>
    </div>
  );
};
```

### 3.7 環境変数の設定

**frontend/.env**:
```bash
# Auth0設定
VITE_AUTH0_DOMAIN=your-tenant.auth0.com
VITE_AUTH0_CLIENT_ID=your_client_id
VITE_AUTH0_AUDIENCE=https://api.your-domain.com

# 既存の設定
VITE_BASE_API_URL=http://localhost:8000
```

### 3.8 動作確認
```bash
# 開発サーバー起動
npm run dev

# ブラウザで http://localhost:5173 を開く
# ログインボタンをクリック
# Auth0 Universal Loginにリダイレクトされることを確認
```

---

## ステップ4: デプロイと検証

### 4.1 Staging環境への環境変数設定

**Render（バックエンド）**:
```
Dashboard → Web Service → Environment

AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://api.your-domain.com
```

**Cloudflare Pages（フロントエンド）**:
```
Dashboard → Pages → Settings → Environment Variables

VITE_AUTH0_DOMAIN=your-tenant.auth0.com
VITE_AUTH0_CLIENT_ID=your_client_id
VITE_AUTH0_AUDIENCE=https://api.your-domain.com
```

**GitHub（Terraform管理の場合）**:
```terraform
# terraform/modules/github/main.tf
resource "github_actions_environment_variable" "auth0_domain" {
  repository       = var.github_repo_name
  environment      = var.environment
  variable_name    = "VITE_AUTH0_DOMAIN"
  value           = var.auth0_domain
}
```

### 4.2 Auth0 Callback URLにStaging URLを追加
```
Auth0 Dashboard → Applications → Settings

Allowed Callback URLs に追加:
  https://your-frontend-staging.pages.dev

Allowed Logout URLs に追加:
  https://your-frontend-staging.pages.dev

Allowed Web Origins に追加:
  https://your-frontend-staging.pages.dev

"Save Changes" をクリック
```

### 4.3 Staging環境にデプロイ
```bash
# developブランチにプッシュ
git checkout -b feature/auth0-integration
git add .
git commit -m "feat: Add Auth0 OIDC authentication"
git push origin feature/auth0-integration

# PRを作成してマージ
# Staging環境に自動デプロイ
```

### 4.4 Staging環境での動作確認
```bash
# 1. Staging URLにアクセス
https://your-frontend-staging.pages.dev

# 2. ログインテスト
- ログインボタンをクリック
- Auth0 Universal Loginで認証
  - Email/Passwordでサインアップ
  - または既存アカウントでログイン
- ダッシュボードにリダイレクトされることを確認

# 3. API呼び出しテスト
- Todoを作成
- Todoを更新
- Todoを削除
- すべての操作が成功することを確認

# 4. ログアウトテスト
- ログアウトボタンをクリック
- ログイン画面にリダイレクトされることを確認

# 5. トークンリフレッシュテスト
- ログイン後、24時間以上放置（または手動でトークンを期限切れに）
- API呼び出しを実行
- 自動的にトークンがリフレッシュされることを確認
```

### 4.5 Django Adminでユーザー確認
```bash
# Staging環境のDjango Adminにアクセス
https://your-backend-staging.onrender.com/admin/

# Users → Custom users を確認
# oidc_sub フィールドに Auth0 User ID が保存されていることを確認
# 例: auth0|507f1f77bcf86cd799439011
```

### 4.6 Production環境へのデプロイ

**問題がなければ本番環境へ**:
```bash
# mainブランチにマージ
git checkout main
git merge develop
git push origin main

# Production環境に自動デプロイ
```

**Production環境の環境変数**:
- Render, Cloudflare Pages, GitHub に同様の環境変数を設定
- Auth0 Callback URLにProduction URLを追加

---

## ロールバック手順

### 問題が発生した場合

**方法1: 環境変数を削除**
```bash
# Cloudflare Pages:
VITE_AUTH0_DOMAIN を削除
VITE_AUTH0_CLIENT_ID を削除
VITE_AUTH0_AUDIENCE を削除

# Render:
AUTH0_DOMAIN を削除
AUTH0_AUDIENCE を削除

# 再デプロイ
# → 既存のJWT Cookie認証に自動フォールバック
```

**方法2: settings.py を元に戻す**
```python
# config/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 'apps.common.auth.oidc.OIDCAuthentication',  # コメントアウト
        'rest_framework.authentication.SessionAuthentication',
    ],
}
```

**方法3: Gitでリバート**
```bash
git revert HEAD
git push origin main
```

---

## 既存ユーザーのマイグレーション

### 戦略1: 自動連携（推奨）

**実装済みの`_get_or_create_user()`が自動的に処理**:
```
1. 既存ユーザーがAuth0でログイン
   ↓
2. emailで既存ユーザーを検索
   ↓
3. oidc_sub を追加
   ↓
4. 以降はAuth0で認証
```

**メリット**:
- ✅ ユーザーの操作不要
- ✅ シームレスな移行
- ✅ パスワードリセット不要

### 戦略2: Auth0へのユーザーインポート

**手順**:
```bash
# 1. ユーザーデータをエクスポート
python manage.py dumpdata users.CustomUser --output=users.json

# 2. Auth0形式に変換（スクリプト作成が必要）
python scripts/convert_to_auth0_format.py users.json > auth0_users.json

# 3. Auth0 Dashboardからインポート
# Users → Import Users → JSONファイルをアップロード

# 注意: パスワードはハッシュ化されているため、
# 初回ログイン時にパスワードリセットが必要
```

**Auth0インポート形式**:
```json
[
  {
    "email": "user@example.com",
    "email_verified": true,
    "given_name": "John",
    "family_name": "Doe",
    "password": "$2a$10$..."  // bcryptハッシュ（オプション）
  }
]
```

### 戦略3: パスワードリセットの案内

**メール送信**:
```
件名: 【重要】認証方式の変更について

本文:
いつもご利用いただきありがとうございます。

認証システムをAuth0に移行しました。
今後のログインは以下の手順で行ってください：

1. ログイン画面で「Forgot Password?」をクリック
2. メールアドレスを入力
3. Auth0からパスワードリセットメールが送信されます
4. 新しいパスワードを設定してください

ご不便をおかけしますが、よろしくお願いいたします。
```

---

## ソーシャルログイン設定

### Google
```
1. Auth0 Dashboard → Authentication → Social
2. "Google" をクリック
3. "Create a Client" をクリック（Auth0が自動設定）

または手動設定:
1. Google Cloud Console でOAuth Client作成
2. Authorized redirect URIs に追加:
   https://your-tenant.auth0.com/login/callback
3. Client ID と Client Secret をAuth0に入力
4. "Save" をクリック
```

### GitHub
```
1. Auth0 Dashboard → Authentication → Social
2. "GitHub" をクリック
3. GitHub Settings → Developer settings → OAuth Apps
4. "New OAuth App" をクリック
5. Authorization callback URL:
   https://your-tenant.auth0.com/login/callback
6. Client ID と Client Secret をAuth0に入力
7. "Save" をクリック
```

### ソーシャルログインのテスト
```
1. Auth0 Universal Loginを開く
2. "Continue with Google" または "Continue with GitHub" をクリック
3. 認証後、ダッシュボードにリダイレクト
4. Django AdminでユーザーのoidcOAuthを確認
   - oidc_sub: google-oauth2|123456789
   - または github|123456789
```

---

## MFA設定

### MFAの有効化
```
1. Auth0 Dashboard → Security → Multi-factor Auth
2. "Enable" をクリック
3. 以下から選択:
   - SMS (有料: $0.05/SMS)
   - TOTP (無料、Google Authenticator等)
   - Email (無料)
4. "Save" をクリック
```

### ユーザーへのMFA適用
```
方法1: 全ユーザーに必須
  Security → Multi-factor Auth → Required

方法2: 特定の条件で必須（Rulesで設定）
  Auth Pipeline → Rules → Create Rule
  
  function(user, context, callback) {
    if (user.email.endsWith('@company.com')) {
      context.multifactor = {
        provider: 'any',
        allowRememberBrowser: false
      };
    }
    callback(null, user, context);
  }
```

### MFAのテスト
```
1. MFA有効化後、ログイン
2. 初回ログイン時、MFA設定画面が表示
3. Google Authenticatorでスキャン
4. 6桁のコードを入力
5. 以降のログインでMFAコードを要求される
```

---

## トラブルシューティング

### エラー: Unable to find appropriate key

**症状**:
```
InvalidTokenError: Unable to find appropriate key
```

**原因**:
- JWTの`kid`とJWKSの公開鍵が一致しない
- JWKSキャッシュが古い

**解決策**:
```bash
# 1. JWKSを確認
curl https://{AUTH0_DOMAIN}/.well-known/jwks.json

# 2. トークンのkidを確認
# https://jwt.io でトークンをデコード

# 3. Djangoのキャッシュをクリア
python manage.py shell
>>> from django.core.cache import cache
>>> cache.delete('auth0_jwks')

# 4. サーバー再起動
docker compose restart backend
```

---

### エラー: Token has expired

**症状**:
```
TokenExpiredError: トークンの有効期限が切れています
```

**原因**:
- アクセストークンの有効期限切れ

**解決策**:
```typescript
// フロントエンドでトークンをリフレッシュ
const token = await getAccessTokenSilently({
  cacheMode: 'off'  // キャッシュを無視して再取得
});
```

**トークンライフタイムの変更**:
```
Auth0 Dashboard → APIs → Settings → Token Settings
- Token Expiration: 86400 (24時間)
- Token Expiration For Browser Flows: 7200 (2時間)
```

---

### エラー: Email not found in token

**症状**:
```
InvalidTokenError: Email not found in token
```

**原因**:
- Auth0のスコープ設定で`email`が含まれていない

**解決策**:
```typescript
// フロントエンドでスコープを指定
<Auth0Provider
  authorizationParams={{
    scope: "openid profile email"  // ← email を追加
  }}
>
```

---

### エラー: Callback URL not allowed

**症状**:
```
Auth0ログイン後にエラー画面
"The redirect URI is wrong. You sent http://localhost:5173..."
```

**解決策**:
```bash
# Auth0 Application Settings を確認
# Allowed Callback URLs に以下が含まれているか確認:
http://localhost:5173
https://your-frontend-staging.pages.dev
https://your-frontend.pages.dev

# "Save Changes" を忘れずにクリック
```

---

### エラー: IntegrityConstraintError

**症状**:
```
IntegrityConstraintError: このメールアドレスは既に使用されています
```

**原因**:
- 同じメールアドレスの既存ユーザーが存在

**解決策**:
```python
# 実装済みの _get_or_create_user() が自動的に処理
# 既存ユーザーに oidc_sub を追加
user = User.objects.filter(email=email).first()
user.oidc_sub = oidc_sub
user.save(update_fields=['oidc_sub'])
```

**手動で修正する場合**:
```bash
python manage.py shell

from apps.users.models import CustomUser

# 重複ユーザーを確認
CustomUser.objects.filter(email='duplicate@example.com')

# 古いユーザーを削除または統合
old_user = CustomUser.objects.get(email='duplicate@example.com', oidc_sub__isnull=True)
old_user.delete()
```

---

### エラー: CORS Error

**症状**:
```
Access to fetch at 'https://your-backend.onrender.com/api/v1/todos/' 
from origin 'https://your-frontend.pages.dev' has been blocked by CORS policy
```

**解決策**:
```python
# config/settings/base.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://your-frontend-staging.pages.dev",
    "https://your-frontend.pages.dev",
]

CORS_ALLOW_HEADERS = list(default_headers) + [
    "Authorization",  # ← Bearer トークン用
]

CORS_ALLOW_CREDENTIALS = True
```

---

### デバッグ方法

**バックエンドのログ確認**:
```bash
# ログをリアルタイムで確認
docker compose logs -f backend

# 特定のログを検索
docker compose logs backend | grep "Authentication error"
```

**フロントエンドのデバッグ**:
```typescript
// useAuth フックにデバッグログを追加
export const useAuth = () => {
  const auth0 = useAuth0();
  
  useEffect(() => {
    console.log('Auth0 State:', {
      isAuthenticated: auth0.isAuthenticated,
      isLoading: auth0.isLoading,
      user: auth0.user,
      error: auth0.error,
    });
  }, [auth0]);
  
  return auth0;
};
```

**JWTトークンのデバッグ**:
```typescript
const token = await getAccessTokenSilently();
console.log('Token:', token);

// https://jwt.io でトークンをデコード
// ペイロードを確認:
// - sub (oidc_sub)
// - email
// - exp (有効期限)
// - iss (発行元)
// - aud (オーディエンス)
```

---

## まとめ

このガイドに従うことで、既存のJWT Cookie認証からAuth0 OIDC認証への移行を安全に実施できます。

**移行後のメリット**:
- ✅ セキュリティ更新をAuth0に委譲
- ✅ ソーシャルログインが数分で実装可能
- ✅ MFAが標準機能で利用可能
- ✅ バックエンドのコード量を削減
- ✅ 監査ログと異常検知が標準機能

**サポート**:
- 問題が発生した場合は、[docs/auth0-integration.md](docs/auth0-integration.md) を参照してください
- Auth0の公式ドキュメント: https://auth0.com/docs