import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { TodoCreateFormRelayContainer } from '@/features/todos/components/TodoCreateFormRelayContainer';

/* =========================
   モック対象
========================= */
import { useRelayMutation } from '@/hooks/useRelayMutation';
import { useExclusiveModal, useUIStore } from '@/hooks/useExclusiveModal';
import { TodoCreateForm } from '@/features/todos/components/TodoCreateForm';
import type { TodoFormValues } from '@/features/todos/schemas';

/* =========================
   vi.mock（トップレベル）
========================= */
vi.mock('react-relay', () => ({
  graphql: vi.fn(() => ({})),
}));

vi.mock('@/hooks/useRelayMutation', () => ({
  useRelayMutation: vi.fn(),
}));

vi.mock('@/hooks/useExclusiveModal', () => ({
  useExclusiveModal: vi.fn(),
  useUIStore: vi.fn(),
}));

vi.mock('@/features/todos/components/TodoCreateForm', () => ({
  TodoCreateForm: vi.fn(),
}));

/* =========================
   モック参照
========================= */
const useRelayMutationMock = useRelayMutation as unknown as Mock;
const useExclusiveModalMock = useExclusiveModal as unknown as Mock;
const useUIStoreMock = useUIStore as unknown as Mock;
const TodoCreateFormMock = TodoCreateForm as unknown as Mock;

/* =========================
   ダミーデータ
========================= */
const mockFormValues: TodoFormValues = {
  todo_title: 'テストタスク',
  priority: 'HIGH',
  progress: 50,
};

const makeCreateTodoPayloadResponse = () => ({
  createTodo: {
    __typename: 'CreateTodoPayload' as const,
    todoEdge: {
      __typename: 'TodoEdge',
      node: {
        __typename: 'Todo',
        id: 'server-id-1',
        todoTitle: 'テストタスク',
        priority: 'HIGH',
        progress: 50,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      },
    },
  },
});

const makeValidationErrorResponse = () => ({
  createTodo: {
    __typename: 'ValidationError' as const,
    message: 'タイトルは必須です',
    field: 'todoTitle',
  },
});

/* =========================
   共通モック
========================= */
const mockExecute = vi.fn();
const mockOpen = vi.fn();
const mockClose = vi.fn();

const setupDefaultMocks = (overrides: {
  isOpen?: boolean;
  isInFlight?: boolean;
  currentModalId?: string | null;
} = {}) => {
  const { isOpen = false, isInFlight = false, currentModalId = null } = overrides;

  useRelayMutationMock.mockReturnValue({
    execute: mockExecute,
    isInFlight,
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

  TodoCreateFormMock.mockImplementation((props: {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSubmit: (values: TodoFormValues) => Promise<void>;
    isLoading: boolean;
    disabled: boolean;
  }) => (
    <div
      data-testid="todo-create-form"
      data-open={props.open}
      data-is-loading={props.isLoading}
      data-disabled={props.disabled}
    />
  ));
};

/* =========================
   ヘルパー
========================= */
const getLastProps = () =>
  TodoCreateFormMock.mock.calls.at(-1)?.[0] as {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSubmit: (values: TodoFormValues) => Promise<void>;
    isLoading: boolean;
    disabled: boolean;
  };

/* =========================
   テスト本体
========================= */
describe('TodoCreateFormRelayContainer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  /* --------------------
     レンダリング
  -------------------- */

  describe('レンダリング', () => {
    it('TodoCreateFormがレンダリングされる', () => {
      render(<TodoCreateFormRelayContainer />);
      expect(screen.getByTestId('todo-create-form')).toBeInTheDocument();
    });

    it('TodoCreateFormが1回だけ呼ばれる', () => {
      render(<TodoCreateFormRelayContainer />);
      expect(TodoCreateFormMock).toHaveBeenCalledTimes(1);
    });
  });

  /* --------------------
     propsの受け渡し
  -------------------- */
  /*
    describe('propsの受け渡し', () => {
      describe('open', () => {
        it('isOpen=falseのとき open=falseが渡される', () => {
          setupDefaultMocks({ isOpen: false });
          render(<TodoCreateFormRelayContainer />);
          expect(getLastProps().open).toBe(false);
        });
  
        it('isOpen=trueのとき open=trueが渡される', () => {
          setupDefaultMocks({ isOpen: true });
          render(<TodoCreateFormRelayContainer />);
          expect(getLastProps().open).toBe(true);
        });
      });
  
      describe('isLoading', () => {
        it('isInFlight=falseのとき isLoading=falseが渡される', () => {
          setupDefaultMocks({ isInFlight: false });
          render(<TodoCreateFormRelayContainer />);
          expect(getLastProps().isLoading).toBe(false);
        });
  
        it('isInFlight=trueのとき isLoading=trueが渡される', () => {
          setupDefaultMocks({ isInFlight: true });
          render(<TodoCreateFormRelayContainer />);
          expect(getLastProps().isLoading).toBe(true);
        });
      });
  
      describe('disabled（isLockedByOther）', () => {
        it('currentModalId=nullのとき disabled=falseが渡される', () => {
          setupDefaultMocks({ currentModalId: null, isOpen: false });
          render(<TodoCreateFormRelayContainer />);
          expect(getLastProps().disabled).toBe(false);
        });
  
        it('currentModalIdがありisOpen=falseのとき disabled=trueが渡される', () => {
          setupDefaultMocks({ currentModalId: 'other-modal', isOpen: false });
          render(<TodoCreateFormRelayContainer />);
          expect(getLastProps().disabled).toBe(true);
        });
  
        it('currentModalIdがありisOpen=trueのとき disabled=falseが渡される（自分が開いている）', () => {
          setupDefaultMocks({ currentModalId: 'some-modal', isOpen: true });
          render(<TodoCreateFormRelayContainer />);
          expect(getLastProps().disabled).toBe(false);
        });
      });
    });
  */
  /* --------------------
     handleOpenChange
  -------------------- */
  /*
    describe('handleOpenChange', () => {
      it('newOpen=trueのとき open()が呼ばれる', () => {
        render(<TodoCreateFormRelayContainer />);
        getLastProps().onOpenChange(true);
  
        expect(mockOpen).toHaveBeenCalledTimes(1);
        expect(mockClose).not.toHaveBeenCalled();
      });
  
      it('newOpen=falseのとき close()が呼ばれる', () => {
        render(<TodoCreateFormRelayContainer />);
        getLastProps().onOpenChange(false);
  
        expect(mockClose).toHaveBeenCalledTimes(1);
        expect(mockOpen).not.toHaveBeenCalled();
      });
    });
  */
  /* --------------------
     handleCreateSubmit: executeの呼び出し
  -------------------- */
  /*
    describe('handleCreateSubmit: executeの呼び出し', () => {
      it('executeがフォーム値を変換したvariablesで呼ばれる', async () => {
        mockExecute.mockResolvedValue(makeCreateTodoPayloadResponse());
        render(<TodoCreateFormRelayContainer />);
  
        await waitFor(async () => {
          await getLastProps().onSubmit(mockFormValues);
        });
  
        expect(mockExecute).toHaveBeenCalledTimes(1);
        expect(mockExecute).toHaveBeenCalledWith(
          expect.objectContaining({
            variables: expect.objectContaining({
              input: {
                todoTitle: 'テストタスク',
                priority: 'HIGH',
                progress: 50,
              },
            }),
          })
        );
      });
  
      it('todo_titleがtodoTitleに変換される', async () => {
        mockExecute.mockResolvedValue(makeCreateTodoPayloadResponse());
        render(<TodoCreateFormRelayContainer />);
  
        await waitFor(async () => {
          await getLastProps().onSubmit({ ...mockFormValues, todo_title: 'NewTitle' });
        });
  
        const input = mockExecute.mock.calls[0][0].variables.input;
        expect(input.todoTitle).toBe('NewTitle');
        expect(input).not.toHaveProperty('todo_title');
      });
  
      it('connectionsに固定のConnection IDが渡される', async () => {
        mockExecute.mockResolvedValue(makeCreateTodoPayloadResponse());
        render(<TodoCreateFormRelayContainer />);
  
        await waitFor(async () => {
          await getLastProps().onSubmit(mockFormValues);
        });
  
        const { connections } = mockExecute.mock.calls[0][0].variables;
        expect(connections).toEqual([
          'client:root:__TodoList_todosConnection_connection',
        ]);
      });
  
      it('errorContextに固定の文字列が渡される', async () => {
        mockExecute.mockResolvedValue(makeCreateTodoPayloadResponse());
        render(<TodoCreateFormRelayContainer />);
  
        await waitFor(async () => {
          await getLastProps().onSubmit(mockFormValues);
        });
  
        expect(mockExecute).toHaveBeenCalledWith(
          expect.objectContaining({
            errorContext: 'タスクの作成に失敗しました',
          })
        );
      });
    });
  */
  /* --------------------
     handleCreateSubmit: optimisticResponse
  -------------------- */
  /*
    describe('handleCreateSubmit: optimisticResponse', () => {
      it('optimisticResponseが渡される', async () => {
        mockExecute.mockResolvedValue(makeCreateTodoPayloadResponse());
        render(<TodoCreateFormRelayContainer />);
  
        await waitFor(async () => {
          await getLastProps().onSubmit(mockFormValues);
        });
  
        expect(mockExecute).toHaveBeenCalledWith(
          expect.objectContaining({
            optimisticResponse: expect.objectContaining({
              createTodo: expect.objectContaining({
                __typename: 'CreateTodoPayload',
              }),
            }),
          })
        );
      });
  
      it('optimisticResponseのnodeにフォーム値が反映される', async () => {
        mockExecute.mockResolvedValue(makeCreateTodoPayloadResponse());
        render(<TodoCreateFormRelayContainer />);
  
        await waitFor(async () => {
          await getLastProps().onSubmit(mockFormValues);
        });
  
        const node =
          mockExecute.mock.calls[0][0].optimisticResponse.createTodo.todoEdge.node;
        expect(node.todoTitle).toBe('テストタスク');
        expect(node.priority).toBe('HIGH');
        expect(node.progress).toBe(50);
      });
  
      it('optimisticResponseのidがtemp-から始まる', async () => {
        mockExecute.mockResolvedValue(makeCreateTodoPayloadResponse());
        render(<TodoCreateFormRelayContainer />);
  
        await waitFor(async () => {
          await getLastProps().onSubmit(mockFormValues);
        });
  
        const node =
          mockExecute.mock.calls[0][0].optimisticResponse.createTodo.todoEdge.node;
        expect(node.id).toMatch(/^temp-\d+$/);
      });
  
      it('optimisticResponseのcreatedAt/updatedAtがISO文字列になっている', async () => {
        mockExecute.mockResolvedValue(makeCreateTodoPayloadResponse());
        render(<TodoCreateFormRelayContainer />);
  
        await waitFor(async () => {
          await getLastProps().onSubmit(mockFormValues);
        });
  
        const node =
          mockExecute.mock.calls[0][0].optimisticResponse.createTodo.todoEdge.node;
        expect(node.createdAt).toMatch(
          /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/
        );
        expect(node.updatedAt).toMatch(
          /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/
        );
      });
    });
  */
  /* --------------------
     handleCreateSubmit: レスポンスによる分岐
  -------------------- */
  /*
    describe('handleCreateSubmit: レスポンスによる分岐', () => {
      it('__typename=CreateTodoPayloadのとき close()が呼ばれる', async () => {
        mockExecute.mockResolvedValue(makeCreateTodoPayloadResponse());
        render(<TodoCreateFormRelayContainer />);
  
        await waitFor(async () => {
          await getLastProps().onSubmit(mockFormValues);
        });
  
        expect(mockClose).toHaveBeenCalledTimes(1);
      });
  
      it('__typename=ValidationErrorのとき close()は呼ばれない', async () => {
        mockExecute.mockResolvedValue(makeValidationErrorResponse());
        render(<TodoCreateFormRelayContainer />);
  
        await waitFor(async () => {
          await getLastProps().onSubmit(mockFormValues);
        });
  
        expect(mockClose).not.toHaveBeenCalled();
      });
  
      it('__typename=ValidationErrorのとき 例外は外に伝播しない', async () => {
        mockExecute.mockResolvedValue(makeValidationErrorResponse());
        render(<TodoCreateFormRelayContainer />);
  
        await expect(
          waitFor(async () => {
            await getLastProps().onSubmit(mockFormValues);
          })
        ).resolves.not.toThrow();
      });
    });
  */
  /* --------------------
     handleCreateSubmit: エラー系
  -------------------- */
  /*
    describe('handleCreateSubmit: エラー系', () => {
      it('executeがエラーをスローしてもclose()は呼ばれない', async () => {
        mockExecute.mockRejectedValue(new Error('Relay Error'));
        render(<TodoCreateFormRelayContainer />);
  
        await waitFor(async () => {
          await getLastProps().onSubmit(mockFormValues);
        });
  
        expect(mockClose).not.toHaveBeenCalled();
      });
  
      it('executeがエラーをスローしても例外は外に伝播しない', async () => {
        mockExecute.mockRejectedValue(new Error('Relay Error'));
        render(<TodoCreateFormRelayContainer />);
  
        await expect(
          waitFor(async () => {
            await getLastProps().onSubmit(mockFormValues);
          })
        ).resolves.not.toThrow();
      });
    });
    */
});