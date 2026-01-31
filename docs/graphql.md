# GraphQL API 詳細ガイド

## 目次

1. [概要](#概要)
2. [設計思想](#設計思想)
3. [アーキテクチャ](#アーキテクチャ)
4. [バックエンド実装](#バックエンド実装)
5. [フロントエンド実装](#フロントエンド実装)
6. [エラーハンドリング](#エラーハンドリング)
7. [認証・認可](#認証・認可)
8. [パフォーマンス最適化](#パフォーマンス最適化)
9. [開発ワークフロー](#開発ワークフロー)
10. [トラブルシューティング](#トラブルシューティング)

---

## 概要

本プロジェクトでは、REST APIと並行して**GraphQL API**を提供しています。

### GraphQL導入の目標
```
【設計目標】
✅ UI層・フック層はREST/GraphQLを意識しない
✅ Service層のみが通信方式を知っている
✅ 型・エラーは完全に統一
✅ 切り替えは環境変数で一元管理
✅ ビジネスロジックは一切重複させない
```

---

## 設計思想

### 1. 完全な抽象化

**原則**: フロントエンドのUI層・フック層は、APIがRESTかGraphQLかを一切意識しない
```typescript
// ❌ 悪い設計：GraphQLを意識している
import { useTodosGraphQL } from '@/features/todo/hooks/useTodosGraphQL';

// ✅ 良い設計：通信方式を意識しない
import { useTodos } from '@/features/todo/hooks/useTodos';
```

**実装方法**:
- Service層で`API_MODE`環境変数を判定
- REST実装とGraphQL実装を自動切り替え
- 型・エラーを完全に統一

---

### 2. Service層の再利用

**原則**: ビジネスロジックは一切重複させない
```python
# ❌ 悪い設計：ロジックが重複
class TodoViewSet(viewsets.ModelViewSet):  # REST
    def create(self, request):
        # ビジネスロジック（重複）
        pass

class TodoMutation:  # GraphQL
    def create_todo(self, input):
        # 同じビジネスロジック（重複）
        pass

# ✅ 良い設計：Service層を再利用
class TodoViewSet(viewsets.ModelViewSet):  # REST
    def create(self, request):
        return TodoCommandService.create_todo(user, data)

class TodoMutation:  # GraphQL
    def create_todo(self, input):
        return TodoCommandService.create_todo(user, data)
```

**メリット**:
- ビジネスロジックが一元管理される
- バグ修正・機能追加が一箇所で完結
- テストコードも一箇所で済む

---

### 3. 統一エラーハンドリング

**原則**: REST/GraphQLで同じエラークラスを使用
```typescript
// ✅ 統一されたエラーハンドリング
try {
  await createTodo(data);
} catch (error) {
  // REST/GraphQL両方で同じ
  if (error instanceof ApiError) {
    if (error.isValidationError()) { }
    if (error.isAuthError) { }
  }
}
```

**実装方法**:
- GraphQLエラー → `ApiError`に変換
- HTTPステータスコードにマッピング
- `errorHandler()`で統一的に処理

---

## アーキテクチャ

### 全体像
```
┌─────────────────────────────────────────────────────────────┐
│                   GraphQL Architecture                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  【フロントエンド】                                          │
│    ├─ UI Components                                        │
│    │   └─ REST/GraphQLを意識しない                          │
│    │                                                        │
│    ├─ Custom Hooks                                         │
│    │   ├─ useTodos.ts                                      │
│    │   └─ useAuth.ts                                       │
│    │       └─ 通信方式を意識しない                          │
│    │                                                        │
│    ├─ Service Layer（統一API）                              │
│    │   ├─ todo-service.ts                                  │
│    │   │   └─ API_MODE で自動切り替え                       │
│    │   │       ├─ REST: todo-service-rest.ts               │
│    │   │       └─ GraphQL: todo-service-graphql.ts         │
│    │   │                                                   │
│    │   └─ auth-service.ts                                  │
│    │       └─ API_MODE で自動切り替え                       │
│    │           ├─ REST: auth-service-rest.ts               │
│    │           └─ GraphQL: auth-service-graphql.ts         │
│    │                                                        │
│    ├─ HTTP Clients                                         │
│    │   ├─ ky-client.ts (REST)                              │
│    │   └─ graphql-client.ts (GraphQL)                      │
│    │       └─ GraphQLエラー → ApiError に変換               │
│    │                                                        │
│    └─ Unified Error Handling                               │
│        └─ error-handler.ts                                 │
│            └─ ApiError を統一的に処理                       │
│                                                             │
│  【バックエンド】                                            │
│    ├─ REST API (Django REST Framework)                     │
│    │   ├─ views.py                                         │
│    │   ├─ serializers.py                                   │
│    │   └─ Service層を呼び出し                               │
│    │                                                        │
│    └─ GraphQL API (Strawberry)                             │
│        ├─ schema.py                                        │
│        ├─ queries/                                         │
│        ├─ mutations/                                       │
│        ├─ types/                                           │
│        │   └─ Result Pattern（Union型）                     │
│        ├─ errors/                                          │
│        │   ├─ formatters.py                                │
│        │   │   └─ BaseAppError → GraphQL型                 │
│        │   └─ handlers.py                                  │
│        │       └─ @graphql_error_handler                   │
│        └─ Service層を再利用                                 │
│            └─ ビジネスロジック重複なし                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### データフロー

#### Query（データ取得）
```
1. UI Component
   const { todos } = useTodos();
   ↓
2. Custom Hook (useTodos)
   queryFn: todoService.getTodos
   ↓
3. Service Layer (todo-service.ts)
   if (API_MODE === 'graphql') {
     return todoServiceGraphQL.getTodos();
   }
   ↓
4. GraphQL Client (graphql-client.ts)
   gqlRequest(GET_TODOS)
   ↓
5. GraphQL API (/graphql/)
   Query.todos
   ↓
6. Service Layer (TodoQueryService)
   get_user_todos(user)
   ↓
7. Model Layer
   Todo.objects.filter(user=user)
   ↓
8. Response
   GraphQL型 → 統一型(Todo) に変換
   ↓
9. UI Component
   todosを表示
```

#### Mutation（データ変更）
```
1. UI Component
   const { createTodo } = useTodos();
   await createTodo(data);
   ↓
2. Custom Hook (useTodos)
   mutationFn: todoService.createTodo
   ↓
3. Service Layer (todo-service.ts)
   if (API_MODE === 'graphql') {
     return todoServiceGraphQL.createTodo(data);
   }
   ↓
4. GraphQL Client (graphql-client.ts)
   gqlMutation(CREATE_TODO, { input })
   ↓
5. GraphQL API (/graphql/)
   Mutation.createTodo
   ↓
6. Validator (TodoValidator)
   validate_create(input)
   ↓
7. Service Layer (TodoCommandService)
   create_todo(user, data)
   ↓
8. Model Layer
   Todo.objects.create(...)
   ↓
9. Result Pattern Check
   if (__typename === 'TodoType') {
     return todo;
   } else {
     throw ApiError(エラー情報);
   }
   ↓
10. Error Handling
   errorHandler() → Toast表示
   ↓
11. UI Component
   成功/失敗に応じて表示更新
```

---

## バックエンド実装

### 1. 型定義（types/）

#### 基本型（types/todo.py）
```python
import strawberry
from datetime import datetime
from typing import Optional
from strawberry import relay

@strawberry.enum
class PriorityEnum:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

@strawberry.django.type(Todo)
class TodoType(relay.Node):
    """Todo型（Relay GlobalID使用）"""
    id: relay.GlobalID
    todo_title: str
    priority: PriorityEnum
    progress: int
    created_at: datetime
    updated_at: datetime
```

**Relay GlobalIDの理由**:
- グローバルに一意なID
- キャッシュの無効化が容易
- GraphQL標準のベストプラクティス

#### Input型（types/todo.py）
```python
@strawberry.input
class TodoCreateInput:
    """Todo作成用Input型"""
    todo_title: str
    priority: PriorityEnum = PriorityEnum.MEDIUM
    progress: int = 0

@strawberry.input
class TodoUpdateInput:
    """Todo更新用Input型（全フィールドOptional）"""
    todo_title: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    progress: Optional[int] = None
```

#### Result Union型（types/todo.py）
```python
TodoResult = strawberry.union(
    "TodoResult",
    types=(
        TodoType,            # 成功
        ValidationError,     # バリデーションエラー
        NotFoundError,       # リソースが見つからない
        InternalError,       # サーバーエラー
    )
)
```

**Result Patternの利点**:
- 型安全なエラーハンドリング
- 例外をthrowしない設計
- フロントエンドでの明示的なエラー処理

---

### 2. Query定義（queries/todo.py）
```python
@strawberry.type
class TodoQuery:
    @strawberry.field(permission_classes=[IsAuthenticated])
    @graphql_error_handler
    def todos(self, info: strawberry.Info) -> List[TodoType]:
        """
        ユーザーのTodo一覧を取得
        
        認可: IsAuthenticated
        エラーハンドリング: @graphql_error_handler
        Service層: TodoQueryService.get_user_todos
        """
        user = info.context.request.user
        return TodoQueryService.get_user_todos(user)
```

**設計のポイント**:
- `@graphql_error_handler`: 例外を自動的にGraphQLエラー型に変換
- `permission_classes`: Djangoの権限チェック
- Service層を呼び出すだけ（ビジネスロジックは書かない）

---

### 3. Mutation定義（mutations/todo.py）
```python
@strawberry.type
class TodoMutation:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    @graphql_error_handler
    def create_todo(
        self,
        info: strawberry.Info,
        input: TodoCreateInput
    ) -> TodoResult:
        """
        Todo作成
        
        1. バリデーション（TodoValidator）
        2. Service層呼び出し
        3. 成功時はTodoType、失敗時はエラー型を返却
        """
        user = info.context.request.user
        
        # 1. バリデーション
        validation_errors = TodoValidator.validate_create(input)
        if validation_errors:
            return validation_errors[0]  # ValidationError型
        
        # 2. Service層呼び出し
        data = {
            "todo_title": input.todo_title,
            "priority": input.priority.value,
            "progress": input.progress,
        }
        todo = TodoCommandService.create_todo(user, data)
        
        # 3. 成功時はTodoType
        return todo
```

**エラーハンドリングの流れ**:
```
1. バリデーションエラー → ValidationError型を返却
2. Service層で例外発生 → @graphql_error_handler がキャッチ
3. ErrorFormatter で適切なGraphQLエラー型に変換
4. Union型として返却
```

---

### 4. エラーハンドリング（errors/）

#### ErrorFormatter（errors/formatters.py）
```python
class ErrorFormatter:
    """BaseAppError → GraphQLエラー型への変換"""
    
    @staticmethod
    def format_exception(exc: Exception, context: Optional[dict] = None):
        # UserAlreadyExistsError → ConflictError
        if isinstance(exc, UserAlreadyExistsError):
            return ConflictError(
                message=exc.message,
                conflicting_field="email"
            )
        
        # Ratelimited → RateLimitError
        if isinstance(exc, Ratelimited):
            return RateLimitError(
                message="リクエストが多すぎます。",
                retry_after=300
            )
        
        # QStashError → ExternalServiceError
        if isinstance(exc, QStashError):
            return ExternalServiceError(
                message="一時的なエラーが発生しました",
                service_name="QStash"
            )
        
        # 予期しないエラー → InternalError
        return InternalError(
            message="サーバー内部でエラーが発生しました"
        )
```

#### @graphql_error_handler（errors/handlers.py）
```python
def graphql_error_handler(func):
    """
    GraphQL Resolver用のエラーハンドラー
    
    責務:
    1. BaseAppErrorをキャッチ
    2. ErrorFormatterで適切なGraphQLエラー型に変換
    3. 500エラーのみErrorMonitorに送信
    4. Union型のエラーとして返却
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BaseAppError as e:
            # 500エラーのみErrorMonitorに送信
            if e.status_code >= 500:
                ErrorMonitor.log_error(exception=e, context={...})
            
            # GraphQLエラー型に変換
            return ErrorFormatter.format_exception(e)
        
        except Exception as e:
            # 予期しないエラーは必ず送信
            ErrorMonitor.log_error(exception=e, context={...})
            return ErrorFormatter.format_exception(e)
    
    return wrapper
```

---

### 5. Validator（validators.py）
```python
class TodoValidator:
    """GraphQL層のバリデーションロジック"""
    
    @staticmethod
    def validate_create(input: TodoCreateInput) -> List[ValidationError]:
        """
        作成時のバリデーション
        
        DRFのSerializerバリデーションに相当
        """
        errors = []
        
        # タイトルの検証
        title = input.todo_title.strip()
        if not title:
            errors.append(ValidationError(
                field="todo_title",
                message="タイトルは空にできません。",
                code="empty_title"
            ))
        
        # 進捗率の検証
        if not (0 <= input.progress <= 100):
            errors.append(ValidationError(
                field="progress",
                message="進捗率は0から100の範囲で指定してください。",
                code="progress_out_of_range"
            ))
        
        return errors
```

---

### 6. Schema統合（schema.py）
```python
@strawberry.type
class Query(TodoQuery, UserQuery):
    """ルートQuery（各アプリのQueryを統合）"""
    pass

@strawberry.type
class Mutation(TodoMutation, UserMutation):
    """ルートMutation（各アプリのMutationを統合）"""
    pass

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        QueryDepthLimiter(max_depth=10),  # ネスト制限
    ],
)
```

---

## フロントエンド実装

### 1. 環境変数で切り替え
```typescript
// lib/constants.ts
export const API_MODE = (import.meta.env.VITE_API_MODE || 'rest') as 'rest' | 'graphql';
export const GRAPHQL_URL = import.meta.env.VITE_GRAPHQL_URL || 'http://localhost:8000/graphql/';
```

---

### 2. GraphQLクライアント（lib/graphql-client.ts）
```typescript
import { GraphQLClient, ClientError } from 'graphql-request';
import { GRAPHQL_URL } from './constants';
import { ApiError } from '@/errors/api-error';
import { NetworkError } from '@/errors/network-error';

export const graphqlClient = new GraphQLClient(GRAPHQL_URL, {
  credentials: 'include',  // JWT Cookie自動送信
  headers: {
    'X-Requested-With': 'XMLHttpRequest',
  },
  timeout: 10000,
});

/**
 * GraphQLリクエストのラッパー
 * エラーを ApiError に変換（REST APIと統一）
 */
export async function gqlRequest<T>(
  document: string,
  variables?: Record<string, unknown>
): Promise<T> {
  try {
    return await graphqlClient.request<T>(document, variables);
  } catch (error) {
    // ✅ GraphQLエラー → ApiError に変換
    throw convertToApiError(error);
  }
}

function convertToApiError(error: unknown): Error {
  if (error instanceof ClientError) {
    const firstError = error.response.errors?.[0];
    
    // Union型エラーの場合
    if (firstError.extensions?.__typename) {
      const statusMap: Record<string, number> = {
        'ValidationError': 400,
        'AuthenticationError': 401,
        'NotFoundError': 404,
        // ...
      };
      
      return new ApiError(
        statusMap[firstError.extensions.__typename] || 500,
        firstError.message,
        firstError.extensions.code as string,
        firstError.extensions.field as string
      );
    }
  }
  
  return new NetworkError('ネットワークエラーが発生しました', error);
}
```

**ポイント**:
- GraphQLエラー → `ApiError`に変換
- HTTPステータスコードにマッピング
- `errorHandler()`で統一的に処理される

---

### 3. GraphQL定義

#### Fragment（graphql/fragments/todo.ts）
```typescript
import { gql } from 'graphql-request';

export const TODO_FRAGMENT = gql`
  fragment TodoFields on TodoType {
    id
    todoTitle
    priority
    progress
    createdAt
    updatedAt
  }
`;
```

#### Query（graphql/queries/todo.ts）
```typescript
export const GET_TODOS = gql`
  ${TODO_FRAGMENT}
  query GetTodos {
    todos {
      ...TodoFields
    }
  }
`;
```

#### Mutation（graphql/mutations/todo.ts）
```typescript
export const CREATE_TODO = gql`
  ${TODO_FRAGMENT}
  mutation CreateTodo($input: TodoCreateInput!) {
    createTodo(input: $input) {
      __typename
      ... on TodoType {
        ...TodoFields
      }
      ... on ValidationError {
        category
        message
        field
        code
      }
    }
  }
`;
```

---

### 4. Service層（統一API）

#### 公開API（services/todo-service.ts）
```typescript
import { API_MODE } from '@/lib/constants';
import { todoServiceRest } from './implementations/todo-service-rest';
import { todoServiceGraphQL } from './implementations/todo-service-graphql';

/**
 * Todoサービス（統一API）
 * 環境変数で自動切り替え
 */
export const todoService = API_MODE === 'graphql' 
  ? todoServiceGraphQL 
  : todoServiceRest;
```

#### GraphQL実装（services/implementations/todo-service-graphql.ts）
```typescript
export const todoServiceGraphQL = {
  getTodos: async (): Promise<Todo[]> => {
    const data = await gqlRequest<GetTodosQuery>(GET_TODOS);
    return data.todos.map(graphqlTodoToRestTodo);
  },

  createTodo: async (input: CreateTodoInput): Promise<Todo> => {
    const graphqlInput: TodoCreateInput = {
      todoTitle: input.todo_title,
      priority: input.priority as any,
      progress: input.progress,
    };
    
    // gqlMutation()がResult Patternを自動チェック
    const todo = await gqlMutation<CreateTodoMutation, 'createTodo'>(
      CREATE_TODO,
      { input: graphqlInput },
      'createTodo'
    );
    
    return graphqlTodoToRestTodo(todo as TodoType);
  },
};

/**
 * GraphQL型 → REST型に変換
 */
function graphqlTodoToRestTodo(graphqlTodo: TodoType): Todo {
  // Relay GlobalID → 整数IDに変換
  const decodedId = atob(graphqlTodo.id);
  const id = parseInt(decodedId.split(':')[1], 10);
  
  return {
    id,
    todo_title: graphqlTodo.todoTitle,
    priority: graphqlTodo.priority as any,
    progress: graphqlTodo.progress,
    user: '',
    created_at: graphqlTodo.createdAt,
    updated_at: graphqlTodo.updatedAt,
  };
}
```

---

### 5. フック（変更不要）
```typescript
// features/todo/hooks/useTodos.ts
import { todoService } from '../services/todo-service';

export const useTodos = () => {
  const todosQuery = useApiSuspenseQuery<Todo[]>({
    queryKey: TODO_QUERY_KEY,
    queryFn: todoService.getTodos,  // ✅ REST/GraphQL自動切り替え
  });

  const createMutation = useApiMutation<Todo, Error | ApiError, ...>({
    mutationFn: ({ data }) => todoService.createTodo(data),
    // ...
  });

  return { todos, createTodo, ... };
};
```

---

### 6. UI Component（変更不要）
```typescript
// pages/TodoPage.tsx
import { useTodos } from '@/features/todo/hooks/useTodos';

export const TodoPage = () => {
  const { todos, createTodo } = useTodos();

  const handleCreate = async (data: CreateTodoInput) => {
    try {
      await createTodo(data);
      toast.success('作成しました');
    } catch (error) {
      // ✅ REST/GraphQL共通のエラーハンドリング
      if (error instanceof ApiError && error.isValidationError()) {
        console.log('Validation failed:', error.field, error.message);
      }
    }
  };

  return <div>{/* ... */}</div>;
};
```

---

## エラーハンドリング

### 統一エラークラス（errors/api-error.ts）
```typescript
export class ApiError extends Error {
  public readonly status: number;
  public readonly code?: string;
  public readonly field?: string;
  public readonly data?: unknown;

  constructor(
    status: number,
    message?: string,
    code?: string,
    field?: string,
    data?: unknown,
    originalError?: unknown,
  ) {
    super(message || `API Error: ${status}`);
    this.status = status;
    this.code = code;
    this.field = field;
    this.data = data;
  }

  // ============================================================================
  // ゲッター（REST/GraphQL共通）
  // ============================================================================

  get isAuthError(): boolean {
    return this.status === 401;
  }

  get isValidationError(): boolean {
    return this.status === 400;
  }

  get isNotFoundError(): boolean {
    return this.status === 404;
  }

  get isConflictError(): boolean {
    return this.status === 409;
  }
}
```

---

### エラーハンドラー（errors/error-handler.ts）
```typescript
export const errorHandler = (error: unknown, context?: string): void => {
  if (import.meta.env.DEV) {
    console.group(`🚨 Error Handler ${context ? `[${context}]` : ''}`);
    console.error(error);
    console.groupEnd();
  }

  // ✅ ApiError のみ（REST/GraphQL共通）
  if (error instanceof ApiError) {
    handleApiError(error);
    return;
  }

  // ...
};

const handleApiError = (error: ApiError): void => {
  if (error.isAuthError) {
    const authStore = useAuthStore.getState();
    if (authStore.user !== null) {
      authStore.logout();
      toast.error('セッションが切れました。再ログインしてください。');
    }
    return;
  }

  if (error.isValidationError() && error.field) {
    const message = `${error.field}: ${error.message}`;
    toast.error(message);
    return;
  }

  // ...
};
```

---

## 認証・認可

### JWT Cookie認証（REST APIと同じ）
```python
# GraphQL View
class CustomGraphQLView(GraphQLView):
    def get_context(self, request, response):
        """
        JWT CookieからユーザーをロードOAuthService 層での例外処理は最小化
- RESTと同じ認証方式
        """
        return Context(request=request, response=response)
```

**ポイント**:
- REST APIと全く同じJWT Cookie認証
- `info.context.request.user`でユーザー取得
- `@strawberry.field(permission_classes=[IsAuthenticated])`で認可

---

### Permission Classes
```python
from strawberry.permission import BasePermission

class IsAuthenticated(BasePermission):
    message = "認証が必要です"

    def has_permission(self, source, info, **kwargs) -> bool:
        request = info.context.request
        return request.user and request.user.is_authenticated
```

---

## パフォーマンス最適化

### 1. DataLoader（N+1問題の解決）
```python
# 将来的な拡張（現状は不要）
from strawberry.dataloader import DataLoader

async def load_users(keys: List[int]) -> List[User]:
    users = await User.objects.filter(id__in=keys)
    user_map = {user.id: user for user in users}
    return [user_map.get(key) for key in keys]

user_loader = DataLoader(load_fn=load_users)
```

---

### 2. Query Complexity（複雑度制限）
```python
from strawberry.extensions import QueryDepthLimiter

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        QueryDepthLimiter(max_depth=10),
    ],
)
```

---

### 3. Persisted Queries（本番環境）
```python
# 将来的な拡張
from strawberry.extensions import PersistedQueries

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[
        PersistedQueries(storage=RedisStorage()),
    ],
)
```

---

## 開発ワークフロー

### 1. GraphQL Playground
```
http://localhost:8000/graphql/
```

**使用例**:
```graphql
# Todo一覧取得
query {
  todos {
    id
    todoTitle
    priority
    progress
  }
}

# Todo作成
mutation {
  createTodo(input: {
    todoTitle: "GraphQLのテスト"
    priority: HIGH
    progress: 0
  }) {
    ... on TodoType {
      id
      todoTitle
    }
    ... on ValidationError {
      message
      field
    }
  }
}
```

---

### 2. GraphQL Code Generator（オプション）

**インストール**:
```bash
npm install -D @graphql-codegen/cli @graphql-codegen/typescript
```

**設定**（codegen.yml）:
```yaml
schema: http://localhost:8000/graphql/
documents: src/graphql/**/*.ts
generates:
  src/graphql/types.ts:
    plugins:
      - typescript
      - typescript-operations
```

**実行**:
```bash
npm run codegen
```

---

### 3. 切り替えテスト
```bash
# REST API使用
VITE_API_MODE=rest npm run dev

# GraphQL API使用
VITE_API_MODE=graphql npm run dev

# 動作確認
# ✅ ログイン・ログアウト
# ✅ Todo作成・更新・削除
# ✅ エラーハンドリング
```

---

## トラブルシューティング

### エラー: CORS設定
```python
# backend/config/settings/base.py
CORS_ALLOW_HEADERS = list(default_headers) + [
    # GraphQL
    "content-type",
    "x-requested-with",
]
```

---

### エラー: Relay GlobalID変換
```typescript
// エラー: Invalid Relay GlobalID
// 原因: Base64デコード失敗

// 解決策: ID変換を確認
const decodedId = atob(graphqlTodo.id);  // "TodoType:123"
const id = parseInt(decodedId.split(':')[1], 10);  // 123
```

---

### エラー: Union型の判定
```typescript
// ❌ 悪い例
const result = data.createTodo;
if (result.message) {  // 型安全でない
  // エラー処理
}

// ✅ 良い例
const result = data.createTodo;
if (result.__typename === 'ValidationError') {  // 型安全
  toast.error(result.message);
}
```

---

### エラー: Result Patternのチェック漏れ
```typescript
// ❌ 悪い例（エラーチェックしていない）
const data = await gqlMutation<CreateTodoMutation>(CREATE_TODO, { input });
return data.createTodo;  // エラー時もTodoTypeとして扱われる

// ✅ 良い例（自動チェック）
const todo = await gqlMutation<CreateTodoMutation, 'createTodo'>(
  CREATE_TODO,
  { input },
  'createTodo'  // ← Result Patternを自動チェック
);
return todo;  // TodoType確定
```

---

## ベストプラクティス

### 1. Service層の再利用を徹底
```python
# ❌ 悪い例（ロジックが重複）
class TodoMutation:
    def create_todo(self, input):
        # ビジネスロジックを直接実装
        todo = Todo.objects.create(...)
        return todo

# ✅ 良い例（Service層を再利用）
class TodoMutation:
    def create_todo(self, input):
        return TodoCommandService.create_todo(user, data)
```

---

### 2. エラーハンドリングを統一
```typescript
// ❌ 悪い例（GraphQL専用エラークラス）
if (error instanceof GraphQLError) { }

// ✅ 良い例（REST/GraphQL統一）
if (error instanceof ApiError) { }
```

---

### 3. 型変換を一箇所に集約
```typescript
// ❌ 悪い例（各所で変換）
const todo = {
  id: parseInt(atob(graphqlTodo.id).split(':')[1]),
  // ...
};

// ✅ 良い例（ヘルパー関数）
function graphqlTodoToRestTodo(graphqlTodo: TodoType): Todo {
  // 変換ロジックを一箇所に集約
}
```

---

### 4. Fragment を活用
```graphql
# ❌ 悪い例（重複）
query GetTodos {
  todos {
    id
    todoTitle
    priority
  }
}

query GetTodo($id: ID!) {
  todo(id: $id) {
    id
    todoTitle
    priority
  }
}

# ✅ 良い例（Fragment）
fragment TodoFields on TodoType {
  id
  todoTitle
  priority
}

query GetTodos {
  todos {
    ...TodoFields
  }
}
```
