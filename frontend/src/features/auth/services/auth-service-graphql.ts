import { gqlRequest, gqlMutation } from '@/lib/graphql-client';
import { GET_ME } from '@/graphql/queries/user';
import { REGISTER, LOGIN, LOGOUT } from '@/graphql/mutations/user';
import type {
  GetMeQuery,
  RegisterMutation,
  LoginMutation,
  LogoutMutation,
  RegisterInput,
  LoginInput,
  //UserType,
  AuthPayload,
} from '@/graphql/types';
import type { Account, TokenResponse, UserInfo } from '../types/auth';

/**
 * GraphQL API実装
 * 外部には公開しない（auth-service.ts経由で使用）
 * 
 * 責務:
 * - GraphQL型 ⇔ 統一型（UserInfo, TokenResponse）の変換
 */

/**
 * ユーザー情報取得
 */
export const fetchMeGraphQL = async (): Promise<UserInfo> => {
  const data = await gqlRequest<GetMeQuery>(GET_ME);

  if (!data.me) {
    throw new Error('ユーザー情報が取得できませんでした');
  }

  return graphqlUserToUserInfo(data.me);
};

/**
 * ログイン
 */
export const loginServiceGraphQL = async (credentials: Account): Promise<TokenResponse> => {
  const input: LoginInput = {
    email: credentials.email,
    password: credentials.password,
  };

  const authPayload = await gqlMutation<LoginMutation, 'login'>(
    LOGIN,
    { input },
    'login'
  );

  return graphqlAuthToTokenResponse(authPayload as AuthPayload);
};

/**
 * サインアップ
 */
export const signupServiceGraphQL = async (credentials: Account): Promise<TokenResponse> => {
  const input: RegisterInput = {
    email: credentials.email,
    password: credentials.password,
    passwordConfirm: credentials.password,
    firstName: '',
    lastName: '',
  };

  const authPayload = await gqlMutation<RegisterMutation, 'register'>(
    REGISTER,
    { input },
    'register'
  );

  return graphqlAuthToTokenResponse(authPayload as AuthPayload);
};

/**
 * トークン更新
 * 
 * Note: Cookie認証ではトークン更新は不要
 * REST APIとのインターフェース互換性のために存在
 */
export const refreshTokenServiceGraphQL = async (): Promise<{ access: string }> => {
  // Cookie認証では不要だが、互換性のためダミー実装
  return { access: '' };
};

/**
 * ログアウト
 */
export const logoutServiceGraphQL = async (): Promise<void> => {
  await gqlMutation<LogoutMutation, 'logout'>(
    LOGOUT,
    undefined,
    'logout'
  );
};

// ============================================================================
// 型変換ヘルパー
// ============================================================================

/**
 * GraphQL UserType → UserInfo に変換
 */
/*
function graphqlUserToUserInfo(graphqlUser: UserType): UserInfo {
  return {
    id: graphqlUser.id,
    email: graphqlUser.email,
    first_name: graphqlUser.firstName,
    last_name: graphqlUser.lastName,
    is_staff: graphqlUser.isStaff,
  };
}
*/
function graphqlUserToUserInfo(
  graphqlUser: 
    | NonNullable<GetMeQuery['me']> 
    | Extract<LoginMutation['login'], { __typename: 'AuthPayload' }>['user']
): UserInfo {
  // ここで graphqlUser が確実に id, email 等を持つ型として扱えるようになります
  return {
    id: Number(graphqlUser.id),
    email: graphqlUser.email,
    is_staff: graphqlUser.isStaff,
    first_name: graphqlUser.firstName ?? undefined,
    last_name: graphqlUser.lastName ?? undefined,
  };
}
/**
 * GraphQL AuthPayload → TokenResponse に変換
 */
function graphqlAuthToTokenResponse(authPayload: AuthPayload): TokenResponse {
  return {
    user: graphqlUserToUserInfo(authPayload.user),
    // Cookie認証ではaccess/refreshトークンは不要だが、
    // 既存のコードとの互換性のためダミー値を返す
    access: '',
    refresh: '',
  };
}