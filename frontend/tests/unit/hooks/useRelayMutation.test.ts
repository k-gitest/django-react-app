import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { useRelayMutation } from '@/hooks/use-relay-mutation';

/* =========================
   モック対象
========================= */
import { useMutation } from 'react-relay';
import { errorHandler } from '@/errors/error-handler';

/* =========================
   vi.mock（トップレベル）
========================= */
vi.mock('react-relay', () => ({
  useMutation: vi.fn(),
}));

vi.mock('@/errors/error-handler', () => ({
  errorHandler: vi.fn(),
}));

/* =========================
   モック参照
========================= */
const useMutationMock = useMutation as unknown as Mock;
const errorHandlerMock = errorHandler as unknown as Mock;

/* =========================
   ダミーデータ
========================= */
const mockMutation = { kind: 'Request', params: {} } as never;

const mockResponse = { createUser: { id: '1', name: 'Alice' } };

/* =========================
   ヘルパー：commitモックのセットアップ
========================= */

// commit呼び出しをキャプチャして onCompleted / onError を手動トリガーできるようにする
const setupCommitMock = () => {
  const commitMock = vi.fn();
  useMutationMock.mockReturnValue([commitMock, false]);
  return commitMock;
};

const setupCommitMockInFlight = () => {
  const commitMock = vi.fn();
  useMutationMock.mockReturnValue([commitMock, true]);
  return commitMock;
};

// commit呼び出しから onCompleted / onError を取り出す
const getCommitCallbacks = (commitMock: Mock) => {
  const callArg = commitMock.mock.calls[0][0];
  return {
    onCompleted: callArg.onCompleted as (
      response: unknown,
      errors: unknown
    ) => void,
    onError: callArg.onError as (error: Error) => void,
    passedConfig: callArg,
  };
};

/* =========================
   テスト本体
========================= */

describe('useRelayMutation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupCommitMock();
  });

  /* --------------------
     戻り値の構造
  -------------------- */

  describe('戻り値の構造', () => {
    it('execute関数とisInFlightを返す', () => {
      const { result } = renderHook(() => useRelayMutation(mockMutation));

      expect(typeof result.current.execute).toBe('function');
      expect(result.current.isInFlight).toBe(false);
    });

    it('isInFlightがtrueのとき trueを返す', () => {
      setupCommitMockInFlight();

      const { result } = renderHook(() => useRelayMutation(mockMutation));

      expect(result.current.isInFlight).toBe(true);
    });

    it('mutationをuseMutationに渡す', () => {
      renderHook(() => useRelayMutation(mockMutation));

      expect(useMutationMock).toHaveBeenCalledWith(mockMutation);
    });
  });

  /* --------------------
     execute: 正常系
  -------------------- */

  describe('execute: 正常系', () => {
    it('Promiseを返す', () => {
      const commitMock = setupCommitMock();
      // onCompletedを呼ばせないためcommitは何もしないまま
      commitMock.mockImplementation(() => { });

      const { result } = renderHook(() => useRelayMutation(mockMutation));

      const promise = result.current.execute({ variables: {} });
      expect(promise).toBeInstanceOf(Promise);
    });

    it('onCompletedが呼ばれたとき resolveされる', async () => {
      const commitMock = setupCommitMock();
      commitMock.mockImplementation((config: { onCompleted: (res: unknown, errors: null) => void }) => {
        config.onCompleted(mockResponse, null);
      });

      const { result } = renderHook(() => useRelayMutation(mockMutation));

      const response = await act(async () =>
        result.current.execute({ variables: {} })
      );

      expect(response).toEqual(mockResponse);
    });

    it('onCompletedで呼び出し元のコールバックも実行される', async () => {
      const commitMock = setupCommitMock();
      const errors = null;
      commitMock.mockImplementation((config: { onCompleted: (res: unknown, errors: null) => void }) => {
        config.onCompleted(mockResponse, errors);
      });

      const callerOnCompleted = vi.fn();
      const { result } = renderHook(() => useRelayMutation(mockMutation));

      await act(async () =>
        result.current.execute({
          variables: {},
          onCompleted: callerOnCompleted,
        })
      );

      expect(callerOnCompleted).toHaveBeenCalledTimes(1);
      expect(callerOnCompleted).toHaveBeenCalledWith(mockResponse, errors);
    });

    it('呼び出し元のonCompletedが未指定でもエラーにならない', async () => {
      const commitMock = setupCommitMock();
      commitMock.mockImplementation((config: { onCompleted: (res: unknown, errors: null) => void }) => {
        config.onCompleted(mockResponse, null);
      });

      const { result } = renderHook(() => useRelayMutation(mockMutation));

      await expect(
        act(async () => result.current.execute({ variables: {} }))
      ).resolves.toEqual(mockResponse);
    });
  });

  /* --------------------
     execute: エラー系
  -------------------- */

  describe('execute: エラー系', () => {
    it('onErrorが呼ばれたとき rejectされる', async () => {
      const commitMock = setupCommitMock();
      const networkError = new Error('Network Error');
      commitMock.mockImplementation((config: { onError: (err: Error) => void }) => {
        config.onError(networkError);
      });

      const { result } = renderHook(() => useRelayMutation(mockMutation));

      await expect(
        act(async () => result.current.execute({ variables: {} }))
      ).rejects.toThrow('Network Error');
    });

    it('onErrorが呼ばれたとき errorHandlerが実行される', async () => {
      const commitMock = setupCommitMock();
      const networkError = new Error('Network Error');
      commitMock.mockImplementation((config: { onError: (err: Error) => void }) => {
        config.onError(networkError);
      });

      const { result } = renderHook(() => useRelayMutation(mockMutation));

      await act(async () =>
        result.current.execute({ variables: {} }).catch(() => { })
      );

      expect(errorHandlerMock).toHaveBeenCalledTimes(1);
      expect(errorHandlerMock).toHaveBeenCalledWith(networkError, 'Mutation');
    });

    it('errorContextが指定されたとき errorHandlerにerrorContextが渡される', async () => {
      const commitMock = setupCommitMock();
      const networkError = new Error('Network Error');
      commitMock.mockImplementation((config: { onError: (err: Error) => void }) => {
        config.onError(networkError);
      });

      const { result } = renderHook(() => useRelayMutation(mockMutation));

      await act(async () =>
        result.current
          .execute({ variables: {}, errorContext: 'CreateUser' })
          .catch(() => { })
      );

      expect(errorHandlerMock).toHaveBeenCalledWith(networkError, 'CreateUser');
    });

    it('errorContextが未指定のとき "Mutation" をデフォルトとして渡す', async () => {
      const commitMock = setupCommitMock();
      const networkError = new Error('Network Error');
      commitMock.mockImplementation((config: { onError: (err: Error) => void }) => {
        config.onError(networkError);
      });

      const { result } = renderHook(() => useRelayMutation(mockMutation));

      await act(async () =>
        result.current.execute({ variables: {} }).catch(() => { })
      );

      expect(errorHandlerMock).toHaveBeenCalledWith(networkError, 'Mutation');
    });

    it('呼び出し元のonErrorコールバックも実行される', async () => {
      const commitMock = setupCommitMock();
      const networkError = new Error('Network Error');
      commitMock.mockImplementation((config: { onError: (err: Error) => void }) => {
        config.onError(networkError);
      });

      const callerOnError = vi.fn();
      const { result } = renderHook(() => useRelayMutation(mockMutation));

      await act(async () =>
        result.current
          .execute({ variables: {}, onError: callerOnError })
          .catch(() => { })
      );

      expect(callerOnError).toHaveBeenCalledTimes(1);
      expect(callerOnError).toHaveBeenCalledWith(networkError);
    });

    it('呼び出し元のonErrorが未指定でもエラーにならない', async () => {
      const commitMock = setupCommitMock();
      const networkError = new Error('Network Error');
      commitMock.mockImplementation((config: { onError: (err: Error) => void }) => {
        config.onError(networkError);
      });

      const { result } = renderHook(() => useRelayMutation(mockMutation));

      await expect(
        act(async () => result.current.execute({ variables: {} }))
      ).rejects.toThrow('Network Error');
    });
  });

  /* --------------------
     errorContextのcommitへの非委譲
  -------------------- */

  describe('errorContextはcommitに渡されない', () => {
    it('commitに渡されるconfigにerrorContextが含まれない', async () => {
      const commitMock = setupCommitMock();
      commitMock.mockImplementation((config: { onCompleted: (res: unknown, errors: null) => void }) => {
        config.onCompleted(mockResponse, null);
      });

      const { result } = renderHook(() => useRelayMutation(mockMutation));

      await act(async () =>
        result.current.execute({
          variables: {},
          errorContext: 'ShouldBeStripped',
        })
      );

      const { passedConfig } = getCommitCallbacks(commitMock);
      expect(passedConfig).not.toHaveProperty('errorContext');
    });
  });

  /* --------------------
     uploadablesのnull→undefined変換
  -------------------- */

  describe('uploadablesのnull→undefined変換', () => {
    it('uploadablesがnullのとき commitにはundefinedが渡される', async () => {
      const commitMock = setupCommitMock();
      commitMock.mockImplementation((config: { onCompleted: (res: unknown, errors: null) => void }) => {
        config.onCompleted(mockResponse, null);
      });

      const { result } = renderHook(() => useRelayMutation(mockMutation));

      await act(async () =>
        result.current.execute({ variables: {}, uploadables: null })
      );

      const { passedConfig } = getCommitCallbacks(commitMock);
      expect(passedConfig.uploadables).toBeUndefined();
    });

    it('uploadablesが指定されているとき そのまま渡される', async () => {
      const commitMock = setupCommitMock();
      commitMock.mockImplementation((config: { onCompleted: (res: unknown, errors: null) => void }) => {
        config.onCompleted(mockResponse, null);
      });

      const mockUploadables = { file: new File([''], 'test.txt') };
      const { result } = renderHook(() => useRelayMutation(mockMutation));

      await act(async () =>
        result.current.execute({
          variables: {},
          uploadables: mockUploadables,
        })
      );

      const { passedConfig } = getCommitCallbacks(commitMock);
      expect(passedConfig.uploadables).toBe(mockUploadables);
    });

    it('uploadablesが未指定のとき undefinedが渡される', async () => {
      const commitMock = setupCommitMock();
      commitMock.mockImplementation((config: { onCompleted: (res: unknown, errors: null) => void }) => {
        config.onCompleted(mockResponse, null);
      });

      const { result } = renderHook(() => useRelayMutation(mockMutation));

      await act(async () =>
        result.current.execute({ variables: {} })
      );

      const { passedConfig } = getCommitCallbacks(commitMock);
      expect(passedConfig.uploadables).toBeUndefined();
    });
  });

  /* --------------------
     executeのメモ化（useCallback）
  -------------------- */

  describe('executeのメモ化', () => {
    it('再レンダリングしてもexecuteの参照が変わらない', () => {
      const { result, rerender } = renderHook(() =>
        useRelayMutation(mockMutation)
      );

      const firstExecute = result.current.execute;
      rerender();
      const secondExecute = result.current.execute;

      expect(firstExecute).toBe(secondExecute);
    });
  });
});