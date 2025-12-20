import { baseKyClient } from './ky-client';

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
export const apiClient = baseKyClient.extend({
  // Cookie認証では特別なhooksは不要
  // baseKyClientの設定（credentials: 'include'）により
  // Cookieは自動的に送信される
  // リクエストヘッダーに付与する値がある場合はここに設定
  // リクエスト前後のフックを使用する場合もここに設定
});