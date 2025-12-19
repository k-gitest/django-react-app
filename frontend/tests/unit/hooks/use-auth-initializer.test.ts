import { renderHook, waitFor } from '@testing-library/react';
import { describe, test, expect, vi, beforeEach, type Mock } from 'vitest';

/* -------------------------------------------------
 * モック定義（⚠️ import より前・外部変数参照なし）
 * ------------------------------------------------- */
vi.mock('@/hooks/use-session-store', () => ({
  useAuthStore: vi.fn(),
}));

vi.mock('@/features/auth/services/auth-service', () => ({
  fetchMe: vi.fn(),
}));

/* -------------------------------------------------
 * import（mock の後）
 * ------------------------------------------------- */
import { useAuthInitializer } from '@/hooks/use-auth-initializer';
import { useAuthStore } from '@/hooks/use-session-store';
import { fetchMe } from '@/features/auth/services/auth-service';

/* -------------------------------------------------
 * 共通モック
 * ------------------------------------------------- */
const mockSetUser = vi.fn();
const mockLogout = vi.fn();
const mockSetInitialized = vi.fn();

const useAuthStoreMock = useAuthStore as unknown as Mock;
const fetchMeMock = fetchMe as Mock;

/* -------------------------------------------------
 * ダミーユーザー
 * ------------------------------------------------- */
type UserInfo = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
};

const mockUser: UserInfo = {
  id: 'user-001',
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  is_staff: false,
};

/* -------------------------------------------------
 * Zustand 状態セット用ヘルパー
 * ------------------------------------------------- */
const setupAuthStoreMock = (isInitialized: boolean) => {
  useAuthStoreMock.mockReturnValue({
    user: null,
    isInitialized,
    setUser: mockSetUser,
    logout: mockLogout,
    setInitialized: mockSetInitialized,
  });
};

/* =================================================
 * テスト本体
 * ================================================= */
describe('useAuthInitializer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /* ----------------------------------------------
   * シナリオ A: 未初期化 + 認証成功
   * ---------------------------------------------- */
  test('未初期化状態で fetchMe が成功した場合、ユーザーを設定し初期化完了する', async () => {
    setupAuthStoreMock(false);
    fetchMeMock.mockResolvedValue(mockUser);

    renderHook(() => useAuthInitializer());

    // fetchMe は即座に呼ばれる
    expect(fetchMeMock).toHaveBeenCalledTimes(1);

    await waitFor(() => {
      expect(mockSetUser).toHaveBeenCalledWith(mockUser);
      expect(mockLogout).not.toHaveBeenCalled();
      expect(mockSetInitialized).toHaveBeenCalledWith(true);
    });
  });

  /* ----------------------------------------------
   * シナリオ B: 未初期化 + 認証失敗
   * ---------------------------------------------- */
  test('未初期化状態で fetchMe が失敗した場合、logout して初期化完了する', async () => {
    setupAuthStoreMock(false);
    const error = new Error('Unauthorized');
    fetchMeMock.mockRejectedValue(error);

    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

    renderHook(() => useAuthInitializer());

    expect(fetchMeMock).toHaveBeenCalledTimes(1);

    await waitFor(() => {
      expect(mockSetUser).not.toHaveBeenCalled();
      expect(mockLogout).toHaveBeenCalledTimes(1);
      expect(mockSetInitialized).toHaveBeenCalledWith(true);
      expect(consoleSpy).toHaveBeenCalledWith('認証が必要です', error);
    });

    consoleSpy.mockRestore();
  });

  /* ----------------------------------------------
   * シナリオ C: 初期化済み
   * ---------------------------------------------- */
  test('既に初期化済みの場合は fetchMe を呼ばず何もしない', async () => {
    setupAuthStoreMock(true);

    renderHook(() => useAuthInitializer());

    expect(fetchMeMock).not.toHaveBeenCalled();
    expect(mockSetUser).not.toHaveBeenCalled();
    expect(mockLogout).not.toHaveBeenCalled();
    expect(mockSetInitialized).not.toHaveBeenCalled();
  });
});
