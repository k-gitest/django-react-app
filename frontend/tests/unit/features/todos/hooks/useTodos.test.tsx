import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useTodos } from '@/features/todos/hooks/useTodos';
import { todoService } from '@/features/todos/services/todo-service';
import type { ReactNode } from 'react';
import type { Todo, CreateTodoInput, UpdateTodoInput } from '@/features/todos/types';

// モック
vi.mock('@/features/todos/services/todo-service');

// コンソールログを抑制
vi.spyOn(console, 'error').mockImplementation(() => {});
vi.spyOn(console, 'warn').mockImplementation(() => {});
vi.spyOn(console, 'log').mockImplementation(() => {});

describe('useTodos', () => {
  let queryClient: QueryClient;

  // モックデータ
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

  beforeEach(() => {
    // 各テストで新しいQueryClientを作成
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    // モックをクリア
    vi.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
    vi.restoreAllMocks();
  });

  // Wrapper コンポーネント
  const createWrapper = () => {
    return ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };

  describe('一覧取得（getTodos）', () => {
    it('Todoリストを正常に取得できる', async () => {
      vi.mocked(todoService.getTodos).mockResolvedValue(mockTodos);

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      // 初期状態
      expect(result.current.isLoading).toBe(true);
      expect(result.current.todos).toEqual([]);

      // データ取得完了を待つ
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // 取得したデータを確認
      expect(result.current.todos).toEqual(mockTodos);
      expect(todoService.getTodos).toHaveBeenCalledTimes(1);
    });

    it('エラー時にisErrorがtrueになる', async () => {
      vi.mocked(todoService.getTodos).mockRejectedValue(new Error('Fetch failed'));

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.todos).toEqual([]);
    });
  });

  describe('作成（createTodo）', () => {
    it('作成APIが呼ばれる', async () => {
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

      // 初期データ
      vi.mocked(todoService.getTodos).mockResolvedValue(mockTodos);
      vi.mocked(todoService.createTodo).mockResolvedValue(createdTodo);

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      // 初期データ読み込み完了
      await waitFor(() => {
        expect(result.current.todos).toHaveLength(2);
      });

      // 作成を実行
      await act(async () => {
        await result.current.createTodo(newTodoInput);
      });

      // APIが呼ばれたことを確認
      expect(todoService.createTodo).toHaveBeenCalledWith(newTodoInput);
    });

    it('作成失敗時にロールバックされる', async () => {
      const newTodoInput: CreateTodoInput = {
        todo_title: 'New Todo',
        priority: 'LOW',
        progress: 0,
      };

      vi.mocked(todoService.getTodos).mockResolvedValue(mockTodos);
      vi.mocked(todoService.createTodo).mockRejectedValue(new Error('Create failed'));

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.todos).toHaveLength(2);
      });

      // 作成を実行（エラーになる）
      await expect(
        act(async () => {
          await result.current.createTodo(newTodoInput);
        })
      ).rejects.toThrow('Create failed');

      // ロールバック: 元の2件のまま
      expect(result.current.todos).toHaveLength(2);
      expect(result.current.todos).toEqual(mockTodos);
    });
  });

  describe('更新（updateTodo）', () => {
    it('更新APIが呼ばれる', async () => {
      const updateInput: UpdateTodoInput = {
        progress: 100,
      };

      const updatedTodo: Todo = {
        ...mockTodos[0],
        progress: 100,
        updated_at: '2024-01-03T00:00:00Z',
      };

      vi.mocked(todoService.getTodos).mockResolvedValue(mockTodos);
      vi.mocked(todoService.updateTodo).mockResolvedValue(updatedTodo);

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.todos[0].progress).toBe(0);
      });

      // 更新を実行
      await act(async () => {
        await result.current.updateTodo({ id: 1, data: updateInput });
      });

      // APIが呼ばれたことを確認
      expect(todoService.updateTodo).toHaveBeenCalledWith(1, updateInput);
    });

    it('更新失敗時にロールバックされる', async () => {
      const updateInput: UpdateTodoInput = {
        progress: 100,
      };

      vi.mocked(todoService.getTodos).mockResolvedValue(mockTodos);
      vi.mocked(todoService.updateTodo).mockRejectedValue(new Error('Update failed'));

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.todos[0].progress).toBe(0);
      });

      // 更新を実行（エラーになる）
      await expect(
        act(async () => {
          await result.current.updateTodo({ id: 1, data: updateInput });
        })
      ).rejects.toThrow('Update failed');

      // ロールバック: 元のprogressのまま
      expect(result.current.todos[0].progress).toBe(0);
      expect(result.current.todos).toEqual(mockTodos);
    });
  });

  describe('削除（deleteTodo）', () => {
    it('削除APIが呼ばれる', async () => {
      vi.mocked(todoService.getTodos).mockResolvedValue(mockTodos);
      vi.mocked(todoService.deleteTodo).mockResolvedValue(undefined);

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.todos).toHaveLength(2);
      });

      // 削除を実行
      await act(async () => {
        await result.current.deleteTodo(1);
      });

      // APIが呼ばれたことを確認
      expect(todoService.deleteTodo).toHaveBeenCalledWith(1);
    });

    it('削除失敗時にロールバックされる', async () => {
      vi.mocked(todoService.getTodos).mockResolvedValue(mockTodos);
      vi.mocked(todoService.deleteTodo).mockRejectedValue(new Error('Delete failed'));

      const { result } = renderHook(() => useTodos(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.todos).toHaveLength(2);
      });

      // 削除を実行（エラーになる）
      await expect(
        act(async () => {
          await result.current.deleteTodo(1);
        })
      ).rejects.toThrow('Delete failed');

      // ロールバック: 元の2件のまま
      expect(result.current.todos).toHaveLength(2);
      expect(result.current.todos).toEqual(mockTodos);
      expect(result.current.todos.find(todo => todo.id === 1)).toBeDefined();
    });
  });
});