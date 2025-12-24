import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useTodoStats } from '@/features/todos/hooks/useTodoStats';
import { todoService } from '@/features/todos/services/todo-service';
import type { ReactNode } from 'react';

// モック
vi.mock('@/features/todos/services/todo-service', () => ({
  todoService: {
    getTodoStats: vi.fn(),
  },
}));

// コンソールログを抑制
vi.spyOn(console, 'error').mockImplementation(() => {});
vi.spyOn(console, 'warn').mockImplementation(() => {});
vi.spyOn(console, 'log').mockImplementation(() => {});

describe('useTodoStats', () => {
  let queryClient: QueryClient;

  // モックデータ（サービスからのレスポンス）
  const mockStatsResponse = [
    { priority: 'HIGH', count: 5 },
    { priority: 'MEDIUM', count: 3 },
    { priority: 'LOW', count: 2 },
  ];

  // 期待される変換後のデータ
  const expectedStatsData = [
    { priority: 'HIGH', count: 5, fill: 'var(--color-high)' },
    { priority: 'MEDIUM', count: 3, fill: 'var(--color-medium)' },
    { priority: 'LOW', count: 2, fill: 'var(--color-low)' },
  ];

  beforeEach(() => {
    // 各テストで新しいQueryClientを作成
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    // モックをクリア
    vi.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
    vi.restoreAllMocks();
  });

  // Wrapper コンポーネント
  const createWrapper = () => {
    return ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };

  describe('統計データ取得と変換', () => {
    it('統計データを正常に取得し、変換する', async () => {
      vi.mocked(todoService.getTodoStats).mockResolvedValue(mockStatsResponse);

      const { result } = renderHook(() => useTodoStats(), {
        wrapper: createWrapper(),
      });

      // 初期状態: ローディング中
      expect(result.current.isLoading).toBe(true);

      // データ取得完了を待つ
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // サービスが正しく呼ばれたことを確認
      expect(todoService.getTodoStats).toHaveBeenCalledTimes(1);

      // データが正しく変換されていることを確認
      expect(result.current.data).toEqual(expectedStatsData);
      expect(result.current.isSuccess).toBe(true);
    });

    it('優先度の大文字小文字が正しく変換される', async () => {
      // 大文字の優先度データ
      const upperCaseResponse = [
        { priority: 'HIGH', count: 1 },
        { priority: 'MEDIUM', count: 2 },
      ];

      vi.mocked(todoService.getTodoStats).mockResolvedValue(upperCaseResponse);

      const { result } = renderHook(() => useTodoStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // fillプロパティが小文字に変換されていることを確認
      expect(result.current.data).toEqual([
        { priority: 'HIGH', count: 1, fill: 'var(--color-high)' },
        { priority: 'MEDIUM', count: 2, fill: 'var(--color-medium)' },
      ]);
    });

    it('空の配列が返された場合も正しく処理される', async () => {
      vi.mocked(todoService.getTodoStats).mockResolvedValue([]);

      const { result } = renderHook(() => useTodoStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // 空配列が返されることを確認
      expect(result.current.data).toEqual([]);
    });

    it('エラー時にisErrorがtrueになる', async () => {
      vi.mocked(todoService.getTodoStats).mockRejectedValue(
        new Error('Service Error')
      );

      const { result } = renderHook(() => useTodoStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      // エラー状態を確認
      expect(result.current.data).toBeUndefined();
      expect(result.current.error).toBeDefined();
    });

    it('ネットワークエラーが発生した場合', async () => {
      const networkError = new Error('Network Error');
      vi.mocked(todoService.getTodoStats).mockRejectedValue(networkError);

      const { result } = renderHook(() => useTodoStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toBe(networkError);
    });
  });

  describe('queryKeyとキャッシュ', () => {
    it('正しいqueryKeyが使用されている', async () => {
      vi.mocked(todoService.getTodoStats).mockResolvedValue(mockStatsResponse);

      const { result } = renderHook(() => useTodoStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // キャッシュが正しいキーで保存されているか確認
      const cachedData = queryClient.getQueryData(['todos', 'stats']);
      expect(cachedData).toEqual(expectedStatsData);
    });

    it('キャッシュが機能することを確認', async () => {
      vi.mocked(todoService.getTodoStats).mockResolvedValue(mockStatsResponse);

      // 1回目のレンダリング
      const { result: result1 } = renderHook(() => useTodoStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result1.current.isSuccess).toBe(true);
      });

      // サービスが1回呼ばれたことを確認
      expect(todoService.getTodoStats).toHaveBeenCalledTimes(1);

      // データが正しいことを確認
      expect(result1.current.data).toEqual(expectedStatsData);

      // キャッシュに保存されていることを確認
      const cachedData = queryClient.getQueryData(['todos', 'stats']);
      expect(cachedData).toEqual(expectedStatsData);
    });
  });

  describe('データ変換', () => {
    it('fillプロパティが正しいCSS変数フォーマットになっている', async () => {
      vi.mocked(todoService.getTodoStats).mockResolvedValue(mockStatsResponse);

      const { result } = renderHook(() => useTodoStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // 各アイテムのfillが正しいフォーマットか確認
      result.current.data?.forEach((item) => {
        expect(item.fill).toMatch(/^var\(--color-[a-z]+\)$/);
      });
    });

    it('元のpriorityとcountが保持されている', async () => {
      vi.mocked(todoService.getTodoStats).mockResolvedValue(mockStatsResponse);

      const { result } = renderHook(() => useTodoStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // 元のデータが保持されているか確認
      result.current.data?.forEach((item, index) => {
        expect(item.priority).toBe(mockStatsResponse[index].priority);
        expect(item.count).toBe(mockStatsResponse[index].count);
      });
    });

    it('混合ケースの優先度も正しく変換される', async () => {
      const mixedCaseResponse = [
        { priority: 'High', count: 1 },
        { priority: 'MeDiUm', count: 2 },
        { priority: 'LoW', count: 3 },
      ];

      vi.mocked(todoService.getTodoStats).mockResolvedValue(mixedCaseResponse);

      const { result } = renderHook(() => useTodoStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // すべてのfillが小文字に変換されていることを確認
      expect(result.current.data).toEqual([
        { priority: 'High', count: 1, fill: 'var(--color-high)' },
        { priority: 'MeDiUm', count: 2, fill: 'var(--color-medium)' },
        { priority: 'LoW', count: 3, fill: 'var(--color-low)' },
      ]);
    });

    it('すべての必須プロパティが含まれている', async () => {
      vi.mocked(todoService.getTodoStats).mockResolvedValue(mockStatsResponse);

      const { result } = renderHook(() => useTodoStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // 各アイテムが必須プロパティを持つことを確認
      result.current.data?.forEach((item) => {
        expect(item).toHaveProperty('priority');
        expect(item).toHaveProperty('count');
        expect(item).toHaveProperty('fill');
      });
    });
  });
});