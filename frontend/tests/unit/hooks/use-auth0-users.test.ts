import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { useAuthUser } from '@/hooks/use-auth-user';

/* =========================
   モック対象
========================= */
import { useAuth0 } from '@auth0/auth0-react';
import { useAuthStore } from '@/hooks/use-session-store';

/* =========================
   vi.mock（トップレベル）
========================= */
vi.mock('@auth0/auth0-react', () => ({
  useAuth0: vi.fn(),
}));

vi.mock('@/hooks/use-session-store', () => ({
  useAuthStore: vi.fn(),
}));

/* =========================
   モック参照
========================= */
const useAuth0Mock = useAuth0 as unknown as Mock;
const useAuthStoreMock = useAuthStore as unknown as Mock;

/* =========================
   ダミーデータ
========================= */
const mockAuth0User = {
  sub: 'auth0|123',
  email: 'alice@example.com',
  given_name: 'Alice',
  family_name: 'Smith',
};

/* =========================
   共通セットアップヘルパー
========================= */

const mockSetUser = vi.fn();
const mockSetInitialized = vi.fn();

const setupAuthStore = () => {
  // useAuthStore は selector 関数を受け取るので、
  // 引数の関数を実行して対応する値を返す
  useAuthStoreMock.mockImplementation(
    (selector: (state: { setUser: Mock; setInitialized: Mock }) => unknown) =>
      selector({ setUser: mockSetUser, setInitialized: mockSetInitialized })
  );
};

const setupAuth0 = (overrides: Partial<{
  user: typeof mockAuth0User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}> = {}) => {
  useAuth0Mock.mockReturnValue({
    user: mockAuth0User,
    isAuthenticated: true,
    isLoading: false,
    ...overrides,
  });
};

/* =========================
   テスト本体
========================= */

describe('useAuthUser', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupAuthStore();
  });

  /* --------------------
     戻り値
  -------------------- */

  describe('戻り値', () => {
    it('isLoadingを返す', () => {
      setupAuth0({ isLoading: false });
      const { result } = renderHook(() => useAuthUser());

      expect(result.current).toHaveProperty('isLoading');
    });

    it('isLoadingがfalseのとき falseを返す', () => {
      setupAuth0({ isLoading: false });
      const { result } = renderHook(() => useAuthUser());

      expect(result.current.isLoading).toBe(false);
    });

    it('isLoadingがtrueのとき trueを返す', () => {
      setupAuth0({ isLoading: true });
      const { result } = renderHook(() => useAuthUser());

      expect(result.current.isLoading).toBe(true);
    });
  });

  /* --------------------
     isLoadingがtrueのとき（ローディング中）
  -------------------- */

  describe('isLoadingがtrueのとき', () => {
    it('setInitializedは呼ばれない', () => {
      setupAuth0({ isLoading: true });
      renderHook(() => useAuthUser());

      expect(mockSetInitialized).not.toHaveBeenCalled();
    });

    it('setUserは呼ばれない', () => {
      setupAuth0({ isLoading: true });
      renderHook(() => useAuthUser());

      expect(mockSetUser).not.toHaveBeenCalled();
    });
  });

  /* --------------------
     isLoadingがfalseのとき（ローディング完了）
  -------------------- */

  describe('isLoadingがfalseのとき', () => {
    it('setInitialized(true)が呼ばれる', () => {
      setupAuth0({ isLoading: false });
      renderHook(() => useAuthUser());

      expect(mockSetInitialized).toHaveBeenCalledTimes(1);
      expect(mockSetInitialized).toHaveBeenCalledWith(true);
    });
  });

  /* --------------------
     認証済み＋userあり
  -------------------- */

  describe('認証済み＋userあり', () => {
    it('setUserが正しいユーザー情報で呼ばれる', () => {
      setupAuth0({
        user: mockAuth0User,
        isAuthenticated: true,
        isLoading: false,
      });
      renderHook(() => useAuthUser());

      expect(mockSetUser).toHaveBeenCalledTimes(1);
      expect(mockSetUser).toHaveBeenCalledWith({
        id: 'auth0|123',
        email: 'alice@example.com',
        first_name: 'Alice',
        last_name: 'Smith',
      });
    });

    it('user.subがidにマッピングされる', () => {
      setupAuth0({
        user: { ...mockAuth0User, sub: 'auth0|999' },
        isAuthenticated: true,
        isLoading: false,
      });
      renderHook(() => useAuthUser());

      expect(mockSetUser).toHaveBeenCalledWith(
        expect.objectContaining({ id: 'auth0|999' })
      );
    });

    it('user.emailがemailにマッピングされる', () => {
      setupAuth0({
        user: { ...mockAuth0User, email: 'bob@example.com' },
        isAuthenticated: true,
        isLoading: false,
      });
      renderHook(() => useAuthUser());

      expect(mockSetUser).toHaveBeenCalledWith(
        expect.objectContaining({ email: 'bob@example.com' })
      );
    });

    it('given_nameがfirst_nameにマッピングされる', () => {
      setupAuth0({
        user: { ...mockAuth0User, given_name: 'Bob' },
        isAuthenticated: true,
        isLoading: false,
      });
      renderHook(() => useAuthUser());

      expect(mockSetUser).toHaveBeenCalledWith(
        expect.objectContaining({ first_name: 'Bob' })
      );
    });

    it('family_nameがlast_nameにマッピングされる', () => {
      setupAuth0({
        user: { ...mockAuth0User, family_name: 'Jones' },
        isAuthenticated: true,
        isLoading: false,
      });
      renderHook(() => useAuthUser());

      expect(mockSetUser).toHaveBeenCalledWith(
        expect.objectContaining({ last_name: 'Jones' })
      );
    });

    it('given_nameが未設定のとき first_nameは空文字になる', () => {
      setupAuth0({
        user: { ...mockAuth0User, given_name: undefined },
        isAuthenticated: true,
        isLoading: false,
      });
      renderHook(() => useAuthUser());

      expect(mockSetUser).toHaveBeenCalledWith(
        expect.objectContaining({ first_name: '' })
      );
    });

    it('family_nameが未設定のとき last_nameは空文字になる', () => {
      setupAuth0({
        user: { ...mockAuth0User, family_name: undefined },
        isAuthenticated: true,
        isLoading: false,
      });
      renderHook(() => useAuthUser());

      expect(mockSetUser).toHaveBeenCalledWith(
        expect.objectContaining({ last_name: '' })
      );
    });

    it('given_nameが空文字のとき first_nameは空文字になる', () => {
      setupAuth0({
        user: { ...mockAuth0User, given_name: '' },
        isAuthenticated: true,
        isLoading: false,
      });
      renderHook(() => useAuthUser());

      expect(mockSetUser).toHaveBeenCalledWith(
        expect.objectContaining({ first_name: '' })
      );
    });
  });

  /* --------------------
     未認証
  -------------------- */

  describe('未認証のとき', () => {
    it('setUser(null)が呼ばれる', () => {
      setupAuth0({
        user: undefined,
        isAuthenticated: false,
        isLoading: false,
      });
      renderHook(() => useAuthUser());

      expect(mockSetUser).toHaveBeenCalledTimes(1);
      expect(mockSetUser).toHaveBeenCalledWith(null);
    });

    it('isAuthenticatedがfalseでuserがあってもsetUser(null)が呼ばれる', () => {
      // 認証フラグが偽である限りuserオブジェクトは無視される
      setupAuth0({
        user: mockAuth0User,
        isAuthenticated: false,
        isLoading: false,
      });
      renderHook(() => useAuthUser());

      expect(mockSetUser).toHaveBeenCalledWith(null);
    });

    it('isAuthenticatedがtrueでuserがnullのときsetUser(null)が呼ばれる', () => {
      setupAuth0({
        user: null,
        isAuthenticated: true,
        isLoading: false,
      });
      renderHook(() => useAuthUser());

      expect(mockSetUser).toHaveBeenCalledWith(null);
    });
  });

  /* --------------------
     ローディング完了時の全体的な呼び出し順
  -------------------- */

  describe('呼び出し順', () => {
    it('setInitializedがsetUserより先に呼ばれる', () => {
      setupAuth0({ isLoading: false, isAuthenticated: true, user: mockAuth0User });
      const callOrder: string[] = [];
      mockSetInitialized.mockImplementation(() => callOrder.push('setInitialized'));
      mockSetUser.mockImplementation(() => callOrder.push('setUser'));

      renderHook(() => useAuthUser());

      expect(callOrder).toEqual(['setInitialized', 'setUser']);
    });
  });

  /* --------------------
     isLoadingの変化によるuseEffectの再実行
  -------------------- */

  describe('isLoadingの変化', () => {
    it('isLoadingがtrue→falseに変わったとき setInitializedとsetUserが呼ばれる', () => {
      setupAuth0({ isLoading: true });
      const { rerender } = renderHook(() => useAuthUser());

      expect(mockSetInitialized).not.toHaveBeenCalled();

      setupAuth0({ isLoading: false, isAuthenticated: true, user: mockAuth0User });
      rerender();

      expect(mockSetInitialized).toHaveBeenCalledWith(true);
      expect(mockSetUser).toHaveBeenCalledWith(
        expect.objectContaining({ id: 'auth0|123' })
      );
    });
  });
});