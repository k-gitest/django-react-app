import type { paths } from './api'; // 生成されたファイルをインポート

/**
 * 特定のパスとメソッドのレスポンス型を抽出
 * ApiRes: 指定したパスとメソッドから「成功レスポンス(200系)」の中身を抽出する
 * * @template P - schema.tsのpathsに定義されている有効なエンドポイントパス
 * @template M - そのパス(P)で許可されているHTTPメソッド (get, post等)
 * * 仕組み:
 * 1. P と M が paths 内に存在するかチェック (extends keyof)
 * 2. 階層を responses -> 200 (または201) -> content -> application/json と掘り進める
 * 3. infer T により、JSONの中身の型を自動推論して取り出す
 * 4. 該当する成功レスポンス定義がない場合は void を返す
 */
export type ApiRes<
  P extends keyof paths,
  M extends keyof paths[P] & string
> = paths[P][M] extends { responses: { 200: { content: { "application/json": infer T } } } }
  ? T
  : paths[P][M] extends { responses: { 201: { content: { "application/json": infer T } } } }
  ? T
  : void;

/**
 * 特定のパスとメソッドのリクエストボディ型を抽出
 * ApiReq: 指定したパスとメソッドから「リクエストボディ」の型を抽出する
 * * * 主に POST, PUT, PATCH 等で送信するデータの型を定義する際に使用する。
 * * 仕組み:
 * 1. 指定されたパス/メソッドの requestBody 階層をのぞき込む
 * 2. application/json 内に定義されている型を infer T で捕捉する
 * 3. スキーマが undefined を許容している場合は Exclude で除去し、スプレッド構文等で使いやすくする
 * 4. リクエストボディを必要としない、または未定義の場合は Record<string, never> (空オブジェクト) を返す
 */
export type ApiReq<
  P extends keyof paths,
  M extends keyof paths[P] & string
> = paths[P][M] extends { requestBody?: { content: { "application/json": infer T } } }
  ? Exclude<T, undefined> 
  : Record<string, never>;