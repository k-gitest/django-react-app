import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { Mock } from 'vitest';

/* =========================
   テスト対象
========================= */
import { TodoList } from '@/features/todos/components/TodoList';

/* =========================
   モック対象
========================= */
import { useTodos } from '@/features/todos/hooks/useTodos';
import { TodoItem } from '@/features/todos/components/TodoItem';
import { TodoItemContainer } from '@/features/todos/components/TodoItemContainer';
import type { Todo } from '@/features/todos/types';

/* =========================
   vi.mock（トップレベル）
========================= */
vi.mock('@/features/todos/hooks/useTodos', () => ({
  useTodos: vi.fn(),
}));

vi.mock('@/features/todos/components/TodoItem', () => ({
  TodoItem: vi.fn(),
}));

vi.mock('@/features/todos/components/TodoItemContainer', () => ({
  TodoItemContainer: vi.fn(),
}));

/* =========================
   モック参照
========================= */
const useTodosMock = useTodos as unknown as Mock;
const TodoItemMock = TodoItem as unknown as Mock;
const TodoItemContainerMock = TodoItemContainer as unknown as Mock;

/* =========================
   ダミーデータ
========================= */
const makeTodo = (id: number, overrides: Partial<Todo> = {}): Todo => ({
  id,
  todo_title: `タスク${id}`,
  priority: 'HIGH',
  progress: 0,
  user: 'user1',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-02T00:00:00Z',
  ...overrides,
});

const mockTodos: Todo[] = [
  makeTodo(1),
  makeTodo(2),
  makeTodo(3),
];

/* =========================
   セットアップヘルパー
========================= */
const setupUseTodos = (todos: Todo[] | { data: Todo[] } | null | undefined) => {
  useTodosMock.mockReturnValue({ todos });
};

/* =========================
   テスト本体
========================= */
describe('TodoList', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // TodoItemContainerのデフォルト実装
    TodoItemContainerMock.mockImplementation(({ todo }: { todo: Todo }) => (
      <div data-testid={`todo-item-container-${todo.id}`} data-id={todo.id} />
    ));

    // TodoItemのデフォルト実装
    TodoItemMock.mockImplementation((props: {
      id: number;
      title: string;
      priority: string;
      progress: number;
      updatedAt: string;
      showActions: boolean;
    }) => (
      <div
        data-testid={`todo-item-${props.id}`}
        data-id={props.id}
        data-title={props.title}
        data-priority={props.priority}
        data-progress={props.progress}
        data-show-actions={props.showActions}
      />
    ));

    setupUseTodos(mockTodos);
  });

  /* --------------------
     空タスク表示
  -------------------- */

  describe('空タスク表示', () => {
    it('safeTodosが空配列のとき 空メッセージが表示される', () => {
      setupUseTodos([]);
      render(<TodoList />);

      expect(screen.getByText(
        'まだタスクがありません。新しいタスクを追加しましょう！'
      )).toBeInTheDocument();
    });

    it('safeTodosが空のとき TodoItemContainerはレンダリングされない', () => {
      setupUseTodos([]);
      render(<TodoList />);

      expect(screen.queryByTestId(/^todo-item-container-/)).not.toBeInTheDocument();
    });

    it('safeTodosが空のとき TodoItemはレンダリングされない', () => {
      setupUseTodos([]);
      render(<TodoList />);

      expect(screen.queryByTestId(/^todo-item-/)).not.toBeInTheDocument();
    });
  });

  /* --------------------
     todosの正規化（safeTodos）
  -------------------- */

  describe('todosの正規化（safeTodos）', () => {
    it('配列そのままの場合 正しくレンダリングされる', () => {
      setupUseTodos(mockTodos);
      render(<TodoList />);

      expect(screen.getByTestId('todo-item-container-1')).toBeInTheDocument();
      expect(screen.getByTestId('todo-item-container-2')).toBeInTheDocument();
      expect(screen.getByTestId('todo-item-container-3')).toBeInTheDocument();
    });

    it('{ data: [] }形式の場合 正しくレンダリングされる', () => {
      setupUseTodos({ data: mockTodos } as unknown as Todo[]);
      render(<TodoList />);

      expect(screen.getByTestId('todo-item-container-1')).toBeInTheDocument();
      expect(screen.getByTestId('todo-item-container-2')).toBeInTheDocument();
      expect(screen.getByTestId('todo-item-container-3')).toBeInTheDocument();
    });

    it('{ data: [] }形式でdataが空配列のとき 空メッセージが表示される', () => {
      setupUseTodos({ data: [] } as unknown as Todo[]);
      render(<TodoList />);

      expect(screen.getByText(
        'まだタスクがありません。新しいタスクを追加しましょう！'
      )).toBeInTheDocument();
    });

    it('todosがnullのとき 空メッセージが表示される', () => {
      setupUseTodos(null);
      render(<TodoList />);

      expect(screen.getByText(
        'まだタスクがありません。新しいタスクを追加しましょう！'
      )).toBeInTheDocument();
    });

    it('todosがundefinedのとき 空メッセージが表示される', () => {
      setupUseTodos(undefined);
      render(<TodoList />);

      expect(screen.getByText(
        'まだタスクがありません。新しいタスクを追加しましょう！'
      )).toBeInTheDocument();
    });
  });

  /* --------------------
     showActions=true（デフォルト）
  -------------------- */

  describe('showActions=true（デフォルト）', () => {
    it('TodoItemContainerがtodosの数だけレンダリングされる', () => {
      render(<TodoList />);

      expect(screen.getByTestId('todo-item-container-1')).toBeInTheDocument();
      expect(screen.getByTestId('todo-item-container-2')).toBeInTheDocument();
      expect(screen.getByTestId('todo-item-container-3')).toBeInTheDocument();
    });

    it('TodoItemContainerにtodoが渡される', () => {
      render(<TodoList />);

      const calls = TodoItemContainerMock.mock.calls;
      expect(calls[0][0].todo).toEqual(mockTodos[0]);
      expect(calls[1][0].todo).toEqual(mockTodos[1]);
      expect(calls[2][0].todo).toEqual(mockTodos[2]);
    });

    it('TodoItemは直接レンダリングされない', () => {
      render(<TodoList />);

      expect(TodoItemMock).not.toHaveBeenCalled();
    });

    it('showActionsを明示的にtrueにしてもTodoItemContainerが使われる', () => {
      render(<TodoList showActions={true} />);

      expect(screen.getByTestId('todo-item-container-1')).toBeInTheDocument();
      expect(TodoItemMock).not.toHaveBeenCalled();
    });
  });

  /* --------------------
     showActions=false
  -------------------- */

  describe('showActions=false', () => {
    it('TodoItemがtodosの数だけレンダリングされる', () => {
      render(<TodoList showActions={false} />);

      expect(screen.getByTestId('todo-item-1')).toBeInTheDocument();
      expect(screen.getByTestId('todo-item-2')).toBeInTheDocument();
      expect(screen.getByTestId('todo-item-3')).toBeInTheDocument();
    });

    it('TodoItemContainerは使われない', () => {
      render(<TodoList showActions={false} />);

      expect(TodoItemContainerMock).not.toHaveBeenCalled();
    });

    it('TodoItemにshowActions=falseが渡される', () => {
      render(<TodoList showActions={false} />);

      TodoItemMock.mock.calls.forEach((call) => {
        expect(call[0].showActions).toBe(false);
      });
    });

    it('todo.todo_titleがtitleにマッピングされる', () => {
      render(<TodoList showActions={false} />);

      const firstCall = TodoItemMock.mock.calls[0][0];
      expect(firstCall.title).toBe('タスク1');
    });

    it('todo.updated_atがupdatedAtにマッピングされる', () => {
      render(<TodoList showActions={false} />);

      const firstCall = TodoItemMock.mock.calls[0][0];
      expect(firstCall.updatedAt).toBe(mockTodos[0].updated_at);
    });

    describe('priorityのフォールバック', () => {
      it('priority=nullのとき "MEDIUM"が渡される', () => {
        setupUseTodos([makeTodo(1, { priority: null as unknown as 'HIGH' })]);
        render(<TodoList showActions={false} />);

        expect(screen.getByTestId('todo-item-1')).toHaveAttribute(
          'data-priority',
          'MEDIUM'
        );
      });

      it('priority=undefinedのとき "MEDIUM"が渡される', () => {
        setupUseTodos([makeTodo(1, { priority: undefined as unknown as 'HIGH' })]);
        render(<TodoList showActions={false} />);

        expect(screen.getByTestId('todo-item-1')).toHaveAttribute(
          'data-priority',
          'MEDIUM'
        );
      });

      it('priorityが有効値のとき そのまま渡される', () => {
        setupUseTodos([makeTodo(1, { priority: 'LOW' })]);
        render(<TodoList showActions={false} />);

        expect(screen.getByTestId('todo-item-1')).toHaveAttribute(
          'data-priority',
          'LOW'
        );
      });
    });

    describe('progressのフォールバック', () => {
      it('progress=nullのとき 0が渡される', () => {
        setupUseTodos([makeTodo(1, { progress: null as unknown as number })]);
        render(<TodoList showActions={false} />);

        expect(screen.getByTestId('todo-item-1')).toHaveAttribute(
          'data-progress',
          '0'
        );
      });

      it('progress=undefinedのとき 0が渡される', () => {
        setupUseTodos([makeTodo(1, { progress: undefined as unknown as number })]);
        render(<TodoList showActions={false} />);

        expect(screen.getByTestId('todo-item-1')).toHaveAttribute(
          'data-progress',
          '0'
        );
      });

      it('progress=0のとき 0がそのまま渡される', () => {
        setupUseTodos([makeTodo(1, { progress: 0 })]);
        render(<TodoList showActions={false} />);

        expect(screen.getByTestId('todo-item-1')).toHaveAttribute(
          'data-progress',
          '0'
        );
      });
    });
  });

  /* --------------------
     limitによる表示件数制御
  -------------------- */

  describe('limitによる表示件数制御', () => {
    it('limit=2のとき 先頭2件だけレンダリングされる', () => {
      render(<TodoList limit={2} />);

      expect(screen.getByTestId('todo-item-container-1')).toBeInTheDocument();
      expect(screen.getByTestId('todo-item-container-2')).toBeInTheDocument();
      expect(screen.queryByTestId('todo-item-container-3')).not.toBeInTheDocument();
    });

    it('limit=1のとき 先頭1件だけレンダリングされる', () => {
      render(<TodoList limit={1} />);

      expect(screen.getByTestId('todo-item-container-1')).toBeInTheDocument();
      expect(screen.queryByTestId('todo-item-container-2')).not.toBeInTheDocument();
    });

    it('limitがtodosの件数以上のとき 全件レンダリングされる', () => {
      render(<TodoList limit={10} />);

      expect(screen.getByTestId('todo-item-container-1')).toBeInTheDocument();
      expect(screen.getByTestId('todo-item-container-2')).toBeInTheDocument();
      expect(screen.getByTestId('todo-item-container-3')).toBeInTheDocument();
    });

    it('limitが未指定のとき 全件レンダリングされる', () => {
      render(<TodoList />);

      expect(screen.getByTestId('todo-item-container-1')).toBeInTheDocument();
      expect(screen.getByTestId('todo-item-container-2')).toBeInTheDocument();
      expect(screen.getByTestId('todo-item-container-3')).toBeInTheDocument();
    });

    it('showActions=falseとlimitを組み合わせた場合も正しく動作する', () => {
      render(<TodoList showActions={false} limit={2} />);

      expect(screen.getByTestId('todo-item-1')).toBeInTheDocument();
      expect(screen.getByTestId('todo-item-2')).toBeInTheDocument();
      expect(screen.queryByTestId('todo-item-3')).not.toBeInTheDocument();
    });
  });

  /* --------------------
     keyプロップ（各アイテムの一意性）
  -------------------- */

  describe('各アイテムの一意性', () => {
    it('showActions=trueのとき todo.idがkeyとして使われる', () => {
      render(<TodoList />);

      // key は内部的なReact仕様のため、レンダリング件数と順序で間接検証
      const containers = screen.getAllByTestId(/^todo-item-container-/);
      expect(containers).toHaveLength(mockTodos.length);
    });

    it('showActions=falseのとき todo.idがkeyとして使われる', () => {
      render(<TodoList showActions={false} />);

      const items = screen.getAllByTestId(/^todo-item-/);
      expect(items).toHaveLength(mockTodos.length);
    });
  });
});