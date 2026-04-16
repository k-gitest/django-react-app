import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { TodoItemRelayContainer } from '@/features/todos/components/TodoItemRelayContainer';

/* =========================
   モック対象
========================= */
import { useFragment } from 'react-relay';
import { useRelayMutation } from '@/hooks/useRelayMutation';
import { useExclusiveModal, useUIStore } from '@/hooks/useExclusiveModal';
import { TodoItem } from '@/features/todos/components/TodoItem';
import { TodoEditModalRelayContainer } from '@/features/todos/components/TodoEditModalRelayContainer';
import { isPriority } from '@/lib/utils';

/* =========================
   vi.mock（トップレベル）
========================= */
vi.mock('react-relay', () => ({
  useFragment: vi.fn(),
  graphql: vi.fn(() => ({})),
}));

vi.mock('@/hooks/useRelayMutation', () => ({
  useRelayMutation: vi.fn(),
}));

vi.mock('@/hooks/useExclusiveModal', () => ({
  useExclusiveModal: vi.fn(),
  useUIStore: vi.fn(),
}));

vi.mock('@/features/todos/components/TodoItem', () => ({
  TodoItem: vi.fn(),
}));

vi.mock('@/features/todos/components/TodoEditModalRelayContainer', () => ({
  TodoEditModalRelayContainer: vi.fn(),
}));

vi.mock('@/lib/utils', () => ({
  isPriority: vi.fn(),
}));

/* =========================
   モック参照
========================= */
const useFragmentMock = useFragment as unknown as Mock;
const useRelayMutationMock = useRelayMutation as unknown as Mock;
const useExclusiveModalMock = useExclusiveModal as unknown as Mock;
const useUIStoreMock = useUIStore as unknown as Mock;
const TodoItemMock = TodoItem as unknown as Mock;
const TodoEditModalRelayContainerMock = TodoEditModalRelayContainer as unknown as Mock;
const isPriorityMock = isPriority as unknown as Mock;

/* =========================
   ダミーデータ
========================= */
const mockTodoFragment = {
  id: 'todo-relay-id-1',
  todoTitle: 'テストタスク',
  priority: 'HIGH',
  progress: 50,
  updatedAt: '2024-01-02T00:00:00Z',
};

/* =========================
   共通モック
========================= */
const mockUpdateExecute = vi.fn();
const mockDeleteExecute = vi.fn();
const mockOpen = vi.fn();
const mockClose = vi.fn();

/* =========================
   セットアップヘルパー
========================= */
const setupDefaultMocks = (overrides: {
  isOpen?: boolean;
  isUpdating?: boolean;
  isDeleting?: boolean;
  currentModalId?: string | null;
  todo?: Partial<typeof mockTodoFragment>;
  isPriorityResult?: boolean;
} = {}) => {
  const {
    isOpen = false,
    isUpdating = false,
    isDeleting = false,
    currentModalId = null,
    todo = {},
    isPriorityResult = true,
  } = overrides;

  useFragmentMock.mockReturnValue({ ...mockTodoFragment, ...todo });

  // useRelayMutationは呼び出し順でupdate→deleteを返す
  useRelayMutationMock
    .mockReturnValueOnce({ execute: mockUpdateExecute, isInFlight: isUpdating })
    .mockReturnValueOnce({ execute: mockDeleteExecute, isInFlight: isDeleting });

  useExclusiveModalMock.mockReturnValue({
    isOpen,
    open: mockOpen,
    close: mockClose,
  });

  useUIStoreMock.mockImplementation(
    (selector: (state: { currentModalId: string | null }) => unknown) =>
      selector({ currentModalId })
  );

  isPriorityMock.mockReturnValue(isPriorityResult);

  TodoItemMock.mockImplementation((props: {
    id: string;
    title: string;
    priority: string;
    progress: number;
    updatedAt: string;
    showActions?: boolean;
    disabled: boolean;
    onEdit: () => void;
    onDelete: () => void;
    onToggleComplete: () => void;
  }) => (
    <div
      data-testid="todo-item"
      data-id={props.id}
      data-title={props.title}
      data-priority={props.priority}
      data-progress={props.progress}
      data-disabled={props.disabled}
    />
  ));

  TodoEditModalRelayContainerMock.mockImplementation(() => (
    <div data-testid="todo-edit-modal-relay-container" />
  ));
};

/* =========================
   ヘルパー
========================= */
const mockTodoRef = {} as never;

const getTodoItemProps = () =>
  TodoItemMock.mock.calls.at(-1)?.[0] as {
    id: string;
    title: string;
    priority: string;
    progress: number;
    updatedAt: string;
    showActions?: boolean;
    disabled: boolean;
    onEdit: () => void;
    onDelete: () => Promise<void>;
    onToggleComplete: () => Promise<void>;
  };

const getTodoEditModalRelayContainerProps = () =>
  TodoEditModalRelayContainerMock.mock.calls.at(-1)?.[0] as {
    todoRef: typeof mockTodoFragment;
    onClose: () => void;
  };

/* =========================
   テスト本体
========================= */
describe('TodoItemRelayContainer', () => {
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
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
      expect(screen.getByTestId('todo-item')).toBeInTheDocument();
    });

    it('isOpen=falseのとき TodoEditModalRelayContainerはレンダリングされない', () => {
      setupDefaultMocks({ isOpen: false });
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
      expect(screen.queryByTestId('todo-edit-modal-relay-container')).not.toBeInTheDocument();
    });

    it('isOpen=trueのとき TodoEditModalRelayContainerがレンダリングされる', () => {
      setupDefaultMocks({ isOpen: true });
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
      expect(screen.getByTestId('todo-edit-modal-relay-container')).toBeInTheDocument();
    });
  });

  /* --------------------
     useFragmentの呼び出し
  -------------------- */

  describe('useFragmentの呼び出し', () => {
    it('useFragmentがtodoRefで呼ばれる', () => {
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
      expect(useFragmentMock).toHaveBeenCalledWith(
        expect.anything(),
        mockTodoRef
      );
    });
  });

  /* --------------------
     TodoItemへのprops
  -------------------- */

  describe('TodoItemへのprops', () => {
    it('todo.idがidとして渡される', () => {
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
      expect(getTodoItemProps().id).toBe(mockTodoFragment.id);
    });

    it('todo.todoTitleがtitleとして渡される', () => {
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
      expect(getTodoItemProps().title).toBe('テストタスク');
    });

    it('todo.updatedAtがupdatedAtとして渡される', () => {
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
      expect(getTodoItemProps().updatedAt).toBe(mockTodoFragment.updatedAt);
    });

    it('showActionsがpropsから渡される', () => {
      render(<TodoItemRelayContainer todoRef={mockTodoRef} showActions={true} />);
      expect(getTodoItemProps().showActions).toBe(true);
    });

    it('showActionsが未指定のとき undefinedが渡される', () => {
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
      expect(getTodoItemProps().showActions).toBeUndefined();
    });

    describe('priorityのバリデーション（isPriority）', () => {
      it('isPriorityがtrueのとき todo.priorityがそのまま渡される', () => {
        isPriorityMock.mockReturnValue(true);
        setupDefaultMocks({ todo: { priority: 'LOW' }, isPriorityResult: true });
        render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
        expect(getTodoItemProps().priority).toBe('LOW');
      });

      it('isPriorityがfalseのとき "MEDIUM"にフォールバックされる', () => {
        setupDefaultMocks({ todo: { priority: 'INVALID' }, isPriorityResult: false });
        render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
        expect(getTodoItemProps().priority).toBe('MEDIUM');
      });

      it('isPriorityにtodo.priorityが渡される', () => {
        render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
        expect(isPriorityMock).toHaveBeenCalledWith(mockTodoFragment.priority);
      });
    });

    describe('progressのフォールバック', () => {
      it('progress=nullのとき 0が渡される', () => {
        setupDefaultMocks({ todo: { progress: null as unknown as number } });
        render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
        expect(getTodoItemProps().progress).toBe(0);
      });

      it('progress=50のとき そのまま渡される', () => {
        render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
        expect(getTodoItemProps().progress).toBe(50);
      });
    });
  });

  /* --------------------
     isDisabledの計算
  -------------------- */

  describe('isDisabledの計算', () => {
    it('すべてfalseのとき disabled=falseが渡される', () => {
      setupDefaultMocks({
        isUpdating: false,
        isDeleting: false,
        currentModalId: null,
      });
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
      expect(getTodoItemProps().disabled).toBe(false);
    });

    it('isUpdating=trueのとき disabled=trueが渡される', () => {
      setupDefaultMocks({ isUpdating: true });
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
      expect(getTodoItemProps().disabled).toBe(true);
    });

    it('isDeleting=trueのとき disabled=trueが渡される', () => {
      setupDefaultMocks({ isDeleting: true });
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
      expect(getTodoItemProps().disabled).toBe(true);
    });

    it('isLockedByOther=trueのとき disabled=trueが渡される', () => {
      setupDefaultMocks({ currentModalId: 'other-modal', isOpen: false });
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
      expect(getTodoItemProps().disabled).toBe(true);
    });

    it('自分がモーダルを開いているとき disabled=falseが渡される', () => {
      setupDefaultMocks({ currentModalId: 'some-modal', isOpen: true });
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
      expect(getTodoItemProps().disabled).toBe(false);
    });
  });

  /* --------------------
     handleEdit
  -------------------- */

  describe('handleEdit', () => {
    it('onEditとしてopen関数が直接渡される（同一参照）', () => {
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);
      expect(getTodoItemProps().onEdit).toBe(mockOpen);
    });
  });

  /* --------------------
     handleToggle
  -------------------- */

  describe('handleToggle', () => {
    it('progress=100のとき nextProgress=0でupdateTodoが呼ばれる', async () => {
      mockUpdateExecute.mockResolvedValue(undefined);
      setupDefaultMocks({ todo: { progress: 100 } });
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      await waitFor(async () => {
        await getTodoItemProps().onToggleComplete();
      });

      const { variables } = mockUpdateExecute.mock.calls[0][0];
      expect(variables.input.progress).toBe(0);
    });

    it('progress=0のとき nextProgress=100でupdateTodoが呼ばれる', async () => {
      mockUpdateExecute.mockResolvedValue(undefined);
      setupDefaultMocks({ todo: { progress: 0 } });
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      await waitFor(async () => {
        await getTodoItemProps().onToggleComplete();
      });

      const { variables } = mockUpdateExecute.mock.calls[0][0];
      expect(variables.input.progress).toBe(100);
    });

    it('variablesにtodo.idが含まれる', async () => {
      mockUpdateExecute.mockResolvedValue(undefined);
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      await waitFor(async () => {
        await getTodoItemProps().onToggleComplete();
      });

      expect(mockUpdateExecute).toHaveBeenCalledWith(
        expect.objectContaining({
          variables: expect.objectContaining({ id: mockTodoFragment.id }),
        })
      );
    });

    it('optimisticResponseが渡される', async () => {
      mockUpdateExecute.mockResolvedValue(undefined);
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      await waitFor(async () => {
        await getTodoItemProps().onToggleComplete();
      });

      expect(mockUpdateExecute).toHaveBeenCalledWith(
        expect.objectContaining({
          optimisticResponse: expect.objectContaining({
            updateTodo: expect.objectContaining({
              __typename: 'UpdateTodoPayload',
            }),
          }),
        })
      );
    });

    it('optimisticResponseのnodeにtodo情報が反映される', async () => {
      mockUpdateExecute.mockResolvedValue(undefined);
      setupDefaultMocks({ todo: { progress: 50 } });
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      await waitFor(async () => {
        await getTodoItemProps().onToggleComplete();
      });

      const { todo } = mockUpdateExecute.mock.calls[0][0].optimisticResponse.updateTodo;
      expect(todo.id).toBe(mockTodoFragment.id);
      expect(todo.todoTitle).toBe(mockTodoFragment.todoTitle);
      expect(todo.priority).toBe(mockTodoFragment.priority);
      expect(todo.progress).toBe(100); // 50→100
    });

    it('optimisticResponseのupdatedAtがISO文字列になっている', async () => {
      mockUpdateExecute.mockResolvedValue(undefined);
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      await waitFor(async () => {
        await getTodoItemProps().onToggleComplete();
      });

      const { todo } = mockUpdateExecute.mock.calls[0][0].optimisticResponse.updateTodo;
      expect(todo.updatedAt).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
    });

    it('errorContextに "進捗更新" が渡される', async () => {
      mockUpdateExecute.mockResolvedValue(undefined);
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      await waitFor(async () => {
        await getTodoItemProps().onToggleComplete();
      });

      expect(mockUpdateExecute).toHaveBeenCalledWith(
        expect.objectContaining({ errorContext: '進捗更新' })
      );
    });

    it('updateTodoがエラーをスローしても例外は外に伝播しない', async () => {
      mockUpdateExecute.mockRejectedValue(new Error('Update failed'));
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      await expect(
        waitFor(async () => {
          await getTodoItemProps().onToggleComplete();
        })
      ).resolves.not.toThrow();
    });
  });

  /* --------------------
     handleDelete
  -------------------- */

  describe('handleDelete', () => {
    it('confirmがtrueのとき deleteTodoが呼ばれる', async () => {
      vi.spyOn(window, 'confirm').mockReturnValue(true);
      mockDeleteExecute.mockResolvedValue(undefined);
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      await waitFor(async () => {
        await getTodoItemProps().onDelete();
      });

      expect(mockDeleteExecute).toHaveBeenCalledTimes(1);
    });

    it('confirmがfalseのとき deleteTodoは呼ばれない', async () => {
      vi.spyOn(window, 'confirm').mockReturnValue(false);
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      await waitFor(async () => {
        await getTodoItemProps().onDelete();
      });

      expect(mockDeleteExecute).not.toHaveBeenCalled();
    });

    it('confirmに確認メッセージが渡される', async () => {
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      await getTodoItemProps().onDelete();

      expect(confirmSpy).toHaveBeenCalledWith('本当に削除しますか？');
    });

    it('variablesにtodo.idと固定のconnectionsが含まれる', async () => {
      mockDeleteExecute.mockResolvedValue(undefined);
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      await waitFor(async () => {
        await getTodoItemProps().onDelete();
      });

      expect(mockDeleteExecute).toHaveBeenCalledWith(
        expect.objectContaining({
          variables: {
            id: mockTodoFragment.id,
            connections: ['client:root:__TodoList_todosConnection_connection'],
          },
        })
      );
    });

    it('optimisticUpdaterが渡される', async () => {
      mockDeleteExecute.mockResolvedValue(undefined);
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      await waitFor(async () => {
        await getTodoItemProps().onDelete();
      });

      expect(mockDeleteExecute).toHaveBeenCalledWith(
        expect.objectContaining({
          optimisticUpdater: expect.any(Function),
        })
      );
    });

    it('optimisticUpdaterがstore.deleteをtodo.idで呼ぶ', async () => {
      mockDeleteExecute.mockResolvedValue(undefined);
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      await waitFor(async () => {
        await getTodoItemProps().onDelete();
      });

      const { optimisticUpdater } = mockDeleteExecute.mock.calls[0][0];
      const mockStore = { delete: vi.fn() };
      optimisticUpdater(mockStore);

      expect(mockStore.delete).toHaveBeenCalledWith(mockTodoFragment.id);
    });

    it('errorContextに "Todo削除" が渡される', async () => {
      mockDeleteExecute.mockResolvedValue(undefined);
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      await waitFor(async () => {
        await getTodoItemProps().onDelete();
      });

      expect(mockDeleteExecute).toHaveBeenCalledWith(
        expect.objectContaining({ errorContext: 'Todo削除' })
      );
    });

    it('deleteTodoがエラーをスローしても例外は外に伝播しない', async () => {
      mockDeleteExecute.mockRejectedValue(new Error('Delete failed'));
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      await expect(
        waitFor(async () => {
          await getTodoItemProps().onDelete();
        })
      ).resolves.not.toThrow();
    });
  });

  /* --------------------
     TodoEditModalRelayContainerへのprops
  -------------------- */

  describe('TodoEditModalRelayContainerへのprops', () => {
    it('todoRefとしてfragmentデータが渡される', () => {
      setupDefaultMocks({ isOpen: true });
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      expect(getTodoEditModalRelayContainerProps().todoRef).toEqual(
        expect.objectContaining({ id: mockTodoFragment.id })
      );
    });

    it('onCloseとしてclose関数が直接渡される（同一参照）', () => {
      setupDefaultMocks({ isOpen: true });
      render(<TodoItemRelayContainer todoRef={mockTodoRef} />);

      expect(getTodoEditModalRelayContainerProps().onClose).toBe(mockClose);
    });
  });
});