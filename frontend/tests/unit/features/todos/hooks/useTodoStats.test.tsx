import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { useTodoStats } from '@/features/todos/hooks/useTodoStats';

/* =========================
   モック対象
========================= */
import { todoService } from '@/features/todos/services/todo-service';
import { useApiSuspenseQuery } from '@/hooks/use-suspense-query';

/* =========================
   vi.mock（すべてトップレベル）
========================= */

// useApiSuspenseQueryをモックしてSuspenseを回避
vi.mock('@/hooks/use-suspense-query', () => ({
  useApiSuspenseQuery: vi.fn(),
}));

// todoServiceはmoックするが、queryFn内で実際に呼ばれるかを検証するため
// useApiSuspenseQueryのqueryFnを手動実行する
vi.mock('@/features/todos/services/todo-service', () => ({
  todoService: {
    getTodoStats: vi.fn(),
  },
}));

/* =========================
   モック参照
========================= */

const useApiSuspenseQueryMock = useApiSuspenseQuery as unknown as Mock;
const mockGetTodoStats = todoService.getTodoStats as Mock;

/* =========================
   ダミーデータ
========================= */

// openapi-fetch形式のレスポンス（{ data, error }）
const mockStatsApiResponse = {
  data: [
    { priority: 'HIGH', count: 5 },
    { priority: 'MEDIUM', count: 3 },
    { priority: 'LOW', count: 2 },
  ],
  error: undefined,
};

// 変換後の期待値（fillが追加される）
const expectedStatsData = [
  { priority: 'HIGH', count: 5, fill: 'var(--color-high)' },
  { priority: 'MEDIUM', count: 3, fill: 'var(--color-medium)' },
  { priority: 'LOW', count: 2, fill: 'var(--color-low)' },
];

/* =========================
   ヘルパー：queryFnを手動実行して変換ロジックを検証
========================= */

// useApiSuspenseQueryに渡されたqueryFnを取り出して実行する
const runQueryFn = async () => {
  const callArg = useApiSuspenseQueryMock.mock.calls[0][0];
  return await callArg.queryFn();
};

/* =========================
   テスト本体
========================= */

describe('useTodoStats', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // デフォルト: 変換済みデータをそのまま返す
    useApiSuspenseQueryMock.mockReturnValue({
      data: expectedStatsData,
    });
  });

  /* --------------------
     queryKeyとqueryFnの設定
  -------------------- */

  describe('useApiSuspenseQueryへの設定', () => {
    it('正しいqueryKeyとqueryFnでuseApiSuspenseQueryを呼ぶ', () => {
      renderHook(() => useTodoStats());

      expect(useApiSuspenseQueryMock).toHaveBeenCalledWith(
        expect.objectContaining({
          queryKey: ['todos', 'stats'],
          queryFn: expect.any(Function),
        })
      );
    });

    it('dataをそのまま返す', () => {
      const { result } = renderHook(() => useTodoStats());

      expect(result.current.data).toEqual(expectedStatsData);
    });

    it('dataがundefinedのとき undefinedをそのまま返す', () => {
      useApiSuspenseQueryMock.mockReturnValue({ data: undefined });

      const { result } = renderHook(() => useTodoStats());

      expect(result.current.data).toBeUndefined();
    });
  });

  /* --------------------
     queryFn内の変換ロジック
     （useApiSuspenseQueryに渡すqueryFnを手動実行して検証）
  -------------------- */

  describe('queryFn内のデータ変換', () => {
    it('todoService.getTodoStatsを呼び、fillを付与して返す', async () => {
      mockGetTodoStats.mockResolvedValue(mockStatsApiResponse);

      renderHook(() => useTodoStats());

      const result = await runQueryFn();

      expect(mockGetTodoStats).toHaveBeenCalledTimes(1);
      expect(result).toEqual(expectedStatsData);
    });

    it('priorityが小文字に変換されてfillのCSS変数が生成される', async () => {
      mockGetTodoStats.mockResolvedValue(mockStatsApiResponse);

      renderHook(() => useTodoStats());

      const result = await runQueryFn();

      result.forEach((item: { fill: string }) => {
        // var(--color-xxx) 形式で小文字
        expect(item.fill).toMatch(/^var\(--color-[a-z]+\)$/);
      });
    });

    it('混合ケースのpriorityも小文字に変換される', async () => {
      mockGetTodoStats.mockResolvedValue({
        data: [
          { priority: 'High', count: 1 },
          { priority: 'MeDiUm', count: 2 },
          { priority: 'LoW', count: 3 },
        ],
        error: undefined,
      });

      renderHook(() => useTodoStats());

      const result = await runQueryFn();

      expect(result).toEqual([
        { priority: 'High', count: 1, fill: 'var(--color-high)' },
        { priority: 'MeDiUm', count: 2, fill: 'var(--color-medium)' },
        { priority: 'LoW', count: 3, fill: 'var(--color-low)' },
      ]);
    });

    it('元のpriorityとcountは変換後も保持される', async () => {
      mockGetTodoStats.mockResolvedValue(mockStatsApiResponse);

      renderHook(() => useTodoStats());

      const result = await runQueryFn();

      result.forEach((item: { priority: string; count: number }, index: number) => {
        expect(item.priority).toBe(mockStatsApiResponse.data[index].priority);
        expect(item.count).toBe(mockStatsApiResponse.data[index].count);
      });
    });

    it('各アイテムにpriority・count・fillが含まれる', async () => {
      mockGetTodoStats.mockResolvedValue(mockStatsApiResponse);

      renderHook(() => useTodoStats());

      const result = await runQueryFn();

      result.forEach((item: object) => {
        expect(item).toHaveProperty('priority');
        expect(item).toHaveProperty('count');
        expect(item).toHaveProperty('fill');
      });
    });

    it('data.dataがnullのとき 空配列として処理される', async () => {
      // openapi-fetchでdataがnullの場合
      mockGetTodoStats.mockResolvedValue({ data: null, error: undefined });

      renderHook(() => useTodoStats());

      const result = await runQueryFn();

      expect(result).toEqual([]);
    });

    it('priorityがnullのとき UNKNOWNにフォールバックされる', async () => {
      mockGetTodoStats.mockResolvedValue({
        data: [{ priority: null, count: 1 }],
        error: undefined,
      });

      renderHook(() => useTodoStats());

      const result = await runQueryFn();

      expect(result[0].priority).toBe('UNKNOWN');
      expect(result[0].fill).toBe('var(--color-unknown)');
    });

    it('countがnullのとき 0にフォールバックされる', async () => {
      mockGetTodoStats.mockResolvedValue({
        data: [{ priority: 'HIGH', count: null }],
        error: undefined,
      });

      renderHook(() => useTodoStats());

      const result = await runQueryFn();

      expect(result[0].count).toBe(0);
    });

    it('空配列のとき 空配列を返す', async () => {
      mockGetTodoStats.mockResolvedValue({ data: [], error: undefined });

      renderHook(() => useTodoStats());

      const result = await runQueryFn();

      expect(result).toEqual([]);
    });

    it('todoService.getTodoStatsがエラーをスローしたとき queryFnもスローする', async () => {
      mockGetTodoStats.mockRejectedValue(new Error('Stats API Error'));

      renderHook(() => useTodoStats());

      await expect(runQueryFn()).rejects.toThrow('Stats API Error');
    });
  });
});