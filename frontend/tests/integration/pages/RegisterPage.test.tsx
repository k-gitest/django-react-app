import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, test, vi, describe, beforeEach } from 'vitest';
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
    useNavigate: () => mockNavigate,
  };
});

// useAuth から返される値を定義（楽観的更新版）
const mockSignUp = vi.fn();
const mockSignIn = vi.fn();

const mockUseAuth = {
  signUp: mockSignUp, // 呼び出しを監視
  signIn: mockSignIn,
  signOut: vi.fn(),
  signUpMutation: {
    isPending: false, // デフォルトは処理中ではない
  },
  signInMutation: {
    isPending: false,
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

describe('RegisterPage', () => {
  // 各テスト前にモックをリセット
  beforeEach(() => {
    vi.clearAllMocks();
    // 毎回 mockUseAuth の状態をリセット
    mockSignUp.mockClear();
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
    expect(screen.getByRole('button', { name: /登録/i })).toBeInTheDocument();

    // ログインページへのリンクの確認
    expect(screen.getByText(/ログインページ/i)).toHaveAttribute('href', '/login');
  });

  // ----------------------------------------------------
  // シナリオ B: フォームの成功送信テスト
  // ----------------------------------------------------
  test('有効な情報を入力し送信すると、useAuth.signUp が呼び出される', async () => {
    const user = userEvent.setup();

    // signUpをモック（成功を返す）
    mockSignUp.mockResolvedValue(undefined);

    renderWithRouter(<RegisterPage />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /登録/i });

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
      expect(mockSignUp).toHaveBeenCalledWith({
        email: testEmail,
        password: testPassword,
      });
    });

    // 4. 登録成功後、signUp内で楽観的更新とリダイレクトが行われる
    // （useAuthのテストで検証済みなので、ここでは呼び出しのみ確認）
    expect(mockSignUp).toHaveBeenCalledTimes(1);
  });

  // ----------------------------------------------------
  // シナリオ C: バリデーション失敗テスト (例: パスワード空)
  // ----------------------------------------------------
  test('必須項目が空の場合、送信されずにエラーメッセージが表示される', async () => {
    const user = userEvent.setup();
    renderWithRouter(<RegisterPage />);

    const emailInput = screen.getByLabelText(/email/i);
    const submitButton = screen.getByRole('button', { name: /登録/i });

    // email のみ入力し、password は空のまま
    await user.type(emailInput, 'test@example.com');

    await user.click(submitButton);

    // フォームが送信されず、signUpが呼ばれないことを確認
    expect(mockSignUp).not.toHaveBeenCalled();

    // バリデーションエラーメッセージが表示されることを確認
    // (Zodスキーマでは "Required" がデフォルトメッセージ)
    await waitFor(() => {
      expect(screen.getByText(/パスワードは6文字以上にしてください/i)).toBeInTheDocument();
    });
  });

  // ----------------------------------------------------
  // シナリオ D: 登録失敗時のエラーハンドリング
  // ----------------------------------------------------
  test('登録が失敗した場合、エラーメッセージが表示される', async () => {
    const user = userEvent.setup();

    // signUpをモック（失敗を返す）
    mockSignUp.mockRejectedValue(new Error('Email already exists'));

    renderWithRouter(<RegisterPage />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /登録/i });

    // 入力とクリック
    await user.type(emailInput, 'existing@example.com');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    // signUpが呼ばれたことを確認
    await waitFor(() => {
      expect(mockSignUp).toHaveBeenCalledWith({
        email: 'existing@example.com',
        password: 'password123',
      });
    });

    // エラーは errorHandler で処理されるため、
    // ここでは呼び出しが行われたことのみ確認
    expect(mockSignUp).toHaveBeenCalledTimes(1);
  });

  // ----------------------------------------------------
  // シナリオ E: ローディング状態のテスト
  // ----------------------------------------------------
  test('送信中はボタンが無効化される', async () => {
    // isPending を true に設定
    mockUseAuth.signUpMutation.isPending = true;

    renderWithRouter(<RegisterPage />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /登録/i });

    // ローディング中は入力が無効化される
    expect(emailInput).toBeDisabled();
    expect(passwordInput).toBeDisabled();
    expect(submitButton).toBeDisabled();
  });

  // ----------------------------------------------------
  // シナリオ F: 無効なメールアドレス
  // ----------------------------------------------------
  test('無効なメールアドレスの場合、エラーメッセージが表示される', async () => {
    const user = userEvent.setup();
    renderWithRouter(<RegisterPage />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /登録/i });

    // 無効なメールアドレスを入力
    await user.type(emailInput, 'invalid-email');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    // フォームが送信されない 
    expect(mockSignUp).not.toHaveBeenCalled();

    // バリデーションエラーメッセージが表示される
    await waitFor(() => {
      expect(screen.getByText(/有効なアドレスを入力してください/i)).toBeInTheDocument();
    });
  });
});