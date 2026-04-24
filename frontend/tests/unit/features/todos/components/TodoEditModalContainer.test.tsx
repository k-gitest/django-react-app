import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { waitFor } from '@testing-library/react';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { TodoEditModalContainer } from '@/features/todos/components/TodoEditModalContainer';

/* =========================
   モック対象
========================= */
import { useTodos } from '@/features/todos/hooks/useTodos';
import { TodoEditModal } from '@/features/todos/components/TodoEditModal';
import type { Todo } from '@/features/todos/types';
import type { TodoFormValues } from '@/features/todos/schemas';

/* =========================
   vi.mock（トップレベル）
========================= */
vi.mock('@/features/todos/hooks/useTodos', () => ({
  useTodos: vi.fn(),
}));

vi.mock('@/features/todos/components/TodoEditModal', () => ({
  TodoEditModal: vi.fn(),
}));

/* =========================
   モック参照
========================= */
const useTodosMock = useTodos as unknown as Mock;
const TodoEditModalMock = TodoEditModal as unknown as Mock;

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
  updated_at: '2024-01-01T00:00:00Z',
};

const mockFormValues: TodoFormValues = {
  todo_title: '更新タスク',
  priority: 'MEDIUM',
  progress: 75,
};

/* =========================
   共通モック
========================= */
const mockUpdateTodo = vi.fn();
const mockOnClose = vi.fn();

/* =========================
   ヘルパー
========================= */
const getLastProps = () =>
  TodoEditModalMock.mock.calls.at(-1)?.[0] as {
    id: number | string;
    title: string;
    priority: 'HIGH' | 'MEDIUM' | 'LOW';
    progress: number;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onSubmit: (values: TodoFormValues) => Promise<void>;
    isSubmitting?: boolean;
  };

/* =========================
   テスト本体
========================= */
describe('TodoEditModalContainer', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    useTodosMock.mockReturnValue({ updateTodo: mockUpdateTodo });

    TodoEditModalMock.mockImplementation((props: ReturnType<typeof getLastProps>) => (
      <div
        data-testid="todo-edit-modal"
        data-id={props.id}
        data-title={props.title}
        data-priority={props.priority}
        data-progress={props.progress}
        data-open={props.open}
      />
    ));
  });

  /* --------------------
     レンダリング
  -------------------- */
  /*
    describe('レンダリング', () => {
      it('TodoEditModalがレンダリングされる', () => {
        render(<TodoEditModalContainer todo={mockTodo} onClose={mockOnClose} />);
        expect(screen.getByTestId('todo-edit-modal')).toBeInTheDocument();
      });
  
      it('TodoEditModalが1回だけ呼ばれる', () => {
        render(<TodoEditModalContainer todo={mockTodo} onClose={mockOnClose} />);
        expect(TodoEditModalMock).toHaveBeenCalledTimes(1);
      });
    });
  */
  /* --------------------
     propsの受け渡し
  -------------------- */
  /*
    describe('propsの受け渡し', () => {
      it('todo.idがidとして渡される', () => {
        render(<TodoEditModalContainer todo={mockTodo} onClose={mockOnClose} />);
        expect(getLastProps().id).toBe(mockTodo.id);
      });
  
      it('todo.todo_titleがtitleにマッピングされる', () => {
        render(<TodoEditModalContainer todo={mockTodo} onClose={mockOnClose} />);
        expect(getLastProps().title).toBe('テストタスク');
      });
  
      it('todo.priorityがpriorityとして渡される', () => {
        render(<TodoEditModalContainer todo={mockTodo} onClose={mockOnClose} />);
        expect(getLastProps().priority).toBe('HIGH');
      });
  
      it('todo.progressがprogressとして渡される', () => {
        render(<TodoEditModalContainer todo={mockTodo} onClose={mockOnClose} />);
        expect(getLastProps().progress).toBe(50);
      });
  
      it('openは常にtrueが渡される', () => {
        render(<TodoEditModalContainer todo={mockTodo} onClose={mockOnClose} />);
        expect(getLastProps().open).toBe(true);
      });
  
      it('onOpenChangeが関数として渡される', () => {
        render(<TodoEditModalContainer todo={mockTodo} onClose={mockOnClose} />);
        expect(typeof getLastProps().onOpenChange).toBe('function');
      });
  
      it('onSubmitが関数として渡される', () => {
        render(<TodoEditModalContainer todo={mockTodo} onClose={mockOnClose} />);
        expect(typeof getLastProps().onSubmit).toBe('function');
      });
  
      describe('priorityのフォールバック', () => {
        it('priority=nullのとき "MEDIUM"が渡される', () => {
          const todo = { ...mockTodo, priority: null as unknown as 'HIGH' };
          render(<TodoEditModalContainer todo={todo} onClose={mockOnClose} />);
          expect(getLastProps().priority).toBe('MEDIUM');
        });
  
        it('priority=undefinedのとき "MEDIUM"が渡される', () => {
          const todo = { ...mockTodo, priority: undefined as unknown as 'HIGH' };
          render(<TodoEditModalContainer todo={todo} onClose={mockOnClose} />);
          expect(getLastProps().priority).toBe('MEDIUM');
        });
  
        it.each(['HIGH', 'MEDIUM', 'LOW'] as const)(
          'priority="%s"のときそのまま渡される',
          (priority) => {
            render(
              <TodoEditModalContainer
                todo={{ ...mockTodo, priority }}
                onClose={mockOnClose}
              />
            );
            expect(getLastProps().priority).toBe(priority);
          }
        );
      });
  
      describe('progressのフォールバック', () => {
        it('progress=nullのとき 0が渡される', () => {
          const todo = { ...mockTodo, progress: null as unknown as number };
          render(<TodoEditModalContainer todo={todo} onClose={mockOnClose} />);
          expect(getLastProps().progress).toBe(0);
        });
  
        it('progress=undefinedのとき 0が渡される', () => {
          const todo = { ...mockTodo, progress: undefined as unknown as number };
          render(<TodoEditModalContainer todo={todo} onClose={mockOnClose} />);
          expect(getLastProps().progress).toBe(0);
        });
  
        it('progress=0のとき 0がそのまま渡される', () => {
          render(
            <TodoEditModalContainer
              todo={{ ...mockTodo, progress: 0 }}
              onClose={mockOnClose}
            />
          );
          expect(getLastProps().progress).toBe(0);
        });
      });
    });
  */
  /* --------------------
     handleOpenChange
  -------------------- */
  /*
    describe('handleOpenChange', () => {
      it('open=falseのとき onCloseが呼ばれる', () => {
        render(<TodoEditModalContainer todo={mockTodo} onClose={mockOnClose} />);
        getLastProps().onOpenChange(false);
  
        expect(mockOnClose).toHaveBeenCalledTimes(1);
      });
  
      it('open=trueのとき onCloseは呼ばれない', () => {
        render(<TodoEditModalContainer todo={mockTodo} onClose={mockOnClose} />);
        getLastProps().onOpenChange(true);
  
        expect(mockOnClose).not.toHaveBeenCalled();
      });
    });
  */
  /* --------------------
     handleSubmit: 正常系
  -------------------- */
  /*
    describe('handleSubmit: 正常系', () => {
      it('updateTodoがtodo.idとフォーム値で呼ばれる', async () => {
        mockUpdateTodo.mockResolvedValue(undefined);
        render(<TodoEditModalContainer todo={mockTodo} onClose={mockOnClose} />);
  
        await waitFor(async () => {
          await getLastProps().onSubmit(mockFormValues);
        });
  
        expect(mockUpdateTodo).toHaveBeenCalledTimes(1);
        expect(mockUpdateTodo).toHaveBeenCalledWith({
          id: mockTodo.id,
          ...mockFormValues,
        });
      });
  
      it('updateTodo成功後にonCloseが呼ばれる', async () => {
        mockUpdateTodo.mockResolvedValue(undefined);
        render(<TodoEditModalContainer todo={mockTodo} onClose={mockOnClose} />);
  
        await waitFor(async () => {
          await getLastProps().onSubmit(mockFormValues);
        });
  
        expect(mockOnClose).toHaveBeenCalledTimes(1);
      });
  
      it('updateTodo完了後にonCloseが呼ばれる（順序保証）', async () => {
        const callOrder: string[] = [];
        mockUpdateTodo.mockImplementation(async () => {
          callOrder.push('updateTodo');
        });
        mockOnClose.mockImplementation(() => {
          callOrder.push('onClose');
        });
  
        render(<TodoEditModalContainer todo={mockTodo} onClose={mockOnClose} />);
  
        await waitFor(async () => {
          await getLastProps().onSubmit(mockFormValues);
        });
  
        expect(callOrder).toEqual(['updateTodo', 'onClose']);
      });
  
      it('idはフォーム値ではなくtodo.idが使われる', async () => {
        mockUpdateTodo.mockResolvedValue(undefined);
        const todo = { ...mockTodo, id: 999 };
        render(<TodoEditModalContainer todo={todo} onClose={mockOnClose} />);
  
        await waitFor(async () => {
          await getLastProps().onSubmit(mockFormValues);
        });
  
        expect(mockUpdateTodo).toHaveBeenCalledWith(
          expect.objectContaining({ id: 999 })
        );
      });
    });
  */
  /* --------------------
     handleSubmit: エラー系
  -------------------- */
  /*
    describe('handleSubmit: エラー系', () => {
      it('updateTodoがエラーをスローしたとき onCloseは呼ばれない', async () => {
        mockUpdateTodo.mockRejectedValue(new Error('Update failed'));
        render(<TodoEditModalContainer todo={mockTodo} onClose={mockOnClose} />);
  
        await expect(
          waitFor(async () => {
            await getLastProps().onSubmit(mockFormValues);
          })
        ).rejects.toThrow('Update failed');
  
        expect(mockOnClose).not.toHaveBeenCalled();
      });
  
      it('updateTodoがエラーをスローしたとき 例外が外に伝播する', async () => {
        const error = new Error('Update failed');
        mockUpdateTodo.mockRejectedValue(error);
        render(<TodoEditModalContainer todo={mockTodo} onClose={mockOnClose} />);
  
        await expect(
          getLastProps().onSubmit(mockFormValues)
        ).rejects.toThrow('Update failed');
      });
    });
    */
});