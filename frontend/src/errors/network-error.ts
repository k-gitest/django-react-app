/**
 * ネットワーク通信エラーを表すカスタムエラークラス
 * タイムアウト、DNS解決失敗、接続失敗などが該当
 */
export class NetworkError extends Error {
  public readonly name = 'NetworkError';
  
  constructor(
    message: string = 'ネットワークエラーが発生しました',
    public readonly originalError?: unknown,
  ) {
    super(message);
    Object.setPrototypeOf(this, NetworkError.prototype);
  }

  /**
   * タイムアウトエラーかどうか
   */
  get isTimeout(): boolean {
    if (this.originalError instanceof Error) {
      return this.originalError.message.includes('timeout');
    }
    return false;
  }
}