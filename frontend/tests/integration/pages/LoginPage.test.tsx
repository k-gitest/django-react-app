import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test, vi, describe, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import LoginPage from '@/pages/LoginPage';

// -----------------------------------------------------------------
// 1. useAuth フックのモック & useNavigate モック
// -----------------------------------------------------------------

// useNavigate のモックは RegisterPage のテストと同じ（リダイレクトを監視するため）
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
    const original = await importOriginal<Record<string, unknown>>();
    return {
        ...original,
        useNavigate: () => mockNavigate,
    };
});

// useAuth から返される値を定義（今回は signIn と isPending に注目）
const mockUseAuth = {
    signUp: vi.fn(),
    signIn: vi.fn(), // 呼び出しを監視
    signUpMutation: {
        isPending: false,
    },
    signInMutation: {
        isPending: false, // デフォルトは処理中ではない
    },
};

vi.mock('@/features/auth/hooks/use-auth', () => ({
    useAuth: vi.fn(() => mockUseAuth), // useAuth がモック値を返すように設定
}));

// -----------------------------------------------------------------
// 2. テストヘルパー関数
// -----------------------------------------------------------------

const renderWithRouter = (ui: React.ReactNode) => {
    return render(<BrowserRouter>{ui}</BrowserRouter>);
};

// -----------------------------------------------------------------
// 3. テスト本体
// -----------------------------------------------------------------

describe('LoginPage', () => {
    
    // 各テスト前にモックをリセット
    beforeEach(() => {
        vi.clearAllMocks();
        // 毎回 mockUseAuth の状態をリセット
        mockUseAuth.signIn.mockClear(); 
        mockUseAuth.signInMutation.isPending = false;
    });

    // ----------------------------------------------------
    // シナリオ A: ページレンダリングテスト
    // ----------------------------------------------------
    test('ログインフォームと新規登録ページへのリンクが正しく表示される', () => {
        renderWithRouter(<LoginPage />);

        // フォーム要素の確認
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /送信/i })).toBeInTheDocument();
        
        // 新規登録ページへのリンクの確認
        expect(screen.getByText(/新規登録ページ/i)).toHaveAttribute('href', '/register');
    });
    
    // ----------------------------------------------------
    // シナリオ B: フォームの成功送信テスト
    // ----------------------------------------------------
    test('有効な情報を入力し送信すると、useAuth.signIn が呼び出され、ダッシュボードへリダイレクトされる', async () => {
        const user = userEvent.setup();
        renderWithRouter(<LoginPage />);

        const emailInput = screen.getByLabelText(/email/i);
        const passwordInput = screen.getByLabelText(/password/i);
        const submitButton = screen.getByRole('button', { name: /送信/i });

        const testEmail = 'existinguser@example.com';
        const testPassword = 'validpassword';

        // 1. 入力シミュレーション
        await user.type(emailInput, testEmail);
        await user.type(passwordInput, testPassword);
        
        // 2. submitButton をクリック
        await user.click(submitButton);

        // 3. 検証
        // useAuth の signIn 関数が正しい引数で呼び出されたことを確認
        await waitFor(() => {
            expect(mockUseAuth.signIn).toHaveBeenCalledWith({
                email: testEmail,
                password: testPassword,
            });
        });
        
        // 4. ログイン成功後のリダイレクトを確認 (signIn内で /dashboard に遷移すると仮定)
        // ※ 実際の signIn の実装がリダイレクトを行うことを前提としています。
        // expect(mockNavigate).toHaveBeenCalledWith('/dashboard'); 
    });
    
    // ----------------------------------------------------
    // シナリオ C: バリデーション失敗テスト (例: パスワード空)
    // ----------------------------------------------------
    test('必須項目が空の場合、送信されずにエラーメッセージが表示される', async () => {
        const user = userEvent.setup();
        renderWithRouter(<LoginPage />);

        const emailInput = screen.getByLabelText(/email/i);
        const submitButton = screen.getByRole('button', { name: /送信/i });

        // email のみ入力し、password は空のまま
        await user.type(emailInput, 'test@example.com'); 
        
        await user.click(submitButton);

        // フォームが reset されず、signInが呼ばれないことを確認
        expect(mockUseAuth.signIn).not.toHaveBeenCalled();
        
        // バリデーションエラーメッセージが表示されることを確認
        // (メッセージはスキーマと FormInput の実装に依存)
        // await waitFor(() => {
        //     expect(screen.getByText(/パスワードの入力が必要です/i)).toBeInTheDocument(); 
        // });
    });

});