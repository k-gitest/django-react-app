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

// Zustand store
import { useAuthStore } from '@/hooks/use-session-store';

// API mutation wrapper
import { useApiMutation } from '@/hooks/use-tanstack-query';

// auth services
import {
  signupService,
  loginService,
  logoutService,
} from '@/features/auth/services/auth-service';

// router
import { useNavigate } from 'react-router-dom';

// queryClient
import { queryClient } from '@/lib/queryClient';

/* =========================
   vi.mock（※すべてトップレベル）
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

vi.mock('@/features/auth/services/auth-service', () => ({
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

const mockUser = {
  id: 1,
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  is_staff: false,
};

const mockTokenResponse = {
  access: 'access-token',
  refresh: 'refresh-token',
  user: mockUser,
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
   テスト本体
========================= */

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // router
    (useNavigate as Mock).mockReturnValue(mockNavigate);

    // useApiMutation（デフォルト：成功系）
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
  });

  /* =========================
     signUp 成功
  ========================= */

  it('signUp が成功したとき invalidateQueries → navigate(/dashboard)', async () => {
    mockSignupService.mockResolvedValue(mockTokenResponse);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.signUp(mockAccount);
    });

    expect(mockSignupService).toHaveBeenCalledWith(mockAccount);
    // 楽観的更新: invalidateQueriesで再フェッチ
    expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['auth', 'me'],
    });
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  /* =========================
     signIn 成功
  ========================= */

  it('signIn が成功したとき レスポンスから直接setUser → navigate(/dashboard)', async () => {
    mockLoginService.mockResolvedValue(mockTokenResponse);

    const mockSetUser = vi.fn();
    const mockSetInitialized = vi.fn();

    // useAuthStore.getState()の返り値を更新
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
    
    // 楽観的更新: レスポンスから直接setUser
    expect(mockSetUser).toHaveBeenCalledWith(mockUser);
    
    // キャッシュも手動で更新
    expect(queryClient.setQueryData).toHaveBeenCalledWith(['auth', 'me'], mockUser);
    
    // 初期化フラグを立てる
    expect(mockSetInitialized).toHaveBeenCalledWith(true);
    
    // 裏側でinvalidateQueries
    expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['auth', 'me'],
    });
    
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  /* =========================
     signUp 成功後にinvalidateQueriesで遷移
  ========================= */

  it('signUp 成功後 invalidateQueries が呼ばれて navigate(/dashboard)', async () => {
    mockSignupService.mockResolvedValue(mockTokenResponse);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.signUp(mockAccount);
    });

    expect(mockSignupService).toHaveBeenCalledTimes(1);
    expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
      queryKey: ['auth', 'me'],
    });
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  /* =========================
     signOut
  ========================= */

  it('signOut が成功したとき queryClient.clear → logout → navigate(/login)', async () => {
    mockLogoutService.mockResolvedValue(undefined);

    const mockLogout = vi.fn();

    // useAuthStoreの返り値をモック（型エラー回避）
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

  /* =========================
     API エラー
  ========================= */

  it('signIn が API エラーで失敗した場合、状態変更も遷移も発生しない', async () => {
    mockLoginService.mockRejectedValue(new Error('Invalid credentials'));

    const mockSetUser = vi.fn();
    
    // useAuthStore.getState()の返り値を更新
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