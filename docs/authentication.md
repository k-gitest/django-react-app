# 認証システム詳細ガイド

## 目次

- [概要](#概要)
- [設計変更の経緯](#設計変更の経緯)
- [認証方式の比較](#認証方式の比較)
- [カスタムユーザーモデル](#カスタムユーザーモデル)
- [Simple JWT設定](#simple-jwt設定)
- [dj-rest-auth Cookie設定](#dj-rest-auth-cookie設定)
- [CSRF対策](#csrf対策)
- [認証フロー](#認証フロー)
- [CustomRegisterViewの実装](#customregisterviewの実装)
- [APIエンドポイント](#apiエンドポイント)
- [重要な注意点](#重要な注意点)
- [フロントエンド実装](#フロントエンド実装)
- [TanStack Query による認証状態の同期](#tanstack-query-による認証状態の同期)
- [本番環境での設定変更](#本番環境での設定変更)
- [トラブルシューティング](#トラブルシューティング)

---

## 概要

**dj-rest-auth + djangorestframework-simplejwt**によるJWT Cookie認証を採用しています。

**主な特徴**:
- ✅ HttpOnly Cookie による XSS 対策
- ✅ JWT トークンローテーション（リプレイ攻撃対策）
- ✅ emailベース認証（username不要）
- ✅ 自動トークンリフレッシュ
- ✅ CSRF対策（Djangoミドルウェア）
- ✅ フロントエンドでのトークン管理不要

---

## 設計変更の経緯

### djoserからdj-rest-authへの移行

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

## 認証方式の比較

| 項目 | 旧設計（djoser） | 新設計（dj-rest-auth） |
|---|---|---|
| **方式** | JWT（Bearer認証） | JWT（Cookie認証） |
| **トークン格納先** | localStorage / sessionStorage | HttpOnly Cookie |
| **セキュリティ上の懸念** | XSS攻撃 | CSRF攻撃（Djangoミドルウェアで対応） |
| **設計判断の理由** | APIの利便性 | Web SPAにおけるXSSリスク回避を最優先 |
| **クライアント側の責務** | トークン管理が必要 | トークン管理不要（サーバー側に委譲） |

**設計判断のポイント**:

1. **XSS vs CSRF**: WebアプリではXSS攻撃の方がリスクが高い
2. **実装の複雑さ**: Cookie認証でもDjangoのCSRF対策で十分に安全
3. **保守性**: フロントエンドのトークン管理コードが不要になる

---

## カスタムユーザーモデル

`AbstractUser`と`BaseUserManager`を継承し、**emailベースの認証**を実装しています。

### 設計判断の理由

| 要件 | 採用した手法 |
|---|---|
| Django標準の認証機能を活用 | `AbstractUser`を継承 |
| username → email に変更 | `username = None`で無効化 |
| メールアドレスの大文字小文字問題 | `get_by_natural_key()`で`__iexact`検索 |
| createsuperuser対応 | `BaseUserManager`を継承してオーバーライド |

### 実装

**models.py**:
```python
from django.contrib.auth.models import AbstractUser, BaseUserManager

class CustomUserManager(BaseUserManager):
    """emailベース認証のカスタムマネージャー"""
    
    def get_by_natural_key(self, username):
        """大文字小文字を区別しない検索"""
        return self.get(**{f"{self.model.USERNAME_FIELD}__iexact": username})
    
    def create_user(self, email, password=None, **extra_fields):
        """通常ユーザーの作成"""
        if not email:
            raise ValueError('メールアドレスは必須です')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """スーパーユーザーの作成"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """emailベース認証のカスタムユーザーモデル"""
    
    username = None  # usernameフィールドを無効化
    email = models.EmailField('メールアドレス', unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # createsuperuser時の追加必須フィールド
    
    objects = CustomUserManager()
    
    def __str__(self):
        return self.email
```

**settings.py**:
```python
AUTH_USER_MODEL = 'users.CustomUser'
```

---

## Simple JWT設定

```python
SIMPLE_JWT = {
    # アクセストークンは短命に設定（セキュリティ優先）
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    
    # リフレッシュトークンは1日間有効（ユーザビリティとのバランス）
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    
    # トークンローテーション: refresh使用時に新しいrefreshを発行
    "ROTATE_REFRESH_TOKENS": True,
    
    # ローテーション後、古いrefreshトークンをブラックリストに追加
    "BLACKLIST_AFTER_ROTATION": True,
    
    # 標準のBearer認証スキームを使用（RFC 6750準拠）
    "AUTH_HEADER_TYPES": ("Bearer",),
}
```

**重要な設定の意味**:

| 設定 | 値 | 理由 |
|---|---|---|
| `ACCESS_TOKEN_LIFETIME` | 5分 | 短命にしてセキュリティリスクを低減 |
| `REFRESH_TOKEN_LIFETIME` | 1日 | ユーザビリティとセキュリティのバランス |
| `ROTATE_REFRESH_TOKENS` | True | refresh使用時に新しいrefreshを発行 |
| `BLACKLIST_AFTER_ROTATION` | True | 古いrefreshを無効化（リプレイ攻撃対策） |
| `AUTH_HEADER_TYPES` | Bearer | 業界標準（RFC 6750）に準拠 |

**トークンローテーションの仕組み**:

```
1. ユーザーがrefresh tokenでアクセス
   ↓
2. 新しいaccess tokenとrefresh tokenを発行
   ↓
3. 古いrefresh tokenをブラックリストに追加
   ↓
4. 古いrefresh tokenは再利用不可（リプレイ攻撃防止）
```

---

## dj-rest-auth Cookie設定

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
| `JWT_AUTH_SAMESITE` | None（本番） | クロスオリジンリクエストを許可 |
| `SESSION_LOGIN` | False | JWT認証に一元化し、アーキテクチャの一貫性を確保 |

**Cookie属性の組み合わせ**:

| 環境 | Secure | SameSite | 説明 |
|------|--------|----------|------|
| **開発（http）** | False | Lax | ローカル開発用 |
| **本番（https）** | True | None | クロスオリジン対応 |

---

## CSRF対策

Cookie認証では、CSRF（Cross-Site Request Forgery）攻撃への対策が必須です。

```python
# settings.py

CSRF_COOKIE_HTTPONLY = False  # フロントエンドがCSRFトークンを読み取り可能に
CSRF_COOKIE_SAMESITE = 'None'  # クロスオリジンリクエストの制御
CSRF_COOKIE_SECURE = True      # 本番環境のみTrue（開発はFalse）
CORS_ALLOW_CREDENTIALS = True  # Cookie送信を許可
```

**重要な設定**:

| 設定 | 値 | 理由 |
|---|---|---|
| `CSRF_COOKIE_HTTPONLY` | False | **SPAがCSRFトークンを読み取る必要がある** |
| `CORS_ALLOW_CREDENTIALS` | True | **Cookie認証にはCredentials送信が必須** |

**CSRF_COOKIE_HTTPONLY = False の理由**:

React（SPA）がCSRFトークンを読み取り、リクエストヘッダーに含める必要があるためです。これはSPAとCookie認証を組み合わせる際の標準的な設定です。

**CSRFトークンの流れ**:

```
1. フロントエンド起動時
   ↓
2. document.cookieからcsrftokenを取得
   ↓
3. APIリクエスト時、X-CSRFTokenヘッダーに含める
   ↓
4. Djangoミドルウェアが検証
```

**フロントエンド実装例**:

```typescript
// CSRFトークンの取得
function getCsrfToken(): string | null {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [key, value] = cookie.trim().split('=');
    if (key === name) return value;
  }
  return null;
}

// APIクライアント設定
const apiClient = ky.create({
  hooks: {
    beforeRequest: [
      (request) => {
        const csrfToken = getCsrfToken();
        if (csrfToken) {
          request.headers.set('X-CSRFToken', csrfToken);
        }
      }
    ]
  }
});
```

---

## 認証フロー

```
1. 新規登録  → POST /api/v1/auth/registration/
              ↓ HttpOnly Cookieでaccess-token, refresh-token発行
              ↓ CustomRegisterViewによる自動JWT設定
              
2. ログイン  → POST /api/v1/auth/login/
              ↓ HttpOnly Cookieでaccess-token, refresh-token発行
              
3. API呼び出し → Cookie自動送信（フロントエンドでのトークン操作不要）

4. トークン更新 → POST /api/v1/auth/token/refresh/
                 ↓ refresh-token Cookieが自動送信される
                 ↓ 新しいaccess-tokenとrefresh-tokenを発行
                 ↓ 古いrefresh-tokenはブラックリスト化
                 
5. ログアウト  → POST /api/v1/auth/logout/
                ↓ refresh-tokenをブラックリスト化
                ↓ Cookieを削除
```

---

## CustomRegisterViewの実装

### 新規登録プロセスの最適化

dj-rest-authの標準RegisterViewは、ユーザー作成後に自動でJWT Cookieを発行しません。本プロジェクトではCustomRegisterViewを実装し、登録成功時に即座にaccess-tokenを発行・Cookieへセットするように拡張しています。

**実装のメリット**:
- ✅ ユーザーは登録後にログイン操作をすることなく、シームレスにダッシュボードへ遷移可能
- ✅ UX向上（登録→ログイン→ダッシュボードの手間を削減）

### 実装コード

```python
from rest_framework_simplejwt.tokens import RefreshToken
from dj_rest_auth.registration.views import RegisterView

class CustomRegisterView(RegisterView):
    """
    カスタム登録ビュー
    
    機能:
        - JWT Cookie自動発行
        - ウェルカムメール送信（QStash経由、非同期）
        - 分析ログ記録（MotherDuck、非同期）
    """

    def create(self, request, *args, **kwargs):
        """
        ユーザー登録処理
        
        JWT Cookieを自動設定。
        """
        response = super().create(request, *args, **kwargs)

        # JWT Cookieを設定
        if hasattr(self, "access_token") and hasattr(self, "refresh_token"):
            self._set_jwt_cookies(response, self.access_token, self.refresh_token)

        return response
        
    def perform_create(self, serializer):
        """
        ユーザー作成の実行
        
        Serializerのsave()メソッドを呼び出し、
        JWT トークンを生成。
        """
        user = serializer.save(self.request)
        self.user = user

        # JWT トークン生成
        refresh = RefreshToken.for_user(user)
        self.access_token = str(refresh.access_token)
        self.refresh_token = str(refresh)

        return user

    def _set_jwt_cookies(self, response, access_token, refresh_token):
        """
        JWTトークンをCookieに設定
        """
        cookie_settings = {
            "httponly": settings.REST_AUTH.get("JWT_AUTH_HTTPONLY", True),
            "secure": settings.REST_AUTH.get("JWT_AUTH_SECURE", False),
            "samesite": settings.REST_AUTH.get("JWT_AUTH_SAMESITE", "Lax"),
            "path": "/",
        }

        response.set_cookie(
            key=settings.REST_AUTH.get("JWT_AUTH_COOKIE", "access-token"),
            value=access_token,
            max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
            **cookie_settings,
        )

        response.set_cookie(
            key=settings.REST_AUTH.get("JWT_AUTH_REFRESH_COOKIE", "refresh-token"),
            value=refresh_token,
            max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
            **cookie_settings,
        )
```

---

## APIエンドポイント

| 機能 | Method | エンドポイント | 認証 |
|---|---|---|---|
| **新規登録** | POST | `/api/v1/auth/registration/` | 不要 |
| **ログイン** | POST | `/api/v1/auth/login/` | 不要 |
| **ログアウト** | POST | `/api/v1/auth/logout/` | Cookie自動送信 |
| **ユーザー情報取得** | GET | `/api/v1/auth/user/` | Cookie自動送信 |
| **ユーザー情報更新** | PUT/PATCH | `/api/v1/auth/user/` | Cookie自動送信 |
| **トークンリフレッシュ** | POST | `/api/v1/auth/token/refresh/` | refresh-token Cookie |
| **パスワード変更** | POST | `/api/v1/auth/password/change/` | Cookie自動送信 |

**使用例**:

```bash
# 新規登録
curl -X POST http://localhost:8000/api/v1/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password1": "secure_password",
    "password2": "secure_password",
    "first_name": "John",
    "last_name": "Doe"
  }'

# ログイン
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password"
  }'

# ユーザー情報取得（Cookie自動送信）
curl -X GET http://localhost:8000/api/v1/auth/user/ \
  --cookie "access-token=xxx; refresh-token=xxx"
```

---

## 重要な注意点

### 1. トークンはHttpOnly Cookieで管理

- クライアントサイド（JavaScript）からトークンにアクセスできない
- XSS攻撃からの防御を実現

### 2. フロントエンドでのトークン管理は不要

- localStorage/sessionStorageへの保存は不要
- ブラウザが自動的にCookieを送信
- セキュリティリスクとコード量を同時に削減

### 3. トークンの自動更新

- `ROTATE_REFRESH_TOKENS=True`により、refresh token使用時に新しいrefresh tokenが発行される
- 古いrefresh tokenは自動的にブラックリストに追加され、再利用できなくなる（リプレイ攻撃対策）

### 4. 本番環境での設定変更

開発環境をhttpで行っていた場合、本番環境で設定の変更が必要です：

```python
# 本番環境では以下に変更
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'
JWT_AUTH_SECURE = True
JWT_AUTH_SAMESITE = 'None'
```

---

## フロントエンド実装

### フロントエンド実装の簡素化

Cookie認証への移行により、フロントエンド側のトークン管理が大幅に簡素化されました。

**不要になったコード**:
- ❌ localStorage/sessionStorageへのトークン保存
- ❌ Authorization ヘッダーの手動設定
- ❌ トークン期限の監視とリフレッシュロジック

**残った責務**:
- ✅ 認証エラー（401）の最終的なハンドリング
- ✅ ログインページへのリダイレクト

### APIクライアント設定

```typescript
// src/lib/api-client.ts
import ky from 'ky';

const apiClient = ky.create({
  prefixUrl: import.meta.env.VITE_BASE_API_URL,
  credentials: 'include',  // Cookie自動送信を有効化
  hooks: {
    beforeRequest: [
      (request) => {
        // CSRFトークンを自動付与
        const csrfToken = getCsrfToken();
        if (csrfToken) {
          request.headers.set('X-CSRFToken', csrfToken);
        }
      }
    ],
    afterResponse: [
      async (_request, _options, response) => {
        // 401エラー時の処理
        if (response.status === 401) {
          // ログアウト処理
          useAuthStore.getState().logout();
          // ログインページへリダイレクト
          window.location.href = '/login';
        }
      }
    ]
  }
});
```

---

## TanStack Query による認証状態の同期

### 従来の課題

useEffectによる認証状態の管理では、以下の課題がありました：

1. **競合状態（Race Condition）**: ログイン直後のリダイレクトとfetchMeのタイミングがずれる
2. **UXのチラつき**: 認証済みでも一瞬ログイン画面が表示される
3. **不要なネットワークリクエスト**: 再レンダリングごとにAPI呼び出し

### TanStack Query + Zustand による解決

```typescript
// src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,  // 5分間キャッシュ
    },
  },
});
```

```typescript
// src/features/auth/hooks/useAuth.ts
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/store/auth';
import { authService } from '../services/auth-service';

export const useAuth = () => {
  const { user, setUser, logout } = useAuthStore();

  const { data, isLoading, error } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: authService.fetchMe,
    enabled: !user,  // Zustandに状態があればスキップ
    staleTime: Infinity,  // 手動で無効化するまでキャッシュ
  });

  // データ取得成功時、Zustandを更新
  useEffect(() => {
    if (data) {
      setUser(data);
    }
  }, [data, setUser]);

  return { user, isLoading, error, logout };
};
```

```typescript
// src/features/auth/services/auth-service.ts
import { useMutation } from '@tanstack/react-query';
import { queryClient } from '@/lib/queryClient';
import { useAuthStore } from '@/store/auth';

export const useLogin = () => {
  const { setUser } = useAuthStore();

  return useMutation({
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
};
```

### 改善効果

| 課題 | 解決方法 | 効果 |
|------|---------|------|
| **競合状態** | setQueryDataによる明示的な同期 | ログイン直後のリダイレクトで確実にガード通過 |
| **UXのチラつき** | Zustand + Query Cacheの即時更新 | 認証済みユーザーの画面遷移が滑らか |
| **不要なリクエスト** | サーバー状態のキャッシュ管理 | 再レンダリング時のAPI呼び出しを削減 |

---

## 本番環境での設定変更

開発環境をhttpで行っていた場合、本番環境で以下の設定変更が必要です。

**settings/production.py**:
```python
# CSRF設定
CSRF_COOKIE_SECURE = True      # HTTPSのみ送信
CSRF_COOKIE_SAMESITE = 'None'  # クロスオリジン対応

# JWT Cookie設定
REST_AUTH = {
    'USE_JWT': True,
    'SESSION_LOGIN': False,
    'JWT_AUTH_COOKIE': 'access-token',
    'JWT_AUTH_REFRESH_COOKIE': 'refresh-token',
    'JWT_AUTH_HTTPONLY': True,
    'JWT_AUTH_SECURE': True,      # HTTPSのみ送信
    'JWT_AUTH_SAMESITE': 'None',  # クロスオリジン対応
}
```

**環境変数**:
```bash
# .env (本番)
DJANGO_SETTINGS_MODULE=config.settings.production
FRONTEND_URL=https://your-frontend.pages.dev
```

---

## トラブルシューティング

### エラー: Cookieが送信されない

**症状**:
```
API呼び出し時に401 Unauthorizedエラー
```

**確認項目**:
```bash
1. フロントエンド設定
   credentials: 'include' が設定されているか確認

2. バックエンド設定
   CORS_ALLOW_CREDENTIALS = True
   CORS_ALLOWED_ORIGINS に フロントエンドURL が含まれているか

3. Cookie設定
   開発環境: SECURE=False, SAMESITE='Lax'
   本番環境: SECURE=True, SAMESITE='None'
```

---

### エラー: CSRF検証失敗

**症状**:
```
403 Forbidden: CSRF verification failed
```

**確認項目**:
```bash
1. CSRFトークンの送信
   X-CSRFToken ヘッダーが設定されているか

2. Cookie設定
   CSRF_COOKIE_HTTPONLY = False
   （フロントエンドが読み取る必要がある）

3. CORS設定
   CORS_ALLOW_CREDENTIALS = True
```

**デバッグ**:
```typescript
// CSRFトークンの確認
console.log('CSRF Token:', getCsrfToken());

// リクエストヘッダーの確認
apiClient.get('/test/', {
  hooks: {
    beforeRequest: [
      (request) => {
        console.log('Headers:', request.headers);
      }
    ]
  }
});
```

---

### エラー: トークンリフレッシュ失敗

**症状**:
```
refresh tokenが無効になる
```

**確認項目**:
```bash
1. トークンローテーション
   ROTATE_REFRESH_TOKENS = True
   BLACKLIST_AFTER_ROTATION = True

2. ブラックリストアプリ
   INSTALLED_APPS に 'rest_framework_simplejwt.token_blacklist' が含まれているか

3. マイグレーション
   python manage.py migrate
```

---

### エラー: ログイン後にリダイレクトされない

**症状**:
```
ログイン成功後、ダッシュボードに遷移しない
```

**確認項目**:
```typescript
1. TanStack Queryキャッシュの更新
   queryClient.setQueryData(['auth', 'me'], userData);

2. Zustand Storeの更新
   setUser(userData);

3. リダイレクト処理
   navigate('/dashboard');
```

---

## まとめ

| 項目 | 実装方法 |
|------|---------|
| **認証方式** | JWT Cookie認証（dj-rest-auth） |
| **ユーザーモデル** | emailベース認証（AbstractUser継承） |
| **セキュリティ** | HttpOnly Cookie + CSRF対策 |
| **トークンライフタイム** | Access: 5分、Refresh: 1日 |
| **トークンローテーション** | 有効（リプレイ攻撃対策） |
| **フロントエンド管理** | 不要（Cookie自動送信） |
| **認証状態管理** | TanStack Query + Zustand |

この設計により、以下を実現しています：

✅ **高いセキュリティ**: XSS攻撃からの防御  
✅ **シンプルな実装**: フロントエンドのトークン管理が不要  
✅ **優れたUX**: 登録後の自動ログイン、滑らかな画面遷移  
✅ **保守性の高さ**: 実績のあるライブラリに基づく設計  
✅ **スケーラビリティ**: トークンローテーションによる長期運用対応