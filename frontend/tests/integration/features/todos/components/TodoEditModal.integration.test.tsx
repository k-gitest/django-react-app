import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TodoEditModal } from '@/features/todos/components/TodoEditModal';
import { useTodos } from '@/features/todos/hooks/useTodos';
import type { Todo } from '@/features/todos/types';

// 1. カスタムフックをモック化
vi.mock('@/features/todos/hooks/useTodos');
const mockedUseTodos = vi.mocked(useTodos);

describe('TodoEditModal', () => {
  const mockTodo: Todo = {
    id: 1,
    todo_title: 'テストタスク',
    priority: 'HIGH',
    progress: 50,
    user: 'test@example.com',
    created_at: '2025-12-22',
    updated_at: '2025-12-22',
  };

  const mockUpdateTodo = vi.fn();
  const mockOnOpenChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // 必要な関数とデータを定義
    const mockReturnValue: ReturnType<typeof useTodos> = {
      todos: [],
      isLoading: false,
      isError: false,
      createTodo: vi.fn(),
      updateTodo: mockUpdateTodo,
      deleteTodo: vi.fn(),
      // 複雑な Mutation オブジェクトを unknown を経由して型安全にキャスト
      // または必要なプロパティ (mutateAsync等) だけを持つダミーを渡す
      createMutation: {} as ReturnType<typeof useTodos>['createMutation'],
      updateMutation: {} as ReturnType<typeof useTodos>['updateMutation'],
      deleteMutation: {} as ReturnType<typeof useTodos>['deleteMutation'],
    };

    mockedUseTodos.mockReturnValue(mockReturnValue);
  });

  it('todoがnullの場合は何もレンダリングされない', () => {
    const { container } = render(
      <TodoEditModal todo={null} open={true} onOpenChange={mockOnOpenChange} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('モーダルが開いたとき、初期値がフォームに反映されている', () => {
    render(<TodoEditModal todo={mockTodo} open={true} onOpenChange={mockOnOpenChange} />);

    // 1. タイトルの初期値確認
    expect(screen.getByLabelText('タイトル')).toHaveValue(mockTodo.todo_title);
    
    // 2. 優先度の初期値確認
    // ボタン(combobox)の中にある「高」というテキストを持つ要素を特定する
    // getAllByTextで複数取得して、そのうち一つが表示されていればOKとする
    const priorityElements = screen.getAllByText('高');
    expect(priorityElements[0]).toBeInTheDocument();

    // あるいは、role="combobox" を持つボタン自体のテキストを確認する
    const selectButton = screen.getByRole('combobox', { name: '優先度' });
    expect(selectButton).toHaveTextContent('高'); 

    // 3. 進捗率の初期値確認 (数値入力input)
    expect(screen.getByRole('spinbutton')).toHaveValue(mockTodo.progress);
  });

  it('フォームを編集して送信すると、正しいデータでupdateTodoが呼ばれモーダルが閉じる', async () => {
    // 成功時をシミュレート
    mockUpdateTodo.mockResolvedValueOnce(undefined);

    render(<TodoEditModal todo={mockTodo} open={true} onOpenChange={mockOnOpenChange} />);

    // タイトルを書き換える
    const titleInput = screen.getByLabelText('タイトル');
    fireEvent.change(titleInput, { target: { value: '新しいタイトル' } });

    // 進捗率を書き換える
    const progressInput = screen.getByRole('spinbutton');
    fireEvent.change(progressInput, { target: { value: '80' } });

    // 保存ボタンをクリック
    const submitButton = screen.getByRole('button', { name: '変更を保存' });
    fireEvent.click(submitButton);

    // 1. updateTodoが正しい引数で呼ばれたか
    await waitFor(() => {
      expect(mockUpdateTodo).toHaveBeenCalledWith({
        id: mockTodo.id,
        data: {
          todo_title: '新しいタイトル',
          priority: 'HIGH',
          progress: 80,
        },
      });
    });

    // 2. onOpenChange(false)が呼ばれてモーダルが閉じたか
    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });

  it('進捗率の数値入力で範囲外の値を入力しても補正されること', async () => {
    render(<TodoEditModal todo={mockTodo} open={true} onOpenChange={mockOnOpenChange} />);

    const progressInput = screen.getByRole('spinbutton');
    
    // 100を超える値を入力
    fireEvent.change(progressInput, { target: { value: '150' } });
    expect(progressInput).toHaveValue(100);

    // 負の値を入力
    fireEvent.change(progressInput, { target: { value: '-10' } });
    expect(progressInput).toHaveValue(0);
  });

  it('送信中（isSubmitting）は保存ボタンが「保存中...」になり無効化される', async () => {
    // 意図的に遅延させる
    mockUpdateTodo.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

    render(<TodoEditModal todo={mockTodo} open={true} onOpenChange={mockOnOpenChange} />);

    const submitButton = screen.getByRole('button', { name: '変更を保存' });
    fireEvent.click(submitButton);

    // 「保存中...」の状態を確認
    expect(screen.getByText('保存中...')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
  });
});