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
import { useAuth0 } from '@auth0/auth0-react';
import { useAuthStore } from '@/hooks/use-session-store';
import { useNavigate } from 'react-router-dom';
import { queryClient } from '@/lib/queryClient';

/* =========================
   vi.mock（すべてトップレベル）
========================= */

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: vi.fn(),
}));

vi.mock('@/hooks/use-session-store', () => ({
  useAuthStore: vi.fn(),
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
    clear: vi.fn(),
  },
}));

/* =========================
   モック参照・ダミーデータ
========================= */

const mockLoginWithRedirect = vi.fn();
const mockAuth0Logout = vi.fn();
const mockNavigate = vi.fn();
const mockZustandLogout = vi.fn();

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
   テスト本体
========================= */

describe('useAuth (Auth0版)', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    (useNavigate as Mock).mockReturnValue(mockNavigate);

    // useAuth0のデフォルトモック
    (useAuth0 as Mock).mockReturnValue({
      loginWithRedirect: mockLoginWithRedirect,
      logout: mockAuth0Logout,
      isAuthenticated: false,
      isLoading: false,
    });

    // useAuthStoreのデフォルトモック
    (useAuthStore as unknown as Mock).mockImplementation((selector) => {
      const state = {
        user: mockUser,
        logout: mockZustandLogout,
      };
      // selectorが渡される場合（state => state.user 等）に対応
      return typeof selector === 'function' ? selector(state) : state;
    });
  });

  /* --------------------
     返り値の構造
  -------------------- */

  describe('返り値', () => {
    it('必要なメソッドと状態を返す', () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      expect(typeof result.current.signIn).toBe('function');
      expect(typeof result.current.signUp).toBe('function');
      expect(typeof result.current.signOut).toBe('function');
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isLoading).toBe(false);
    });

    it('Mutation互換オブジェクトを返す', () => {
      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      // 既存コードとの互換性のために返すオブジェクト
      expect(result.current.signInMutation).toEqual({
        isPending: false, // isLoadingと連動
        isError: false,
        error: null,
      });
      expect(result.current.signUpMutation).toEqual({
        isPending: false,
        isError: false,
        error: null,
      });
      expect(result.current.signOutMutation).toEqual({
        isPending: false,
        isError: false,
        error: null,
      });
    });

    it('isLoadingがtrueのとき signInMutation.isPending も true になる', () => {
      (useAuth0 as Mock).mockReturnValue({
        loginWithRedirect: mockLoginWithRedirect,
        logout: mockAuth0Logout,
        isAuthenticated: false,
        isLoading: true, // ローディング中
      });

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      expect(result.current.signInMutation.isPending).toBe(true);
      expect(result.current.signUpMutation.isPending).toBe(true);
    });
  });

  /* --------------------
     signIn
  -------------------- */

  describe('signIn', () => {
    it('デフォルトのreturnTo(/dashboard)でloginWithRedirectを呼ぶ', async () => {
      mockLoginWithRedirect.mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.signIn();
      });

      expect(mockLoginWithRedirect).toHaveBeenCalledWith({
        appState: { returnTo: '/dashboard' },
      });
    });

    it('returnToを指定したとき、そのパスでloginWithRedirectを呼ぶ', async () => {
      mockLoginWithRedirect.mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.signIn('/todos');
      });

      expect(mockLoginWithRedirect).toHaveBeenCalledWith({
        appState: { returnTo: '/todos' },
      });
    });

    it('loginWithRedirectが失敗したときエラーをスローする', async () => {
      mockLoginWithRedirect.mockRejectedValue(new Error('Auth0 error'));

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await expect(
        act(async () => {
          await result.current.signIn();
        })
      ).rejects.toThrow('Auth0 error');
    });
  });

  /* --------------------
     signUp
  -------------------- */

  describe('signUp', () => {
    it('screen_hint:signupとデフォルトreturnToでloginWithRedirectを呼ぶ', async () => {
      mockLoginWithRedirect.mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.signUp();
      });

      expect(mockLoginWithRedirect).toHaveBeenCalledWith({
        authorizationParams: { screen_hint: 'signup' },
        appState: { returnTo: '/dashboard' },
      });
    });

    it('returnToを指定したとき、そのパスでloginWithRedirectを呼ぶ', async () => {
      mockLoginWithRedirect.mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.signUp('/welcome');
      });

      expect(mockLoginWithRedirect).toHaveBeenCalledWith({
        authorizationParams: { screen_hint: 'signup' },
        appState: { returnTo: '/welcome' },
      });
    });

    it('loginWithRedirectが失敗したときエラーをスローする', async () => {
      mockLoginWithRedirect.mockRejectedValue(new Error('Signup failed'));

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await expect(
        act(async () => {
          await result.current.signUp();
        })
      ).rejects.toThrow('Signup failed');
    });
  });

  /* --------------------
     signOut
  -------------------- */

  describe('signOut', () => {
    it('成功時: zustandLogout → queryClient.clear → auth0Logout の順で呼ばれる', async () => {
      const callOrder: string[] = [];

      mockZustandLogout.mockImplementation(() => callOrder.push('zustandLogout'));
      (queryClient.clear as Mock).mockImplementation(() => callOrder.push('queryClientClear'));
      mockAuth0Logout.mockImplementation(() => callOrder.push('auth0Logout'));

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.signOut();
      });

      expect(callOrder).toEqual(['zustandLogout', 'queryClientClear', 'auth0Logout']);

      // auth0Logoutに渡す引数も検証
      expect(mockAuth0Logout).toHaveBeenCalledWith({
        logoutParams: { returnTo: window.location.origin },
      });
    });

    it('失敗時: zustandLogout と navigate(/login) が呼ばれる', async () => {
      // auth0Logoutより前の処理で例外が発生するケース
      (queryClient.clear as Mock).mockImplementation(() => {
        throw new Error('clear failed');
      });

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      // onError内でthrowしないのでrejectsにはならない
      await act(async () => {
        await result.current.signOut();
      });

      // エラーが発生してもクライアント側はクリアされる
      expect(mockZustandLogout).toHaveBeenCalledTimes(2); // try内1回 + catch内1回
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });

    it('成功時: navigate は呼ばれない（auth0Logoutがリダイレクトを担うため）', async () => {
      mockAuth0Logout.mockResolvedValue(undefined);

      const { result } = renderHook(() => useAuth(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.signOut();
      });

      // Auth0がリダイレクトを担うのでnavigateは不要
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });
});