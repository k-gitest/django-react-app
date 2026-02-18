/**
 * 認証付きfetch（最小実装）
 * 
 * 役割：Auth0トークンをヘッダーに付与するだけ
 * - エラーハンドリングは各クライアントに任せる
 * - リトライ・タイムアウトはTanStack Queryに任せる
 */

let getAccessTokenFn: (() => Promise<string>) | null = null;

export function setAuth0TokenGetter(fn: () => Promise<string>) {
  getAccessTokenFn = fn;
}

export async function authenticatedFetch(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<Response> {
  // 1. 既存のヘッダーを取得
  const headers = new Headers(init?.headers);

  // 2. トークン取得して追加
  if (getAccessTokenFn) {
    try {
      const token = await getAccessTokenFn();
      headers.set('Authorization', `Bearer ${token}`);
    } catch (error) {
      console.error('Failed to get access token:', error);
      // トークン取得失敗時もリクエストは続行
      // 401が返ってきたら各クライアントのエラーハンドリングで処理
    }
  }

  // 3. 標準fetchを呼んでResponseを返すだけ
  // エラーハンドリングは各クライアントに任せる
  return fetch(input, {
    ...init,
    headers,
  });
}