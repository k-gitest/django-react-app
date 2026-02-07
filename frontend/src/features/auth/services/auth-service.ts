import { apiClient } from '@/lib/api-client';
import type { Account, UserInfo } from '../types/auth';
//import type { ApiRes, ApiReq } from '@/types/api-utils';

/**
 * ユーザー情報取得
 * エンドポイント: GET /api/v1/auth/user/
 * 認証: Cookie（自動送信）
 */
export const fetchMe = async (): Promise<UserInfo> => {
  const { data } = await apiClient.GET("/api/v1/auth/user/");
  if (!data) throw new Error("User not found");
  return data;
};

/**
 * ログイン
 * POST /api/v1/auth/login/
 * @param credentials - 認証情報 (email, password)
 */
export const loginService = async (credentials: Account): Promise<UserInfo> => {
  const { data } = await apiClient.POST("/api/v1/auth/login/", {
    body: credentials,
  });
  
  if (!data?.user) throw new Error("User not found");

  // ここで access, refresh を捨てて user だけを返す
  return {
    id: data.user.id,
    email: data.user.email,
    is_staff: data.user.is_staff,
    first_name: data.user.first_name,
    last_name: data.user.last_name,
  };
};

/**
 * サインアップ
 * エンドポイント: POST /api/v1/auth/registration/
 * 認証: 不要
 * backendのスキーマに合わせて password1/2 を送信
 */
export const signupService = async (credentials: Account): Promise<UserInfo> => {
  const { data } = await apiClient.POST('/api/v1/auth/registration/', {
    body: {
      email: credentials.email,
      password1: credentials.password,
      password2: credentials.password,
    },
  });
  return data;
};

/**
 * トークン更新
 * エンドポイント: POST /api/v1/auth/token/refresh/
 * 認証: refresh-token Cookie（自動送信）
 * 成功時、新しいaccess-tokenとrefresh-tokenがCookieで設定される
 * 注意: Cookie認証では通常このエンドポイントを直接呼ぶ必要はありません
 * ブラウザが自動的にCookieを管理します
 */
export const refreshTokenService = async (refreshToken: string) => {
  const { data } = await apiClient.POST('/api/v1/auth/token/refresh/', {
    body: {
      refresh: refreshToken,
    },
  });
  return data;
};

/**
 * ログアウト
 * エンドポイント: POST /api/v1/auth/logout/
 * 認証: Cookie（自動送信）
 * サーバー側でrefresh-tokenをブラックリストに追加し、Cookieを削除
 * 注意: エラーが発生してもクライアント側の状態はクリアされます（use-auth.tsで処理）
 */
export const logoutService = async () => {
  await apiClient.POST('/api/v1/auth/logout/');
};