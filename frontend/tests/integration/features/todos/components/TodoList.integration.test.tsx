import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TodoList } from '@/features/todos/components/TodoList';
import { useTodos } from '@/features/todos/hooks/useTodos';
import type { Todo } from '@/features/todos/types';
import userEvent from '@testing-library/user-event';

// --- モック定義 ---

vi.mock('@/features/todos/hooks/useTodos');
const mockedUseTodos = vi.mocked(useTodos);

// TodoItem と TodoEditModal は子コンポーネントとして動作を確認するため、
// ここではモックせず実体、あるいは簡易的な表示の差し替えに留めます。
// もし TodoItem が重い場合は個別にモックしても良いですが、まずはそのままで書きます。

describe('TodoList', () => {
  const mockTodos: Todo[] = [
    {
      id: 1,
      todo_title: 'タスク1',
      priority: 'HIGH',
      progress: 0,
      user: 'test@example.com',
      created_at: '2025-12-22',
      updated_at: '2025-12-22',
    },
    {
      id: 2,
      todo_title: 'タスク2',
      priority: 'LOW',
      progress: 100,
      user: 'test@example.com',
      created_at: '2025-12-22',
      updated_at: '2025-12-22',
    },
  ];

  const mockUpdateTodo = vi.fn();
  const mockDeleteTodo = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    // window.confirm をモック
    vi.spyOn(window, 'confirm');
  });

  // 型安全なモック戻り値を作成するユーティリティ
  const setMockReturnValue = (overrides: Partial<ReturnType<typeof useTodos>>) => {
    mockedUseTodos.mockReturnValue({
      todos: [],
      isLoading: false,
      isError: false,
      createTodo: vi.fn(),
      updateTodo: mockUpdateTodo,
      deleteTodo: mockDeleteTodo,
      createMutation: {} as unknown as ReturnType<typeof useTodos>['createMutation'],
      updateMutation: {} as unknown as ReturnType<typeof useTodos>['updateMutation'],
      deleteMutation: {} as unknown as ReturnType<typeof useTodos>['deleteMutation'],
      ...overrides,
    } as ReturnType<typeof useTodos>);
  };

  it('読み込み中はスピナーが表示されること', () => {
    setMockReturnValue({ isLoading: true });
    render(<TodoList />);
    // Spinnerコンポーネントが何らかの識別子を持っている場合（ここではRoleやクラス名を想定）
    // Spinnerの実装に合わせて調整してください
    const spinner = screen.getByRole('status') || document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('エラー時はエラーメッセージが表示されること', () => {
    setMockReturnValue({ isError: true });
    render(<TodoList />);
    expect(screen.getByText('タスクの読み込みに失敗しました。')).toBeInTheDocument();
  });

  it('タスクが空の場合は専用のメッセージが表示されること', () => {
    setMockReturnValue({ todos: [] });
    render(<TodoList />);
    expect(screen.getByText('まだタスクがありません。新しいタスクを追加しましょう！')).toBeInTheDocument();
  });

  it('タスク一覧が正しく表示されること', () => {
    setMockReturnValue({ todos: mockTodos });
    render(<TodoList />);
    expect(screen.getByText('タスク1')).toBeInTheDocument();
    expect(screen.getByText('タスク2')).toBeInTheDocument();
  });

  it('削除ボタンをクリックし、confirmでOKを押すとdeleteTodoが呼ばれる', async () => {
    const user = userEvent.setup(); // setup
    setMockReturnValue({ todos: [mockTodos[0]] });
    vi.mocked(window.confirm).mockReturnValue(true);

    render(<TodoList />);
    
    // 1. メニューを開く (userEventを使う)
    const menuButton = screen.getByRole('button', { name: /Open menu/i });
    await user.click(menuButton);

    // 2. 削除ボタンが表示されるのを待つ
    const deleteButton = await screen.findByRole('menuitem', { name: /削除/i });
    await user.click(deleteButton);

    expect(window.confirm).toHaveBeenCalled();
    expect(mockDeleteTodo).toHaveBeenCalledWith(mockTodos[0].id);
  });

  it('編集ボタンをクリックすると編集モーダルが開くこと', async () => {
    const user = userEvent.setup();
    setMockReturnValue({ todos: [mockTodos[0]] });
    render(<TodoList />);

    // 1. メニューを開く
    const menuButton = screen.getByRole('button', { name: /Open menu/i });
    await user.click(menuButton);

    // 2. 編集ボタンを findByRole で取得
    const editButton = await screen.findByRole('menuitem', { name: /編集/i });
    fireEvent.click(editButton);

    // 3. モーダルのタイトルが表示されるのを待機
    // モーダルもポータルなので findByText が確実です
    expect(await screen.findByText('タスクを編集')).toBeInTheDocument();
  });
});