import { describe, it, expect, vi, beforeEach } from 'vitest';
import { todoService } from '@/features/todos/services/todo-service';
import type { Todo, CreateTodoInput, UpdateTodoInput } from '@/features/todos/types';

/* =========================
   モック
========================= */

vi.mock('@/lib/api-client', () => ({
  apiClient: {
    GET: vi.fn(),
    POST: vi.fn(),
    PATCH: vi.fn(),
    DELETE: vi.fn(),
  },
}));

// vi.mockの後でimportする
import { apiClient } from '@/lib/api-client';

/* =========================
   ダミーデータ
========================= */

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

/* =========================
   ヘルパー
========================= */

// openapi-fetchはPromiseを返し { data, error } の形式になる
const mockOkResponse = <T,>(data: T) =>
  Promise.resolve({ data, error: undefined });

const mockErrResponse = (error: unknown) =>
  Promise.resolve({ data: undefined, error });

/* =========================
   テスト本体
========================= */

describe('todoService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /* --------------------
     getTodos
  -------------------- */

  describe('getTodos', () => {
    it('GET /api/v1/todos/ を呼び、レスポンスをそのまま返す', async () => {
      vi.mocked(apiClient.GET).mockReturnValue(mockOkResponse(mockTodos));

      const result = await todoService.getTodos();

      expect(apiClient.GET).toHaveBeenCalledWith('/api/v1/todos/');
      expect(apiClient.GET).toHaveBeenCalledTimes(1);
      expect(result).toEqual({ data: mockTodos, error: undefined });
    });

    it('空配列が返される場合', async () => {
      vi.mocked(apiClient.GET).mockReturnValue(mockOkResponse([]));

      const result = await todoService.getTodos();

      expect(apiClient.GET).toHaveBeenCalledWith('/api/v1/todos/');
      expect(result).toEqual({ data: [], error: undefined });
    });

    it('APIがエラーを返したときそのまま返す', async () => {
      vi.mocked(apiClient.GET).mockReturnValue(
        mockErrResponse({ status: 500, message: 'Server Error' })
      );

      const result = await todoService.getTodos();

      // openapi-fetchはエラーもdataと同じ形式で返す（throwしない）
      expect(result.error).toBeDefined();
      expect(result.data).toBeUndefined();
    });

    it('ネットワークエラーが発生したときスローする', async () => {
      vi.mocked(apiClient.GET).mockRejectedValue(new Error('Network Error'));

      await expect(todoService.getTodos()).rejects.toThrow('Network Error');
    });
  });

  /* --------------------
     createTodo
  -------------------- */

  describe('createTodo', () => {
    const createInput: CreateTodoInput = {
      todo_title: 'New Todo',
      priority: 'LOW',
      progress: 0,
    };

    it('POST /api/v1/todos/ をbody付きで呼び、レスポンスをそのまま返す', async () => {
      vi.mocked(apiClient.POST).mockReturnValue(mockOkResponse(mockTodo));

      const result = await todoService.createTodo(createInput);

      expect(apiClient.POST).toHaveBeenCalledWith('/api/v1/todos/', {
        body: createInput,
      });
      expect(apiClient.POST).toHaveBeenCalledTimes(1);
      expect(result).toEqual({ data: mockTodo, error: undefined });
    });

    it('ネットワークエラーが発生したときスローする', async () => {
      vi.mocked(apiClient.POST).mockRejectedValue(new Error('Validation Error'));

      await expect(todoService.createTodo(createInput)).rejects.toThrow(
        'Validation Error'
      );
      expect(apiClient.POST).toHaveBeenCalledWith('/api/v1/todos/', {
        body: createInput,
      });
    });
  });

  /* --------------------
     updateTodo
  -------------------- */

  describe('updateTodo', () => {
    it('PATCH /api/v1/todos/{id}/ をpath params・body付きで呼ぶ', async () => {
      const updateInput: UpdateTodoInput = {
        id: 1,
        progress: 100,
      };
      const updatedTodo: Todo = {
        ...mockTodo,
        progress: 100,
        updated_at: '2024-01-02T00:00:00Z',
      };

      vi.mocked(apiClient.PATCH).mockReturnValue(mockOkResponse(updatedTodo));

      const result = await todoService.updateTodo(updateInput);

      // idはpath paramsに、残りはbodyに分離される
      expect(apiClient.PATCH).toHaveBeenCalledWith('/api/v1/todos/{id}/', {
        params: { path: { id: 1 } },
        body: { progress: 100 },
      });
      expect(apiClient.PATCH).toHaveBeenCalledTimes(1);
      expect(result).toEqual({ data: updatedTodo, error: undefined });
    });

    it('複数フィールドを同時に更新できる', async () => {
      const updateInput: UpdateTodoInput = {
        id: 1,
        todo_title: 'Updated Title',
        priority: 'HIGH',
        progress: 75,
      };

      vi.mocked(apiClient.PATCH).mockReturnValue(
        mockOkResponse({ ...mockTodo, ...updateInput })
      );

      await todoService.updateTodo(updateInput);

      expect(apiClient.PATCH).toHaveBeenCalledWith('/api/v1/todos/{id}/', {
        params: { path: { id: 1 } },
        // idはbodyに含まれない
        body: { todo_title: 'Updated Title', priority: 'HIGH', progress: 75 },
      });
    });

    it('ネットワークエラーが発生したときスローする', async () => {
      vi.mocked(apiClient.PATCH).mockRejectedValue(new Error('Not Found'));

      await expect(
        todoService.updateTodo({ id: 999, progress: 100 })
      ).rejects.toThrow('Not Found');

      expect(apiClient.PATCH).toHaveBeenCalledWith('/api/v1/todos/{id}/', {
        params: { path: { id: 999 } },
        body: { progress: 100 },
      });
    });
  });

  /* --------------------
     deleteTodo
  -------------------- */

  describe('deleteTodo', () => {
    it('DELETE /api/v1/todos/{id}/ をpath params付きで呼ぶ', async () => {
      vi.mocked(apiClient.DELETE).mockReturnValue(mockOkResponse(undefined));

      await todoService.deleteTodo(1);

      expect(apiClient.DELETE).toHaveBeenCalledWith('/api/v1/todos/{id}/', {
        params: { path: { id: 1 } },
      });
      expect(apiClient.DELETE).toHaveBeenCalledTimes(1);
    });

    it('戻り値はundefined', async () => {
      vi.mocked(apiClient.DELETE).mockReturnValue(mockOkResponse(undefined));

      const result = await todoService.deleteTodo(1);

      expect(result).toBeUndefined();
    });

    it('複数のTodoを順番に削除できる', async () => {
      vi.mocked(apiClient.DELETE).mockReturnValue(mockOkResponse(undefined));

      await todoService.deleteTodo(1);
      await todoService.deleteTodo(2);
      await todoService.deleteTodo(3);

      expect(apiClient.DELETE).toHaveBeenCalledTimes(3);
      expect(apiClient.DELETE).toHaveBeenNthCalledWith(1, '/api/v1/todos/{id}/', {
        params: { path: { id: 1 } },
      });
      expect(apiClient.DELETE).toHaveBeenNthCalledWith(2, '/api/v1/todos/{id}/', {
        params: { path: { id: 2 } },
      });
      expect(apiClient.DELETE).toHaveBeenNthCalledWith(3, '/api/v1/todos/{id}/', {
        params: { path: { id: 3 } },
      });
    });

    it('ネットワークエラーが発生したときスローする', async () => {
      vi.mocked(apiClient.DELETE).mockRejectedValue(new Error('Not Found'));

      await expect(todoService.deleteTodo(999)).rejects.toThrow('Not Found');
      expect(apiClient.DELETE).toHaveBeenCalledWith('/api/v1/todos/{id}/', {
        params: { path: { id: 999 } },
      });
    });
  });

  /* --------------------
     getTodoStats
  -------------------- */

  describe('getTodoStats', () => {
    const mockStatsResponse = [
      { priority: 'HIGH', count: 5 },
      { priority: 'MEDIUM', count: 3 },
      { priority: 'LOW', count: 2 },
    ];

    it('GET /api/v1/todos/stats/ を呼び、レスポンスをそのまま返す', async () => {
      vi.mocked(apiClient.GET).mockReturnValue(mockOkResponse(mockStatsResponse));

      const result = await todoService.getTodoStats();

      expect(apiClient.GET).toHaveBeenCalledWith('/api/v1/todos/stats/');
      expect(apiClient.GET).toHaveBeenCalledTimes(1);
      expect(result).toEqual({ data: mockStatsResponse, error: undefined });
    });

    it('空配列が返される場合', async () => {
      vi.mocked(apiClient.GET).mockReturnValue(mockOkResponse([]));

      const result = await todoService.getTodoStats();

      expect(result).toEqual({ data: [], error: undefined });
    });

    it('ネットワークエラーが発生したときスローする', async () => {
      vi.mocked(apiClient.GET).mockRejectedValue(new Error('Stats API Error'));

      await expect(todoService.getTodoStats()).rejects.toThrow('Stats API Error');
    });
  });

  /* --------------------
     getProgressStats
  -------------------- */

  describe('getProgressStats', () => {
    const mockProgressResponse = {
      range_0_20: 5,
      range_21_40: 3,
      range_41_60: 7,
      range_61_80: 4,
      range_81_100: 2,
    };

    it('GET /api/v1/todos/progress-stats/ を呼び、レスポンスをそのまま返す', async () => {
      vi.mocked(apiClient.GET).mockReturnValue(mockOkResponse(mockProgressResponse));

      const result = await todoService.getProgressStats();

      expect(apiClient.GET).toHaveBeenCalledWith('/api/v1/todos/progress-stats/');
      expect(apiClient.GET).toHaveBeenCalledTimes(1);
      expect(result).toEqual({ data: mockProgressResponse, error: undefined });
    });

    it('カウントが0の場合も正しく処理される', async () => {
      const zeroCountResponse = {
        range_0_20: 0,
        range_21_40: 0,
        range_41_60: 0,
        range_61_80: 0,
        range_81_100: 0,
      };
      vi.mocked(apiClient.GET).mockReturnValue(mockOkResponse(zeroCountResponse));

      const result = await todoService.getProgressStats();

      expect(result).toEqual({ data: zeroCountResponse, error: undefined });
    });

    it('ネットワークエラーが発生したときスローする', async () => {
      vi.mocked(apiClient.GET).mockRejectedValue(
        new Error('Progress Stats API Error')
      );

      await expect(todoService.getProgressStats()).rejects.toThrow(
        'Progress Stats API Error'
      );
    });
  });
});