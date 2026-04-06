import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { useRelayLazyLoadQuery } from '@/hooks/use-relay-lazy-load-query';

/* =========================
   モック対象
========================= */
import { useLazyLoadQuery } from 'react-relay';

/* =========================
   vi.mock（トップレベル）
========================= */
vi.mock('react-relay', () => ({
  useLazyLoadQuery: vi.fn(),
}));

/* =========================
   モック参照
========================= */
const useLazyLoadQueryMock = useLazyLoadQuery as unknown as Mock;

/* =========================
   ダミーデータ
========================= */

// GraphQLTaggedNode の最小スタブ
const mockQuery = { kind: 'Request', params: {} } as never;

const mockVariables = { id: '1' };

const mockData = {
  user: { id: '1', name: 'Alice' },
};

const mockDataUpdated = {
  user: { id: '1', name: 'Alice Updated' },
};

/* =========================
   テスト本体
========================= */

describe('useRelayLazyLoadQuery', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useLazyLoadQueryMock.mockReturnValue(mockData);
  });

  /* --------------------
     useLazyLoadQueryへの委譲
  -------------------- */

  describe('useLazyLoadQueryへの委譲', () => {
    it('query・variables・fetchPolicyをuseLazyLoadQueryに渡す', () => {
      renderHook(() =>
        useRelayLazyLoadQuery(mockQuery, mockVariables, {
          fetchPolicy: 'network-only',
        })
      );

      expect(useLazyLoadQueryMock).toHaveBeenCalledWith(
        mockQuery,
        mockVariables,
        { fetchPolicy: 'network-only' }
      );
    });

    it('fetchPolicyが未指定のとき store-or-network をデフォルトで渡す', () => {
      renderHook(() =>
        useRelayLazyLoadQuery(mockQuery, mockVariables)
      );

      expect(useLazyLoadQueryMock).toHaveBeenCalledWith(
        mockQuery,
        mockVariables,
        { fetchPolicy: 'store-or-network' }
      );
    });

    it('fetchPolicyが未指定のときも store-or-network になる（options自体がundefined）', () => {
      renderHook(() =>
        useRelayLazyLoadQuery(mockQuery, mockVariables, undefined)
      );

      expect(useLazyLoadQueryMock).toHaveBeenCalledWith(
        mockQuery,
        mockVariables,
        { fetchPolicy: 'store-or-network' }
      );
    });

    it('useLazyLoadQueryのdataをそのまま返す', () => {
      const { result } = renderHook(() =>
        useRelayLazyLoadQuery(mockQuery, mockVariables)
      );

      expect(result.current).toEqual(mockData);
    });
  });

  /* --------------------
     onSuccessコールバック
  -------------------- */

  describe('onSuccessコールバック', () => {
    it('dataがある場合 onSuccessが呼ばれる', () => {
      const onSuccess = vi.fn();

      renderHook(() =>
        useRelayLazyLoadQuery(mockQuery, mockVariables, { onSuccess })
      );

      expect(onSuccess).toHaveBeenCalledTimes(1);
      expect(onSuccess).toHaveBeenCalledWith(mockData);
    });

    it('dataがnullのとき onSuccessは呼ばれない', () => {
      useLazyLoadQueryMock.mockReturnValue(null);
      const onSuccess = vi.fn();

      renderHook(() =>
        useRelayLazyLoadQuery(mockQuery, mockVariables, { onSuccess })
      );

      expect(onSuccess).not.toHaveBeenCalled();
    });

    it('dataがundefinedのとき onSuccessは呼ばれない', () => {
      useLazyLoadQueryMock.mockReturnValue(undefined);
      const onSuccess = vi.fn();

      renderHook(() =>
        useRelayLazyLoadQuery(mockQuery, mockVariables, { onSuccess })
      );

      expect(onSuccess).not.toHaveBeenCalled();
    });

    it('onSuccessが未指定のとき エラーにならない', () => {
      expect(() =>
        renderHook(() =>
          useRelayLazyLoadQuery(mockQuery, mockVariables)
        )
      ).not.toThrow();
    });

    it('dataが更新されたとき onSuccessが再度呼ばれる', () => {
      const onSuccess = vi.fn();
      useLazyLoadQueryMock.mockReturnValue(mockData);

      const { rerender } = renderHook(() =>
        useRelayLazyLoadQuery(mockQuery, mockVariables, { onSuccess })
      );

      expect(onSuccess).toHaveBeenCalledTimes(1);

      // data が変わったことをシミュレート
      useLazyLoadQueryMock.mockReturnValue(mockDataUpdated);
      rerender();

      expect(onSuccess).toHaveBeenCalledTimes(2);
      expect(onSuccess).toHaveBeenLastCalledWith(mockDataUpdated);
    });

    it('dataが変わらなければ onSuccessは追加で呼ばれない', () => {
      const onSuccess = vi.fn();

      const { rerender } = renderHook(() =>
        useRelayLazyLoadQuery(mockQuery, mockVariables, { onSuccess })
      );

      expect(onSuccess).toHaveBeenCalledTimes(1);

      // 同じdataで再レンダリング（参照同一）
      rerender();

      expect(onSuccess).toHaveBeenCalledTimes(1);
    });
  });

  /* --------------------
     onSuccessRefによるcallback安定化
     （refで管理しているため、最新のcallbackが常に呼ばれる）
  -------------------- */

  describe('onSuccessRefによるcallback安定化', () => {
    it('onSuccessが差し替わっても最新のcallbackが呼ばれる', () => {
      const onSuccess1 = vi.fn();
      const onSuccess2 = vi.fn();

      // 初回: onSuccess1
      const { rerender } = renderHook(
        ({ cb }: { cb: Mock }) =>
          useRelayLazyLoadQuery(mockQuery, mockVariables, { onSuccess: cb }),
        { initialProps: { cb: onSuccess1 } }
      );

      expect(onSuccess1).toHaveBeenCalledTimes(1);

      // dataを更新してonSuccess2に差し替え
      useLazyLoadQueryMock.mockReturnValue(mockDataUpdated);
      rerender({ cb: onSuccess2 });

      // 古いonSuccess1ではなく新しいonSuccess2が呼ばれる
      expect(onSuccess2).toHaveBeenCalledTimes(1);
      expect(onSuccess2).toHaveBeenCalledWith(mockDataUpdated);
    });

    it('onSuccessが差し替わってもdata変化なければ追加で呼ばれない', () => {
      const onSuccess1 = vi.fn();
      const onSuccess2 = vi.fn();

      const { rerender } = renderHook(
        ({ cb }: { cb: Mock }) =>
          useRelayLazyLoadQuery(mockQuery, mockVariables, { onSuccess: cb }),
        { initialProps: { cb: onSuccess1 } }
      );

      expect(onSuccess1).toHaveBeenCalledTimes(1);

      // dataは同じまま、callbackだけ差し替え
      rerender({ cb: onSuccess2 });

      // dataが変化していないのでどちらも追加で呼ばれない
      expect(onSuccess1).toHaveBeenCalledTimes(1);
      expect(onSuccess2).not.toHaveBeenCalled();
    });
  });

  /* --------------------
     fetchPolicyの各値
  -------------------- */

  describe('fetchPolicyの各値', () => {
    it.each([
      'store-or-network',
      'store-and-network',
      'network-only',
      'store-only',
    ] as const)(
      'fetchPolicy="%s" がそのまま渡される',
      (fetchPolicy) => {
        renderHook(() =>
          useRelayLazyLoadQuery(mockQuery, mockVariables, { fetchPolicy })
        );

        expect(useLazyLoadQueryMock).toHaveBeenCalledWith(
          mockQuery,
          mockVariables,
          { fetchPolicy }
        );
      }
    );
  });

  /* --------------------
     戻り値
  -------------------- */

  describe('戻り値', () => {
    it('useLazyLoadQueryのdataをそのまま返す（参照同一）', () => {
      const dataRef = { user: { id: '99', name: 'Bob' } };
      useLazyLoadQueryMock.mockReturnValue(dataRef);

      const { result } = renderHook(() =>
        useRelayLazyLoadQuery(mockQuery, mockVariables)
      );

      expect(result.current).toBe(dataRef);
    });

    it('dataがnullのとき nullを返す', () => {
      useLazyLoadQueryMock.mockReturnValue(null);

      const { result } = renderHook(() =>
        useRelayLazyLoadQuery(mockQuery, mockVariables)
      );

      expect(result.current).toBeNull();
    });
  });
});