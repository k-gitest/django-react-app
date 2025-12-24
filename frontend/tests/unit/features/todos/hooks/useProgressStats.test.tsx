import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useProgressStats } from '@/features/todos/hooks/useProgressStats';
import { todoService } from '@/features/todos/services/todo-service';
import type { ReactNode } from 'react';

// モック
vi.mock('@/features/todos/services/todo-service', () => ({
  todoService: {
    getProgressStats: vi.fn(),
  },
}));

// コンソールログを抑制
vi.spyOn(console, 'error').mockImplementation(() => {});
vi.spyOn(console, 'warn').mockImplementation(() => {});
vi.spyOn(console, 'log').mockImplementation(() => {});

describe('useProgressStats', () => {
  let queryClient: QueryClient;

  // モックデータ（サービスからのレスポンス）
  const mockProgressResponse = {
    range_0_20: 5,
    range_21_40: 3,
    range_41_60: 7,
    range_61_80: 4,
    range_81_100: 2,
  };

  // 期待される変換後のデータ
  const expectedProgressData = [
    { range: '0-20%', count: 5 },
    { range: '21-40%', count: 3 },
    { range: '41-60%', count: 7 },
    { range: '61-80%', count: 4 },
    { range: '81-100%', count: 2 },
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

  describe('進捗統計データ取得と変換', () => {
    it('進捗統計データを正常に取得し、変換する', async () => {
      vi.mocked(todoService.getProgressStats).mockResolvedValue(
        mockProgressResponse
      );

      const { result } = renderHook(() => useProgressStats(), {
        wrapper: createWrapper(),
      });

      // 初期状態: ローディング中
      expect(result.current.isLoading).toBe(true);

      // データ取得完了を待つ
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // サービスが正しく呼ばれたことを確認
      expect(todoService.getProgressStats).toHaveBeenCalledTimes(1);

      // データが正しく変換されていることを確認
      expect(result.current.data).toEqual(expectedProgressData);
      expect(result.current.isSuccess).toBe(true);
    });

    it('すべての進捗範囲が含まれている', async () => {
      vi.mocked(todoService.getProgressStats).mockResolvedValue(
        mockProgressResponse
      );

      const { result } = renderHook(() => useProgressStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // 5つの進捗範囲が含まれていることを確認
      expect(result.current.data).toHaveLength(5);

      // 各範囲が正しく存在することを確認
      const ranges = result.current.data?.map(item => item.range);
      expect(ranges).toEqual([
        '0-20%',
        '21-40%',
        '41-60%',
        '61-80%',
        '81-100%',
      ]);
    });

    it('カウントが0の場合も正しく処理される', async () => {
      const zeroCountResponse = {
        range_0_20: 0,
        range_21_40: 0,
        range_41_60: 0,
        range_61_80: 0,
        range_81_100: 0,
      };

      vi.mocked(todoService.getProgressStats).mockResolvedValue(
        zeroCountResponse
      );

      const { result } = renderHook(() => useProgressStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // すべてのカウントが0であることを確認
      result.current.data?.forEach((item) => {
        expect(item.count).toBe(0);
      });

      // データの長さは5のまま
      expect(result.current.data).toHaveLength(5);
    });

    it('大きな数値も正しく処理される', async () => {
      const largeCountResponse = {
        range_0_20: 1000,
        range_21_40: 500,
        range_41_60: 250,
        range_61_80: 100,
        range_81_100: 50,
      };

      vi.mocked(todoService.getProgressStats).mockResolvedValue(
        largeCountResponse
      );

      const { result } = renderHook(() => useProgressStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // 大きな数値が正しく変換されていることを確認
      expect(result.current.data).toEqual([
        { range: '0-20%', count: 1000 },
        { range: '21-40%', count: 500 },
        { range: '41-60%', count: 250 },
        { range: '61-80%', count: 100 },
        { range: '81-100%', count: 50 },
      ]);
    });

    it('エラー時にisErrorがtrueになる', async () => {
      vi.mocked(todoService.getProgressStats).mockRejectedValue(
        new Error('Service Error')
      );

      const { result } = renderHook(() => useProgressStats(), {
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
      vi.mocked(todoService.getProgressStats).mockRejectedValue(networkError);

      const { result } = renderHook(() => useProgressStats(), {
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
      vi.mocked(todoService.getProgressStats).mockResolvedValue(
        mockProgressResponse
      );

      const { result } = renderHook(() => useProgressStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // キャッシュが正しいキーで保存されているか確認
      const cachedData = queryClient.getQueryData(['todos', 'progress-stats']);
      expect(cachedData).toEqual(expectedProgressData);
    });

    it('キャッシュが機能することを確認', async () => {
      vi.mocked(todoService.getProgressStats).mockResolvedValue(
        mockProgressResponse
      );

      const { result } = renderHook(() => useProgressStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // サービスが1回呼ばれたことを確認
      expect(todoService.getProgressStats).toHaveBeenCalledTimes(1);

      // データが正しいことを確認
      expect(result.current.data).toEqual(expectedProgressData);

      // キャッシュに保存されていることを確認
      const cachedData = queryClient.getQueryData(['todos', 'progress-stats']);
      expect(cachedData).toEqual(expectedProgressData);
    });
  });

  describe('データ変換', () => {
    it('レスポンスのフィールド名が正しくマッピングされている', async () => {
      vi.mocked(todoService.getProgressStats).mockResolvedValue(
        mockProgressResponse
      );

      const { result } = renderHook(() => useProgressStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // 各フィールドが正しくマッピングされていることを確認
      expect(result.current.data?.[0]).toEqual({
        range: '0-20%',
        count: mockProgressResponse.range_0_20,
      });
      expect(result.current.data?.[1]).toEqual({
        range: '21-40%',
        count: mockProgressResponse.range_21_40,
      });
      expect(result.current.data?.[2]).toEqual({
        range: '41-60%',
        count: mockProgressResponse.range_41_60,
      });
      expect(result.current.data?.[3]).toEqual({
        range: '61-80%',
        count: mockProgressResponse.range_61_80,
      });
      expect(result.current.data?.[4]).toEqual({
        range: '81-100%',
        count: mockProgressResponse.range_81_100,
      });
    });

    it('rangeフォーマットが正しい', async () => {
      vi.mocked(todoService.getProgressStats).mockResolvedValue(
        mockProgressResponse
      );

      const { result } = renderHook(() => useProgressStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // すべてのrangeが%を含むフォーマットであることを確認
      result.current.data?.forEach((item) => {
        expect(item.range).toMatch(/^\d+-\d+%$/);
      });
    });

    it('配列の順序が保持されている', async () => {
      vi.mocked(todoService.getProgressStats).mockResolvedValue(
        mockProgressResponse
      );

      const { result } = renderHook(() => useProgressStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // 配列が昇順（0-20% → 81-100%）であることを確認
      const ranges = result.current.data?.map(item => item.range);
      expect(ranges).toEqual([
        '0-20%',
        '21-40%',
        '41-60%',
        '61-80%',
        '81-100%',
      ]);
    });

    it('すべての必須プロパティが含まれている', async () => {
      vi.mocked(todoService.getProgressStats).mockResolvedValue(
        mockProgressResponse
      );

      const { result } = renderHook(() => useProgressStats(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // 各アイテムが必須プロパティを持つことを確認
      result.current.data?.forEach((item) => {
        expect(item).toHaveProperty('range');
        expect(item).toHaveProperty('count');
      });
    });
  });
});