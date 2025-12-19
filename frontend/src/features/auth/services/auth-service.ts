import { authFetch } from '@/lib/auth-client';
import { baseKyClient } from '@/lib/ky-client';
import type { Account, TokenResponse, UserInfo } from '../types/auth';

/**
 * ユーザー情報取得: 認証済みリクエスト (GETリクエスト)
 * エンドポイント: GET /api/v1/auth/user/
 * 必須: Authorization ヘッダー または Cookie
 * 
 * @throws {ApiError} 401 - 認証が必要
 * @throws {ApiError} 500 - サーバーエラー
 * @throws {NetworkError} ネットワークエラー
 */
export const fetchMe = async (): Promise<UserInfo> => {
  return authFetch<UserInfo>('auth/user/');
};

/**
 * ログインAPIを呼び出し、JWTトークンを返します。
 * エンドポイント: POST /api/v1/auth/login/
 * 認証: 不要
 * 
 * @param credentials - 認証情報 (email, password)
 * @returns {Promise<TokenResponse>} - accessトークン、refreshトークン（空文字）、user情報
 * 
 * @throws {ApiError} 400 - バリデーションエラー
 * @throws {ApiError} 401 - 認証情報が不正
 * @throws {ApiError} 500 - サーバーエラー
 * @throws {NetworkError} ネットワークエラー
 */
export const loginService = async (credentials: Account): Promise<TokenResponse> => {
  return baseKyClient('auth/login/', {
    method: 'post',
    json: {
      email: credentials.email,
      password: credentials.password,
    },
  }).json<TokenResponse>();
};

/**
 * サインアップAPIを呼び出し、アカウントを作成します。
 * 作成後、自動でログインされ、JWTトークンを返します。
 * エンドポイント: POST /api/v1/auth/registration/
 * 認証: 不要
 * 
 * @param credentials - ユーザー登録情報 (email, password)
 * @returns {Promise<TokenResponse>} - accessトークン、refreshトークン（空文字）、user情報
 * 
 * @throws {ApiError} 400 - バリデーションエラー（パスワード不一致、既存メールなど）
 * @throws {ApiError} 500 - サーバーエラー
 * @throws {NetworkError} ネットワークエラー
 */
export const signupService = async (credentials: Account): Promise<TokenResponse> => {
  return baseKyClient('auth/registration/', {
    method: 'post',
    json: {
      email: credentials.email,
      password1: credentials.password,
      password2: credentials.password,
    },
  }).json<TokenResponse>();
};

/**
 * トークン更新APIを呼び出し、新しいアクセストークンを取得します。
 * エンドポイント: POST /api/v1/auth/token/refresh/
 * 認証: 不要（refresh-token Cookieが自動送信される）
 * 
 * @returns {Promise<{access: string}>} - 新しいaccessトークン
 * 
 * @throws {ApiError} 401 - リフレッシュトークンが無効
 * @throws {ApiError} 500 - サーバーエラー
 * @throws {NetworkError} ネットワークエラー
 */
export const refreshTokenService = async (): Promise<{ access: string }> => {
  return baseKyClient('auth/token/refresh/', {
    method: 'post',
  }).json<{ access: string }>();
};

/**
 * ログアウトAPIを呼び出し、サーバー側でトークンを無効化します。
 * エンドポイント: POST /api/v1/auth/logout/
 * 必須: Authorization ヘッダー または Cookie
 * 
 * @returns {Promise<void>}
 * 
 * @throws {ApiError} 401 - 認証が必要
 * @throws {ApiError} 500 - サーバーエラー
 * @throws {NetworkError} ネットワークエラー
 * 
 * 【重要】エラーハンドリングについて：
 * - try-catch は削除しました
 * - エラーは呼び出し元（use-auth.ts）に伝播します
 * - React Query の onError で errorHandler が自動実行されます
 */
export const logoutService = async (): Promise<void> => {
  await authFetch<void>('auth/logout/', {
    method: 'post',
  });
};