import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { waitFor } from '@testing-library/react';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { TodoItemContainer } from '@/features/todos/components/TodoItemContainer';

/* =========================
   モック対象
========================= */
import { useTodos } from '@/features/todos/hooks/useTodos';
import { useExclusiveModal, useUIStore } from '@/hooks/useExclusiveModal';
import { TodoItem } from '@/features/todos/components/TodoItem';
import { TodoEditModalContainer } from '@/features/todos/components/TodoEditModalContainer';
import type { Todo } from '@/features/todos/types';

/* =========================
   vi.mock（トップレベル）
========================= */
vi.mock('@/features/todos/hooks/useTodos', () => ({
  useTodos: vi.fn(),
}));

vi.mock('@/hooks/useExclusiveModal', () => ({
  useExclusiveModal: vi.fn(),
  useUIStore: vi.fn(),
}));

vi.mock('@/features/todos/components/TodoItem', () => ({
  TodoItem: vi.fn(),
}));

vi.mock('@/features/todos/components/TodoEditModalContainer', () => ({
  TodoEditModalContainer: vi.fn(),
}));

/* =========================
   モック参照
========================= */
const useTodosMock = useTodos as unknown as Mock;
const useExclusiveModalMock = useExclusiveModal as unknown as Mock;
const useUIStoreMock = useUIStore as unknown as Mock;
const TodoItemMock = TodoItem as unknown as Mock;
const TodoEditModalContainerMock = TodoEditModalContainer as unknown as Mock;

/* =========================
   ダミーデータ
========================= */
const mockTodo: Todo = {
  id: 1,
  todo_title: 'テストタスク',
  priority: 'HIGH',
  progress: 50,
  user: 'user1',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-02T00:00:00Z',
};

/* =========================
   共通モック
========================= */
const mockUpdateTodo = vi.fn();
const mockDeleteTodo = vi.fn();
const mockOpen = vi.fn();
const mockClose = vi.fn();

/* =========================
   セットアップヘルパー
========================= */
const setupDefaultMocks = (overrides: {
  isOpen?: boolean;
  updateIsPending?: boolean;
  deleteIsPending?: boolean;
  currentModalId?: string | null;
} = {}) => {
  const {
    isOpen = false,
    updateIsPending = false,
    deleteIsPending = false,
    currentModalId = null,
  } = overrides;

  useTodosMock.mockReturnValue({
    updateTodo: mockUpdateTodo,
    deleteTodo: mockDeleteTodo,
    updateMutation: { isPending: updateIsPending },
    deleteMutation: { isPending: deleteIsPending },
  });

  useExclusiveModalMock.mockReturnValue({
    isOpen,
    open: mockOpen,
    close: mockClose,
  });

  useUIStoreMock.mockImplementation(
    (selector: (state: { currentModalId: string | null }) => unknown) =>
      selector({ currentModalId })
  );

  TodoItemMock.mockImplementation((props: {
    id: number;
    title: string;
    priority: string;
    progress: number;
    updatedAt: string;
    showActions: boolean;
    onToggleComplete: () => void;
    disabled: boolean;
    onEdit: () => void;
    onDelete: () => void;
  }) => (
    <div
      data-testid="todo-item"
      data-id={props.id}
      data-title={props.title}
      data-priority={props.priority}
      data-progress={props.progress}
      data-disabled={props.disabled}
      data-show-actions={props.showActions}
    />
  ));

  TodoEditModalContainerMock.mockImplementation(() => (
    <div data-testid="todo-edit-modal-container" />
  ));
};

/* =========================
   ヘルパー
========================= */
const getTodoItemProps = () =>
  TodoItemMock.mock.calls.at(-1)?.[0] as {
    id: number;
    title: string;
    priority: 'HIGH' | 'MEDIUM' | 'LOW';
    progress: number;
    updatedAt: string;
    showActions: boolean;
    onToggleComplete: () => Promise<void>;
    disabled: boolean;
    onEdit: () => void;
    onDelete: () => Promise<void>;
  };

const getTodoEditModalContainerProps = () =>
  TodoEditModalContainerMock.mock.calls.at(-1)?.[0] as {
    todo: Todo;
    onClose: () => void;
  };

/* =========================
   テスト本体
========================= */
describe('TodoItemContainer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
    vi.spyOn(window, 'confirm').mockReturnValue(true);
  });

  /* --------------------
     レンダリング
  -------------------- */

  describe('レンダリング', () => {
    it('TodoItemがレンダリングされる', () => {
      render(<TodoItemContainer todo={mockTodo} />);
      expect(screen.getByTestId('todo-item')).toBeInTheDocument();
    });

    it('isOpen=falseのとき TodoEditModalContainerはレンダリングされない', () => {
      setupDefaultMocks({ isOpen: false });
      render(<TodoItemContainer todo={mockTodo} />);
      expect(screen.queryByTestId('todo-edit-modal-container')).not.toBeInTheDocument();
    });

    it('isOpen=trueのとき TodoEditModalContainerがレンダリングされる', () => {
      setupDefaultMocks({ isOpen: true });
      render(<TodoItemContainer todo={mockTodo} />);
      expect(screen.getByTestId('todo-edit-modal-container')).toBeInTheDocument();
    });
  });

  /* --------------------
     TodoItemへのprops
  -------------------- */

  describe('TodoItemへのprops', () => {
    it('todo.idがidとして渡される', () => {
      render(<TodoItemContainer todo={mockTodo} />);
      expect(getTodoItemProps().id).toBe(mockTodo.id);
    });

    it('todo.todo_titleがtitleにマッピングされる', () => {
      render(<TodoItemContainer todo={mockTodo} />);
      expect(getTodoItemProps().title).toBe('テストタスク');
    });

    it('todo.priorityがpriorityとして渡される', () => {
      render(<TodoItemContainer todo={mockTodo} />);
      expect(getTodoItemProps().priority).toBe('HIGH');
    });

    it('todo.progressがprogressとして渡される', () => {
      render(<TodoItemContainer todo={mockTodo} />);
      expect(getTodoItemProps().progress).toBe(50);
    });

    it('todo.updated_atがupdatedAtとして渡される', () => {
      render(<TodoItemContainer todo={mockTodo} />);
      expect(getTodoItemProps().updatedAt).toBe(mockTodo.updated_at);
    });

    it('showActionsは常にtrueが渡される', () => {
      render(<TodoItemContainer todo={mockTodo} />);
      expect(getTodoItemProps().showActions).toBe(true);
    });

    describe('priorityのフォールバック', () => {
      it('priority=nullのとき "MEDIUM"が渡される', () => {
        const todo = { ...mockTodo, priority: null as unknown as 'HIGH' };
        render(<TodoItemContainer todo={todo} />);
        expect(getTodoItemProps().priority).toBe('MEDIUM');
      });

      it('priority=undefinedのとき "MEDIUM"が渡される', () => {
        const todo = { ...mockTodo, priority: undefined as unknown as 'HIGH' };
        render(<TodoItemContainer todo={todo} />);
        expect(getTodoItemProps().priority).toBe('MEDIUM');
      });
    });

    describe('progressのフォールバック', () => {
      it('progress=nullのとき 0が渡される', () => {
        const todo = { ...mockTodo, progress: null as unknown as number };
        render(<TodoItemContainer todo={todo} />);
        expect(getTodoItemProps().progress).toBe(0);
      });

      it('progress=undefinedのとき 0が渡される', () => {
        const todo = { ...mockTodo, progress: undefined as unknown as number };
        render(<TodoItemContainer todo={todo} />);
        expect(getTodoItemProps().progress).toBe(0);
      });
    });
  });

  /* --------------------
     isDisabledの計算
  -------------------- */

  describe('isDisabledの計算', () => {
    it('すべてfalseのとき disabled=falseが渡される', () => {
      setupDefaultMocks({
        updateIsPending: false,
        deleteIsPending: false,
        currentModalId: null,
      });
      render(<TodoItemContainer todo={mockTodo} />);
      expect(getTodoItemProps().disabled).toBe(false);
    });

    it('updateMutation.isPending=trueのとき disabled=trueが渡される', () => {
      setupDefaultMocks({ updateIsPending: true });
      render(<TodoItemContainer todo={mockTodo} />);
      expect(getTodoItemProps().disabled).toBe(true);
    });

    it('deleteMutation.isPending=trueのとき disabled=trueが渡される', () => {
      setupDefaultMocks({ deleteIsPending: true });
      render(<TodoItemContainer todo={mockTodo} />);
      expect(getTodoItemProps().disabled).toBe(true);
    });

    it('isLockedByOther=trueのとき disabled=trueが渡される', () => {
      setupDefaultMocks({ currentModalId: 'other-modal', isOpen: false });
      render(<TodoItemContainer todo={mockTodo} />);
      expect(getTodoItemProps().disabled).toBe(true);
    });

    it('自分がモーダルを開いているとき disabled=falseが渡される', () => {
      setupDefaultMocks({ currentModalId: 'some-modal', isOpen: true });
      render(<TodoItemContainer todo={mockTodo} />);
      expect(getTodoItemProps().disabled).toBe(false);
    });

    it('3条件のうち複数trueでも disabled=trueが渡される', () => {
      setupDefaultMocks({
        updateIsPending: true,
        deleteIsPending: true,
        currentModalId: 'other-modal',
        isOpen: false,
      });
      render(<TodoItemContainer todo={mockTodo} />);
      expect(getTodoItemProps().disabled).toBe(true);
    });
  });

  /* --------------------
     handleEdit
  -------------------- */

  describe('handleEdit', () => {
    it('onEditとしてopen関数が直接渡される（同一参照）', () => {
      render(<TodoItemContainer todo={mockTodo} />);
      expect(getTodoItemProps().onEdit).toBe(mockOpen);
    });

    it('onEditを呼ぶとopen()が実行される', () => {
      render(<TodoItemContainer todo={mockTodo} />);
      getTodoItemProps().onEdit();
      expect(mockOpen).toHaveBeenCalledTimes(1);
    });
  });

  /* --------------------
     handleToggleComplete
  -------------------- */

  describe('handleToggleComplete', () => {
    it('progress=100のとき updateTodoにprogress=0で呼ばれる', async () => {
      mockUpdateTodo.mockResolvedValue(undefined);
      const todo = { ...mockTodo, progress: 100 };
      render(<TodoItemContainer todo={todo} />);

      await waitFor(async () => {
        await getTodoItemProps().onToggleComplete();
      });

      expect(mockUpdateTodo).toHaveBeenCalledWith({ id: todo.id, progress: 0 });
    });

    it('progress=0のとき updateTodoにprogress=100で呼ばれる', async () => {
      mockUpdateTodo.mockResolvedValue(undefined);
      const todo = { ...mockTodo, progress: 0 };
      render(<TodoItemContainer todo={todo} />);

      await waitFor(async () => {
        await getTodoItemProps().onToggleComplete();
      });

      expect(mockUpdateTodo).toHaveBeenCalledWith({ id: todo.id, progress: 100 });
    });

    it('progress=50（100以外）のとき updateTodoにprogress=100で呼ばれる', async () => {
      mockUpdateTodo.mockResolvedValue(undefined);
      render(<TodoItemContainer todo={mockTodo} />);

      await waitFor(async () => {
        await getTodoItemProps().onToggleComplete();
      });

      expect(mockUpdateTodo).toHaveBeenCalledWith({ id: mockTodo.id, progress: 100 });
    });

    it('todo.idが正しく渡される', async () => {
      mockUpdateTodo.mockResolvedValue(undefined);
      const todo = { ...mockTodo, id: 42 };
      render(<TodoItemContainer todo={todo} />);

      await waitFor(async () => {
        await getTodoItemProps().onToggleComplete();
      });

      expect(mockUpdateTodo).toHaveBeenCalledWith(
        expect.objectContaining({ id: 42 })
      );
    });
  });

  /* --------------------
     handleDelete
  -------------------- */

  describe('handleDelete', () => {
    it('confirmがtrueのとき deleteTodoがtodo.idで呼ばれる', async () => {
      vi.spyOn(window, 'confirm').mockReturnValue(true);
      mockDeleteTodo.mockResolvedValue(undefined);
      render(<TodoItemContainer todo={mockTodo} />);

      await waitFor(async () => {
        await getTodoItemProps().onDelete();
      });

      expect(mockDeleteTodo).toHaveBeenCalledTimes(1);
      expect(mockDeleteTodo).toHaveBeenCalledWith(mockTodo.id);
    });

    it('confirmがfalseのとき deleteTodoは呼ばれない', async () => {
      vi.spyOn(window, 'confirm').mockReturnValue(false);
      render(<TodoItemContainer todo={mockTodo} />);

      await waitFor(async () => {
        await getTodoItemProps().onDelete();
      });

      expect(mockDeleteTodo).not.toHaveBeenCalled();
    });

    it('confirmに確認メッセージが渡される', async () => {
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
      render(<TodoItemContainer todo={mockTodo} />);

      await getTodoItemProps().onDelete();

      expect(confirmSpy).toHaveBeenCalledWith('本当にこのタスクを削除しますか？');
    });
  });

  /* --------------------
     TodoEditModalContainerへのprops
  -------------------- */

  describe('TodoEditModalContainerへのprops', () => {
    it('todoがそのまま渡される', () => {
      setupDefaultMocks({ isOpen: true });
      render(<TodoItemContainer todo={mockTodo} />);

      expect(getTodoEditModalContainerProps().todo).toEqual(mockTodo);
    });

    it('onCloseとしてclose関数が直接渡される（同一参照）', () => {
      setupDefaultMocks({ isOpen: true });
      render(<TodoItemContainer todo={mockTodo} />);

      expect(getTodoEditModalContainerProps().onClose).toBe(mockClose);
    });

    it('onCloseを呼ぶとclose()が実行される', () => {
      setupDefaultMocks({ isOpen: true });
      render(<TodoItemContainer todo={mockTodo} />);

      getTodoEditModalContainerProps().onClose();
      expect(mockClose).toHaveBeenCalledTimes(1);
    });
  });
});