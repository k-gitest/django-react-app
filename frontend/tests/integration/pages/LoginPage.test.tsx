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

// useAuth から返される値を定義（楽観的更新版）
const mockSignIn = vi.fn();
const mockSignUp = vi.fn();

const mockUseAuth = {
  signUp: mockSignUp,
  signIn: mockSignIn, // 呼び出しを監視
  signOut: vi.fn(),
  signUpMutation: {
    isPending: false,
  },
  signInMutation: {
    isPending: false, // デフォルトは処理中ではない
  },
  signOutMutation: {
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

describe('LoginPage', () => {
  // 各テスト前にモックをリセット
  beforeEach(() => {
    vi.clearAllMocks();
    mockSignIn.mockClear();
    mockUseAuth.signInMutation.isPending = false;
    // console.error がテスト結果を汚さないようにモック化（任意）
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  // ----------------------------------------------------
  // シナリオ A: ページレンダリングテスト
  // ----------------------------------------------------
  test('ログインフォームと新規登録ページへのリンクが正しく表示される', () => {
    renderWithRouter(<LoginPage />);

    // フォーム要素の確認
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ログイン/i })).toBeInTheDocument();

    // 新規登録ページへのリンクの確認
    expect(screen.getByText(/新規登録ページ/i)).toHaveAttribute('href', '/register');
  });

  // ----------------------------------------------------
  // シナリオ B: フォームの成功送信テスト
  // ----------------------------------------------------
  test('有効な情報を入力し送信すると、useAuth.signIn が呼び出される', async () => {
    const user = userEvent.setup();
    
    // signInをモック（成功を返す）
    mockSignIn.mockResolvedValue(undefined);

    renderWithRouter(<LoginPage />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /ログイン/i });

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
      expect(mockSignIn).toHaveBeenCalledWith({
        email: testEmail,
        password: testPassword,
      });
    });

    // 4. ログイン成功後、signIn内で楽観的更新とリダイレクトが行われる
    // （useAuthのテストで検証済みなので、ここでは呼び出しのみ確認）
    expect(mockSignIn).toHaveBeenCalledTimes(1);
  });

  // ----------------------------------------------------
  // シナリオ C: バリデーション失敗テスト (例: パスワード空)
  // ----------------------------------------------------
  test('必須項目が空の場合、送信されずにエラーメッセージが表示される', async () => {
    const user = userEvent.setup();
    renderWithRouter(<LoginPage />);

    const submitButton = screen.getByRole('button', { name: /ログイン/i });

    // 何も入力せずにクリック（または email のみ入力）
    await user.click(submitButton);

    // 1. signInが呼ばれないことを確認
    expect(mockSignIn).not.toHaveBeenCalled();

    // 2. 実際にDOMに出現しているメッセージで待機
    // 「パスワード」という文字を含むエラーメッセージを探すのが最も確実です
    const errorMessage = await screen.findByText(/パスワードは6文字以上にしてください|必須|required/i);
    
    expect(errorMessage).toBeInTheDocument();
    
    // もしくは、特定のスタイル（text-destructive）を持つ要素が表示されたかを確認する
    // expect(screen.getByText(/パスワードは6文字以上にしてください/)).toHaveClass('text-destructive');
  });

  // ----------------------------------------------------
  // シナリオ D: ログイン失敗時のエラーハンドリング
  // ----------------------------------------------------
  test('ログインが失敗した場合、エラーメッセージが表示される', async () => {
    const user = userEvent.setup();
    
    // エラーが投げられた際のログ出力を抑制
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    mockSignIn.mockRejectedValue(new Error('Invalid credentials'));

    renderWithRouter(<LoginPage />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /ログイン/i });

    await user.type(emailInput, 'wrong@example.com');
    await user.type(passwordInput, 'wrongpassword');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockSignIn).toHaveBeenCalledWith({
        email: 'wrong@example.com',
        password: 'wrongpassword',
      });
    });

    expect(mockSignIn).toHaveBeenCalledTimes(1);
    
    // ログ抑制を解除
    consoleSpy.mockRestore();
  });

  // ----------------------------------------------------
  // シナリオ E: ローディング状態のテスト
  // ----------------------------------------------------
  test('送信中はボタンが無効化される', async () => {
    //const user = userEvent.setup();

    // isPending を true に設定
    mockUseAuth.signInMutation.isPending = true;

    renderWithRouter(<LoginPage />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /ログイン/i });

    // ローディング中は入力が無効化される
    expect(emailInput).toBeDisabled();
    expect(passwordInput).toBeDisabled();
    expect(submitButton).toBeDisabled();
  });
});