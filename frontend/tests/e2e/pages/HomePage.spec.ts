import { test, expect } from '@playwright/test';

test.describe('HomePage E2E', () => {
  const url = '/'; // ContentHomeが表示されるルートパス

  // --- シナリオ 1: 未ログイン状態 ---
  test('未ログイン状態の場合、新規登録とログインボタンが表示されること', async ({ page }) => {

    await page.goto(url);

    // 1. タイトルが表示されていること
    await expect(page.getByRole('heading', { level: 2 })).toHaveText(
      'django + react APP'
    );

    // 2. 「新規登録」ボタンが表示され、正しいリンクを持っていること
    const registerButton = page.getByTestId('register-button-content-home');
    await expect(registerButton).toBeVisible();
    await expect(registerButton.getByRole('link')).toHaveAttribute(
      'href',
      '/register'
    );

    // 3. 「ログイン」ボタンが表示され、正しいリンクを持っていること
    const loginButton = page.getByTestId('login-button-content-home');
    await expect(loginButton).toBeVisible();
    await expect(loginButton.getByRole('link')).toHaveAttribute(
      'href',
      '/login'
    );

    // 4. 「dashboard」ボタンは表示されていないこと
    await expect(
      page.getByTestId('dashboard-button-content-home')
    ).not.toBeAttached();
  });

  // --- シナリオ 2: ログイン状態 ---
  /*
  test('ログイン状態の場合、dashboardボタンが表示され、新規登録とログインボタンは表示されないこと', async ({ page, worker }) => {
    // ログインハンドラを適用
    await worker.use(loggedInSessionHandler);

    await page.goto(url);

    // 1. タイトルが表示されていること (再確認)
    await expect(page.getByRole('heading', { level: 2 })).toHaveText(
      'django + react APP'
    );

    // 2. 「dashboard」ボタンが表示され、正しいリンクを持っていること
    const dashboardButton = page.getByTestId('dashboard-button-content-home');
    await expect(dashboardButton).toBeVisible();
    await expect(dashboardButton.getByRole('link')).toHaveAttribute(
      'href',
      '/dashboard'
    );

    // 3. 「新規登録」と「ログイン」ボタンが表示されていないこと
    await expect(
      page.getByTestId('register-button-content-home')
    ).not.toBeAttached();
    await expect(
      page.getByTestId('login-button-content-home')
    ).not.toBeAttached();
  });
  */
});