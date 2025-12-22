import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TodoCreateForm } from '@/features/todos/components/TodoCreateForm';
import { useTodos } from '@/features/todos/hooks/useTodos';

// --- モック定義 ---

vi.mock('@/features/todos/hooks/useTodos');
const mockedUseTodos = vi.mocked(useTodos);

describe('TodoCreateForm', () => {
  const mockCreateTodo = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // anyを使わず、ReturnTypeを使用して完全に型を合わせる
    const mockReturnValue: ReturnType<typeof useTodos> = {
      todos: [],
      isLoading: false,
      isError: false,
      createTodo: mockCreateTodo,
      updateTodo: vi.fn(),
      deleteTodo: vi.fn(),
      // Mutationオブジェクトは unknown を経由して目的の型へキャスト（型安全な手法）
      createMutation: { mutateAsync: mockCreateTodo } as unknown as ReturnType<typeof useTodos>['createMutation'],
      updateMutation: { mutateAsync: vi.fn() } as unknown as ReturnType<typeof useTodos>['updateMutation'],
      deleteMutation: { mutateAsync: vi.fn() } as unknown as ReturnType<typeof useTodos>['deleteMutation'],
    };

    mockedUseTodos.mockReturnValue(mockReturnValue);
  });

  it('初期状態では「新規タスク追加」ボタンが表示され、ダイアログは閉じている', () => {
    render(<TodoCreateForm />);
    
    expect(screen.getByRole('button', { name: /新規タスク追加/i })).toBeInTheDocument();
    // ダイアログ内のタイトルが表示されていないことを確認
    expect(screen.queryByText('新しいタスクを作成')).not.toBeInTheDocument();
  });

  it('ボタンをクリックするとダイアログが開く', () => {
    render(<TodoCreateForm />);

    const triggerButton = screen.getByRole('button', { name: /新規タスク追加/i });
    fireEvent.click(triggerButton);

    expect(screen.getByText('新しいタスクを作成')).toBeInTheDocument();
    expect(screen.getByLabelText('タイトル')).toBeInTheDocument();
  });

  it('フォームを入力して送信すると、createTodoが呼ばれダイアログが閉じる', async () => {
    mockCreateTodo.mockResolvedValueOnce({}); // 成功をシミュレート

    render(<TodoCreateForm />);

    // ダイアログを開く
    fireEvent.click(screen.getByRole('button', { name: /新規タスク追加/i }));

    // タイトルを入力
    const titleInput = screen.getByLabelText('タイトル');
    fireEvent.change(titleInput, { target: { value: '新しい統合テストタスク' } });

    // 作成ボタンをクリック
    const submitButton = screen.getByRole('button', { name: 'タスクを作成' });
    fireEvent.click(submitButton);

    // 1. createTodoが正しい値で呼ばれたか確認
    await waitFor(() => {
      expect(mockCreateTodo).toHaveBeenCalledWith(
        expect.objectContaining({
          todo_title: '新しい統合テストタスク',
          priority: 'MEDIUM', // デフォルト値
          progress: 0,        // デフォルト値
        })
      );
    });

    // 2. ダイアログが閉じていることを確認
    await waitFor(() => {
      expect(screen.queryByText('新しいタスクを作成')).not.toBeInTheDocument();
    });
  });

  it('送信中（isSubmitting）はボタンが「保存中...」になる', async () => {
    // 意図的に非同期処理を待機させる
    mockCreateTodo.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

    render(<TodoCreateForm />);
    fireEvent.click(screen.getByRole('button', { name: /新規タスク追加/i }));

    fireEvent.change(screen.getByLabelText('タイトル'), { target: { value: '待機テスト' } });
    fireEvent.click(screen.getByRole('button', { name: 'タスクを作成' }));

    // TodoForm内の送信ボタンの文言を確認
    expect(screen.getByText('保存中...')).toBeInTheDocument();
  });
});