import { expect, test, describe, beforeEach } from 'vitest';
import { useAuthStore } from '@/hooks/use-session-store';
import type { UserInfo } from '@/features/auth/types/auth';

const mockUser: UserInfo = {
    id: 1,
    email: 'test@example.com',
    first_name: 'Test', 
    last_name: 'User',
    is_staff: false,
};

// -----------------------------------------------------------------
// useAuthStore のテスト
// -----------------------------------------------------------------

describe('useAuthStore (Cookie認証ストア)', () => {

    // 各テスト前にストアの状態をリセット
    beforeEach(() => {        
        useAuthStore.getState();

        // 状態データ部分のみをリセットし、アクション関数はそのまま維持します。
        // replace: false (デフォルト) で実行するため、Partial<AuthState> のみを渡せます。
        useAuthStore.setState({ 
            user: null, 
            isInitialized: false,
            // アクション関数は省略
        }, 
        false // replace: false を明示（省略可能）
        ); 
        
        // 🚨 補足: 厳密なクリーンアップを行う場合は、Zustandの非公開APIである
        // useAuthStore.setState(initialState, true) の代わりに、
        // useAuthStore.getInitialState() を使ってリセットする別の方法もありますが、
        // シンプルに状態を部分的に上書きするのが最も簡単です。
    });

    // ----------------------------------------------------
    // シナリオ A: 初期状態の確認
    // ----------------------------------------------------
    test('ストアは正しい初期状態を持つ', () => {
        const initialState = useAuthStore.getState();
        
        // 1. userはnull
        expect(initialState.user).toBeNull();
        // 2. isInitializedはfalse
        expect(initialState.isInitialized).toBe(false);
    });

    // ----------------------------------------------------
    // シナリオ B: setUser のテスト
    // ----------------------------------------------------
    test('setUser でユーザー情報を正しく設定できる', () => {
        const { setUser } = useAuthStore.getState();

        // ユーザーを設定
        setUser(mockUser);

        // 状態を確認
        const stateAfterSet = useAuthStore.getState();
        expect(stateAfterSet.user).toEqual(mockUser);
        expect(stateAfterSet.user?.first_name).toBe('Test');
    });

    // ----------------------------------------------------
    // シナリオ C: logout のテスト
    // ----------------------------------------------------
    test('logout でユーザー情報が null にリセットされる', () => {
        const { setUser, logout } = useAuthStore.getState();

        // 前提としてユーザーを設定
        setUser(mockUser);
        expect(useAuthStore.getState().user).not.toBeNull();

        // logoutを実行
        logout();

        // 状態を確認
        const stateAfterLogout = useAuthStore.getState();
        expect(stateAfterLogout.user).toBeNull();
    });

    // ----------------------------------------------------
    // シナリオ D: setInitialized のテスト
    // ----------------------------------------------------
    test('setInitialized で初期化フラグが正しく設定される', () => {
        const { setInitialized } = useAuthStore.getState();
        
        // 初期値は false であることを確認
        expect(useAuthStore.getState().isInitialized).toBe(false);

        // trueに設定
        setInitialized(true);
        expect(useAuthStore.getState().isInitialized).toBe(true);

        // falseに再設定
        setInitialized(false);
        expect(useAuthStore.getState().isInitialized).toBe(false);
    });
});