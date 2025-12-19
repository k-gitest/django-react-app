/**
 * API通信エラーを表すカスタムエラークラス
 * HTTPステータスコードとレスポンスボディを保持
 */
export class ApiError extends Error {
  public readonly name = 'ApiError';
  
  constructor(
    public readonly status: number,
    message?: string,
    public readonly data?: unknown,
    public readonly originalError?: unknown,
  ) {
    super(message || `API Error: ${status}`);
    
    // TypeScriptのビルトインErrorとの互換性を保つ
    Object.setPrototypeOf(this, ApiError.prototype);
  }

  /**
   * サーバーから返されたエラーメッセージを取得
   */
  get serverMessage(): string | null {
    if (this.data && typeof this.data === 'object' && 'detail' in this.data) {
      return String(this.data.detail);
    }
    if (this.data && typeof this.data === 'object' && 'message' in this.data) {
      return String(this.data.message);
    }
    return null;
  }

  /**
   * バリデーションエラーの場合、フィールド別エラーを取得
   */
  get fieldErrors(): Record<string, string[]> | null {
    if (this.status === 400 && this.data && typeof this.data === 'object') {
      // Django REST Framework形式: { field_name: ["error1", "error2"] }
      const errors: Record<string, string[]> = {};
      for (const [key, value] of Object.entries(this.data)) {
        if (Array.isArray(value)) {
          errors[key] = value.map(String);
        } else if (typeof value === 'string') {
          errors[key] = [value];
        }
      }
      return Object.keys(errors).length > 0 ? errors : null;
    }
    return null;
  }

  /**
   * 認証エラーかどうか
   */
  get isAuthError(): boolean {
    return this.status === 401;
  }

  /**
   * 権限エラーかどうか
   */
  get isForbiddenError(): boolean {
    return this.status === 403;
  }

  /**
   * サーバーエラーかどうか
   */
  get isServerError(): boolean {
    return this.status >= 500;
  }
}