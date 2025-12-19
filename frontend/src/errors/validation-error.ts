/**
 * クライアント側のバリデーションエラーを表すクラス
 * Zodなどのスキーマバリデーションで使用
 */
export class ValidationError extends Error {
  public readonly name = 'ValidationError';
  
  constructor(
    message: string = '入力内容に誤りがあります',
    public readonly fields?: Record<string, string[]>,
  ) {
    super(message);
    Object.setPrototypeOf(this, ValidationError.prototype);
  }

  /**
   * 特定フィールドのエラーメッセージを取得
   */
  getFieldErrors(fieldName: string): string[] | null {
    return this.fields?.[fieldName] || null;
  }

  /**
   * 全てのエラーメッセージをフラットな配列で取得
   */
  get allMessages(): string[] {
    if (!this.fields) return [this.message];
    
    return Object.values(this.fields).flat();
  }
}