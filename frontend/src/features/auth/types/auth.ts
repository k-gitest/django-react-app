import type { ApiRes } from '@/types/api-utils';

// ============================================================================
// APIレスポンスから型を抽出
// ============================================================================
type LoginRes = ApiRes<"/api/v1/auth/login/", "post">;

// ============================================================================
// ユーザー情報の型定義
// ============================================================================
/*
export interface UserInfo {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
}
  */

// loginレスポンス内の user 型を抽出し、null/undefined を除外する
export type UserInfo = NonNullable<LoginRes['user']>;

// ============================================================================
// トークンレスポンスの型定義
// ============================================================================
/*
export interface TokenResponse {
  access: string;
  refresh: string;  // dj-rest-authでは空文字 ""（Cookieで管理）
  user?: UserInfo;  // dj-rest-authはuser情報を含む（オプション）
}
*/

// ============================================================================
// アカウント（ログイン・サインアップ）の型定義
// ============================================================================
export interface Account {
  email: string;
  password: string;
}

// ============================================================================
// 認証ストアの型定義（Cookie専用）
// ============================================================================
// GET /api/v1/auth/user/ の 200 OK レスポンスの型を抽出
//export type User = ApiRes<'/api/v1/auth/user/', 'get'>;
export type DjangoUser = ApiRes<'/api/v1/auth/user/', 'get'>;

// Auth0ユーザー型（OIDC統合後）
export interface Auth0User {
  id: string;  // Auth0のsub（例: "auth0|507f1f77bcf86cd799439011"）
  email: string;
  first_name: string;
  last_name: string;
}

// 統合されたユーザー型（どちらでも受け入れる）
export type User = DjangoUser | Auth0User;

// 型ガード関数
export function isDjangoUser(user: User): user is DjangoUser {
  return typeof (user as DjangoUser).id === 'number';
}
export function isAuth0User(user: User): user is Auth0User {
  return typeof (user as Auth0User).id === 'string';
}

export interface AuthState {
  user: User | null;
  isInitialized: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;
  setInitialized: (value: boolean) => void;
}

// ============================================================================
// 認証フォーム型定義
// ============================================================================
export type AccountFormType = 'login' | 'register';