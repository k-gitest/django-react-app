import type { paths } from './api'; // 生成されたファイルをインポート

/**
 * 特定のパスとメソッドのレスポンス型を抽出
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
 */
export type ApiReq<
  P extends keyof paths,
  M extends keyof paths[P] & string
> = paths[P][M] extends { requestBody: { content: { "application/json": infer T } } }
  ? T
  : never;