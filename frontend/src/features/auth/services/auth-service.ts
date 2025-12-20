import { apiClient } from '@/lib/api-client';
import type { Account, TokenResponse, UserInfo } from '../types/auth';

/**
 * ユーザー情報取得
 * 
 * エンドポイント: GET /api/v1/auth/user/
 * 認証: Cookie（自動送信）
 * 
 * @throws {ApiError} 401 - 認証が必要（errorHandlerで自動処理）
 * @throws {ApiError} 500 - サーバーエラー
 * @throws {NetworkError} ネットワークエラー
 */
export const fetchMe = async (): Promise<UserInfo> => {
  return apiClient.get('auth/user/').json<UserInfo>();
};

/**
 * ログイン
 * 
 * エンドポイント: POST /api/v1/auth/login/
 * 認証: 不要
 * 
 * 成功時、HttpOnly CookieでJWTトークンが自動設定される
 * 
 * @param credentials - 認証情報 (email, password)
 * @returns {Promise<TokenResponse>} - user情報を含むレスポンス
 * 
 * @throws {ApiError} 400 - バリデーションエラー
 * @throws {ApiError} 401 - 認証情報が不正
 * @throws {ApiError} 500 - サーバーエラー
 * @throws {NetworkError} ネットワークエラー
 */
export const loginService = async (credentials: Account): Promise<TokenResponse> => {
  return apiClient.post('auth/login/', {
    json: {
      email: credentials.email,
      password: credentials.password,
    },
  }).json<TokenResponse>();
};

/**
 * サインアップ
 * 
 * エンドポイント: POST /api/v1/auth/registration/
 * 認証: 不要
 * 
 * 成功時、自動でログインされ、HttpOnly CookieでJWTトークンが設定される
 * 
 * @param credentials - ユーザー登録情報 (email, password)
 * @returns {Promise<TokenResponse>} - user情報を含むレスポンス
 * 
 * @throws {ApiError} 400 - バリデーションエラー（パスワード不一致、既存メールなど）
 * @throws {ApiError} 500 - サーバーエラー
 * @throws {NetworkError} ネットワークエラー
 */
export const signupService = async (credentials: Account): Promise<TokenResponse> => {
  return apiClient.post('auth/registration/', {
    json: {
      email: credentials.email,
      password1: credentials.password,
      password2: credentials.password,
    },
  }).json<TokenResponse>();
};

/**
 * トークン更新
 * 
 * エンドポイント: POST /api/v1/auth/token/refresh/
 * 認証: refresh-token Cookie（自動送信）
 * 
 * 成功時、新しいaccess-tokenとrefresh-tokenがCookieで設定される
 * 
 * @returns {Promise<{access: string}>} - 新しいaccessトークン
 * 
 * @throws {ApiError} 401 - リフレッシュトークンが無効
 * @throws {ApiError} 500 - サーバーエラー
 * @throws {NetworkError} ネットワークエラー
 * 
 * 注意: Cookie認証では通常このエンドポイントを直接呼ぶ必要はありません
 * ブラウザが自動的にCookieを管理します
 */
export const refreshTokenService = async (): Promise<{ access: string }> => {
  return apiClient.post('auth/token/refresh/').json<{ access: string }>();
};

/**
 * ログアウト
 * 
 * エンドポイント: POST /api/v1/auth/logout/
 * 認証: Cookie（自動送信）
 * 
 * サーバー側でrefresh-tokenをブラックリストに追加し、Cookieを削除
 * 
 * @returns {Promise<void>}
 * 
 * @throws {ApiError} 401 - 認証が必要
 * @throws {ApiError} 500 - サーバーエラー
 * @throws {NetworkError} ネットワークエラー
 * 
 * 注意: エラーが発生してもクライアント側の状態はクリアされます（use-auth.tsで処理）
 */
export const logoutService = async (): Promise<void> => {
  await apiClient.post('auth/logout/').json<void>();
};