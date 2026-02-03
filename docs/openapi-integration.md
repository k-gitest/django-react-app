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
apiClient (ky): HTTP通信を薄くラップ
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

#### Todoアプリケーション
```python
# backend/apps/todos/rest_schemas.py

from drf_spectacular.utils import extend_schema, OpenApiParameter
from apps.common.schemas import CommonSchemas
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
    
    retrieve = extend_schema(
        summary="Todo詳細取得",
        description="指定されたIDのTodoアイテムの詳細を取得します。",
        responses={
            200: TodoSerializer,
            404: CommonSchemas.ERROR_404,
            **CommonSchemas.COMMON_RESPONSES
        },
        tags=['Todos']
    )
    
    update = extend_schema(
        summary="Todo更新（全体）",
        description="""
        指定されたIDのTodoアイテムを更新します。
        
        更新後、非同期でベクトルインデックスが更新されます（QStash経由）。
        """,
        request=TodoSerializer,
        responses={
            200: TodoSerializer,
            400: CommonSchemas.ERROR_400,
            404: CommonSchemas.ERROR_404,
            **CommonSchemas.COMMON_RESPONSES
        },
        tags=['Todos']
    )
    
    partial_update = extend_schema(
        summary="Todo更新（部分）",
        description="""
        指定されたIDのTodoアイテムの一部を更新します。
        
        更新後、非同期でベクトルインデックスが更新されます（QStash経由）。
        """,
        request=TodoSerializer,
        responses={
            200: TodoSerializer,
            400: CommonSchemas.ERROR_400,
            404: CommonSchemas.ERROR_404,
            **CommonSchemas.COMMON_RESPONSES
        },
        tags=['Todos']
    )
    
    destroy = extend_schema(
        summary="Todo削除",
        description="""
        指定されたIDのTodoアイテムを削除します。
        
        削除後、非同期でベクトルインデックスからも削除されます（QStash経由）。
        """,
        responses={
            204: None,
            404: CommonSchemas.ERROR_404,
            **CommonSchemas.COMMON_RESPONSES
        },
        tags=['Todos']
    )
    
    stats = extend_schema(
        summary="優先度別統計",
        description="優先度ごとのTodo件数を取得します。Redisキャッシュを使用（15分間）。",
        responses={
            200: {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'priority': {'type': 'string', 'enum': ['HIGH', 'MEDIUM', 'LOW']},
                        'count': {'type': 'integer'},
                    }
                }
            },
            **CommonSchemas.COMMON_RESPONSES
        },
        tags=['Todos', 'Statistics']
    )
    
    search = extend_schema(
        summary="セマンティック検索",
        description="""
        自然言語でTodoを検索します。
        
        Google Gemini APIによるベクトル検索を使用し、
        「明日の会議関連」などの曖昧な検索が可能です。
        """,
        parameters=[
            OpenApiParameter(
                name='q',
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description='検索クエリ（例: "明日の会議関連"）'
            ),
            OpenApiParameter(
                name='top_k',
                type=int,
                location=OpenApiParameter.QUERY,
                required=False,
                description='取得件数（デフォルト: 5、最大: 20）'
            ),
            OpenApiParameter(
                name='min_score',
                type=float,
                location=OpenApiParameter.QUERY,
                required=False,
                description='最小類似度スコア（デフォルト: 0.5、範囲: 0.0-1.0）'
            ),
        ],
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string'},
                    'results': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'score': {'type': 'number', 'format': 'float'},
                                'title': {'type': 'string'},
                                'priority': {'type': 'string', 'enum': ['HIGH', 'MEDIUM', 'LOW']},
                                'progress': {'type': 'integer'},
                            }
                        }
                    },
                    'count': {'type': 'integer'},
                }
            },
            400: CommonSchemas.ERROR_400,
            **CommonSchemas.COMMON_RESPONSES
        },
        tags=['Todos', 'Search']
    )
```

#### 認証アプリケーション
```python
# backend/apps/users/rest_schemas.py

from drf_spectacular.utils import extend_schema, OpenApiExample
from apps.common.schemas import CommonSchemas
from dj_rest_auth.serializers import LoginSerializer
from .serializers import CustomRegisterSerializer

class AuthSchemas:
    """認証関連のOpenAPIスキーマ定義"""
    
    login = extend_schema(
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
            200: {
                'type': 'object',
                'properties': {
                    'user': {
                        'type': 'object',
                        'properties': {
                            'pk': {'type': 'integer'},
                            'email': {'type': 'string', 'format': 'email'},
                            'first_name': {'type': 'string'},
                            'last_name': {'type': 'string'},
                        }
                    },
                    'access': {'type': 'string'},
                    'refresh': {'type': 'string'},
                }
            },
            400: OpenApiExample(
                'Bad Request',
                value={
                    'non_field_errors': ['メールアドレスまたはパスワードが正しくありません。']
                },
                response_only=True,
            ),
            429: CommonSchemas.ERROR_429,
        },
        tags=['Authentication']
    )
    
    register = extend_schema(
        summary="新規登録",
        description="""
        新規ユーザーを登録します。
        
        **機能:**
        - HttpOnly CookieにJWTトークンを自動設定
        - ウェルカムメールを非同期送信（QStash経由）
        - 登録イベントを記録（MotherDuck Analytics）
        
        **レート制限:** 3回/1時間
        """,
        request=CustomRegisterSerializer,
        responses={
            201: {
                'type': 'object',
                'properties': {
                    'user': {
                        'type': 'object',
                        'properties': {
                            'pk': {'type': 'integer'},
                            'email': {'type': 'string', 'format': 'email'},
                            'first_name': {'type': 'string'},
                            'last_name': {'type': 'string'},
                        }
                    },
                    'access': {'type': 'string'},
                    'refresh': {'type': 'string'},
                }
            },
            400: OpenApiExample(
                'User Already Exists',
                value={
                    'error': 'user_already_exists',
                    'detail': 'メールアドレス user@example.com は既に登録されています',
                    'data': {'field': 'email'}
                },
                response_only=True,
            ),
            429: CommonSchemas.ERROR_429,
        },
        tags=['Authentication']
    )
    
    logout = extend_schema(
        summary="ログアウト",
        description="""
        ログアウトし、JWTトークンをブラックリスト化します。
        """,
        request=None,
        responses={
            200: OpenApiExample(
                'Success',
                value={'detail': 'ログアウトしました。'},
                response_only=True,
            ),
            **CommonSchemas.COMMON_RESPONSES
        },
        tags=['Authentication']
    )
```

---

### 4. Viewへのデコレーター適用
```python
# backend/apps/todos/views.py

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import TodoSerializer
from .service import TodoCommandService, TodoQueryService
from .rest_schemas import TodoSchemas

class TodoViewSet(viewsets.ModelViewSet):
    serializer_class = TodoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TodoQueryService.get_user_todos(self.request.user)
    
    @TodoSchemas.list
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @TodoSchemas.create
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @TodoSchemas.retrieve
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @TodoSchemas.update
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @TodoSchemas.partial_update
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @TodoSchemas.destroy
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @TodoSchemas.stats
    @action(detail=False, methods=["get"])
    def stats(self, request):
        # 実装...
        pass
    
    @TodoSchemas.search
    @action(detail=False, methods=["get"])
    def search(self, request):
        # 実装...
        pass
```
```python
# backend/apps/users/views.py

from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import LoginView, LogoutView

from .rest_schemas import AuthSchemas

class CustomLoginView(LoginView):
    @AuthSchemas.login
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class CustomRegisterView(RegisterView):
    @AuthSchemas.register
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

class CustomLogoutView(LogoutView):
    @AuthSchemas.logout
    def logout(self, request):
        return super().logout(request)
```

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

### 2. 型定義の生成
```bash
# バックエンドが起動している場合
npm run generate:api

# ローカルファイルから生成する場合
npm run generate:api:local
```

生成される型定義：
```typescript
// frontend/src/types/api.d.ts（自動生成）

export interface paths {
  '/api/v1/todos/': {
    get: {
      responses: {
        200: {
          content: {
            'application/json': components['schemas']['Todo'][];
          };
        };
      };
    };
    post: {
      requestBody: {
        content: {
          'application/json': components['schemas']['TodoRequest'];
        };
      };
      responses: {
        201: {
          content: {
            'application/json': components['schemas']['Todo'];
          };
        };
      };
    };
  };
}

export interface components {
  schemas: {
    Todo: {
      id: number;
      todo_title: string;
      priority: 'HIGH' | 'MEDIUM' | 'LOW';
      progress: number;
      created_at: string;
      updated_at: string;
    };
    TodoRequest: {
      todo_title: string;
      priority?: 'HIGH' | 'MEDIUM' | 'LOW';
      progress?: number;
    };
  };
}
```

---

### 3. サービス層での型適用
```typescript
// frontend/src/features/todo/services/todo-service.ts

import type { components } from '@/types/api';
import { apiClient } from '@/lib/api-client';

// OpenAPIから自動生成された型を使用
type Todo = components['schemas']['Todo'];
type TodoCreate = components['schemas']['TodoRequest'];

export const todoService = {
  /**
   * Todoリスト取得
   */
  async list(): Promise<Todo[]> {
    return apiClient.get('todos/').json<Todo[]>();
  },
  
  /**
   * Todo作成
   */
  async create(data: TodoCreate): Promise<Todo> {
    return apiClient.post('todos/', { json: data }).json<Todo>();
  },
  
  /**
   * Todo更新
   */
  async update(id: number, data: Partial<TodoCreate>): Promise<Todo> {
    return apiClient.patch(`todos/${id}/`, { json: data }).json<Todo>();
  },
  
  /**
   * Todo削除
   */
  async delete(id: number): Promise<void> {
    await apiClient.delete(`todos/${id}/`);
  },
  
  /**
   * セマンティック検索
   */
  async search(params: {
    q: string;
    top_k?: number;
    min_score?: number;
  }): Promise<{
    query: string;
    results: Array<Todo & { score: number }>;
    count: number;
  }> {
    return apiClient
      .get('todos/search/', { searchParams: params })
      .json();
  },
  
  /**
   * 優先度別統計
   */
  async getStats(): Promise<Array<{
    priority: 'HIGH' | 'MEDIUM' | 'LOW';
    count: number;
  }>> {
    return apiClient.get('todos/stats/').json();
  },
};
```
```typescript
// frontend/src/features/auth/services/auth-service.ts

import type { components } from '@/types/api';
import { apiClient } from '@/lib/api-client';

type LoginRequest = components['schemas']['Login'];
type RegisterRequest = components['schemas']['Register'];
type UserInfo = components['schemas']['UserDetails'];

export const authService = {
  /**
   * ログイン
   */
  async login(credentials: LoginRequest): Promise<UserInfo> {
    const response = await apiClient
      .post('auth/login/', { json: credentials })
      .json<{ user: UserInfo }>();
    
    return response.user;
  },
  
  /**
   * 新規登録
   */
  async register(data: RegisterRequest): Promise<UserInfo> {
    const response = await apiClient
      .post('auth/registration/', { json: data })
      .json<{ user: UserInfo }>();
    
    return response.user;
  },
  
  /**
   * ログアウト
   */
  async logout(): Promise<void> {
    await apiClient.post('auth/logout/');
  },
  
  /**
   * ユーザー情報取得
   */
  async getMe(): Promise<UserInfo> {
    return apiClient.get('auth/user/').json<UserInfo>();
  },
};
```

---

### 4. コンポーネントでの使用
```typescript
// frontend/src/features/todo/components/TodoList.tsx

import { useQuery } from '@tanstack/react-query';
import type { components } from '@/types/api';
import { todoService } from '../services/todo-service';

type Todo = components['schemas']['Todo'];

export const TodoList = () => {
  const { data: todos, isLoading } = useQuery({
    queryKey: ['todos'],
    queryFn: todoService.list,
  });
  
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  return (
    <div>
      {todos?.map((todo: Todo) => (
        <div key={todo.id}>
          <h3>{todo.todo_title}</h3>
          <span>{todo.priority}</span>
          <progress value={todo.progress} max={100} />
        </div>
      ))}
    </div>
  );
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
