/* response statusで取得する場合 */
export const handleApiResponseError = (response: Response) => {
  if (response.status) {
    switch (response.status) {
      case 400:
        return 'Bad Request: 無効なリクエストです。入力内容を確認してください。';
      case 401:
        return 'Unauthorized: ログインが必要です。ログインしてください。';
      case 403:
        return 'Forbidden: この操作を行う権限がありません。';
      case 404:
        return 'Not Found: リソースが見つかりません。URLを確認してください。';
      case 409:
        return 'Conflict: 競合が発生しました。入力内容を確認してください。';
      case 500:
        return 'Internal Server Error: サーバーエラーが発生しました。後ほど再試行してください。';
      case 502:
        return 'Bad Gateway: 一時的な問題が発生しました。後ほど再試行してください。';
      case 503:
        return 'Service Unavailable: サービスが一時的に利用できません。後ほど再試行してください。';
      case 504:
        return 'Gateway Timeout: タイムアウトが発生しました。後ほど再試行してください。';
      default:
        return `Unexpected error: ${response.status} - ${response.statusText}`;
    }
  }
  return 'Error: 不明なエラー';
};