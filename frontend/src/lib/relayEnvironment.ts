import { Environment, Network, RecordSource, Store } from 'relay-runtime';
import type {
  FetchFunction,
  RequestParameters,
  Variables,
  GraphQLResponse
} from 'relay-runtime';
import { authenticatedFetch } from './authenticated-fetch';
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
 * 
 * GraphQLエラーを含むレスポンスかどうかを判定します。
 * - errors 配列が存在し、少なくとも1つのエラーが含まれている場合に true を返します。
 */
function hasGraphQLErrors(json: unknown): json is GraphQLErrorResponse {
  // 1. まず null ではなくオブジェクトであることを確認
  if (typeof json !== 'object' || json === null) {
    return false;
  }

  // 2. 'errors' プロパティがあるか確認
  // この時点で TypeScript は json を "object" と認識しているため 'in' が使える
  if (!('errors' in json)) {
    return false;
  }

  // 3. 'errors' が配列であり、かつ中身があるか確認
  // json.errors ではなく、一旦定数に受けるか
  // Array.isArray(json.errors) で絞り込む
  const errors = json.errors;
  return Array.isArray(errors) && errors.length > 0;
}

/**
 * GraphQLレスポンスの型ガード
 * 
 * Relayが処理できる正規のGraphQLレスポンス形式かどうかを判定します。
 * GraphQLレスポンスは必ず data または errors プロパティを持ちます。
 */
function isGraphQLResponse(json: unknown): json is GraphQLResponse {
  if (typeof json !== 'object' || json === null) {
    return false;
  }

  return 'data' in json || 'errors' in json;
}

/**
 * Relay用のFetch関数
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
    const response = await authenticatedFetch(GRAPHQL_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
      },
      credentials: 'include',
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

    if (isGraphQLResponse(json)) {
      return json;
    }
    throw new NetworkError(
      '不正なGraphQLレスポンスを受信しました',
      new Error(`Invalid response: ${Object.keys(json)}`)
    );
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof Error) throw new NetworkError(error.message, error);
    throw new NetworkError('予期しないエラーが発生しました', error);
  }
};

export const relayEnvironment = new Environment({
  network: Network.create(fetchRelay),
  store: new Store(new RecordSource()),
});