import { test, expect } from '@tests/test-utils/playwright-msw';
import { todoHandlers } from '@tests/mocks/todo.handlers';
import { http, HttpResponse } from 'msw';

interface TodoRequestPayload {
  todo_title: string;
  priority: string;
  progress: number;
}

test.describe('Todo CRUD Operations', () => {
  test.beforeEach(async ({ page, worker }) => {
    await worker.use(...todoHandlers);
    await page.goto('/todo');
  });

  test('新規タスクを作成できること', async ({ page, worker }) => {
    // 1. 型を明示的に指定 (TodoFormValues または Partial<TodoFormValues>)
    let createPayload: TodoRequestPayload | null = null;

    await worker.use(
      http.post('**/todos/', async ({ request }) => {
        // request.json() にジェネリクスを渡して型を確定させる
        const body = await request.json() as TodoRequestPayload;
        createPayload = body;
        return HttpResponse.json({ id: 999, ...body }, { status: 201 });
      })
    );

    await page.getByRole('button', { name: /新規タスク追加/i }).click();
    await page.getByLabel('タイトル').fill('新しく作るタスク');
    await page.getByLabel('優先度').click();
    await page.getByRole('option', { name: '高' }).click();
    await page.getByRole('button', { name: 'タスクを作成' }).click();

    await expect(page.getByText('新しいタスクを作成')).not.toBeVisible();
    
    // createPayload が null でないことを保証してアサーション
    expect(createPayload).toMatchObject({
      todo_title: '新しく作るタスク',
      priority: 'HIGH'
    });
  });

  test('チェックボックスで進捗を100%（完了）に切り替えられること', async ({ page, worker }) => {
    // 2. number 型で初期化
    let patchedProgress: number | null = null;

    await worker.use(
      http.patch('**/todos/:id/', async ({ request }) => {
        // 部分的な更新なので Partial を使用
        const body = await request.json() as TodoRequestPayload;
        patchedProgress = body.progress ?? null;
        return HttpResponse.json({ id: 1, progress: patchedProgress });
      })
    );

    // 未完了（progress: 50）のタスクをクリック
    await page.getByRole('checkbox').first().click();

    // 検証: 暗黙のanyが解消され、型の安全性が保たれる
    await expect.poll(() => patchedProgress).toBe(100);
  });

  test('タスクを削除できること', async ({ page, worker }) => {
    // 3. IDの型（string | null）を明示
    let deleteId: string | null = null;

    await worker.use(
      http.delete('**/todos/:id/', ({ params }) => {
        deleteId = params.id as string;
        return new HttpResponse(null, { status: 204 });
      })
    );

    page.on('dialog', dialog => dialog.accept());
    await page.getByRole('button', { name: /open menu/i }).first().click();
    await page.getByRole('menuitem', { name: /削除/i }).click();

    await expect.poll(() => deleteId).toBe('1');
  });

  test('タイトルが空の場合、バリデーションエラーを表示しAPIを叩かない', async ({ page, worker }) => {
    let postCalled = false;
    await worker.use(
      http.post('**/todos/', () => {
        postCalled = true;
        return new HttpResponse(null, { status: 201 });
      })
    );

    await page.goto('/todo');
    await page.getByRole('button', { name: /新規タスク追加/i }).click();
    
    // タイトルを入力せずに送信
    await page.getByRole('button', { name: 'タスクを作成' }).click();

    // 検証: エラーメッセージが出ているか（React Hook Form + Zod のメッセージ）
    await expect(page.getByText(/タイトルを入力してください/i)).toBeVisible();
    // 検証: APIは呼ばれていないか
    expect(postCalled).toBe(false);
  });

  test('APIが500エラーを返した時、エラーアラートが表示されること', async ({ page, worker }) => {
    await worker.use(
      http.get('**/todos/', () => {
        return HttpResponse.json(
          { detail: "Internal Server Error" },
          { 
            status: 500,
            headers: {
              'Content-Type': 'application/json',
            }
          }
        );
      })
    );

    // リトライ無効の設定
    await page.addInitScript(() => {
      window.__IS_E2E_TESTING__ = true;
    });

    await page.goto('/todo');

    await expect(page.getByText('タスクの読み込みに失敗しました。')).toBeVisible();
  });
});