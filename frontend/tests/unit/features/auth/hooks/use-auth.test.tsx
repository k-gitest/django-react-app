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
  fetchMe,
} from '@/features/auth/services/auth-service';

// router
import { useNavigate } from 'react-router-dom';

/* =========================
   vi.mock（※すべてトップレベル）
========================= */

vi.mock('@/hooks/use-session-store', () => ({
  useAuthStore: vi.fn(),
}));

vi.mock('@/hooks/use-tanstack-query', () => ({
  useApiMutation: vi.fn(),
}));

vi.mock('@/features/auth/services/auth-service', () => ({
  signupService: vi.fn(),
  loginService: vi.fn(),
  logoutService: vi.fn(),
  fetchMe: vi.fn(),
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

/* =========================
   モック参照
========================= */

const useAuthStoreMock = useAuthStore as unknown as Mock;
const useApiMutationMock = useApiMutation as unknown as Mock;

const mockSignupService = signupService as Mock;
const mockLoginService = loginService as Mock;
const mockLogoutService = logoutService as Mock;
const mockFetchMe = fetchMe as Mock;

const mockNavigate = vi.fn();

/* =========================
   ダミーデータ
========================= */

const mockAccount = {
  email: 'test@example.com',
  password: 'password',
};

const mockUser = {
  id: 'user-001',
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  is_staff: false,
};

/* =========================
   Zustand の action モック
========================= */

const mockSetUser = vi.fn();
const mockLogout = vi.fn();

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

    // Zustand store
    useAuthStoreMock.mockReturnValue({
      user: null,
      isInitialized: true,
      setUser: mockSetUser,
      logout: mockLogout,
    });

    // useApiMutation（デフォルト：成功系）
    useApiMutationMock.mockImplementation(({ mutationFn, onSuccess, onError }) => {
    	type GenericMutationFn = (variables: unknown) => Promise<unknown>;
      return {
        mutateAsync: async (variables: unknown) => {
					try {
						// mutationFn を GenericMutationFn 型としてアサートし、呼び出す
						const result = await (mutationFn as GenericMutationFn)(variables);
						
						// onSuccess/onError の引数も unknown に合わせて型アサーションを適用
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
     signUp / signIn 成功
  ========================= */

  it('signUp が成功したとき fetchMe → setUser → navigate(/dashboard)', async () => {
    mockSignupService.mockResolvedValue(undefined);
    mockFetchMe.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.signUp(mockAccount);
    });

    expect(mockSignupService).toHaveBeenCalledWith(mockAccount);
    expect(mockFetchMe).toHaveBeenCalledTimes(1);
    expect(mockSetUser).toHaveBeenCalledWith(mockUser);
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  it('signIn が成功したとき fetchMe → setUser → navigate(/dashboard)', async () => {
    mockLoginService.mockResolvedValue(undefined);
    mockFetchMe.mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.signIn(mockAccount);
    });

    expect(mockLoginService).toHaveBeenCalledWith(mockAccount);
    expect(mockFetchMe).toHaveBeenCalledTimes(1);
    expect(mockSetUser).toHaveBeenCalledWith(mockUser);
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  /* =========================
     fetchMe 失敗でも遷移
  ========================= */

  it('signUp 成功後 fetchMe が失敗しても navigate(/dashboard) は呼ばれる', async () => {
    mockSignupService.mockResolvedValue(undefined);
    mockFetchMe.mockRejectedValue(new Error('fetch failed'));

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.signUp(mockAccount);
    });

    expect(mockSignupService).toHaveBeenCalledTimes(1);
    expect(mockFetchMe).toHaveBeenCalledTimes(1);
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  /* =========================
     signOut
  ========================= */

  it('signOut が成功したとき logoutService → logout → navigate(/login)', async () => {
    mockLogoutService.mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.signOut();
    });

    expect(mockLogoutService).toHaveBeenCalledTimes(1);
    expect(mockLogout).toHaveBeenCalledTimes(1);
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  /* =========================
     API エラー
  ========================= */

  it('signIn が API エラーで失敗した場合、状態変更も遷移も発生しない', async () => {
    mockLoginService.mockRejectedValue(new Error('Invalid credentials'));

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
