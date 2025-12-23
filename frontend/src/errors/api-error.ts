/**
 * API通信エラーを表すカスタムエラークラス
 * HTTPステータスコードとレスポンスボディを保持
 */
export class ApiError extends Error {
  public override readonly name = 'ApiError'; // overrideを追加するとより安全
  
  // プロパティを明示的に宣言
  public readonly status: number;
  public readonly data?: unknown;
  public readonly originalError?: unknown;

  constructor(
    status: number,
    message?: string,
    data?: unknown,
    originalError?: unknown,
  ) {
    super(message || `API Error: ${status}`);
    
    // 手動で値を代入
    this.status = status;
    this.data = data;
    this.originalError = originalError;
    
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

  get isAuthError(): boolean {
    return this.status === 401;
  }

  get isForbiddenError(): boolean {
    return this.status === 403;
  }

  get isServerError(): boolean {
    return this.status >= 500;
  }
}