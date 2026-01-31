import { ApiError } from '@/errors/api-error';
import { NetworkError } from '@/errors/network-error';
import { ClientError, GraphQLClient } from 'graphql-request';
import { GRAPHQL_URL } from './constants';

export const graphqlClient = new GraphQLClient(GRAPHQL_URL, {
  credentials: 'include',
  headers: {
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/json',
  },
});

/**
 * GraphQLリクエストのラッパー
 * エラーをApiErrorに変換（GraphQLErrorは使わない）
 */
export async function gqlRequest<T>(document: string, variables?: Record<string, unknown>): Promise<T> {
  try {
    return await graphqlClient.request<T>({
      document,
      variables,
      signal: AbortSignal.timeout(10000),
    });
  } catch (error) {
    // ✅ GraphQLエラー → ApiError に統一
    throw convertToApiError(error);
  }
}

export async function gqlMutation<TMutation, TKey extends keyof TMutation = keyof TMutation>(
  document: string,
  variables?: Record<string, unknown>,
  resultKey?: TKey,
): Promise<TMutation[TKey]> {
  const data = await gqlRequest<TMutation>(document, variables);

  if (resultKey && data && typeof data === 'object' && resultKey in data) {
    const result = data[resultKey];

    if (isErrorResult(result)) {
      throw resultToApiError(result);
    }

    return result as TMutation[TKey];
  }

  return data as unknown as TMutation[TKey];
}

// ============================================================================
// ヘルパー関数（ApiErrorに統一）
// ============================================================================

/**
 * GraphQLエラー → ApiError に変換
 */
function convertToApiError(error: unknown): Error {
  if (error instanceof ClientError) {
    const graphqlErrors = error.response.errors;

    if (graphqlErrors && graphqlErrors.length > 0) {
      const firstError = graphqlErrors[0];

      // Union型エラーの場合
      if (firstError.extensions?.__typename) {
        const typename = firstError.extensions.__typename as string;
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

        return new ApiError(
          statusMap[typename] || 500, // 1. status
          firstError.message, // 2. message
          {
            // 3. data (一纏めにする)
            code: firstError.extensions.code,
            field: firstError.extensions.field,
            ...((firstError.extensions.data as object) || {}),
            __typename: typename,
          },
          error, // 4. originalError
        );
      }
    }

    // 標準GraphQLエラー
    return new ApiError(500, error.message || 'GraphQLエラーが発生しました', { code: 'graphql_error' }, error);
  }

  if (error instanceof Error) {
    return new NetworkError(error.message || 'ネットワークエラーが発生しました', error);
  }

  return new NetworkError('予期しないエラーが発生しました', error);
}

interface ResultPatternResponse {
  __typename: string;
  message?: string;
  category?: string;
  code?: string;
  field?: string;
  [key: string]: unknown;
}

function isErrorResult(result: unknown): result is ResultPatternResponse {
  if (!result || typeof result !== 'object') {
    return false;
  }

  const errorTypes = [
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'NotFoundError',
    'ConflictError',
    'RateLimitError',
    'ExternalServiceError',
    'InternalError',
  ];

  return '__typename' in result && typeof result.__typename === 'string' && errorTypes.includes(result.__typename);
}

/**
 * Result Patternのエラー → ApiError に変換
 */
function resultToApiError(result: ResultPatternResponse): ApiError {
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

  return new ApiError(
    statusMap[result.__typename] || 500, // 1. status
    result.message || 'エラーが発生しました', // 2. message
    result, // 3. data (result自体を渡す)
    // 4. originalError は無いので省略
  );
}
