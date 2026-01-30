/**
 * GraphQLエラー
 * 
 * GraphQL APIから返されるエラーを表現
 * Union型のエラー（ValidationError, ConflictError等）を扱う
 */
export class GraphQLError extends Error {
  constructor(
    public typename: string,      // __typename (例: "ValidationError")
    public category: string,       // error.category
    public message: string,        // error.message
    public code: string,           // error.code
    public field?: string,         // error.field (ValidationErrorの場合)
    public data?: Record<string, unknown>, // 追加データ
    public originalError?: unknown // 元のエラー
  ) {
    super(message);
    this.name = 'GraphQLError';
  }

  /**
   * エラーが特定の型かどうかを判定
   */
  isType(typename: string): boolean {
    return this.typename === typename;
  }

  /**
   * バリデーションエラーかどうか
   */
  isValidationError(): boolean {
    return this.typename === 'ValidationError';
  }

  /**
   * 認証エラーかどうか
   */
  isAuthenticationError(): boolean {
    return this.typename === 'AuthenticationError';
  }

  /**
   * 認可エラーかどうか
   */
  isAuthorizationError(): boolean {
    return this.typename === 'AuthorizationError';
  }

  /**
   * 競合エラーかどうか
   */
  isConflictError(): boolean {
    return this.typename === 'ConflictError';
  }
}