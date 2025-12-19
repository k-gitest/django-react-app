import ky from 'ky';
import { BASE_API_URL } from '@/lib/constants';
import { ApiError } from '@/errors/api-error';
import { NetworkError } from '@/errors/network-error';

interface ApiErrorResponse {
  detail?: string;
  message?: string;
  [key: string]: string | string[] | undefined;
}

/**
 * ベースとなる ky クライアント
 * 全てのHTTPリクエストで使用される共通設定
 */
export const baseKyClient = ky.create({
  prefixUrl: BASE_API_URL,
  timeout: 5000,
  // クッキー（リフレッシュトークン）の送受信を許可
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
  },
  retry: {
    limit: 3,
    methods: ['get', 'put', 'delete'],
    statusCodes: [500, 502, 503, 504],
  },
  hooks: {
    beforeError: [
      async (error) => {
        const { response } = error;

        // HTTPレスポンスがある場合（4xx, 5xxエラー）
        if (response) {
          // レスポンスボディを取得（JSONパース失敗時はnull）
          const errorBody = await response
          .json()
          .then((data) => data as ApiErrorResponse)
          .catch(() => null);

          // カスタムApiErrorをthrow
          throw new ApiError(
            response.status,
            errorBody?.detail || errorBody?.message || response.statusText,
            errorBody,
            error,
          );
        }

        // HTTPレスポンスがない場合（ネットワークエラー、タイムアウトなど）
        throw new NetworkError(
          error.message || 'ネットワークエラーが発生しました',
          error,
        );
      },
    ],
  },
});