import { describe, it, expect, vi, beforeEach } from 'vitest';
import { todoService } from '@/features/todos/services/todo-service';
import { apiClient } from '@/lib/api-client';
import type { Todo, CreateTodoInput, UpdateTodoInput } from '@/features/todos/types';

// モック
vi.mock('@/lib/api-client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('todoService', () => {
  // モックデータ
  const mockTodo: Todo = {
    id: 1,
    todo_title: 'Test Todo',
    priority: 'HIGH',
    progress: 50,
    user: 'user1',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };

  const mockTodos: Todo[] = [
    mockTodo,
    {
      id: 2,
      todo_title: 'Test Todo 2',
      priority: 'MEDIUM',
      progress: 30,
      user: 'user1',
      created_at: '2024-01-02T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    },
  ];

  beforeEach(() => {
    // モックをクリア
    vi.clearAllMocks();
  });

  // モックレスポンスを作成するヘルパー関数
  const mockApiResponse = <T,>(data: T) => {
    const mockJson = vi.fn().mockResolvedValue(data);
    return {
      json: mockJson,
    } as unknown as ReturnType<typeof apiClient.get>;
  };

  describe('getTodos', () => {
    it('すべてのTodoを取得する', async () => {
      const mockResponse = mockApiResponse(mockTodos);
      vi.mocked(apiClient.get).mockReturnValue(mockResponse);

      const result = await todoService.getTodos();

      // APIが正しく呼ばれたことを確認
      expect(apiClient.get).toHaveBeenCalledWith('todos/');
      expect(apiClient.get).toHaveBeenCalledTimes(1);

      // 結果が正しいことを確認
      expect(result).toEqual(mockTodos);
    });

    it('空配列が返される場合', async () => {
      const mockResponse = mockApiResponse([]);
      vi.mocked(apiClient.get).mockReturnValue(mockResponse);

      const result = await todoService.getTodos();

      expect(apiClient.get).toHaveBeenCalledWith('todos/');
      expect(result).toEqual([]);
    });

    it('エラーが発生した場合はそのまま投げる', async () => {
      const error = new Error('Network Error');
      const mockJson = vi.fn().mockRejectedValue(error);
      vi.mocked(apiClient.get).mockReturnValue({
        json: mockJson,
      } as unknown as ReturnType<typeof apiClient.get>);

      await expect(todoService.getTodos()).rejects.toThrow('Network Error');
      expect(apiClient.get).toHaveBeenCalledWith('todos/');
    });
  });

  describe('createTodo', () => {
    it('新しいTodoを作成する', async () => {
      const createInput: CreateTodoInput = {
        todo_title: 'New Todo',
        priority: 'LOW',
        progress: 0,
      };

      const mockResponse = mockApiResponse(mockTodo);
      vi.mocked(apiClient.post).mockReturnValue(mockResponse);

      const result = await todoService.createTodo(createInput);

      // APIが正しく呼ばれたことを確認
      expect(apiClient.post).toHaveBeenCalledWith('todos/', {
        json: createInput,
      });
      expect(apiClient.post).toHaveBeenCalledTimes(1);

      // 結果が正しいことを確認
      expect(result).toEqual(mockTodo);
    });

    it('必須フィールドのみで作成できる', async () => {
      const minimalInput: CreateTodoInput = {
        todo_title: 'Minimal Todo',
        priority: 'MEDIUM',
        progress: 0,
      };

      const mockResponse = mockApiResponse(mockTodo);
      vi.mocked(apiClient.post).mockReturnValue(mockResponse);

      const result = await todoService.createTodo(minimalInput);

      expect(apiClient.post).toHaveBeenCalledWith('todos/', {
        json: minimalInput,
      });
      expect(result).toEqual(mockTodo);
    });

    it('エラーが発生した場合はそのまま投げる', async () => {
      const createInput: CreateTodoInput = {
        todo_title: 'New Todo',
        priority: 'LOW',
        progress: 0,
      };

      const error = new Error('Validation Error');
      const mockJson = vi.fn().mockRejectedValue(error);
      vi.mocked(apiClient.post).mockReturnValue({
        json: mockJson,
      } as unknown as ReturnType<typeof apiClient.post>);

      await expect(todoService.createTodo(createInput)).rejects.toThrow(
        'Validation Error'
      );

      expect(apiClient.post).toHaveBeenCalledWith('todos/', {
        json: createInput,
      });
    });
  });

  describe('updateTodo', () => {
    it('Todoを更新する', async () => {
      const updateInput: UpdateTodoInput = {
        progress: 100,
      };

      const updatedTodo: Todo = {
        ...mockTodo,
        progress: 100,
        updated_at: '2024-01-02T00:00:00Z',
      };

      const mockResponse = mockApiResponse(updatedTodo);
      vi.mocked(apiClient.patch).mockReturnValue(mockResponse);

      const result = await todoService.updateTodo(1, updateInput);

      // APIが正しく呼ばれたことを確認
      expect(apiClient.patch).toHaveBeenCalledWith('todos/1/', {
        json: updateInput,
      });
      expect(apiClient.patch).toHaveBeenCalledTimes(1);

      // 結果が正しいことを確認
      expect(result).toEqual(updatedTodo);
    });

    it('複数のフィールドを同時に更新できる', async () => {
      const updateInput: UpdateTodoInput = {
        todo_title: 'Updated Title',
        priority: 'HIGH',
        progress: 75,
      };

      const updatedTodo: Todo = {
        ...mockTodo,
        ...updateInput,
        updated_at: '2024-01-02T00:00:00Z',
      };

      const mockResponse = mockApiResponse(updatedTodo);
      vi.mocked(apiClient.patch).mockReturnValue(mockResponse);

      const result = await todoService.updateTodo(1, updateInput);

      expect(apiClient.patch).toHaveBeenCalledWith('todos/1/', {
        json: updateInput,
      });
      expect(result).toEqual(updatedTodo);
    });

    it('1つのフィールドのみを更新できる', async () => {
      const updateInput: UpdateTodoInput = {
        todo_title: 'New Title Only',
      };

      const updatedTodo: Todo = {
        ...mockTodo,
        todo_title: 'New Title Only',
        updated_at: '2024-01-02T00:00:00Z',
      };

      const mockResponse = mockApiResponse(updatedTodo);
      vi.mocked(apiClient.patch).mockReturnValue(mockResponse);

      const result = await todoService.updateTodo(1, updateInput);

      expect(apiClient.patch).toHaveBeenCalledWith('todos/1/', {
        json: updateInput,
      });
      expect(result).toEqual(updatedTodo);
    });

    it('存在しないIDで404エラーが発生する', async () => {
      const updateInput: UpdateTodoInput = {
        progress: 100,
      };

      const error = new Error('Not Found');
      const mockJson = vi.fn().mockRejectedValue(error);
      vi.mocked(apiClient.patch).mockReturnValue({
        json: mockJson,
      } as unknown as ReturnType<typeof apiClient.patch>);

      await expect(todoService.updateTodo(999, updateInput)).rejects.toThrow(
        'Not Found'
      );

      expect(apiClient.patch).toHaveBeenCalledWith('todos/999/', {
        json: updateInput,
      });
    });
  });

  describe('deleteTodo', () => {
    it('Todoを削除する', async () => {
      vi.mocked(apiClient.delete).mockResolvedValue(undefined as never);

      await todoService.deleteTodo(1);

      // APIが正しく呼ばれたことを確認
      expect(apiClient.delete).toHaveBeenCalledWith('todos/1/');
      expect(apiClient.delete).toHaveBeenCalledTimes(1);
    });

    it('削除は戻り値がない', async () => {
      vi.mocked(apiClient.delete).mockResolvedValue(undefined as never);

      const result = await todoService.deleteTodo(1);

      expect(result).toBeUndefined();
    });

    it('複数のTodoを順番に削除できる', async () => {
      vi.mocked(apiClient.delete).mockResolvedValue(undefined as never);

      await todoService.deleteTodo(1);
      await todoService.deleteTodo(2);
      await todoService.deleteTodo(3);

      expect(apiClient.delete).toHaveBeenCalledTimes(3);
      expect(apiClient.delete).toHaveBeenNthCalledWith(1, 'todos/1/');
      expect(apiClient.delete).toHaveBeenNthCalledWith(2, 'todos/2/');
      expect(apiClient.delete).toHaveBeenNthCalledWith(3, 'todos/3/');
    });

    it('存在しないIDで404エラーが発生する', async () => {
      const error = new Error('Not Found');
      vi.mocked(apiClient.delete).mockRejectedValue(error);

      await expect(todoService.deleteTodo(999)).rejects.toThrow('Not Found');

      expect(apiClient.delete).toHaveBeenCalledWith('todos/999/');
    });

    it('削除中にネットワークエラーが発生する', async () => {
      const error = new Error('Network Error');
      vi.mocked(apiClient.delete).mockRejectedValue(error);

      await expect(todoService.deleteTodo(1)).rejects.toThrow('Network Error');

      expect(apiClient.delete).toHaveBeenCalledWith('todos/1/');
    });
  });

  describe('エンドポイントのフォーマット', () => {
    it('すべてのエンドポイントが正しいフォーマットである', async () => {
      // getTodos
      const mockGetResponse = mockApiResponse(mockTodos);
      vi.mocked(apiClient.get).mockReturnValue(mockGetResponse);
      await todoService.getTodos();
      expect(apiClient.get).toHaveBeenCalledWith('todos/');

      // createTodo
      const mockPostResponse = mockApiResponse(mockTodo);
      vi.mocked(apiClient.post).mockReturnValue(mockPostResponse);
      await todoService.createTodo({
        todo_title: 'Test',
        priority: 'LOW',
        progress: 0,
      });
      expect(apiClient.post).toHaveBeenCalledWith(
        'todos/',
        expect.any(Object)
      );

      // updateTodo
      const mockPatchResponse = mockApiResponse(mockTodo);
      vi.mocked(apiClient.patch).mockReturnValue(mockPatchResponse);
      await todoService.updateTodo(1, { progress: 50 });
      expect(apiClient.patch).toHaveBeenCalledWith(
        'todos/1/',
        expect.any(Object)
      );

      // deleteTodo
      vi.mocked(apiClient.delete).mockResolvedValue(undefined as never);
      await todoService.deleteTodo(1);
      expect(apiClient.delete).toHaveBeenCalledWith('todos/1/');
    });

    it('IDが動的に埋め込まれる', async () => {
      const mockPatchResponse = mockApiResponse(mockTodo);
      vi.mocked(apiClient.patch).mockReturnValue(mockPatchResponse);

      await todoService.updateTodo(123, { progress: 50 });
      expect(apiClient.patch).toHaveBeenCalledWith(
        'todos/123/',
        expect.any(Object)
      );

      vi.mocked(apiClient.delete).mockResolvedValue(undefined as never);

      await todoService.deleteTodo(456);
      expect(apiClient.delete).toHaveBeenCalledWith('todos/456/');
    });
  });
});