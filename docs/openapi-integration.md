# OpenAPI統合 詳細ガイド

## 目次

- [概要](#概要)
- [アーキテクチャ](#アーキテクチャ)
- [バックエンド実装](#バックエンド実装)
- [フロントエンド実装](#フロントエンド実装)
- [CI/CD統合](#cicd統合)
- [ベストプラクティス](#ベストプラクティス)
- [トラブルシューティング](#トラブルシューティング)

---

## 概要

本プロジェクトでは、**drf-spectacular**を使用してDjango REST FrameworkのAPIからOpenAPIスキーマを自動生成し、**openapi-typescript**でTypeScript型定義を生成することで、型安全なAPI開発を実現しています。

### なぜOpenAPI統合が必要なのか

| 課題 | OpenAPI統合による解決 |
|------|---------------------|
| **API仕様の不一致** | スキーマから自動生成するため常に同期 |
| **手動の型定義メンテナンス** | 自動生成により手動メンテナンス不要 |
| **API変更時の見落とし** | 型エラーでコンパイル時に検出 |
| **ドキュメントの陳腐化** | 実装と常に一致したドキュメント |

---

## アーキテクチャ

### 全体像
```
┌─────────────────────────────────────────────────────────────┐
│              OpenAPI Integration Architecture               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  【定義】                                                    │
│    Backend (Django)                                         │
│    ├─ rest_schemas.py                                      │
│    │   └─ extend_schema でAPIを詳細に定義                  │
│    │                                                       │
│    └─ views.py                                             │
│        └─ @スキーマデコレーター でViewに適用               │
│                                                             │
│  【生成】                                                    │
│    python manage.py spectacular                             │
│    └─ schema.yml (OpenAPI 3.0仕様)                         │
│                                                             │
│  【CI/CD】                                                  │
│    GitHub Actions                                           │
│    ├─ Backend: schema.yml を生成・アップロード             │
│    └─ Frontend: schema.yml から型定義を生成                │
│                                                             │
│  【適用】                                                    │
│    Frontend (React + TypeScript)                           │
│    ├─ api.d.ts (自動生成型定義)                            │
│    └─ サービス層で型を適用                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### データフロー
```
1. 開発者がAPIを実装
   ↓
2. rest_schemas.py でスキーマを定義
   ↓
3. views.py にデコレーターを追加
   ↓
4. CI/CDでスキーマを自動生成
   ↓
5. フロントエンドの型定義を自動生成
   ↓
6. 型チェックで不整合を検出
   ↓
7. デプロイ
```

---

### 設計判断：openapi-typescriptを採用

本プロジェクトでは、OpenAPIスキーマからTypeScript型を生成する際に、**openapi-typescript**を採用し、**Orval**は不採用としました。

#### openapi-typescriptとは

[openapi-typescript](https://github.com/drwpow/openapi-typescript)は、OpenAPIスキーマから**型定義のみ**を生成する軽量なツールです。

| 機能 | 説明 |
|------|------|
| TypeScript型定義 | `paths`, `components`等の型を生成 |
| シンプルな設計 | 型生成のみに特化 |
| ゼロ依存 | 軽量で高速 |

---

#### Orvalとの比較

[Orval](https://orval.dev/)は、OpenAPIスキーマから型定義だけでなく、APIクライアント、React Query hooks、MSWハンドラーを自動生成できる多機能ツールです。

| 項目 | openapi-typescript（採用） | Orval |
|------|--------------------------|-------|
| **型定義** | ✅ 自動生成 | ✅ 自動生成 |
| **APIクライアント** | ❌ 手動実装 | ✅ 自動生成（`postAuthLogin()`等） |
| **React Query hooks** | ❌ 手動実装 | ✅ 自動生成（`useGetAuthUser()`等） |
| **MSWハンドラー** | ❌ 手動実装 | ✅ 自動生成（Faker.js使用） |
| **バンドルサイズ** | ⭐ 軽量 | やや重い |
| **学習コスト** | ⭐ 低い | 中程度 |
| **カスタマイズ性** | ⭐ 高い | 中程度 |

---

#### Orval不採用の理由

##### 1. MSWハンドラーは「テストシナリオ」である

Orvalが生成するMSWハンドラーは、Faker.jsを使ってランダムな値を返します：
```typescript
// ❌ Orval生成（ランダム値）
export const getPostAuthLoginMockHandler = () => {
  return http.post('**/auth/login/', () => {
    return HttpResponse.json({
      user: { 
        id: faker.string.uuid(),        // ← 毎回違う値
        email: faker.internet.email()   // ← 毎回違う値
      }
    })
  })
}
```

しかし、実際のテストでは**特定のシナリオ**を表現する必要があります：
```typescript
// ✅ 現在の実装（シナリオを明確に表現）
export const authHandlers = [
  http.post(`**/auth/login/`, async ({ request }) => {
    const body = await request.json();
    
    // シナリオ1: 正常ログイン
    if (body.email === 'test@example.com') {
      return HttpResponse.json(mockToken, { status: 200 });
    }
    
    // シナリオ2: パスワード間違い
    if (body.password === 'wrong') {
      return HttpResponse.json(
        { detail: 'パスワードが正しくありません。' },
        { status: 400 }
      );
    }
    
    // シナリオ3: レート制限
    if (body.email === 'rate-limited@example.com') {
      return HttpResponse.json(
        { detail: 'リクエストが多すぎます。' },
        { status: 429 }
      );
    }
  }),
];
```

**Orvalの問題点**:
- ❌ エラーケース（401, 400, 429）を表現できない
- ❌ 条件分岐（email/passwordによる挙動変更）ができない
- ❌ 特定の値でアサーションできない
- ❌ テストシナリオを明示的に表現できない

---

##### 2. 不要な中間層の増加

Orvalを導入すると、レイヤードアーキテクチャに不要な中間層が増えます：
```typescript
// ❌ Orval導入後
useAuth (Hook)
  ↓
auth-service (Service)
  ↓
postAuthLogin (Orval生成) ← 中間層
  ↓
customInstance (Mutator) ← さらに中間層
  ↓
apiClient (ky)
  ↓
Backend API

// ✅ 現在の構成
useAuth (Hook)
  ↓
auth-service (Service)
  ↓
apiClient (ky)
  ↓
Backend API
```

**問題点**:
- ❌ デバッグが困難（中間層が多い）
- ❌ リクエストボディの変換ロジックが不透明
- ❌ エラーハンドリングが複雑化
- ❌ カスタマイズが難しい

現在の実装は明確で保守しやすい：
```typescript
// ✅ 現在の実装（明確）
export const loginService = async (
  credentials: ApiReq<"/api/v1/auth/login/", "post">
): Promise<ApiRes<"/api/v1/auth/login/", "post">> => {
  return apiClient.post('auth/login/', {
    json: credentials,
  }).json<ApiRes<"/api/v1/auth/login/", "post">>();
};
```

---

##### 3. 既存ツールとの重複

本プロジェクトでは既に以下のツールを使用しており、Orvalと機能が重複します：

| コンポーネント | 現在 | Orval導入後 |
|--------------|------|------------|
| HTTPクライアント | apiClient (ky) | customInstance + apiClient |
| データフェッチ | TanStack Query | Orval生成hooks |
| 型定義 | openapi-typescript | Orval生成型 |
| MSWハンドラー | 手動実装（シナリオ明確） | Orval生成（ランダム値） |

移行コストがメリットを上回りません。

---

##### 4. プロジェクトの設計哲学との不整合

本プロジェクトは以下の原則を重視しています：

| 原則 | openapi-typescript | Orval |
|------|-------------------|-------|
| シンプルで理解しやすい | ✅ 型定義のみ自動生成 | ❌ 多機能だがブラックボックス化 |
| 適切な抽象化 | ✅ 必要最小限 | ❌ 過剰な自動化 |
| チーム開発を想定 | ✅ 標準的なTS/React | ❌ Orval固有の知識が必要 |
| 保守性 | ✅ コードが明確 | ❌ 生成コードの変更が困難 |

---

#### Orvalが有効なケース（本プロジェクトには該当しない）

Orvalは以下のようなプロジェクトには有効です：

| ケース | 理由 |
|--------|------|
| 巨大なAPI（100+ エンドポイント） | 手動実装のコストが高い |
| 複数チームでの開発 | 統一されたAPIクライアントが必要 |
| 短期プロジェクト | 開発速度を最優先 |
| API仕様が頻繁に変わる | 手動更新が追いつかない |

**本プロジェクトの状況**:
- ✅ API数が少ない（auth, todos, webhooks）
- ✅ 単一チーム（または個人開発）
- ✅ 長期保守を重視
- ✅ API仕様は安定している

---

#### 採用アプローチ：openapi-typescript + 手動実装

本プロジェクトでは、以下の構成を採用しています：
```
openapi-typescript: 型定義のみ自動生成（シンプル）
  ↓
apiClient: HTTP通信を薄くラップ
  ↓
auth-service: ビジネスロジックを集約
  ↓
useAuth (TanStack Query): データフェッチを制御
  ↓
MSWハンドラー: テストシナリオを明確に表現
```

**メリット**:
- ✅ バックエンドのAPIスキーマと常に同期
- ✅ 型エラーでスキーマ変更を検知
- ✅ テストシナリオを細かく制御可能
- ✅ IDEの補完が効く
- ✅ デバッグが容易
- ✅ 学習コストが低い

---

#### MSWハンドラーに型を適用

手動実装のMSWハンドラーにも、OpenAPI生成型を適用することで型安全性を確保：
```typescript
// tests/mocks/handlers/auth.handlers.ts
import type { components } from '@/types/api';

type UserInfo = components['schemas']['UserDetails'];
type TokenResponse = components['schemas']['TokenObtainPair'];

export const mockUser: UserInfo = {
  pk: 1,
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
};

export const mockToken: TokenResponse = {
  access: 'access-token',
  refresh: 'refresh-token',
  user: mockUser,
};

export const authHandlers = [
  http.get(`**/auth/user/`, () =>
    HttpResponse.json(mockUser, { status: 200 })
  ),

  http.post(`**/auth/login/`, async ({ request }) => {
    const body = await request.json();
    
    if (body.email === 'test@example.com' && body.password === 'password') {
      return HttpResponse.json(mockToken, { status: 200 });
    }
    
    return HttpResponse.json(
      { detail: 'Invalid credentials' },
      { status: 401 }
    );
  }),
];
```

**これにより**:
- ✅ バックエンドのスキーマ変更を型エラーで検知
- ✅ モックデータの型安全性を確保
- ✅ テストシナリオの表現力を維持

### HTTPクライアントの選択：openapi-fetch

本プロジェクトでは、OpenAPI統合を最大限に活用するため、**openapi-fetch**を採用しています。

#### 技術スタック

| コンポーネント | 役割 |
|--------------|------|
| **drf-spectacular** | DjangoからOpenAPIスキーマを生成 |
| **openapi-typescript** | スキーマからTypeScript型を生成 |
| **openapi-fetch** | 型安全なHTTPクライアント |
| **Middleware** | エラーハンドリング・ログ記録 |

#### データフロー
```
1. Backend: drf-spectacular
   ↓ schema.yml
2. openapi-typescript
   ↓ api.d.ts
3. openapi-fetch
   ↓ client.POST("/path", {...})
4. Middleware
   ↓ エラーハンドリング
5. Service Layer
   ↓ 型安全なAPIコール
6. TanStack Query
   ↓ リトライ・キャッシュ管理
```

---

## バックエンド実装

### 1. セットアップ

#### 依存関係のインストール
```bash
# backend/requirements.txt に追加
drf-spectacular==0.27.0
```
```bash
pip install -r requirements.txt
```

#### Django設定
```python
# backend/config/settings/base.py

INSTALLED_APPS = [
    # ...
    'drf_spectacular',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # 既存の設定...
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Django React App API',
    'DESCRIPTION': 'Django/React モノレポベースのSPAアプリケーション',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    
    # Cookie認証の設定
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'cookieAuth': {
                'type': 'apiKey',
                'in': 'cookie',
                'name': 'access-token',
                'description': 'JWT Access Token（HttpOnly Cookie）'
            }
        }
    },
    'SECURITY': [{'cookieAuth': []}],
    
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/v1',
}
```

#### URL設定
```python
# backend/config/urls.py

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    # OpenAPI Schema（常に有効）
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
]

# 開発環境のみSwagger UIを有効化
if settings.DEBUG:
    urlpatterns += [
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ]
```

---

### 2. 共通エラーレスポンスの定義
```python
# backend/apps/common/schemas.py

from drf_spectacular.utils import OpenApiExample

class CommonSchemas:
    """共通のスキーマ定義"""
    
    # エラーレスポンス
    ERROR_400 = OpenApiExample(
        'Bad Request',
        value={
            'error': 'validation_error',
            'detail': 'リクエストデータが不正です',
            'data': {
                'field_name': ['エラーメッセージ']
            }
        },
        response_only=True,
    )
    
    ERROR_401 = OpenApiExample(
        'Unauthorized',
        value={
            'error': 'authentication_failed',
            'detail': '認証情報が提供されていません。'
        },
        response_only=True,
    )
    
    ERROR_403 = OpenApiExample(
        'Forbidden',
        value={
            'error': 'permission_denied',
            'detail': 'この操作を実行する権限がありません。'
        },
        response_only=True,
    )
    
    ERROR_404 = OpenApiExample(
        'Not Found',
        value={
            'error': 'not_found',
            'detail': 'リソースが見つかりません。'
        },
        response_only=True,
    )
    
    ERROR_429 = OpenApiExample(
        'Too Many Requests',
        value={
            'detail': 'リクエストが多すぎます。しばらく時間を置いてから再度お試しください。'
        },
        response_only=True,
    )
    
    ERROR_500 = OpenApiExample(
        'Internal Server Error',
        value={
            'error': 'internal_error',
            'detail': 'サーバーエラーが発生しました。'
        },
        response_only=True,
    )
    
    # よく使うレスポンス定義
    COMMON_RESPONSES = {
        401: ERROR_401,
        403: ERROR_403,
        404: ERROR_404,
        429: ERROR_429,
        500: ERROR_500,
    }
```

---

### 3. アプリケーション別のスキーマ定義

#### スキーマ定義の設計判断：関数 vs クラス属性

本プロジェクトでは、アプリケーションの特性に応じて**関数**と**クラス属性**を使い分けています。

##### 認証アプリケーション：関数による遅延評価

認証APIでは、`get_serializer_class`をオーバーライドしてリクエストとレスポンスで異なるシリアライザーを使用するため、**関数**でスキーマを定義します。

**なぜ関数にするのか？**

| 方式 | 評価タイミング | 問題 |
|------|-------------|------|
| **クラス属性** | ファイル読み込み時 | ❌ シリアライザーがまだ読み込まれていない可能性<br>❌ `extend_schema_view`との組み合わせで循環参照 |
| **関数** | 呼び出し時（View適用時） | ✅ 確実にシリアライザーが読み込まれている<br>✅ 循環参照を回避 |

**実装例**:
```python
# backend/apps/users/rest_schemas.py

from drf_spectacular.utils import extend_schema, OpenApiExample

def get_register_schema():
    """
    登録APIのスキーマ定義を返す
    
    関数にすることで、インポート時ではなく使用時に評価される。
    これにより、CustomRegisterSerializerとAuthResponseSerializerが
    確実に読み込まれた後にスキーマが構築される。
    """
    from .serializers import CustomRegisterSerializer, AuthResponseSerializer
    
    return extend_schema(
        summary="新規登録",
        description="""
        新規ユーザーを登録します。
        
        **機能:**
        - HttpOnly CookieにJWTトークンを自動設定
        - ウェルカムメールを非同期送信（QStash経由）
        - 登録イベントを記録（MotherDuck Analytics）
        
        **レート制限:** 3回/1時間
        """,
        request=CustomRegisterSerializer,  # リクエスト用
        responses={
            201: AuthResponseSerializer,    # レスポンス用
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'},
                    'data': {'type': 'object'},
                }
            },
            429: {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'}
                }
            },
        },
        examples=[
            OpenApiExample(
                'Success',
                value={
                    'user': {
                        'id': 1,
                        'email': 'user@example.com',
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'is_staff': False
                    },
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
                    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...'
                },
                response_only=True,
                status_codes=['201'],
            ),
            OpenApiExample(
                'User Already Exists',
                value={
                    'error': 'user_already_exists',
                    'detail': 'メールアドレス user@example.com は既に登録されています',
                    'data': {'field': 'email'}
                },
                response_only=True,
                status_codes=['400'],
            ),
            OpenApiExample(
                'Too Many Requests',
                value={
                    'detail': 'リクエストが多すぎます。'
                },
                response_only=True,
                status_codes=['429'],
            ),
        ],
        tags=['Authentication']
    )


def get_login_schema():
    """ログインAPIのスキーマ定義を返す"""
    from .serializers import LoginSerializer, AuthResponseSerializer
    
    return extend_schema(
        summary="ログイン",
        description="""
        メールアドレスとパスワードでログインします。
        
        **機能:**
        - HttpOnly CookieにJWTトークンを設定
        - ログイン履歴を記録（MotherDuck Analytics）
        
        **レート制限:** 5回/5分
        """,
        request=LoginSerializer,
        responses={
            200: AuthResponseSerializer,
            400: {
                'type': 'object',
                'properties': {
                    'non_field_errors': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    }
                }
            },
            429: {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string'}
                }
            },
        },
        examples=[
            OpenApiExample(
                'Success',
                value={
                    'user': {
                        'id': 1,
                        'email': 'user@example.com',
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'is_staff': False
                    },
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
                    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...'
                },
                response_only=True,
                status_codes=['200'],
            ),
            OpenApiExample(
                'Bad Request - Invalid Credentials',
                value={
                    'non_field_errors': ['メールアドレスまたはパスワードが正しくありません。']
                },
                response_only=True,
                status_codes=['400'],
            ),
            OpenApiExample(
                'Too Many Requests',
                value={
                    'detail': 'リクエストが多すぎます。しばらく時間を置いてから再度お試しください。'
                },
                response_only=True,
                status_codes=['429'],
            ),
        ],
        tags=['Authentication']
    )


def get_logout_schema():
    """ログアウトAPIのスキーマ定義を返す"""
    return extend_schema(
        summary="ログアウト",
        description="""
        現在のセッションからログアウトします。
        
        **機能:**
        - リフレッシュトークンをブラックリストに追加
        - Cookieをクリア
        - ログアウトイベントを記録（MotherDuck Analytics）
        
        **注意:** ログアウト後は、再度ログインが必要です。
        """,
        request=None,
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'detail': {
                        'type': 'string',
                        'example': 'ログアウトしました。'
                    }
                }
            },
        },
        tags=['Authentication']
    )
```

**Viewへのデコレーター適用**:
```python
# backend/apps/users/views.py

from drf_spectacular.utils import extend_schema_view
from .rest_schemas import get_register_schema, get_login_schema, get_logout_schema

@extend_schema_view(post=get_register_schema())  # ← 関数を呼び出す
@method_decorator(...)
class CustomRegisterView(RegisterView):
    """カスタム登録ビュー"""
    
    def create(self, request, *args, **kwargs):
        # ...
        pass


@extend_schema_view(post=get_login_schema())  # ← 関数を呼び出す
@method_decorator(...)
class CustomLoginView(LoginView):
    """カスタムログインビュー"""
    
    def post(self, request, *args, **kwargs):
        # ...
        pass


@extend_schema_view(post=get_logout_schema())  # ← 関数を呼び出す
class CustomLogoutView(LogoutView):
    """カスタムログアウトビュー"""
    
    def post(self, request, *args, **kwargs):
        # ...
        pass
```

---

##### TodoアプリケーションとCommon：クラス属性のまま

TodoアプリケーションとCommon（共通定義）では、従来通り**クラス属性**で定義しています。これらは以下の理由で問題ありません：

**問題が発生しない理由**:
- ✅ ViewSetで直接使われている（`@extend_schema_view`を使わない）
- ✅ シンプルな`ModelSerializer`を使用
- ✅ リクエストとレスポンスで同じシリアライザー
- ✅ 循環参照の問題が発生していない
- ✅ スキーマが正しく生成されている

**実装例（Todos）**:
```python
# backend/apps/todos/rest_schemas.py

from drf_spectacular.utils import extend_schema, OpenApiParameter
from apps.common.rest_schemas import CommonSchemas
from .serializers import TodoSerializer

class TodoSchemas:
    """Todo関連のOpenAPIスキーマ定義"""
    
    list = extend_schema(
        summary="Todoリスト取得",
        description="ログインユーザーに紐づくTodoアイテムの一覧を取得します。",
        responses={
            200: TodoSerializer(many=True),
            **CommonSchemas.COMMON_RESPONSES
        },
        tags=['Todos']
    )
    
    create = extend_schema(
        summary="Todo作成",
        description="""
        新しいTodoアイテムを作成します。
        
        作成後、非同期でベクトルインデックスに追加されます（QStash経由）。
        """,
        request=TodoSerializer,
        responses={
            201: TodoSerializer,
            400: CommonSchemas.ERROR_400,
            **CommonSchemas.COMMON_RESPONSES
        },
        tags=['Todos']
    )
    
    # ... その他のエンドポイント
```

**Viewへのデコレーター適用**:
```python
# backend/apps/todos/views.py

from .rest_schemas import TodoSchemas

class TodoViewSet(viewsets.ModelViewSet):
    serializer_class = TodoSerializer
    permission_classes = [IsAuthenticated]
    
    @TodoSchemas.list  # ← クラス属性として直接参照
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @TodoSchemas.create  # ← クラス属性として直接参照
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    # ...
```

---

##### 使い分けガイドライン

| 状況 | 推奨方式 | 理由 |
|------|---------|------|
| **`get_serializer_class`を使用** | 関数 | スキーマ生成が複雑化し、循環参照のリスクがあるため |
| **リクエストとレスポンスで異なるシリアライザー** | 関数 | 循環参照を避け、確実にシリアライザーが読み込まれるため |
| **`extend_schema_view`を使用** | 関数 | デコレーター適用時の評価タイミングを制御するため |
| **スキーマ生成に問題が発生** | 関数 | 遅延評価で解決できるため |
| **ViewSetでシンプルに使用** | クラス属性 | コードが読みやすく、問題が発生しないため |
| **問題なく動作している** | クラス属性 | 不要な変更を避けるため |

**設計原則**:
- ✅ 各アプリケーションの特性に応じた最適な方法を選択
- ✅ 問題が発生していない場合は変更しない
- ✅ 問題が発生した場合は関数化で解決

この設計により、保守性と実用性のバランスを保ちながら、型安全なAPI開発を実現しています。

---

### 5. スキーマ生成コマンド
```bash
# スキーマを生成
cd backend
python manage.py spectacular --color --file schema.yml

# 生成されたスキーマを確認
cat schema.yml
```

---

## フロントエンド実装

### 1. セットアップ

#### 依存関係のインストール
```bash
cd frontend
npm install openapi-fetch
npm install -D openapi-typescript
```

#### package.json スクリプト
```json
{
  "scripts": {
    "generate:api": "openapi-typescript http://localhost:8000/api/schema/ -o src/types/api.d.ts",
    "generate:api:local": "openapi-typescript ../backend/schema.yml -o src/types/api.d.ts"
  }
}
```

---

### 2. クライアントのセットアップ

#### api-client.ts の作成
```typescript
// frontend/src/lib/api-client.ts
import createClient, { type Middleware } from "openapi-fetch";
import type { paths } from "@/types/api";
import { BASE_API_URL } from "@/lib/constants";
import { ApiError } from "@/errors/api-error";
import { NetworkError } from "@/errors/network-error";

/**
 * OpenAPI型付きクライアント
 */
export const client = createClient<paths>({
  baseUrl: BASE_API_URL,
  credentials: "include",
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * ログ出力ミドルウェア（開発時のみ）
 */
const loggerMiddleware: Middleware = {
  async onRequest({ request }) {
    if (import.meta.env.DEV) {
      console.log(`🚀 [API] ${request.method} ${request.url}`);
    }
    return request;
  },
};

/**
 * HTTPエラーハンドリング (4xx, 5xx)
 */
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

/**
 * 通信エラーハンドリング (オフライン, タイムアウト)
 */
const networkErrorMiddleware: Middleware = {
  async onError({ error }) {
    const message = error instanceof Error 
      ? error.message 
      : "ネットワークエラーが発生しました";
    throw new NetworkError(message, error instanceof Error ? error : undefined);
  },
};

// ミドルウェアの登録（上から順に適用）
client.use(loggerMiddleware);
client.use(httpErrorMiddleware);
client.use(networkErrorMiddleware);

export const apiClient = client;
```

---

### 3. 型ユーティリティ（オプション）

openapi-fetchでは基本的に型ユーティリティは不要ですが、既存のコードとの互換性のために残すこともできます：
```typescript
// frontend/src/types/api-utils.ts
import type { paths } from './api';

/**
 * レスポンス型抽出（後方互換用）
 * openapi-fetchでは不要だが、既存コードのために残す
 */
export type ApiRes
  P extends keyof paths,
  M extends keyof paths[P] & string
> = paths[P][M] extends { responses: { 200: { content: { "application/json": infer T } } } }
  ? T
  : paths[P][M] extends { responses: { 201: { content: { "application/json": infer T } } } }
  ? T
  : void;

/**
 * リクエスト型抽出（後方互換用）
 */
export type ApiReq
  P extends keyof paths,
  M extends keyof paths[P] & string
> = paths[P][M] extends { requestBody?: { content: { "application/json": infer T } } }
  ? Exclude<T, undefined> 
  : Record<string, never>;
```

**推奨**: 新規コードでは`ApiReq`/`ApiRes`を使わず、直接`paths`から型を取得してください。

---

### 4. サービス層の実装

#### 基本的な実装
```typescript
// frontend/src/features/auth/services/auth-service.ts
import { apiClient } from '@/lib/api-client';

/**
 * ログイン
 * 
 * 型は完全に自動推論される
 */
export const loginService = async (credentials: {
  email: string;
  password: string;
}) => {
  const { data } = await apiClient.POST("/api/v1/auth/login/", {
    body: credentials,
  });
  return data; // data は TokenResponse 型として推論される
};

/**
 * サインアップ
 */
export const signupService = async (credentials: {
  email: string;
  password: string;
}) => {
  const { data } = await apiClient.POST("/api/v1/auth/registration/", {
    body: {
      email: credentials.email,
      password1: credentials.password,
      password2: credentials.password,
    },
  });
  return data;
};

/**
 * ログアウト
 */
export const logoutService = async () => {
  await apiClient.POST("/api/v1/auth/logout/", {
    body: {},
  });
};

/**
 * ユーザー情報取得
 */
export const fetchMe = async () => {
  const { data } = await apiClient.GET("/api/v1/auth/user/");
  return data; // data は UserInfo 型として推論される
};
```

#### Todoサービス
```typescript
// frontend/src/features/todo/services/todo-service.ts
import { apiClient } from '@/lib/api-client';
import type { CreateTodoInput, UpdateTodoInput } from '../types';

export const todoService = {
  /**
   * Todoリスト取得
   */
  getTodos: async () => {
    return await apiClient.GET('/api/v1/todos/');
  },

  /**
   * Todo作成
   */
  createTodo: async (data: CreateTodoInput) => {
    return await apiClient.POST('/api/v1/todos/', { body: data });
  },

  /**
   * Todo更新
   */
  updateTodo: async (data: UpdateTodoInput) => {
    const { id, ...body } = data;
    return await apiClient.PATCH('/api/v1/todos/{id}/', { 
      params: { path: { id } }, 
      body: body 
    });
  },

  /**
   * Todo削除
   */
  deleteTodo: async (id: number) => {
    await apiClient.DELETE('/api/v1/todos/{id}/', { 
      params: { path: { id } } 
    });
  },

  /**
   * 優先度別統計
   */
  getTodoStats: async () => {
    return await apiClient.GET('/api/v1/todos/stats/');
  },

  /**
   * 進捗分布統計
   */
  getProgressStats: async () => {
    return await apiClient.GET('/api/v1/todos/progress-stats/');
  },
};
```

---

### 5. 型定義の取得

#### 直接pathsから型を取得（推奨）
```typescript
// frontend/src/features/todo/types/index.ts
import type { paths } from '@/types/api';

// レスポンス型の取得
type TodosPath = paths['/api/v1/todos/'];
export type TodoListResponse = TodosPath['get']['responses']['200']['content']['application/json'];
export type Todo = TodoListResponse[number];

// リクエスト型の取得
export type CreateTodoInput = TodosPath['post']['requestBody']['content']['application/json'];
export type UpdateTodoInput = paths['/api/v1/todos/{id}/']['patch']['requestBody']['content']['application/json'] & { id: number };

// その他
export type Priority = Todo['priority'];
```

#### ApiReq/ApiResを使用（後方互換）
```typescript
// frontend/src/features/todo/types/index.ts
import type { ApiRes, ApiReq } from '@/types/api-utils';

export type Todo = NonNullable<ApiRes<'/api/v1/todos/', 'get'> extends Array<infer T> ? T : never>;
export type CreateTodoInput = ApiReq<'/api/v1/todos/', 'post'>;
export type UpdateTodoInput = { id: number } & ApiReq<'/api/v1/todos/{id}/', 'patch'>;
```

---

### 6. フック層での使用
```typescript
// frontend/src/features/auth/hooks/use-auth.ts
import { loginService } from '../services/auth-service';
import { useApiMutation } from '@/hooks/use-tanstack-query';

export const useAuth = () => {
  // ✅ サービスの戻り値から型を自動推論
  type LoginRes = Awaited<ReturnType<typeof loginService>>;
  type LoginReq = Parameters<typeof loginService>[0];

  const signInMutation = useApiMutation<LoginRes, Error, LoginReq>({
    mutationFn: (data) => loginService(data),
    onSuccess: async (data) => {
      // data の型は自動推論される
      if (data?.user) {
        useAuthStore.getState().setUser(data.user);
        queryClient.setQueryData(['auth', 'me'], data.user);
      }
      navigate('/dashboard');
    },
  });

  return { signIn: signInMutation.mutateAsync };
};
```

---

## CI/CD統合

### ワークフロー構成
```
Backend Test Workflow:
  1. lint
  2. test
     ├─ Run tests
     ├─ Generate OpenAPI Schema
     └─ Upload Schema Artifact
  3. security

Frontend Test Workflow:
  1. backend-test (スキーマ生成)
  2. prepare-types
     ├─ Download Schema
     ├─ Generate TypeScript Types
     └─ Check API Types Sync
  3. lint, typecheck, test, build
```

### バックエンドワークフロー
```yaml
# .github/workflows/reusable-backend-test.yml

jobs:
  test:
    steps:
      # ... テスト実行 ...
      
      - name: Generate OpenAPI Schema
        run: |
          cd backend
          python manage.py spectacular --color --file schema.yml
          
          if [ ! -f schema.yml ]; then
            echo "❌ Schema generation failed"
            exit 1
          fi
          
          echo "✅ OpenAPI schema generated successfully"
      
      - name: Upload OpenAPI Schema
        uses: actions/upload-artifact@v4
        with:
          name: openapi-schema-${{ github.sha }}
          path: backend/schema.yml
          retention-days: 1
          if-no-files-found: error
```

### フロントエンドワークフロー
```yaml
# .github/workflows/reusable-frontend-test.yml

jobs:
  prepare-types:
    steps:
      - name: Download OpenAPI Schema
        uses: actions/download-artifact@v4
        with:
          name: openapi-schema-${{ github.sha }}
          path: .
      
      - name: Generate TypeScript Types
        run: |
          npx openapi-typescript ../backend/schema.yml -o src/types/api.d.ts
        working-directory: frontend
      
      - name: Check API Types Sync
        run: |
          if git diff --exit-code frontend/src/types/api.d.ts; then
            echo "✅ API types are up to date"
          else
            echo "⚠️ API types changed"
            if [ "${{ inputs.environment }}" == "production" ]; then
              exit 1
            fi
          fi
```

---

## ベストプラクティス

### 1. スキーマ定義の分離

✅ **推奨**:
```python
# rest_schemas.py に分離
class TodoSchemas:
    list = extend_schema(...)
    create = extend_schema(...)
```

❌ **非推奨**:
```python
# views.py に直接記述
@extend_schema(summary="...", description="...")
def list(self, request):
    pass
```

### 2. 共通エラーレスポンスの再利用

✅ **推奨**:
```python
from apps.common.schemas import CommonSchemas

responses={
    200: TodoSerializer,
    **CommonSchemas.COMMON_RESPONSES
}
```

❌ **非推奨**:
```python
# 毎回同じエラーレスポンスを定義
responses={
    200: TodoSerializer,
    401: {...},
    403: {...},
    404: {...},
}
```

### 3. デコレーターの順序

✅ **推奨**:
```python
@TodoSchemas.search
@action(detail=False, methods=["get"])
def search(self, request):
    pass
```

❌ **非推奨**:
```python
@action(detail=False, methods=["get"])
@TodoSchemas.search  # actionデコレーターは最後
def search(self, request):
    pass
```

### 4. 型定義の適用

✅ **推奨**:
```typescript
// サービス層で型を適用
type Todo = components['schemas']['Todo'];

export const todoService = {
  async list(): Promise<Todo[]> {
    return apiClient.get('todos/').json<Todo[]>();
  }
};
```

❌ **非推奨**:
```typescript
// 手動で型を定義
interface Todo {
  id: number;
  title: string;
  // ...
}
```

### 5. openapi-fetchでの型定義

✅ **推奨（シンプル）**:
```typescript
// サービスの戻り値から型を推論
type LoginRes = Awaited<ReturnType<typeof loginService>>;
type LoginReq = Parameters<typeof loginService>[0];
```

✅ **推奨（明示的）**:
```typescript
// pathsから直接型を取得
import type { paths } from '@/types/api';

type TodosPath = paths['/api/v1/todos/'];
type Todo = TodosPath['get']['responses']['200']['content']['application/json'][number];
```

❌ **非推奨**:
```typescript
// 手動で型を定義
interface Todo {
  id: number;
  title: string;
  // ...
}
```

---

### 6. リトライはTanStack Queryで制御

✅ **推奨**:
```typescript
// HTTPクライアント層ではリトライしない
const { data } = await apiClient.GET('/api/v1/todos/');

// TanStack Queryでリトライを制御
const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: todoService.getTodos,
  retry: 3,
  retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
});
```

❌ **非推奨**:
```typescript
// HTTPクライアント層でリトライを実装
const client = createClient({
  // ...
  retry: 3, // openapi-fetchにはこの機能はない
});
```

---

## トラブルシューティング

### 問題1: スキーマが生成されない

**症状**:
```bash
$ python manage.py spectacular --file schema.yml
CommandError: Unknown command: 'spectacular'
```

**解決方法**:
```bash
# drf-spectacularがインストールされているか確認
pip list | grep drf-spectacular

# インストールされていなければインストール
pip install drf-spectacular

# INSTALLED_APPSに追加されているか確認
# config/settings/base.py
INSTALLED_APPS = [
    # ...
    'drf_spectacular',
]
```

---

### 問題2: 型定義が更新されない

**症状**:
```bash
$ npm run generate:api
# 型定義ファイルが更新されない
```

**解決方法**:
```bash
# バックエンドでスキーマを再生成
cd backend
python manage.py spectacular --color --file schema.yml

# フロントエンドで型定義を再生成
cd ../frontend
npm run generate:api:local

# 型定義ファイルを確認
git diff src/types/api.d.ts
```

---

### 問題3: CI/CDで型定義エラー

**症状**:
```
❌ API types must be committed before production deployment
```

**解決方法**:
```bash
# ローカルで型定義を更新
npm run generate:api

# 変更をコミット
git add src/types/api.d.ts
git commit -m "chore: update API types from OpenAPI schema"
git push
```

---

### 問題4: Swagger UIでCookie認証が動作しない

**症状**:
Swagger UIからAPIを呼び出すと401エラーになる

**解決方法**:

Swagger UIはCookie認証のテストに制限があります。以下の方法を使用してください：
```bash
# curlでテスト
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  -c cookies.txt

# Cookieを使ってAPIを呼び出し
curl http://localhost:8000/api/v1/todos/ \
  -b cookies.txt
```

または、Postman/Insomniaを使用（Cookieサポートあり）

---

### 問題5: 型定義のパスエラー

**症状**:
```
Cannot find module '@/types/api' or its corresponding type declarations.
```

**解決方法**:
```bash
# 型定義ファイルが存在するか確認
ls -la frontend/src/types/api.d.ts

# 存在しない場合は生成
npm run generate:api

# tsconfig.jsonのパスエイリアスを確認
# frontend/tsconfig.json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### 問題6: dj-rest-auth関連のスキーマ生成警告

**症状**:
```bash
$ python manage.py spectacular --color --file schema.yml

Warning [CustomLogoutView > Serializer]: Component name "" contains illegal characters.
Only "A-Z a-z 0-9 - . _" are allowed.

Schema generation summary:
Warnings: 1 (1 unique)
Errors:   0 (0 unique)
```

**原因**:

`dj-rest-auth`の`LogoutView`が内部で`serializers.Serializer`（DRFの基底クラス）をデフォルトとして使用しているため、`drf-spectacular`がOpenAPIスキーマのコンポーネント名を生成できない状態になっています。

**技術的な背景**:
- `dj-rest-auth`：「ログアウトにリクエストボディは不要」→DRFの基底クラス（`serializers.Serializer`）を使用
- `drf-spectacular`：「全てのシリアライザーに一意の名前が必要」→基底クラスには名前を付けられない

この2つのライブラリの設計思想の違いにより、警告が発生します。

**対処方法**:

**この警告は許容してください。** 以下の理由により、修正を試みるとより深刻な問題を引き起こします：

1. **実害なし**: `Errors: 0`であり、フロントエンドの型生成（`api.d.ts`）には影響しません
2. **修正リスク**: カスタムシリアライザーを割り当てると、`dj-rest-auth`の内部ロジックと競合し、スキーマ生成が途中で停止するか、実行時に認証エラーを引き起こします

---

## まとめ

### 導入のメリット

| メリット | 詳細 |
|---------|------|
| **型安全性** | API仕様変更時に型エラーで検出 |
| **開発効率** | 手動の型定義メンテナンス不要 |
| **ドキュメント** | 常に最新のAPI仕様を提供 |
| **CI/CD統合** | 型の不整合をデプロイ前に検出 |

### 運用フロー
```
1. APIを実装
   ↓
2. rest_schemas.py でスキーマを定義
   ↓
3. views.py にデコレーターを追加
   ↓
4. ローカルで型定義を生成・確認
   ↓
5. コミット・プッシュ
   ↓
6. CI/CDで自動チェック
   ↓
7. デプロイ
```

---
