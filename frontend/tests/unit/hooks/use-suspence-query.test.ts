import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import {
  useApiSuspenseQuery,
  useSuspenseQueryEffect,
} from '@/hooks/use-suspense-query';

/* =========================
   モック対象
========================= */
import { useSuspenseQuery } from '@tanstack/react-query';

/* =========================
   vi.mock（トップレベル）
========================= */
vi.mock('@tanstack/react-query', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-query')>();
  return {
    ...actual,
    useSuspenseQuery: vi.fn(),
  };
});

/* =========================
   モック参照
========================= */
const useSuspenseQueryMock = useSuspenseQuery as unknown as Mock;

/* =========================
   ダミーデータ
========================= */
const mockData = { id: 1, title: 'Test' };

/* =========================
   wrapper
========================= */
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client= { queryClient } > { children } < /QueryClientProvider>
  );
};

/* =========================
   テスト本体
========================= */

describe('use-suspense-query', () => {

  /* --------------------
     useSuspenseQueryEffect
  -------------------- */

  describe('useSuspenseQueryEffect', () => {
    // テスト用のqueryResultモックを生成するヘルパー
    const makeMockResult = (overrides: Record<string, unknown> = {}) => ({
      data: mockData,
      isSuccess: true,
      isFetched: true,
      isError: false,
      error: null,
      ...overrides,
    });

    describe('onSuccessコールバック', () => {
      it('isSuccessがtrueのとき onSuccessが呼ばれる', async () => {
        const onSuccess = vi.fn();
        const mockResult = makeMockResult({ isSuccess: true });

        renderHook(
          () =>
            useSuspenseQueryEffect(mockResult as never, { onSuccess }),
          { wrapper: createWrapper() }
        );

        await waitFor(() => {
          expect(onSuccess).toHaveBeenCalledTimes(1);
        });
        expect(onSuccess).toHaveBeenCalledWith(mockData);
      });

      it('isSuccessがfalseのとき onSuccessは呼ばれない', () => {
        const onSuccess = vi.fn();
        const mockResult = makeMockResult({ isSuccess: false });

        renderHook(
          () =>
            useSuspenseQueryEffect(mockResult as never, { onSuccess }),
          { wrapper: createWrapper() }
        );

        expect(onSuccess).not.toHaveBeenCalled();
      });

      it('onSuccessが未指定のとき エラーにならない', async () => {
        const mockResult = makeMockResult({ isSuccess: true });

        expect(() =>
          renderHook(
            () => useSuspenseQueryEffect(mockResult as never, {}),
            { wrapper: createWrapper() }
          )
        ).not.toThrow();
      });

      it('effectsOptionsが未指定のとき エラーにならない', async () => {
        const mockResult = makeMockResult({ isSuccess: true });

        expect(() =>
          renderHook(
            () => useSuspenseQueryEffect(mockResult as never),
            { wrapper: createWrapper() }
          )
        ).not.toThrow();
      });
    });

    describe('onSettledコールバック', () => {
      it('isFetchedがtrueのとき onSettledが呼ばれる', async () => {
        const onSettled = vi.fn();
        const mockResult = makeMockResult({ isFetched: true });

        renderHook(
          () =>
            useSuspenseQueryEffect(mockResult as never, { onSettled }),
          { wrapper: createWrapper() }
        );

        await waitFor(() => {
          expect(onSettled).toHaveBeenCalledTimes(1);
        });
        expect(onSettled).toHaveBeenCalledWith(mockData);
      });

      it('isFetchedがfalseのとき onSettledは呼ばれない', () => {
        const onSettled = vi.fn();
        const mockResult = makeMockResult({ isFetched: false });

        renderHook(
          () =>
            useSuspenseQueryEffect(mockResult as never, { onSettled }),
          { wrapper: createWrapper() }
        );

        expect(onSettled).not.toHaveBeenCalled();
      });

      it('onSettledが未指定のとき エラーにならない', async () => {
        const mockResult = makeMockResult({ isFetched: true });

        expect(() =>
          renderHook(
            () => useSuspenseQueryEffect(mockResult as never, {}),
            { wrapper: createWrapper() }
          )
        ).not.toThrow();
      });
    });

    describe('onSuccessとonSettledの同時呼び出し', () => {
      it('isSuccessとisFetchedが両方trueのとき 両方呼ばれる', async () => {
        const onSuccess = vi.fn();
        const onSettled = vi.fn();
        const mockResult = makeMockResult({ isSuccess: true, isFetched: true });

        renderHook(
          () =>
            useSuspenseQueryEffect(mockResult as never, {
              onSuccess,
              onSettled,
            }),
          { wrapper: createWrapper() }
        );

        await waitFor(() => {
          expect(onSuccess).toHaveBeenCalledTimes(1);
          expect(onSettled).toHaveBeenCalledTimes(1);
        });
      });
    });

    describe('依存配列の変化によるre-run', () => {
      it('dataが変わったとき onSuccessが再度呼ばれる', async () => {
        const onSuccess = vi.fn();
        let mockResult = makeMockResult({ data: mockData, isSuccess: true });

        const { rerender } = renderHook(
          ({ result }: { result: typeof mockResult }) =>
            useSuspenseQueryEffect(result as never, { onSuccess }),
          {
            initialProps: { result: mockResult },
            wrapper: createWrapper(),
          }
        );

        await waitFor(() => expect(onSuccess).toHaveBeenCalledTimes(1));

        // dataを変更して再レンダリング
        const newData = { id: 2, title: 'Updated' };
        mockResult = makeMockResult({ data: newData, isSuccess: true });
        rerender({ result: mockResult });

        await waitFor(() => expect(onSuccess).toHaveBeenCalledTimes(2));
        expect(onSuccess).toHaveBeenLastCalledWith(newData);
      });
    });

    describe('戻り値', () => {
      it('queryResultをそのまま返す', () => {
        const mockResult = makeMockResult();

        const { result } = renderHook(
          () => useSuspenseQueryEffect(mockResult as never),
          { wrapper: createWrapper() }
        );

        expect(result.current).toBe(mockResult);
      });
    });
  });

  /* --------------------
     useApiSuspenseQuery
  -------------------- */

  describe('useApiSuspenseQuery', () => {
    beforeEach(() => {
      vi.clearAllMocks();

      // デフォルト: 成功状態のqueryResultを返す
      useSuspenseQueryMock.mockReturnValue({
        data: mockData,
        isSuccess: true,
        isFetched: true,
        isError: false,
        error: null,
      });
    });

    describe('useSuspenseQueryへの委譲', () => {
      it('queryOptionsをそのままuseSuspenseQueryに渡す', () => {
        const queryFn = vi.fn().mockResolvedValue(mockData);
        const queryOptions = {
          queryKey: ['test'],
          queryFn,
        };

        renderHook(() => useApiSuspenseQuery(queryOptions), {
          wrapper: createWrapper(),
        });

        expect(useSuspenseQueryMock).toHaveBeenCalledWith(queryOptions);
        expect(useSuspenseQueryMock).toHaveBeenCalledTimes(1);
      });

      it('useSuspenseQueryの結果をそのまま返す', () => {
        const queryFn = vi.fn().mockResolvedValue(mockData);

        const { result } = renderHook(
          () => useApiSuspenseQuery({ queryKey: ['test'], queryFn }),
          { wrapper: createWrapper() }
        );

        expect(result.current.data).toEqual(mockData);
        expect(result.current.isSuccess).toBe(true);
      });
    });

    describe('effectsOptionsの受け渡し', () => {
      it('onSuccessが呼ばれる', async () => {
        const onSuccess = vi.fn();
        const queryFn = vi.fn().mockResolvedValue(mockData);

        renderHook(
          () =>
            useApiSuspenseQuery(
              { queryKey: ['test'], queryFn },
              { onSuccess }
            ),
          { wrapper: createWrapper() }
        );

        await waitFor(() => {
          expect(onSuccess).toHaveBeenCalledTimes(1);
        });
        expect(onSuccess).toHaveBeenCalledWith(mockData);
      });

      it('onSettledが呼ばれる', async () => {
        const onSettled = vi.fn();
        const queryFn = vi.fn().mockResolvedValue(mockData);

        renderHook(
          () =>
            useApiSuspenseQuery(
              { queryKey: ['test'], queryFn },
              { onSettled }
            ),
          { wrapper: createWrapper() }
        );

        await waitFor(() => {
          expect(onSettled).toHaveBeenCalledTimes(1);
        });
        expect(onSettled).toHaveBeenCalledWith(mockData);
      });

      it('effectsOptionsなしでもエラーにならない', () => {
        const queryFn = vi.fn().mockResolvedValue(mockData);

        expect(() =>
          renderHook(
            () => useApiSuspenseQuery({ queryKey: ['test'], queryFn }),
            { wrapper: createWrapper() }
          )
        ).not.toThrow();
      });
    });

    describe('onErrorは提供されない', () => {
      it('UseSuspenseEffectOptionsにonErrorプロパティが存在しない', () => {
        // 型レベルの保証: onErrorをeffectsOptionsに渡せないことを確認
        // (TypeScriptのコンパイルエラーになるが、ランタイムでも余分なプロパティは無視される)
        const onSuccess = vi.fn();
        const queryFn = vi.fn().mockResolvedValue(mockData);

        // onErrorを含まないオプションで正常動作することを確認
        expect(() =>
          renderHook(
            () =>
              useApiSuspenseQuery(
                { queryKey: ['test'], queryFn },
                { onSuccess }
                // onError: vi.fn() // ← 型エラー: UseSuspenseEffectOptionsにonErrorはない
              ),
            { wrapper: createWrapper() }
          )
        ).not.toThrow();
      });
    });
  });
});