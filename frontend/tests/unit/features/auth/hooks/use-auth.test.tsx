import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { Mock } from 'vitest';
import { MemoryRouter } from 'react-router-dom';

/* =========================
   テスト対象
========================= */
import { useAuth } from '@/features/auth/hooks/use-auth';

/* =========================
   モック対象
========================= */

import { useAuthStore } from '@/hooks/use-session-store';
import { useApiMutation } from '@/hooks/use-tanstack-query';

// use-auth.ts は index からimportしているので合わせる
import {
  signupService,
  loginService,
  logoutService,
} from '@/features/auth/services/index';

import { useNavigate } from 'react-router-dom';
import { queryClient } from '@/lib/queryClient';

/* =========================
   vi.mock（すべてトップレベル）
========================= */

vi.mock('@/hooks/use-session-store', () => {
  const mockSetUser = vi.fn();
  const mockLogout = vi.fn();
  const mockSetInitialized = vi.fn();

  const mockStore = {
    user: null,
    isInitialized: false,
    setUser: mockSetUser,
    logout: mockLogout,
    setInitialized: mockSetInitialized,
  };

  return {
    useAuthStore: Object.assign(
      vi.fn(() => mockStore),
      {
        getState: vi.fn(() => mockStore),
        setState: vi.fn(),
        subscribe: vi.fn(),
        destroy: vi.fn(),
      }
    ),
  };
});

vi.mock('@/hooks/use-tanstack-query', () => ({
  useApiMutation: vi.fn(),
}));

// use-auth.ts のimportパスに合わせて index をモック
vi.mock('@/features/auth/services/index', () => ({
  signupService: vi.fn(),
  loginService: vi.fn(),
  logoutService: vi.fn(),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>(
    'react-router-dom'
  );
  return {
    ...actual,
    useNavigate: vi.fn(),
  };
});

vi.mock('@/lib/queryClient', () => ({
  queryClient: {
    invalidateQueries: vi.fn(),
    setQueryData: vi.fn(),
    clear: vi.fn(),
  },
}));

/* =========================
   モック参照
========================= */

const useApiMutationMock = useApiMutation as unknown as Mock;
const mockSignupService = signupService as Mock;
const mockLoginService = loginService as Mock;
const mockLogoutService = logoutService as Mock;
const mockNavigate = vi.fn();

/* =========================
   ダミーデータ
========================= */

const mockAccount = {
  email: 'test@example.com',
  password: 'password',
};

// auth-service.tsはdata.userを返すので、
// signupService/loginServiceのモック戻り値はUserInfo型にする
const mockUser = {
  id: 1,
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  is_staff: false,
};

/* =========================
   wrapper
========================= */

const createWrapper = () => {
  return ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter>{children}</MemoryRouter>
  );
};

/* =========================
   共通のuseApiMutationセットアップ
========================= */

const setupApiMutation = () => {
  useApiMutationMock.mockImplementation(({ mutationFn, onSuccess, onError }) => {
    type GenericMutationFn = (variables: unknown) => Promise<unknown>;
    return {
      mutateAsync: async (variables: unknown) => {
        try {
          const result = await (mutationFn as GenericMutationFn)(variables);
          await onSuccess?.(result, variables, undefined);
          return result;
        } catch (e) {
          await onError?.(e);
          throw e;
        }
      },
    };
  });
};

/* =========================
   テスト本体
========================= */

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useNavigate as Mock).mockReturnValue(mockNavigate);
    setupApiMutation();
  });

  /* --------------------
     signUp
  -------------------- */

  describe('signUp', () => {
    it('成功時: setUser・setQueryData・setInitialized・invalidateQueries・navigate が呼ばれる', async () => {
      // auth-service.tsがdata.userを返すのでUserInfoをそのまま返す
      mockSignupService.mockResolvedValue(mockUser);

      const mockSetUser = vi.fn();
      const mockSetInitialized = vi.fn();
      (useAuthStore.getState as Mock).mockReturnValue({
        user: null,
        isInitialized: false,
        setUser: mockSetUser,
        logout: vi.fn(),
        setInitialized: mockSetInitialized,
      });

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.signUp(mockAccount);
      });

      expect(mockSignupService).toHaveBeenCalledWith(mockAccount);

      // onSuccess内: userが存在するのでsetUser・setQueryDataが呼ばれる
      expect(mockSetUser).toHaveBeenCalledWith(mockUser);
      expect(queryClient.setQueryData).toHaveBeenCalledWith(['auth', 'me'], mockUser);

      // 初期化フラグ
      expect(mockSetInitialized).toHaveBeenCalledWith(true);

      // 念のためのinvalidate
      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['auth', 'me'],
      });

      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });

    it('失敗時: setUser・navigate が呼ばれない', async () => {
      mockSignupService.mockRejectedValue(new Error('Registration failed'));

      const mockSetUser = vi.fn();
      (useAuthStore.getState as Mock).mockReturnValue({
        user: null,
        isInitialized: false,
        setUser: mockSetUser,
        logout: vi.fn(),
        setInitialized: vi.fn(),
      });

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await expect(
        act(async () => {
          await result.current.signUp(mockAccount);
        })
      ).rejects.toThrow('Registration failed');

      expect(mockSetUser).not.toHaveBeenCalled();
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  /* --------------------
     signIn
  -------------------- */

  describe('signIn', () => {
    it('成功時: setUser・setQueryData・setInitialized・invalidateQueries・navigate が呼ばれる', async () => {
      mockLoginService.mockResolvedValue(mockUser);

      const mockSetUser = vi.fn();
      const mockSetInitialized = vi.fn();
      (useAuthStore.getState as Mock).mockReturnValue({
        user: null,
        isInitialized: false,
        setUser: mockSetUser,
        logout: vi.fn(),
        setInitialized: mockSetInitialized,
      });

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.signIn(mockAccount);
      });

      expect(mockLoginService).toHaveBeenCalledWith(mockAccount);

      // 楽観的更新
      expect(mockSetUser).toHaveBeenCalledWith(mockUser);
      expect(queryClient.setQueryData).toHaveBeenCalledWith(['auth', 'me'], mockUser);

      // 初期化フラグ
      expect(mockSetInitialized).toHaveBeenCalledWith(true);

      // 裏側でのinvalidate
      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['auth', 'me'],
      });

      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });

    it('失敗時: setUser・navigate が呼ばれない', async () => {
      mockLoginService.mockRejectedValue(new Error('Invalid credentials'));

      const mockSetUser = vi.fn();
      (useAuthStore.getState as Mock).mockReturnValue({
        user: null,
        isInitialized: false,
        setUser: mockSetUser,
        logout: vi.fn(),
        setInitialized: vi.fn(),
      });

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await expect(
        act(async () => {
          await result.current.signIn(mockAccount);
        })
      ).rejects.toThrow('Invalid credentials');

      expect(mockSetUser).not.toHaveBeenCalled();
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  /* --------------------
     signOut
  -------------------- */

  describe('signOut', () => {
    it('成功時: queryClient.clear・logout・navigate(/login) が呼ばれる', async () => {
      mockLogoutService.mockResolvedValue(undefined);

      const mockLogout = vi.fn();
      (useAuthStore as unknown as Mock).mockReturnValue({
        logout: mockLogout,
      });

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.signOut();
      });

      expect(mockLogoutService).toHaveBeenCalledTimes(1);
      expect(queryClient.clear).toHaveBeenCalledTimes(1);
      expect(mockLogout).toHaveBeenCalledTimes(1);
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });

    it('失敗時: APIエラーでも logout・navigate(/login) が呼ばれる（クライアント状態を優先）', async () => {
      mockLogoutService.mockRejectedValue(new Error('Logout API failed'));

      const mockLogout = vi.fn();
      (useAuthStore as unknown as Mock).mockReturnValue({
        logout: mockLogout,
      });

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      // onErrorでlogout+navigateを呼んだ後にthrowするのでrejectsになる
      await expect(
        act(async () => {
          await result.current.signOut();
        })
      ).rejects.toThrow('Logout API failed');

      // APIが失敗してもクライアント側はクリアする
      expect(mockLogout).toHaveBeenCalledTimes(1);
      expect(mockNavigate).toHaveBeenCalledWith('/login');

      // queryClient.clearはonErrorでは呼ばれない（onSuccessのみ）
      expect(queryClient.clear).not.toHaveBeenCalled();
    });
  });
});