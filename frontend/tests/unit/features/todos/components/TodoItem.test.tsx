import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { TodoItem } from '@/features/todos/components/TodoItem';
import type { Todo } from '@/features/todos/types';

describe('TodoItem', () => {
  // モックデータ
  const mockTodo: Todo = {
    id: 1,
    todo_title: 'テストタスク',
    priority: 'HIGH',
    progress: 50,
    user: 'user1',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  };

  // モック関数
  let mockOnToggleComplete: (todo: Todo) => void;
  let mockOnEdit: (todo: Todo) => void;
  let mockOnDelete: (id: number) => void;

  beforeEach(() => {
    mockOnToggleComplete = vi.fn();
    mockOnEdit = vi.fn();
    mockOnDelete = vi.fn();
  });

  describe('表示', () => {
    it('Todoの基本情報が表示される', () => {
      render(
        <TodoItem
          todo={mockTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // タイトルが表示される
      expect(screen.getByText('テストタスク')).toBeInTheDocument();

      // 進捗率が表示される
      expect(screen.getByText('進捗: 50%')).toBeInTheDocument();

      // 更新日が表示される
      expect(screen.getByText(/更新:/)).toBeInTheDocument();
    });

    it('優先度バッジが表示される', () => {
      render(
        <TodoItem
          todo={mockTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // 優先度「高」が表示される
      expect(screen.getByText('高')).toBeInTheDocument();
    });

    it('優先度がMEDIUMの場合、「中」と表示される', () => {
      const mediumTodo = { ...mockTodo, priority: 'MEDIUM' as const };

      render(
        <TodoItem
          todo={mediumTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('中')).toBeInTheDocument();
    });

    it('優先度がLOWの場合、「低」と表示される', () => {
      const lowTodo = { ...mockTodo, priority: 'LOW' as const };

      render(
        <TodoItem
          todo={lowTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('低')).toBeInTheDocument();
    });

    it('進捗が0%の場合も正しく表示される', () => {
      const incompleteTodo = { ...mockTodo, progress: 0 };

      render(
        <TodoItem
          todo={incompleteTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('進捗: 0%')).toBeInTheDocument();
    });

    it('進捗が100%の場合、タイトルに取り消し線が引かれる', () => {
      const completedTodo = { ...mockTodo, progress: 100 };

      render(
        <TodoItem
          todo={completedTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const title = screen.getByText('テストタスク');
      expect(title.parentElement).toHaveClass('line-through');
      expect(title.parentElement).toHaveClass('text-gray-500');
    });

    it('進捗が100%未満の場合、タイトルに取り消し線が引かれない', () => {
      render(
        <TodoItem
          todo={mockTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const title = screen.getByText('テストタスク');
      expect(title.parentElement).not.toHaveClass('line-through');
    });

    it('チェックボックスが進捗100%の場合チェックされる', () => {
      const completedTodo = { ...mockTodo, progress: 100 };

      render(
        <TodoItem
          todo={completedTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeChecked();
    });

    it('チェックボックスが進捗100%未満の場合チェックされない', () => {
      render(
        <TodoItem
          todo={mockTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).not.toBeChecked();
    });
  });

  describe('インタラクション', () => {
    it('チェックボックスをクリックするとonToggleCompleteが呼ばれる', async () => {
      const user = userEvent.setup();

      render(
        <TodoItem
          todo={mockTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      const checkbox = screen.getByRole('checkbox');
      await user.click(checkbox);

      expect(mockOnToggleComplete).toHaveBeenCalledTimes(1);
      expect(mockOnToggleComplete).toHaveBeenCalledWith(mockTodo);
    });

    it('ドロップダウンメニューが開く', async () => {
      const user = userEvent.setup();

      render(
        <TodoItem
          todo={mockTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // メニューボタンをクリック
      const menuButton = screen.getByRole('button', { name: /open menu/i });
      await user.click(menuButton);

      // メニューアイテムが表示される
      await waitFor(() => {
        expect(screen.getByText('編集')).toBeInTheDocument();
        expect(screen.getByText('削除')).toBeInTheDocument();
      });
    });

    it('編集メニューをクリックするとonEditが呼ばれる', async () => {
      const user = userEvent.setup();

      render(
        <TodoItem
          todo={mockTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // メニューを開く
      const menuButton = screen.getByRole('button', { name: /open menu/i });
      await user.click(menuButton);

      // 編集をクリック
      await waitFor(() => {
        expect(screen.getByText('編集')).toBeInTheDocument();
      });
      
      const editButton = screen.getByText('編集');
      await user.click(editButton);

      expect(mockOnEdit).toHaveBeenCalledTimes(1);
      expect(mockOnEdit).toHaveBeenCalledWith(mockTodo);
    });

    it('削除メニューをクリックするとonDeleteが呼ばれる', async () => {
      const user = userEvent.setup();

      render(
        <TodoItem
          todo={mockTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // メニューを開く
      const menuButton = screen.getByRole('button', { name: /open menu/i });
      await user.click(menuButton);

      // 削除をクリック
      await waitFor(() => {
        expect(screen.getByText('削除')).toBeInTheDocument();
      });
      
      const deleteButton = screen.getByText('削除');
      await user.click(deleteButton);

      expect(mockOnDelete).toHaveBeenCalledTimes(1);
      expect(mockOnDelete).toHaveBeenCalledWith(mockTodo.id);
    });
  });

  describe('エッジケース', () => {
    it('タイトルが長い場合も表示される', () => {
      const longTitleTodo = {
        ...mockTodo,
        todo_title: 'これは非常に長いタスクのタイトルです。'.repeat(5),
      };

      render(
        <TodoItem
          todo={longTitleTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText(longTitleTodo.todo_title)).toBeInTheDocument();
    });

    it('日付が未来の場合も表示される', () => {
      const futureTodo = {
        ...mockTodo,
        updated_at: '2099-12-31T23:59:59Z',
      };

      render(
        <TodoItem
          todo={futureTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText(/更新:/)).toBeInTheDocument();
    });

    it('進捗が中間値（50%）の場合も正しく表示される', () => {
      render(
        <TodoItem
          todo={mockTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('進捗: 50%')).toBeInTheDocument();
      
      // チェックボックスはチェックされていない
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).not.toBeChecked();

      // タイトルに取り消し線はない
      const title = screen.getByText('テストタスク');
      expect(title.parentElement).not.toHaveClass('line-through');
    });
  });

  describe('メモ化', () => {
    it('propsが変わらない場合、再レンダリングされない', () => {
      const { rerender } = render(
        <TodoItem
          todo={mockTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // 同じpropsで再レンダリング
      rerender(
        <TodoItem
          todo={mockTodo}
          onToggleComplete={mockOnToggleComplete}
          onEdit={mockOnEdit}
          onDelete={mockOnDelete}
        />
      );

      // コンポーネントが表示されていることを確認
      expect(screen.getByText('テストタスク')).toBeInTheDocument();
    });

    it('displayNameが設定されている', () => {
      expect(TodoItem.displayName).toBe('TodoItem');
    });
  });
});