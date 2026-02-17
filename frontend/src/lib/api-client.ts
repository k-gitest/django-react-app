//import { baseKyClient } from './ky-client';
import createClient, { type Middleware } from "openapi-fetch";
import type { paths } from "@/types/api";
import { BASE_API_URL } from "@/lib/constants";
import { ApiError } from "@/errors/api-error";
import { NetworkError } from "@/errors/network-error";

/**
 * APIクライアント（Cookie認証）
 * 
 * Django JWT Cookie認証用のHTTPクライアント
 * - Cookieは自動的にブラウザが送信（手動管理不要）
 * - 全エラーはApiErrorとしてthrowされ、errorHandlerで処理
 * - 401エラー時は自動的にログインページへリダイレクト（errorHandlerで処理）
 * 
 * @example
 * // GET リクエスト
 * const user = await apiClient.get('auth/user/').json<UserInfo>();
 * 
 * @example
 * // POST リクエスト
 * const response = await apiClient.post('auth/login/', { 
 *   json: { email: 'user@example.com', password: 'pass' }
 * }).json<TokenResponse>();
 * 
 * @example
 * // PATCH リクエスト
 * const updated = await apiClient.patch(`todos/${id}/`, {
 *   json: { progress: 100 }
 * }).json<Todo>();
 * 
 * @example
 * // DELETE リクエスト
 * await apiClient.delete(`todos/${id}/`);
 */
/*
export const apiClient = baseKyClient.extend({
  // Cookie認証では特別なhooksは不要
  // baseKyClientの設定（credentials: 'include'）により
  // Cookieは自動的に送信される
  // リクエストヘッダーに付与する値がある場合はここに設定
  // リクエスト前後のフックを使用する場合もここに設定
});
*/

// Auth0のトークン取得関数を外部から注入
let getAccessTokenFn: (() => Promise<string>) | null = null

export function setAuth0TokenGetter(fn: () => Promise<string>) {
  getAccessTokenFn = fn
}

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
 * エラーハンドリングミドルウェア
 * kyの hooks.beforeError に相当
 */
// ログ出力（開発時のみ）
const loggerMiddleware: Middleware = {
  async onRequest({ request }) {
    if (import.meta.env.DEV) {
      console.log(`🚀 [API] ${request.method} ${request.url}`);
    }

    if (getAccessTokenFn) {
      const token = await getAccessTokenFn()
      request.headers.set('Authorization', `Bearer ${token}`)
    }
    
    return request;
  },
};

// HTTPエラーハンドリング (4xx, 5xx)
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

// 通信エラーハンドリング (オフライン, タイムアウト)
const networkErrorMiddleware: Middleware = {
  async onError({ error }) {
    // error が Error オブジェクトかどうかをチェック
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