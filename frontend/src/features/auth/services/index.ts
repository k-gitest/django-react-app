import * as rest from './auth-service';
import * as graphql from './auth-service-graphql';
//import type { Account, TokenResponse, UserInfo } from '../types/auth';

/**
 * 💡 サービス切り替えスイッチ
 * true にしたメソッドは GraphQL、false は REST が使われます。
 */
const useGraphQL = {
  fetchMe: true,    // ユーザー情報取得を先行してGraphQL化
  login: false,     // ログインもGraphQL化
  signup: false,    // サインアップはまだREST
  logout: true,     // ログアウトもGraphQL
};

export const authService = {
  // ユーザー情報取得
  fetchMe: useGraphQL.fetchMe ? graphql.fetchMeGraphQL : rest.fetchMe,

  // ログイン
  loginService: useGraphQL.login ? graphql.loginServiceGraphQL : rest.loginService,

  // サインアップ
  signupService: useGraphQL.signup ? graphql.signupServiceGraphQL : rest.signupService,

  // ログアウト
  logoutService: useGraphQL.logout ? graphql.logoutServiceGraphQL : rest.logoutService,

  // トークンリフレッシュ（REST特有だが互換性のために残す）
  refreshToken: rest.refreshTokenService,
};

export const { fetchMe, loginService, signupService, logoutService, refreshToken } = authService;