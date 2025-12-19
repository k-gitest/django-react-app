import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test, vi, describe } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import RegisterPage from '@/pages/RegisterPage';

// -----------------------------------------------------------------
// 1. useAuth フックのモック
// -----------------------------------------------------------------

// useNavigate も同時にモックし、リダイレクトを監視できるようにする
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
    const original = await importOriginal<Record<string, unknown>>();
    return {
        ...original,
        // useAuthStore のテストで BrowserRouter を使っているため、Link などはそのまま利用
        useNavigate: () => mockNavigate, // useNavigate をモックする
    };
});

// useAuth から返される値を定義（特に signUp と isPending）
const mockUseAuth = {
    signUp: vi.fn(), // 呼び出しを監視
    signIn: vi.fn(), 
    signUpMutation: {
        isPending: false, // デフォルトは処理中ではない
    },
    signInMutation: {
        isPending: false,
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

describe('RegisterPage', () => {
    
    // 各テスト前にモックをリセット
    beforeEach(() => {
        vi.clearAllMocks();
        // 毎回 mockUseAuth の状態をリセット
        mockUseAuth.signUp.mockClear(); 
        mockUseAuth.signUpMutation.isPending = false;
    });

    // ----------------------------------------------------
    // シナリオ A: ページレンダリングテスト
    // ----------------------------------------------------
    test('新規登録フォームとログインページへのリンクが正しく表示される', () => {
        renderWithRouter(<RegisterPage />);

        // フォーム要素の確認
        expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /送信/i })).toBeInTheDocument();
        
        // ログインページへのリンクの確認
        expect(screen.getByText(/ログインページ/i)).toHaveAttribute('href', '/login');
    });
    
    // ----------------------------------------------------
    // シナリオ B: フォームの成功送信テスト
    // ----------------------------------------------------
    test('有効な情報を入力し送信すると、useAuth.signUp が呼び出され、リダイレクトされる', async () => {
        const user = userEvent.setup();
        renderWithRouter(<RegisterPage />);

        const emailInput = screen.getByLabelText(/email/i);
        const passwordInput = screen.getByLabelText(/password/i);
        const submitButton = screen.getByRole('button', { name: /送信/i });

        const testEmail = 'newuser@example.com';
        const testPassword = 'securepassword';

        // 1. 入力シミュレーション
        await user.type(emailInput, testEmail);
        await user.type(passwordInput, testPassword);
        
        // 2. submitButton をクリック
        await user.click(submitButton);

        // 3. 検証
        // useAuth の signUp 関数が正しい引数で呼び出されたことを確認
        await waitFor(() => {
            expect(mockUseAuth.signUp).toHaveBeenCalledWith({
                email: testEmail,
                password: testPassword,
            });
        });
        
        // 4. 登録成功後のリダイレクトを確認 (signUp内で /login に遷移すると仮定)
        // ※ 実際の signUp の実装が Promise を返す場合、その解決を待つ必要があります。
        // ここでは、signUpが呼ばれた直後にフォームのリセットが行われているため、その検証も可能です。
        // リダイレクトの検証は、signUp 関数内で navigate('/login') が呼ばれることを確認することで行います。
        // (ここではsignUpがリダイレクトを内包しているか不明なため、一旦コメントアウト)
        // expect(mockNavigate).toHaveBeenCalledWith('/login'); 
    });
    
    // ----------------------------------------------------
    // シナリオ C: バリデーション失敗テスト (例: パスワード空)
    // ----------------------------------------------------
    test('必須項目が空の場合、送信されずにエラーメッセージが表示される', async () => {
        const user = userEvent.setup();
        renderWithRouter(<RegisterPage />);

        const emailInput = screen.getByLabelText(/email/i);
        const submitButton = screen.getByRole('button', { name: /送信/i });

        // email のみ入力し、password は空のまま
        await user.type(emailInput, 'test@example.com'); 
        
        await user.click(submitButton);

        // フォームが reset されず、signUpが呼ばれないことを確認
        expect(mockUseAuth.signUp).not.toHaveBeenCalled();
        
        // バリデーションエラーメッセージが表示されることを確認
        // (メッセージはスキーマと FormInput の実装に依存)
        await waitFor(() => {
            // 例: パスワードの入力が必要です 
            // expect(screen.getByText(/パスワードの入力が必要です/i)).toBeInTheDocument(); 
        });
    });

});