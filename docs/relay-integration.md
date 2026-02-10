# Relay統合詳細ガイド

## 目次

1. [概要](#概要)
2. [設計思想](#設計思想)
3. [Relay環境のセットアップ](#relay環境のセットアップ)
4. [カスタムフックの実装](#カスタムフックの実装)
5. [エラーハンドリングの統合](#エラーハンドリングの統合)
6. [コンポーネント実装パターン](#コンポーネント実装パターン)
7. [Result Patternの処理](#result-patternの処理)
8. [ベストプラクティス](#ベストプラクティス)
9. [トラブルシューティング](#トラブルシューティング)

---

## 概要

本プロジェクトでは、REST API・GraphQL APIと並行して**Relay**を使用したGraphQL統合を提供しています。

### Relayとは
Relayは、Facebookが開発したGraphQLクライアントフレームワークで、以下の特徴を持ちます：

- **宣言的データフェッチ**: コンポーネントが必要なデータを宣言
- **自動キャッシュ管理**: Relay Storeが最適化されたキャッシュを提供
- **型安全性**: Relay Compilerが完全な型定義を自動生成
- **楽観的更新**: UIの即座な更新とロールバック
- **ページネーション**: Connection仕様による標準化

### Relayを選択する理由

| 項目 | GraphQL（graphql-request） | **Relay** |
|------|---------------------------|-----------|
| **キャッシュ管理** | 手動実装が必要 | 自動最適化 ⭐ |
| **型安全性** | 手動型定義 | Compiler自動生成 ⭐ |
| **パフォーマンス** | 手動最適化 | 自動最適化 ⭐ |
| **学習コスト** | 低い | 高い |
| **適用規模** | 小〜中規模 | 中〜大規模 ⭐ |
| **開発速度** | 速い | 初期は遅い、中長期で速い ⭐ |
| **エコシステム** | 豊富 | Facebook製、枯れた技術 ⭐ |

**採用判断**:
- ✅ 大規模アプリケーション
- ✅ 最高のパフォーマンスが必要
- ✅ 型安全性を徹底したい
- ❌ シンプルなCRUDのみ → REST推奨
- ❌ 小・中規模プロジェクト → GraphQL（graphql-request）推奨

---

## 設計思想

### 1. 完全な抽象化

**原則**: フロントエンドのUI層・フック層は、APIがREST/GraphQL/Relayかを一切意識しない

**実装方法**:

- REST/GraphQL/Relay実装を切り替え
- 型・エラーを完全に統一

---

### 2. TanStack QueryとRelayの一貫性
**設計方針**: REST（TanStack Query）とRelay APIを統一

| **種類** | **TanStack Query** | **Relay** |
|------|---------------------------|-----------|
| **Query** | useSuspenseQuery + AsyncBoundary | useLazyLoadQuery + AsyncBoundary |
| **Mutation** | useMutation + onError | useRelayMutation + onError |
| **エラーハンドリング** | errorHandler | errorHandler |
| **API** | { data } + suspenseQuery | { data } + Suspense |

**統一された開発体験**:
```typescript
// REST API（TanStack Query）
const { data: todos } = useQuery({
  queryKey: ['todos'],
  queryFn: todoService.getTodos,
});

// Relay
const todos = useRelayLazyLoadQuery(TodoListQuery, {});

// ✅ どちらも同じように使える
```

---

### 3. エラーハンドリングの責務分離

┌─────────────────────────────────────────────────────────────┐
│     エラーハンドリングの責務分離                              │
├─────────────────────────────────────────────────────────────┤
│ 1. relay-environment.ts                                     │
│    └─ GraphQLエラー → ApiError変換                          │
│                                                             │
│ 2. errorHandler                                             │
│    └─ ApiError → トースト + ログ送信                         │
│                                                             │
│ 3. useRelayMutation                                         │
│    └─ errorHandlerに渡すだけ                                │
│                                                             │
│ 4. useRelayLazyLoadQuery                                    │
│    └─ ErrorBoundaryで処理                                   │
│                                                             │
│ 5. コンポーネント                                            │
│    └─ fieldErrorsをRHFに渡す                                │
└─────────────────────────────────────────────────────────────┘

## Relay環境のセットアップ

### 1. インストール
```bash
npm install react-relay relay-runtime
npm install --save-dev relay-compiler @types/react-relay @types/relay-runtime
```

### 2. relay-environment.ts

**役割**: Relay環境の構築と、すべてのGraphQLエラーをApiErrorに変換

```typescript
// frontend/src/lib/relay-environment.ts
import { Environment, Network, RecordSource, Store } from 'relay-runtime';
import type { 
  FetchFunction, 
  RequestParameters, 
  Variables, 
  GraphQLResponse 
} from 'relay-runtime';
import { GRAPHQL_URL } from '@/lib/constants';
import { ApiError } from '@/errors/api-error';
import { NetworkError } from '@/errors/network-error';

/**
 * GraphQLエラーレスポンスの型定義
 */
interface GraphQLErrorResponse {
  errors: Array<{
    message: string;
    extensions?: {
      __typename?: string;
      code?: string;
      field?: string;
      data?: unknown;
      [key: string]: unknown;
    };
  }>;
  data?: unknown;
}

/**
 * GraphQLエラーレスポンスの型ガード
 */
function hasGraphQLErrors(json: unknown): json is GraphQLErrorResponse {
  if (typeof json !== 'object' || json === null) {
    return false;
  }

  if (!('errors' in json)) {
    return false;
  }

  const errors = json.errors;
  return Array.isArray(errors) && errors.length > 0;
}

/**
 * GraphQLレスポンスの型ガード
 */
function isGraphQLResponse(json: unknown): json is GraphQLResponse {
  if (typeof json !== 'object' || json === null) {
    return false;
  }
  
  return 'data' in json || 'errors' in json;
}

/**
 * Relay用のFetch関数
 * 
 * エラー処理の階層:
 * 1. HTTP層: ステータスコードが 200 か？
 * 2. GraphQLエラー層: errors 配列が含まれているか？
 * 3. Result Pattern層: extensions にエラー詳細（__typename）が含まれているか？
 * 4. 構造妥当性: 最終的に Relay が処理できる形式か？
 */
const fetchRelay: FetchFunction = async (
  params: RequestParameters,
  variables: Variables
): Promise<GraphQLResponse> => {
  try {
    const response = await fetch(GRAPHQL_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      },
      credentials: 'include',  // JWT Cookie自動送信
      body: JSON.stringify({
        query: params.text,
        variables,
      }),
    });

    // HTTPエラー処理
    if (!response.ok) {
      const errorBody = await response.json().catch(() => null);
      throw new ApiError(
        response.status,
        errorBody?.detail || errorBody?.message || response.statusText,
        errorBody,
        new Error(response.statusText)
      );
    }

    const json = await response.json();

    // GraphQLエラー処理
    if (hasGraphQLErrors(json)) {
      const firstError = json.errors[0];
      const extensions = firstError.extensions;

      // Union型エラー（Result Pattern）
      if (extensions?.__typename) {
        const typename = extensions.__typename;
        const statusMap: Record<string, number> = {
          ValidationError: 400,
          AuthenticationError: 401,
          AuthorizationError: 403,
          NotFoundError: 404,
          ConflictError: 409,
          RateLimitError: 429,
          ExternalServiceError: 503,
          InternalError: 500,
        };

        const status = statusMap[typename] || 500;
        const data: Record<string, unknown> = { __typename: typename };

        if (extensions.code) data.code = extensions.code;
        if (extensions.field) data.field = extensions.field;
        if (extensions.data && typeof extensions.data === 'object') {
          Object.assign(data, extensions.data);
        }

        throw new ApiError(status, firstError.message, data, new Error(firstError.message));
      }

      // 標準GraphQLエラー
      throw new ApiError(
        500,
        firstError.message || 'GraphQLエラーが発生しました',
        { code: 'graphql_error' },
        new Error(firstError.message)
      );
    }

    // 正常なGraphQLレスポンスを返却
    if (isGraphQLResponse(json)) {
      return json;
    }

    // 不正なレスポンス
    throw new NetworkError(
      '不正なGraphQLレスポンスを受信しました',
      new Error(`Invalid response: ${Object.keys(json)}`)
    );
  } catch (error) {
    // ApiError/NetworkErrorはそのまま再送出
    if (error instanceof ApiError) throw error;
    if (error instanceof NetworkError) throw error;

    // その他のエラーはNetworkErrorに変換
    if (error instanceof Error) throw new NetworkError(error.message, error);
    throw new NetworkError('予期しないエラーが発生しました', error);
  }
};

/**
 * Relay Environment
 */
export const relayEnvironment = new Environment({
  network: Network.create(fetchRelay),
  store: new Store(new RecordSource()),
});
```

**ポイント**:

- ✅ HTTPエラー → ApiError
- ✅ GraphQLエラー（Result Pattern） → ApiError
- ✅ 標準GraphQLエラー → ApiError
- ✅ ネットワークエラー → NetworkError
- ✅ すべてのエラーが統一形式に変換される


### 3. Relay Compiler設定
**relay.config.js/package.json**:
```javascript
module.exports = {
  src: "./src",
  language: "typescript",
  schema: "./schema.graphql",
  exclude: ["**/node_modules/**", "**/__mocks__/**", "**/__generated__/**"],
  artifactDirectory: "./src/__generated__",
};
```
```json
{
  "scripts": {
    "relay": "relay-compiler",
    "relay:watch": "relay-compiler --watch"
  }
}
```

**schema.graphql取得**:
```bash
# バックエンドから取得
curl http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { types { name } } }"}' \
  --output schema.graphql
```


---

## カスタムフックの実装

### useRelayMutation
**役割**: Mutation実行とエラーハンドリングの自動化

```typescript
// frontend/src/hooks/useRelayMutation.ts
import { useCallback } from 'react';
import { useMutation } from 'react-relay';
import type {
  MutationParameters,
  GraphQLTaggedNode,
  MutationConfig,
  PayloadError,
} from 'relay-runtime';
import { errorHandler } from '@/errors/error-handler';

/**
 * 拡張されたMutation設定
 */
interface ExtendedMutationConfig<TMutation extends MutationParameters>
  extends Omit<MutationConfig<TMutation>, 'mutation'> {
  errorContext?: string;
}

/**
 * Relay用カスタムMutationフック
 * 
 * エラーハンドリングの自動化:
 * - relay-environment.tsで全エラーをApiError/NetworkErrorに変換済み
 * - onErrorでerrorHandlerを呼び出してトースト表示・ログ送信
 * - コンポーネント側でfieldErrorsを使ってRHFのsetErrorに渡す
 * 
 * @example
 * const { execute, isInFlight } = useRelayMutation(CreateTodoMutation);
 * 
 * try {
 *   const response = await execute({
 *     variables: { input: data },
 *     errorContext: 'CreateTodo',
 *   });
 *   toast.success('作成しました');
 * } catch (error) {
 *   if (error instanceof ApiError && error.fieldErrors) {
 *     Object.entries(error.fieldErrors).forEach(([field, messages]) => {
 *       setError(field, { type: 'server', message: messages[0] });
 *     });
 *   }
 * }
 */
export const useRelayMutation = <TMutation extends MutationParameters>(
  mutation: GraphQLTaggedNode
) => {
  const [commit, isInFlight] = useMutation<TMutation>(mutation);

  const execute = useCallback(
    (config: ExtendedMutationConfig<TMutation>): Promise<TMutation['response']> => {
      const { errorContext, ...relayConfig } = config;

      return new Promise((resolve, reject) => {
        commit({
          ...relayConfig,
          onCompleted: (response: TMutation['response'], errors: PayloadError[] | null) => {
            // ✅ fetchRelayでエラー時にthrowしているため、ここに来る時は基本成功
            relayConfig.onCompleted?.(response, errors);
            resolve(response);
          },
          onError: (error: Error) => {
            // ✅ すでに fetchRelay で ApiError/NetworkError に変換済み
            errorHandler(error, errorContext || 'Mutation');
            relayConfig.onError?.(error);
            reject(error);
          },
        } as MutationConfig<TMutation>); // 型アサーションで型エラー回避
      });
    },
    [commit]
  );

  return { execute, isInFlight };
};

```

**設計のポイント**:

| **項目** | **詳細** |
|------|---------------------------|
| **Promiseベース** | async/awaitが使える（TanStack Query互換） |
| **エラー自動処理** | errorHandlerが自動的にトースト表示・ログ送信 |
| **型安全** | MutationConfigを継承、型アサーションで型エラー回避 |
| **シンプル** | showToast等の拡張不要（errorHandler側で処理） |


### useRelayLazyLoadQuery
**役割**: Query実行とデータ取得、成功時コールバック

```typescript
// frontend/src/hooks/useRelayLazyLoadQuery.ts
import { useEffect, useRef } from 'react';
import { useLazyLoadQuery } from 'react-relay';
import type { OperationType, GraphQLTaggedNode, FetchPolicy } from 'relay-runtime';

interface UseRelayQueryOptions<TQuery extends OperationType> {
  fetchPolicy?: FetchPolicy;
  onSuccess?: (data: TQuery['response']) => void;
}

/**
 * Relay用カスタムQueryフック
 * 
 * Suspenseベースのデータフェッチ:
 * - ErrorBoundaryで自動エラーハンドリング
 * - onSuccessコールバックで成功時処理
 * 
 * @example
 * const data = useRelayLazyLoadQuery(TodoListQuery, {}, {
 *   onSuccess: (data) => console.log('取得成功:', data.todos.edges.length),
 * });
 * 
 * return (
 *   <div>
 *     {data.todos.edges.map(({ node }) => (
 *       <TodoItem key={node.id} todo={node} />
 *     ))}
 *   </div>
 * );
 */
export const useRelayLazyLoadQuery = <TQuery extends OperationType>(
  query: GraphQLTaggedNode,
  variables: TQuery['variables'],
  options?: UseRelayQueryOptions<TQuery>
): TQuery['response'] => {
  const data = useLazyLoadQuery<TQuery>(query, variables, {
    fetchPolicy: options?.fetchPolicy || 'store-or-network',
  });

  // callbackが再生成されても副作用が暴走しないようrefで管理
  const onSuccessRef = useRef(options?.onSuccess);
  useEffect(() => {
    onSuccessRef.current = options?.onSuccess;
  }, [options?.onSuccess]);

  // データが取得・更新されたタイミングで実行
  useEffect(() => {
    if (data) {
      onSuccessRef.current?.(data);
    }
  }, [data]);

  return data;
};
```

**エラーハンドリング**:
- ✅ エラーは`AsyncBoundary`（ErrorBoundary + Suspense）がキャッチ
- ✅ `ErrorBoundary.componentDidCatch`で`errorHandler`が呼ばれる
- ✅ コンポーネント内でエラーハンドリング不要

---

## エラーハンドリングの統合

### エラーフロー全体像
```
┌─────────────────────────────────────────────────────────────┐
│              Relayエラーハンドリングフロー                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. relay-environment.ts (fetchRelay)                       │
│     ↓ GraphQLエラー → ApiError に変換してthrow              │
│     ↓ HTTPエラー → ApiError に変換してthrow                 │
│     ↓ ネットワークエラー → NetworkError に変換してthrow      │
│                                                             │
│  2. useRelayMutation.onError / AsyncBoundary.catch          │
│     ↓ errorHandler(error) → トースト表示・ログ送信           │
│     ↓ reject(error) / ErrorBoundary表示                     │
│                                                             │
│  3. コンポーネント.catch                                     │
│     ↓ error.fieldErrors があればsetErrorで個別フィールドに表示 │
│                                                             │
│  完了                                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### ケース別エラーハンドリング

#### ケース1: バリデーションエラー（field: "email"）
```
1. relay-environment.ts
   ↓ ApiError(400, "メールアドレスは既に使用されています", { field: "email" })
   
2. useRelayMutation.onError
   ↓ errorHandler(error) → トースト表示
   ↓ reject(error)
   
3. AuthFormRelayContainer.catch
   ↓ （何もしない）
   
4. AccountForm.catch
   ↓ mapErrorsToForm(error, form.setError)
   ↓ setError("email", { type: "server", message: "..." })
   
5. UI
   ✅ トースト: "メールアドレスは既に使用されています"
   ✅ インライン: email フィールドの下に赤字表示
```

---

#### ケース2: 認証エラー（401）
```
1. relay-environment.ts
   ↓ ApiError(401, "認証に失敗しました")
   
2. useRelayMutation.onError
   ↓ errorHandler(error)
   ↓ → handleApiError → 自動ログアウト + トースト
   ↓ reject(error)
   
3. AuthFormRelayContainer.catch
   ↓ console.error (DEVのみ)
   
4. AccountForm.catch
   ↓ mapErrorsToForm(error, form.setError)
   ↓ （fieldErrors が null なので何もしない）
   
5. UI
   ✅ 自動ログアウト
   ✅ トースト: "セッションが切れました"
```

---

#### ケース3: Queryエラー（AsyncBoundary）
```
1. relay-environment.ts
   ↓ ApiError(500, "サーバーエラー")
   
2. AsyncBoundary.componentDidCatch
   ↓ errorHandler(error) → トースト表示・ログ送信
   
3. UI
   ✅ ErrorBoundaryのFallback UI表示
   ✅ トースト: "サーバーエラーが発生しました"
```

---

### ApiError.fieldErrors の実装

```typescript
// frontend/src/errors/api-error.ts

export class ApiError extends Error {
  public readonly status: number;
  public readonly data?: unknown;
  public readonly originalError?: unknown;

  constructor(
    status: number,
    message?: string,
    data?: unknown,
    originalError?: unknown,
  ) {
    super(message || `API Error: ${status}`);
    this.status = status;
    this.data = data;
    this.originalError = originalError;
    Object.setPrototypeOf(this, ApiError.prototype);
  }

  /**
   * dataプロパティの中から 'field' を安全に取得する
   */
  public get field(): string | undefined {
    if (this.data && typeof this.data === 'object' && 'field' in this.data) {
      return (this.data as { field: string }).field;
    }
    return undefined;
  }

  /**
   * dataプロパティの中から 'fields' を安全に取得する
   */
  public get fields(): Record<string, unknown> | undefined {
    if (this.data && typeof this.data === 'object' && 'fields' in this.data) {
      return (this.data as { fields: Record<string, unknown> }).fields;
    }
    return undefined;
  }

  /**
   * バリデーションエラーの場合、フィールド別エラーを取得
   */
  get fieldErrors(): Record<string, string[]> | null {
    // 400と409以外は、フォームに紐付けないので null で即復帰
    if (this.status !== 400 && this.status !== 409) return null;

    // 1. 明示的なフィールド指定がある場合（GraphQL Result Pattern）
    if (this.field) {
      return {
        [this.field]: [this.message],
      };
    }

    // 2. fieldsオブジェクトがある場合（GraphQL Result Pattern）
    if (this.fields && typeof this.fields === 'object') {
      const normalized: Record<string, string[]> = {};
      for (const [key, value] of Object.entries(this.fields)) {
        normalized[key] = Array.isArray(value) ? value.map(String) : [String(value)];
      }
      return Object.keys(normalized).length > 0 ? normalized : null;
    }

    // 3. dataオブジェクトから一括抽出（REST/DRF用）
    if (this.data && typeof this.data === 'object') {
      const errors: Record<string, string[]> = {};
      for (const [key, value] of Object.entries(this.data)) {
        if (Array.isArray(value)) {
          errors[key] = value.map(String);
        } else if (typeof value === 'string') {
          errors[key] = [value];
        }
      }
      return Object.keys(errors).length > 0 ? errors : null;
    }

    return null;
  }

...中略
}
```

---

### mapErrorsToForm の実装

```typescript
// frontend/src/lib/utils.ts
import type { UseFormSetError } from 'react-hook-form';
import { ApiError } from '@/errors/api-error';

/**
 * エラーをReact Hook Formのフィールドエラーにマッピング
 * 
 * @param error - ApiError
 * @param setError - React Hook Form の setError 関数
 */
export const mapErrorsToForm = <T extends FieldValues>(
  error: unknown,
  setError: UseFormSetError<T>
) => {
  // fetchRelay が投げているのは ApiError クラスのインスタンス
  if (error instanceof ApiError) {
    // 400 (Validation) も 409 (Conflict) も、
    // ApiError の fieldErrors が値を返してくれるならこれだけで OK
    const errors = error.fieldErrors;

    if (errors) {
      Object.entries(errors).forEach(([field, messages]) => {
        setError(field as Path<T>, {
          type: 'server',
          message: messages[0]
        });
      });
    }
  }
};
```

---

### コンポーネント実装パターン

#### Container/View分離パターン

**Container（データフェッチとビジネスロジック）**
```typescript
// frontend/src/features/auth/components/AuthFormRelayContainer.tsx
import { graphql } from 'react-relay';
import { useNavigate } from 'react-router-dom';
import { AccountForm } from './auth-form';
import type { AccountFormType, Account } from '@/features/auth/types/auth';
import { useRelayMutation } from '@/hooks/useRelayMutation';

// 自動生成される型をインポート
import type {
  AuthFormRelayContainerRegisterMutation
} from '@/__generated__/AuthFormRelayContainerRegisterMutation.graphql';

import type {
  AuthFormRelayContainerLoginMutation
} from '@/__generated__/AuthFormRelayContainerLoginMutation.graphql';

const RegisterMutation = graphql`
  mutation AuthFormRelayContainerRegisterMutation($input: RegisterInput!) {
    register(input: $input) {
      __typename
      ... on AuthPayload {
        user {
          id
          email
          firstName
          lastName
          isStaff
          dateJoined
        }
        message
      }
      ... on ValidationError {
        category
        message
        field
        code
      }
      ... on ConflictError {
        category
        message
        conflictingField
        code
      }
      ... on InternalError {
        category
        message
        code
      }
    }
  }
`;

const LoginMutation = graphql`
  mutation AuthFormRelayContainerLoginMutation($input: LoginInput!) {
    login(input: $input) {
      __typename
      ... on AuthPayload {
        user {
          id
          email
          firstName
          lastName
          isStaff
          dateJoined
        }
        message
      }
      ... on ValidationError {
        category
        message
        field
        code
      }
      ... on InternalError {
        category
        message
        code
      }
    }
  }
`;

export const AuthFormRelayContainer = ({ type }: { type: AccountFormType }) => {
  const navigate = useNavigate();

  const { execute: commitRegister, isInFlight: isRegisterPending } = 
    useRelayMutation<AuthFormRelayContainerRegisterMutation>(RegisterMutation);
  const { execute: commitLogin, isInFlight: isLoginPending } = 
    useRelayMutation<AuthFormRelayContainerLoginMutation>(LoginMutation);

  const isLogin = type === 'login';
  const label = isLogin ? 'ログイン' : '登録';
  const isPending = isLogin ? isLoginPending : isRegisterPending;

  const handleSubmit = async (data: Account) => {
    const config = {
      variables: { 
        input: { 
          email: data.email, 
          password: data.password, 
          passwordConfirm: data.password 
        } 
      },
      errorContext: isLogin ? 'ログインに失敗しました' : 'ユーザー登録に失敗しました'
    };

    try {
      const response = isLogin ? await commitLogin(config) : await commitRegister(config);

      // 「login か register のどちらかに入っている result」を型安全に抽出
      const result = ('login' in response ? response.login : response.register);

      if (result?.__typename === 'AuthPayload') {
        navigate('/dashboard');
      }
    } catch (error) {
      // errorHandlerはuseRelayMutation内部で実行されるので、ここでは何もしなくてOK
      if (import.meta.env.DEV) console.error("error: ", error);
    }
  };

  return (
    <AccountForm
      submitLabel={label}
      onSubmit={handleSubmit}
      isLoading={isPending}
    />
  );
};
```

**設計のポイント**:

- ✅ Result Patternの型安全な処理
- ✅ エラーはuseRelayMutationが自動処理
- ✅ 成功時のみ画面遷移

---

#### View（UIとフォーム）
```typescript
// frontend/src/features/auth/components/auth-form.tsx
import { FormInput, FormWrapper } from '@/components/form/form-parts';
import { FormPasswordInput } from '@/components/form/form-password-input';
import { Button } from '@/components/ui/button';
import { validatedAccount } from '@/features/auth/schemas/account-schema';
import type { Account } from '@/features/auth/types/auth';
import { zodResolver } from '@hookform/resolvers/zod';
import { Loader } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { mapErrorsToForm } from '@/lib/utils';

interface AccountFormProps {
  submitLabel: string;
  onSubmit: (data: Account) => Promise<unknown>;
  isLoading: boolean;
}

export const AccountForm = ({ submitLabel, onSubmit, isLoading }: AccountFormProps) => {
  const form = useForm<Account>({
    resolver: zodResolver(validatedAccount),
    defaultValues: { email: '', password: '' },
  });

  const handleSubmit = async (formData: Account) => {
    try {
      await onSubmit(formData);
      form.reset();
    } catch (error) {
      // 1. ValidationError (Zodやすり抜けた400エラー) の場合
      mapErrorsToForm(error, form.setError);
      
      // エラーは useRelayMutation の onError と errorHandler で処理済み
      if (import.meta.env.DEV) {
        console.error('Form submission error:', error);
      }
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="w-full flex flex-col gap-2 items-center">
        <FormWrapper onSubmit={handleSubmit} form={form}>
          <FormInput 
            label="email" 
            name="email" 
            placeholder="emailを入力してください" 
            disabled={isLoading} 
          />
          <FormPasswordInput 
            label="password" 
            name="password" 
            disabled={isLoading} 
            placeholder="パスワードを入力してください" 
          />
          <div className="text-center">
            <Button type="submit" className="w-32" disabled={isLoading}>
              {isLoading && <Loader className="mr-2 h-4 w-4 animate-spin" />}
              {submitLabel}
            </Button>
          </div>
        </FormWrapper>
      </div>
    </div>
  );
};
```

**設計のポイント**:

- ✅ フォームの状態管理（React Hook Form）
- ✅ mapErrorsToFormでフィールドエラーを自動マッピング
- ✅ ローディング状態の表示

---

#### Result Patternの処理

**Result Pattern とは**
GraphQLのUnion型を使用したエラーハンドリングパターン：
```graphql
type Mutation {
  createTodo(input: TodoCreateInput!): TodoResult!
}

union TodoResult = TodoType | ValidationError | InternalError
```

**特徴**:

- ✅ 型安全なエラーハンドリング
- ✅ 例外をthrowしない設計
- ✅ フロントエンドでの明示的なエラー処理

---

**バックエンド（GraphQL）**
```python
# backend/apps/graphql_api/types/todo.py
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
---

**フロントエンド（Relay）**
```typescript
const CreateTodoMutation = graphql`
  mutation TodoFormMutation($input: TodoCreateInput!) {
    createTodo(input: $input) {
      __typename
      ... on TodoType {
        id
        todoTitle
        priority
        progress
      }
      ... on ValidationError {
        category
        message
        field
        code
      }
      ... on InternalError {
        category
        message
        code
      }
    }
  }
`;
```

---

**Result Patternの処理**
```typescript
const handleSubmit = async (data: TodoCreateInput) => {
  try {
    const response = await execute({
      variables: { input: data },
      errorContext: 'CreateTodo',
    });

    // Result Patternのチェック
    const result = response.createTodo;

    if (result.__typename === 'TodoType') {
      // ✅ 成功
      toast.success('作成しました');
      navigate('/todos');
    } else if (result.__typename === 'ValidationError') {
      // ✅ バリデーションエラー
      // relay-environment.tsでApiErrorに変換されてthrowされる
      // ここには到達しない
    } else if (result.__typename === 'InternalError') {
      // ✅ サーバーエラー
      // relay-environment.tsでApiErrorに変換されてthrowされる
      // ここには到達しない
    }
  } catch (error) {
    // ApiErrorとして処理される
    if (error instanceof ApiError && error.fieldErrors) {
      Object.entries(error.fieldErrors).forEach(([field, messages]) => {
        setError(field, { type: 'server', message: messages[0] });
      });
    }
  }
};
```

**ポイント**:

- ✅ __typenameで型を判定
- ✅ エラー型はrelay-environment.tsでApiErrorに変換されてthrow
- ✅ catchブロックでエラーハンドリング

---

#### relay-environment.ts でのエラー変換
```typescript
// GraphQLエラー処理
if (hasGraphQLErrors(json)) {
  const firstError = json.errors[0];
  const extensions = firstError.extensions;

  // Union型エラー（Result Pattern）
  if (extensions?.__typename) {
    const typename = extensions.__typename;
    const statusMap: Record<string, number> = {
      ValidationError: 400,
      AuthenticationError: 401,
      AuthorizationError: 403,
      NotFoundError: 404,
      ConflictError: 409,
      RateLimitError: 429,
      ExternalServiceError: 503,
      InternalError: 500,
    };

    const status = statusMap[typename] || 500;
    const data: Record<string, unknown> = { __typename: typename };

    if (extensions.code) data.code = extensions.code;
    if (extensions.field) data.field = extensions.field;
    if (extensions.data && typeof extensions.data === 'object') {
      Object.assign(data, extensions.data);
    }

    throw new ApiError(status, firstError.message, data, new Error(firstError.message));
  }
}
```

---

## ベストプラクティス

### 1. Relay Compiler を定期的に実行
```bash
# 開発中は常にWatch
npm run relay:watch

# デプロイ前に実行
npm run relay
```
**理由**:

- ✅ GraphQLスキーマ変更を自動反映
- ✅ 型定義を最新に保つ
- ✅ ビルドエラーを事前に検出

---

### 2. Fragment を活用
```typescript
# ❌ 悪い例（重複）
query GetTodos {
  todos {
    edges {
      node {
        id
        todoTitle
        priority
        progress
      }
    }
  }
}

query GetTodo($id: ID!) {
  todo(id: $id) {
    id
    todoTitle
    priority
    progress
  }
}

# ✅ 良い例（Fragment）
fragment TodoFields on TodoType {
  id
  todoTitle
  priority
  progress
  createdAt
  updatedAt
}

query GetTodos {
  todos {
    edges {
      node {
        ...TodoFields
      }
    }
  }
}

query GetTodo($id: ID!) {
  todo(id: $id) {
    ...TodoFields
  }
}
```
**メリット**:

- ✅ フィールドの重複を削減
- ✅ 変更が一箇所で済む
- ✅ Relayのキャッシュが最適化される

---

### 3. Service層でのID変換を一箇所に集約
```typescript
// ❌ 悪い例（各所で変換）
const id = parseInt(atob(node.id).split(':')[1], 10);

// ✅ 良い例（ヘルパー関数）
function decodeRelayGlobalId(globalId: string): number {
  const decodedId = atob(globalId);
  return parseInt(decodedId.split(':')[1], 10);
}

// 使用例
const id = decodeRelayGlobalId(node.id);
```

---

### 4. エラーハンドリングを統一
```typescript
// ❌ 悪い例（Relay専用エラー処理）
if (error instanceof RelayError) { }

// ✅ 良い例（REST/GraphQL/Relay統一）
if (error instanceof ApiError) { }
```

---

## トラブルシューティング

### エラー: Relay Compiler が実行されない
```bash
# 原因: schema.graphqlが古い

# 解決策: スキーマを再取得
curl http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { types { name } } }"}' \
  --output schema.graphql

# Relay Compiler実行
npm run relay
```

---

### エラー: 型定義が生成されない
```bash
# 原因: __generated__フォルダが壊れている

# 解決策: フォルダを削除して再生成
rm -rf src/__generated__
npm run relay
```

---

### エラー: Result Patternのチェック漏れ
```typescript
// ❌ 悪い例（エラーチェックしていない）
const result = response.createTodo;
// result.__typename をチェックせずに使用
toast.success('作成しました');

// ✅ 良い例（型安全にチェック）
const result = response.createTodo;

if (result.__typename === 'TodoType') {
  toast.success('作成しました');
} else {
  // エラー処理
}
```

---

### エラー: Relay GlobalID変換エラー
```typescript
// エラー: Invalid Relay GlobalID
// 原因: Base64デコード失敗

// 解決策: ID変換を確認
function decodeRelayGlobalId(globalId: string): number {
  try {
    const decodedId = atob(globalId);  // "TodoType:123"
    const parts = decodedId.split(':');
    
    if (parts.length !== 2) {
      throw new Error('Invalid GlobalID format');
    }
    
    return parseInt(parts[1], 10);  // 123
  } catch (error) {
    console.error('Failed to decode GlobalID:', globalId, error);
    throw error;
  }
}
```

---

### エラー: キャッシュが更新されない
```typescript
// 原因: Mutationの後にキャッシュが更新されていない

// 解決策: updaterを使用
commitMutation(relayEnvironment, {
  mutation: CreateTodoMutation,
  variables: { input },
  updater: (store) => {
    const payload = store.getRootField('createTodo');
    
    if (payload.getValue('__typename') === 'TodoType') {
      const root = store.getRoot();
      const todos = root.getLinkedRecords('todos') || [];
      root.setLinkedRecords([...todos, payload], 'todos');
    }
  },
});
```

---

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

## まとめ

#### ✅ Relay統合の利点

| **項目** | **詳細** |
|------|---------------------------|
| **完全な抽象化** | UI層はREST/GraphQL/Relayを一切意識しない |
| **統一エラーハンドリング** | ApiErrorクラスに統一、エラーハンドラーも共通 |
| **型安全性** | Relay Compilerで完全な型推論 |
| **自動キャッシュ管理** | Relay Storeが最適化されたキャッシュを提供 |
| **楽観的更新** | UIの即座な更新とロールバック |

**✅ 実装のポイント**

1. relay-environment.ts でエラー変換
  - すべてのGraphQLエラーをApiErrorに変換
2. useRelayMutation/useRelayLazyLoadQuery でラップ
  - TanStack Queryと同じAPIを提供
3. AsyncBoundary で自動エラーハンドリング
  - Suspense + ErrorBoundary を一箇所で管理
4. Result Pattern の処理
  - __typenameで型安全にエラー判定

---

**✅ この実装で対応できるすべてのケース**

- ✅ GraphQL ValidationError（単一フィールド）
- ✅ GraphQL ValidationError（複数フィールド）
- ✅ GraphQL ConflictError（409）
- ✅ 認証エラー（401）→ 自動ログアウト
- ✅ ネットワークエラー → トースト表示
- ✅ サーバーエラー（500）→ トースト + ログ送信