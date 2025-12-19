import type { Options } from 'ky';
import { baseKyClient } from './ky-client';

/**
 * 認証済みリクエスト用の ky インスタンス
 * 
 * 【重要】401エラーの処理について：
 * - オプションA: ここで処理（早期インターセプト）
 * - オプションB: errorHandler で処理（統一化）
 * 
 * 現在は オプションB を採用（afterResponse は使用しない）
 * 全てのエラーは ApiError として throw され、errorHandler で処理される
 */
export const authKyClient = baseKyClient.extend({
  // オプションA: 401エラーをここで処理する場合（コメントアウト中）
  /*
  hooks: {
    afterResponse: [
      async (_request, _options, response) => {
        if (response.status === 401) {
          // エラーは既に beforeError でカスタムエラーに変換済み
          // ここでは何もせず、errorHandler に任せる
        }
        return response;
      },
    ],
  },
  */
});

/**
 * 認証済みフェッチ関数（型安全）
 * 
 * @template T - 期待するレスポンスの型
 * @param path - エンドポイントのパス
 * @param options - kyのリクエストオプション（method, json, searchParams等）
 * @returns パースされたレスポンスデータ
 * 
 * @throws {ApiError} HTTPエラーが発生した場合
 * @throws {NetworkError} ネットワークエラーが発生した場合
 * 
 * @example
 * // GET リクエスト
 * try {
 *   const user = await authFetch<UserInfo>('/users/me');
 * } catch (error) {
 *   // エラーは errorHandler で自動処理されるが、
 *   // 個別の状態更新などが必要な場合はここで処理
 * }
 * 
 * @example
 * // POST リクエスト
 * const result = await authFetch<TokenResponse>('/auth/login', {
 *   method: 'POST',
 *   json: { email, password }
 * });
 */
export async function authFetch<T>(
  path: string,
  options?: Options,
): Promise<T> {
  return authKyClient(path, options).json<T>();
}

// 特殊な用途向けに authKyClient も export
export { authKyClient as authenticatedClient };