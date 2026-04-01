import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'vitest';

/* =========================
   テスト対象
========================= */
import { useTodos } from '@/features/todos/hooks/useTodos';

/* =========================
   モック対象
========================= */

// serviceのimportパスをuse-todos.tsに合わせる
import { todoService } from '@/features/todos/services/index';
import { useApiMutation } from '@/hooks/use-tanstack-query';
import { useApiSuspenseQuery } from '@/hooks/use-suspense-query';
import { queryClient } from '@/lib/queryClient';
import type { Mock } from 'vitest';
import type { Todo, CreateTodoInput, UpdateTodoInput } from '@/features/todos/types';

/* =========================
   vi.mock（すべてトップレベル）
========================= */

vi.mock('@/features/todos/services/index', () => ({
  todoService: {
    getTodos: vi.fn(),
    createTodo: vi.fn(),
    updateTodo: vi.fn(),
    deleteTodo: vi.fn(),
  },
}));

vi.mock('@/hooks/use-tanstack-query', () => ({
  useApiMutation: vi.fn(),
}));

vi.mock('@/hooks/use-suspense-query', () => ({
  useApiSuspenseQuery: vi.fn(),
}));

vi.mock('@/lib/queryClient', () => ({
  queryClient: {
    cancelQueries: vi.fn(),
    getQueryData: vi.fn(),
    setQueryData: vi.fn(),
    invalidateQueries: vi.fn(),
  },
}));

/* =========================
   モック参照
========================= */

const useApiMutationMock = useApiMutation as unknown as Mock;
const useApiSuspenseQueryMock = useApiSuspenseQuery as unknown as Mock;

const mockCreateTodo = todoService.createTodo as Mock;
const mockUpdateTodo = todoService.updateTodo as Mock;
const mockDeleteTodo = todoService.deleteTodo as Mock;

/* =========================
   ダミーデータ
========================= */

const mockTodos: Todo[] = [
  {
    id: 1,
    todo_title: 'Test Todo 1',
    priority: 'HIGH',
    progress: 0,
    user: 'user1',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    todo_title: 'Test Todo 2',
    priority: 'MEDIUM',
    progress: 50,
    user: 'user1',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
];

/* =========================
   wrapper
========================= */

const createWrapper = () => {
  return ({ children }: { children: ReactNode }) => (
    <MemoryRouter>{children}</MemoryRouter>
  );
};

/* =========================
   共通セットアップ
========================= */

// useApiMutationのデフォルト実装
// onMutate→mutationFn→onSettled の流れを再現する
const setupApiMutation = () => {
  useApiMutationMock.mockImplementation(
    ({ mutationFn, onMutate, onError, onSettled }) => {
      type Vars = unknown;
      return {
        mutateAsync: async (variables: Vars) => {
          let context: unknown;
          try {
            // onMutateで楽観的更新
            if (onMutate) context = await onMutate(variables);

            const result = await mutationFn(variables);

            // 成功後にonSettled
            await onSettled?.();
            return result;
          } catch (e) {
            await onError?.(e, variables, context);
            await onSettled?.();
            throw e;
          }
        },
      };
    }
  );
};

/* =========================
   テスト本体
========================= */

describe('useTodos', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // useApiSuspenseQueryのデフォルト: mockTodosを返す
    useApiSuspenseQueryMock.mockReturnValue({
      data: mockTodos,
    });

    setupApiMutation();

    // queryClientのgetQueryDataはデフォルトでmockTodosを返す
    (queryClient.getQueryData as Mock).mockReturnValue(mockTodos);
  });

  /* --------------------
     一覧取得
  -------------------- */

  describe('一覧取得（getTodos）', () => {
    it('useApiSuspenseQueryを正しいqueryKeyとqueryFnで呼ぶ', () => {
      renderHook(() => useTodos(), { wrapper: createWrapper() });

      expect(useApiSuspenseQueryMock).toHaveBeenCalledWith(
        expect.objectContaining({
          queryKey: ['todos'],
          queryFn: todoService.getTodos,
        })
      );
    });

    it('todosにキャッシュのデータが返る', () => {
      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      expect(result.current.todos).toEqual(mockTodos);
    });

    it('dataがundefinedのとき todosは空配列になる', () => {
      useApiSuspenseQueryMock.mockReturnValue({ data: undefined });

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      expect(result.current.todos).toEqual([]);
    });
  });

  /* --------------------
     作成（createTodo）
  -------------------- */

  describe('作成（createTodo）', () => {
    const newTodoInput: CreateTodoInput = {
      todo_title: 'New Todo',
      priority: 'LOW',
      progress: 0,
    };

    const createdTodo: Todo = {
      id: 3,
      ...newTodoInput,
      user: 'user1',
      created_at: '2024-01-03T00:00:00Z',
      updated_at: '2024-01-03T00:00:00Z',
    };

    it('createTodoを呼ぶとtodoService.createTodoが実行される', async () => {
      mockCreateTodo.mockResolvedValue(createdTodo);

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.createTodo(newTodoInput);
      });

      expect(mockCreateTodo).toHaveBeenCalledWith(newTodoInput);
      expect(mockCreateTodo).toHaveBeenCalledTimes(1);
    });

    it('成功時: onMutateで楽観的更新、onSettledでinvalidateQueriesが呼ばれる', async () => {
      mockCreateTodo.mockResolvedValue(createdTodo);

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.createTodo(newTodoInput);
      });

      // onMutate: cancelQueriesとsetQueryDataが呼ばれる
      expect(queryClient.cancelQueries).toHaveBeenCalledWith({
        queryKey: ['todos'],
      });
      expect(queryClient.setQueryData).toHaveBeenCalled();

      // onSettled: invalidateQueriesで同期
      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['todos'],
      });
    });

    it('失敗時: onErrorでロールバックされ、onSettledでinvalidateQueriesが呼ばれる', async () => {
      mockCreateTodo.mockRejectedValue(new Error('Create failed'));

      // getQueryDataでロールバック用のデータを返す
      (queryClient.getQueryData as Mock).mockReturnValue(mockTodos);

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      await expect(
        act(async () => {
          await result.current.createTodo(newTodoInput);
        })
      ).rejects.toThrow('Create failed');

      // onError: previousTodosにロールバック
      expect(queryClient.setQueryData).toHaveBeenCalledWith(
        ['todos'],
        mockTodos
      );

      // onSettled: エラー時もinvalidateQueriesは呼ばれる
      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['todos'],
      });
    });
  });

  /* --------------------
     更新（updateTodo）
  -------------------- */

  describe('更新（updateTodo）', () => {
    const updateInput: UpdateTodoInput = {
      id: 1,
      progress: 100,
    };

    const updatedTodo: Todo = {
      ...mockTodos[0],
      progress: 100,
      updated_at: '2024-01-03T00:00:00Z',
    };

    it('updateTodoを呼ぶとtodoService.updateTodoが実行される', async () => {
      mockUpdateTodo.mockResolvedValue(updatedTodo);

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.updateTodo(updateInput);
      });

      // 旧テストは(id, data)だったが現在の実装は(data)1引数
      expect(mockUpdateTodo).toHaveBeenCalledWith(updateInput);
      expect(mockUpdateTodo).toHaveBeenCalledTimes(1);
    });

    it('成功時: onMutateで楽観的更新、onSettledでinvalidateQueriesが呼ばれる', async () => {
      mockUpdateTodo.mockResolvedValue(updatedTodo);

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.updateTodo(updateInput);
      });

      expect(queryClient.cancelQueries).toHaveBeenCalledWith({
        queryKey: ['todos'],
      });
      expect(queryClient.setQueryData).toHaveBeenCalled();
      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['todos'],
      });
    });

    it('失敗時: onErrorでロールバックされる', async () => {
      mockUpdateTodo.mockRejectedValue(new Error('Update failed'));

      (queryClient.getQueryData as Mock).mockReturnValue(mockTodos);

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      await expect(
        act(async () => {
          await result.current.updateTodo(updateInput);
        })
      ).rejects.toThrow('Update failed');

      // ロールバック: previousTodosが復元される
      expect(queryClient.setQueryData).toHaveBeenCalledWith(
        ['todos'],
        mockTodos
      );
    });
  });

  /* --------------------
     削除（deleteTodo）
  -------------------- */

  describe('削除（deleteTodo）', () => {
    it('deleteTodoを呼ぶとtodoService.deleteTodoがidで実行される', async () => {
      mockDeleteTodo.mockResolvedValue(undefined);

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.deleteTodo(1);
      });

      expect(mockDeleteTodo).toHaveBeenCalledWith(1);
      expect(mockDeleteTodo).toHaveBeenCalledTimes(1);
    });

    it('成功時: onMutateでidのTodoが楽観的に除外され、onSettledでinvalidateQueriesが呼ばれる', async () => {
      mockDeleteTodo.mockResolvedValue(undefined);

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      await act(async () => {
        await result.current.deleteTodo(1);
      });

      expect(queryClient.cancelQueries).toHaveBeenCalledWith({
        queryKey: ['todos'],
      });
      expect(queryClient.setQueryData).toHaveBeenCalled();
      expect(queryClient.invalidateQueries).toHaveBeenCalledWith({
        queryKey: ['todos'],
      });
    });

    it('失敗時: onErrorでロールバックされる', async () => {
      mockDeleteTodo.mockRejectedValue(new Error('Delete failed'));

      (queryClient.getQueryData as Mock).mockReturnValue(mockTodos);

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      await expect(
        act(async () => {
          await result.current.deleteTodo(1);
        })
      ).rejects.toThrow('Delete failed');

      expect(queryClient.setQueryData).toHaveBeenCalledWith(
        ['todos'],
        mockTodos
      );
    });
  });

  /* --------------------
     返り値の構造
  -------------------- */

  describe('返り値の構造', () => {
    it('必要なメソッドとMutationオブジェクトを返す', () => {
      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      expect(typeof result.current.createTodo).toBe('function');
      expect(typeof result.current.updateTodo).toBe('function');
      expect(typeof result.current.deleteTodo).toBe('function');
      expect(result.current.createMutation).toBeDefined();
      expect(result.current.updateMutation).toBeDefined();
      expect(result.current.deleteMutation).toBeDefined();
    });
  });
});