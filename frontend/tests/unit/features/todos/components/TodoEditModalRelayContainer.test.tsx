import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { TodoEditModalRelayContainer } from '@/features/todos/components/TodoEditModalRelayContainer';

/* =========================
   モック対象
========================= */
import { useFragment } from 'react-relay';
import { useRelayMutation } from '@/hooks/useRelayMutation';
import { isPriority } from '@/lib/utils';

/* =========================
   vi.mock（すべてトップレベル）
========================= */

// react-relayをモック（graphqlタグとuseFragmentのみ使用）
vi.mock('react-relay', () => ({
  useFragment: vi.fn(),
  graphql: vi.fn((query) => query), // graphqlタグはそのまま返す
}));

vi.mock('@/hooks/useRelayMutation', () => ({
  useRelayMutation: vi.fn(),
}));

vi.mock('@/lib/utils', () => ({
  isPriority: vi.fn(),
}));

// TodoEditModalを最小限のモックコンポーネントに置き換え
// onSubmit/onOpenChangeを外部から呼び出せるようにpropsを渡す
vi.mock('./TodoEditModal', () => ({
  TodoEditModal: vi.fn(({ open, title, priority, progress, onOpenChange, onSubmit, isSubmitting, id }) => (
    open ? (
      <div data-testid="todo-edit-modal">
        <span data-testid="modal-id">{id}</span>
        <span data-testid="modal-title">{title}</span>
        <span data-testid="modal-priority">{priority}</span>
        <span data-testid="modal-progress">{progress}</span>
        <span data-testid="modal-submitting">{String(isSubmitting)}</span>
        <button
          data-testid="submit-button"
          onClick={() => onSubmit({ todo_title: title, priority, progress })}
        >
          保存
        </button>
        <button
          data-testid="close-button"
          onClick={() => onOpenChange(false)}
        >
          閉じる
        </button>
      </div>
    ) : null
  )),
}));

/* =========================
   モック参照
========================= */

const mockUseFragment = useFragment as Mock;
const mockUseRelayMutation = useRelayMutation as unknown as Mock;
const mockIsPriority = isPriority as Mock;

/* =========================
   ダミーデータ
========================= */

// useFragmentが返すtodoデータ
const mockTodo = {
  id: 'VG9kb1R5cGU6MQ==',
  todoTitle: 'Test Todo',
  priority: 'HIGH',
  progress: 50,
};

/* =========================
   テスト本体
========================= */

describe('TodoEditModalRelayContainer', () => {
  const mockOnClose = vi.fn();
  const mockExecute = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    // useFragmentはmockTodoを返す
    mockUseFragment.mockReturnValue(mockTodo);

    // useRelayMutationのデフォルト: 成功レスポンス
    mockUseRelayMutation.mockReturnValue({
      execute: mockExecute,
      isInFlight: false,
    });

    // isPriorityのデフォルト: 有効な優先度はtrueを返す
    mockIsPriority.mockImplementation((priority: string) =>
      ['HIGH', 'MEDIUM', 'LOW'].includes(priority)
    );
  });

  /* --------------------
     レンダリング
  -------------------- */
  /*
    describe('レンダリング', () => {
      it('TodoEditModalにuseFragmentのデータが渡される', () => {
        render(
          <TodoEditModalRelayContainer
            todoRef={{} as never}
            onClose={mockOnClose}
          />
        );
  
        // useFragmentのデータがpropsに反映される
        expect(screen.getByTestId('modal-id')).toHaveTextContent(mockTodo.id);
        expect(screen.getByTestId('modal-title')).toHaveTextContent(mockTodo.todoTitle);
        expect(screen.getByTestId('modal-priority')).toHaveTextContent(mockTodo.priority);
        expect(screen.getByTestId('modal-progress')).toHaveTextContent(String(mockTodo.progress));
      });
  
      it('isUpdatingがfalseのときisSubmittingはfalse', () => {
        mockUseRelayMutation.mockReturnValue({
          execute: mockExecute,
          isInFlight: false,
        });
  
        render(
          <TodoEditModalRelayContainer todoRef={{} as never} onClose={mockOnClose} />
        );
  
        expect(screen.getByTestId('modal-submitting')).toHaveTextContent('false');
      });
  
      it('isUpdatingがtrueのときisSubmittingはtrue', () => {
        mockUseRelayMutation.mockReturnValue({
          execute: mockExecute,
          isInFlight: true,
        });
  
        render(
          <TodoEditModalRelayContainer todoRef={{} as never} onClose={mockOnClose} />
        );
  
        expect(screen.getByTestId('modal-submitting')).toHaveTextContent('true');
      });
  
      it('priorityが無効な値のとき MEDIUMにフォールバックされる', () => {
        mockUseFragment.mockReturnValue({
          ...mockTodo,
          priority: 'INVALID_PRIORITY',
        });
        // isPriorityが無効な値にfalseを返す
        mockIsPriority.mockReturnValue(false);
  
        render(
          <TodoEditModalRelayContainer todoRef={{} as never} onClose={mockOnClose} />
        );
  
        expect(screen.getByTestId('modal-priority')).toHaveTextContent('MEDIUM');
      });
  
      it('progressがnullのとき 0が渡される', () => {
        mockUseFragment.mockReturnValue({
          ...mockTodo,
          progress: null,
        });
  
        render(
          <TodoEditModalRelayContainer todoRef={{} as never} onClose={mockOnClose} />
        );
  
        expect(screen.getByTestId('modal-progress')).toHaveTextContent('0');
      });
    });
  */
  /* --------------------
     handleSave（onSubmit）
  -------------------- */
  /*
    describe('handleSave（保存ボタン押下時）', () => {
      it('updateTodoが正しい引数で呼ばれる', async () => {
        const user = userEvent.setup();
  
        mockExecute.mockResolvedValue({
          updateTodo: {
            __typename: 'UpdateTodoPayload',
            todo: { ...mockTodo, updatedAt: '2024-01-01T00:00:00Z' },
          },
        });
  
        render(
          <TodoEditModalRelayContainer todoRef={{} as never} onClose={mockOnClose} />
        );
  
        await user.click(screen.getByTestId('submit-button'));
  
        await waitFor(() => {
          expect(mockExecute).toHaveBeenCalledWith(
            expect.objectContaining({
              variables: {
                id: mockTodo.id,
                input: {
                  todoTitle: mockTodo.todoTitle,
                  priority: mockTodo.priority,
                  progress: mockTodo.progress,
                },
              },
              errorContext: 'Todo更新',
            })
          );
        });
      });
  
      it('optimisticResponseが正しく設定される', async () => {
        const user = userEvent.setup();
  
        mockExecute.mockResolvedValue({
          updateTodo: {
            __typename: 'UpdateTodoPayload',
            todo: { ...mockTodo, updatedAt: '2024-01-01T00:00:00Z' },
          },
        });
  
        render(
          <TodoEditModalRelayContainer todoRef={{} as never} onClose={mockOnClose} />
        );
  
        await user.click(screen.getByTestId('submit-button'));
  
        await waitFor(() => {
          const callArg = mockExecute.mock.calls[0][0];
          expect(callArg.optimisticResponse.updateTodo).toMatchObject({
            __typename: 'UpdateTodoPayload',
            todo: {
              id: mockTodo.id,
              todoTitle: mockTodo.todoTitle,
              priority: mockTodo.priority,
              progress: mockTodo.progress,
            },
          });
        });
      });
  
      it('UpdateTodoPayload成功時にonCloseが呼ばれる', async () => {
        const user = userEvent.setup();
  
        mockExecute.mockResolvedValue({
          updateTodo: {
            __typename: 'UpdateTodoPayload',
            todo: { ...mockTodo, updatedAt: '2024-01-01T00:00:00Z' },
          },
        });
  
        render(
          <TodoEditModalRelayContainer todoRef={{} as never} onClose={mockOnClose} />
        );
  
        await user.click(screen.getByTestId('submit-button'));
  
        await waitFor(() => {
          expect(mockOnClose).toHaveBeenCalledTimes(1);
        });
      });
  
      it('__typenameがUpdateTodoPayload以外のとき onCloseは呼ばれない', async () => {
        const user = userEvent.setup();
  
        mockExecute.mockResolvedValue({
          updateTodo: {
            __typename: 'ValidationError',
            message: 'タイトルは必須です',
            field: 'todoTitle',
          },
        });
  
        render(
          <TodoEditModalRelayContainer todoRef={{} as never} onClose={mockOnClose} />
        );
  
        await user.click(screen.getByTestId('submit-button'));
  
        // ValidationError時はonCloseは呼ばれない
        await waitFor(() => {
          expect(mockExecute).toHaveBeenCalledTimes(1);
        });
        expect(mockOnClose).not.toHaveBeenCalled();
      });
  
      it('priorityが無効な値のとき MEDIUMにフォールバックしてmutationを呼ぶ', async () => {
        const user = userEvent.setup();
  
        // isPriorityがformValuesのpriorityに対してfalseを返す
        mockIsPriority.mockReturnValue(false);
  
        mockExecute.mockResolvedValue({
          updateTodo: {
            __typename: 'UpdateTodoPayload',
            todo: { ...mockTodo, updatedAt: '2024-01-01T00:00:00Z' },
          },
        });
  
        render(
          <TodoEditModalRelayContainer todoRef={{} as never} onClose={mockOnClose} />
        );
  
        await user.click(screen.getByTestId('submit-button'));
  
        await waitFor(() => {
          const callArg = mockExecute.mock.calls[0][0];
          expect(callArg.variables.input.priority).toBe('MEDIUM');
        });
      });
  
      it('executeがエラーをスローしたとき onCloseは呼ばれない', async () => {
        const user = userEvent.setup();
  
        mockExecute.mockRejectedValue(new Error('Mutation failed'));
  
        render(
          <TodoEditModalRelayContainer todoRef={{} as never} onClose={mockOnClose} />
        );
  
        await user.click(screen.getByTestId('submit-button'));
  
        await waitFor(() => {
          expect(mockExecute).toHaveBeenCalledTimes(1);
        });
        expect(mockOnClose).not.toHaveBeenCalled();
      });
    });
  */
  /* --------------------
     handleOpenChange
  -------------------- */
  /*
    describe('handleOpenChange（モーダルのopen状態変更時）', () => {
      it('open=falseのとき onCloseが呼ばれる', async () => {
        const user = userEvent.setup();
  
        render(
          <TodoEditModalRelayContainer todoRef={{} as never} onClose={mockOnClose} />
        );
  
        await user.click(screen.getByTestId('close-button'));
  
        expect(mockOnClose).toHaveBeenCalledTimes(1);
      });
  
      it('閉じるボタンを複数回押しても onCloseがその都度呼ばれる', async () => {
        const user = userEvent.setup();
  
        // モーダルは常にopenなので何度でも閉じるボタンを押せる
        render(
          <TodoEditModalRelayContainer todoRef={{} as never} onClose={mockOnClose} />
        );
  
        await user.click(screen.getByTestId('close-button'));
        await user.click(screen.getByTestId('close-button'));
  
        expect(mockOnClose).toHaveBeenCalledTimes(2);
      });
    });
    */
});