import { test, expect } from '@tests/test-utils/playwright-msw';
import { todoHandlers } from '@tests/mocks/todo.handlers';

test.describe('Dashboard Page', () => {
  test('ダッシュボードの表示制約テスト', async ({ page, worker }) => {
    // 1. Todo関連のハンドラーを適用（4件のデータを返す設定）
    await worker.use(...todoHandlers);
    
    // 2. ページ遷移
    await page.goto('/dashboard');

    // 💡 グラフの読み込み待ち（Loading... が消えるまで待機）
    await expect(page.getByText('Loading...')).toHaveCount(0);

    // 3. リストの件数チェック（limit={3} の検証）
    // MSWは4件返しているが、表示は3件であることを確認
    const todoCards = page.locator('div.w-full.rounded-lg.border');
    await expect(todoCards).toHaveCount(3);

    // 4. 読み取り専用（showActions={false}）のチェック
    // 編集・削除ボタン（MoreHorizontalアイコン）が存在しないことを確認
    const menuButton = page.getByRole('button', { name: /open menu/i });
    await expect(menuButton).not.toBeVisible();

    // 5. グラフタイトルが表示されているか確認
    await expect(page.getByText('進捗分布（%）')).toBeVisible();
    await expect(page.getByText('優先度別タスク分布')).toBeVisible();
  });
});