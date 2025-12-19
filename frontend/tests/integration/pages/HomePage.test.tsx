import { render, screen } from '@testing-library/react';
import { expect, test, vi, describe } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import Home from '@/pages/HomePage';
import { useAuthStore } from '@/hooks/use-session-store';
import type { UserInfo, AuthState } from '@/features/auth/types/auth';
import React from 'react';

// -----------------------------------------------------------------
// 1. Zustand ストアのモック設定
// -----------------------------------------------------------------

// ダミーの認証済みユーザーオブジェクト
const MOCK_AUTH_USER: UserInfo = {
  id: 1,
  email: 'test@example.com',
  first_name: 'Test',
  last_name: 'User',
  is_staff: false,
};

// 実際の useAuthStore のモック定義
vi.mock('@/hooks/use-session-store', async (importOriginal) => {
    // 既存のモジュールをそのまま利用し、useAuthStore のみ置き換える
    const actual = await importOriginal<Record<string, unknown>>(); 
    
    return {
        ...actual,
        // useAuthStore をモック関数として置き換える
        useAuthStore: vi.fn(), 
    };
});

const useAuthStoreMock = useAuthStore as unknown as ReturnType<typeof vi.fn>;

// -----------------------------------------------------------------
// 2. テストの実行
// -----------------------------------------------------------------

// テスト実行時にBrowserRouterでラップする必要があります
const renderWithRouter = (ui: React.ReactNode) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};


describe('HomePage/ContentHome', () => {

  // ----------------------------------------------------
  // シナリオ 1: ユーザーが非認証状態の場合
  // ----------------------------------------------------
  test('ユーザーが非認証状態の場合、「新規登録」と「ログイン」ボタンが表示される', () => {
    // useAuthStoreのモックを設定: userを null にする
    // useAuthStore.mockImplementation が利用可能であればそちらを使用
    useAuthStoreMock.mockImplementation((selector) => 
            selector({ user: null } as AuthState)
        );

    renderWithRouter(<Home />);

    // 非認証ユーザー向けのボタンが存在することを確認
    expect(screen.getByTestId('register-button-content-home')).toBeInTheDocument();
    expect(screen.getByTestId('login-button-content-home')).toBeInTheDocument();

    // 認証ユーザー向けのボタンが存在しないことを確認
    expect(screen.queryByTestId('dashboard-button-content-home')).not.toBeInTheDocument();
  });


  // ----------------------------------------------------
  // シナリオ 2: ユーザーが認証状態の場合
  // ----------------------------------------------------
  test('ユーザーが認証状態の場合、「dashboard」ボタンが表示される', () => {
    // useAuthStoreのモックを設定: userに認証済みオブジェクトを設定
    useAuthStoreMock.mockImplementation((selector) => 
            selector({ user: MOCK_AUTH_USER } as AuthState)
        );

    renderWithRouter(<Home />);

    // 認証ユーザー向けのボタンが存在することを確認
    expect(screen.getByTestId('dashboard-button-content-home')).toBeInTheDocument();

    // 非認証ユーザー向けのボタンが存在しないことを確認
    expect(screen.queryByTestId('register-button-content-home')).not.toBeInTheDocument();
    expect(screen.queryByTestId('login-button-content-home')).not.toBeInTheDocument();
  });


  // ----------------------------------------------------
  // 共通の要素のテスト
  // ----------------------------------------------------
  test('常にメインタイトル「django + react APP」が表示されている', () => {
    // どちらの状態でも共通のタイトルが表示されることを確認するため、認証状態を適当に設定
    useAuthStoreMock.mockImplementation((selector) => {
        return selector({ user: null } as AuthState);
    });
    renderWithRouter(<Home />);
    
    expect(screen.getByText('django + react APP')).toBeInTheDocument();
  });
});