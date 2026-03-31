import { describe, it, expect, vi, beforeEach } from 'vitest';

/* =========================
   テスト対象
========================= */
import { todoServiceGraphQL } from '@/features/todos/services/implementations/todo-service-graphql';

/* =========================
   モック対象
========================= */
import { gqlRequest, gqlMutation } from '@/lib/graphql-client';

/* =========================
   vi.mock（すべてトップレベル）
========================= */

vi.mock('@/lib/graphql-client', () => ({
  gqlRequest: vi.fn(),
  gqlMutation: vi.fn(),
}));

vi.mock('@/graphql/queries/todo', () => ({
  GET_TODOS: 'GET_TODOS',
  GET_TODO_STATS: 'GET_TODO_STATS',
  GET_PROGRESS_STATS: 'GET_PROGRESS_STATS',
}));

vi.mock('@/graphql/mutations/todo', () => ({
  CREATE_TODO: 'CREATE_TODO',
  UPDATE_TODO: 'UPDATE_TODO',
  DELETE_TODO: 'DELETE_TODO',
}));

/* =========================
   モック参照
========================= */

const mockGqlRequest = gqlRequest as ReturnType<typeof vi.fn>;
const mockGqlMutation = gqlMutation as ReturnType<typeof vi.fn>;

/* =========================
   ダミーデータ
========================= */

// Relay GlobalID: btoa('TodoType:1') = 'VG9kb1R5cGU6MQ=='
const makeGlobalId = (id: number) => btoa(`TodoType:${id}`);

// GraphQL側のTodoType形式（キャメルケース・GlobalID）
const mockGraphQLTodo = {
  id: makeGlobalId(1),
  todoTitle: 'Test Todo',
  priority: 'HIGH',
  progress: 50,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-01T00:00:00Z',
};

const mockGraphQLTodo2 = {
  id: makeGlobalId(2),
  todoTitle: 'Test Todo 2',
  priority: 'MEDIUM',
  progress: 30,
  createdAt: '2024-01-02T00:00:00Z',
  updatedAt: '2024-01-02T00:00:00Z',
};

// graphqlToTodoで変換後の統一型Todo
const expectedTodo = {
  id: 1,                          // GlobalID → 整数に変換される
  todo_title: 'Test Todo',        // todoTitle → todo_title
  priority: 'HIGH',
  progress: 50,
  user: '',                       // GraphQLにはuserフィールドがないのでデフォルト空文字
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const expectedTodo2 = {
  id: 2,
  todo_title: 'Test Todo 2',
  priority: 'MEDIUM',
  progress: 30,
  user: '',
  created_at: '2024-01-02T00:00:00Z',
  updated_at: '2024-01-02T00:00:00Z',
};

/* =========================
   テスト本体
========================= */

describe('todoServiceGraphQL', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /* --------------------
     getTodos
  -------------------- */

  describe('getTodos', () => {
    it('GET_TODOSを呼び、GraphQL型→統一型に変換して返す', async () => {
      mockGqlRequest.mockResolvedValue({
        todos: [mockGraphQLTodo, mockGraphQLTodo2],
      });

      const result = await todoServiceGraphQL.getTodos();

      expect(mockGqlRequest).toHaveBeenCalledWith('GET_TODOS');
      expect(mockGqlRequest).toHaveBeenCalledTimes(1);
      expect(result).toEqual([expectedTodo, expectedTodo2]);
    });

    it('空配列のとき空配列を返す', async () => {
      mockGqlRequest.mockResolvedValue({ todos: [] });

      const result = await todoServiceGraphQL.getTodos();

      expect(result).toEqual([]);
    });

    it('gqlRequestが失敗したときエラーをスローする', async () => {
      mockGqlRequest.mockRejectedValue(new Error('Network Error'));

      await expect(todoServiceGraphQL.getTodos()).rejects.toThrow('Network Error');
    });
  });

  /* --------------------
     createTodo
  -------------------- */

  describe('createTodo', () => {
    const createInput = {
      todo_title: 'New Todo',
      priority: 'LOW' as const,
      progress: 0,
    };

    it('TodoCreateInputに変換してCREATE_TODOを呼び、統一型を返す', async () => {
      const newGraphQLTodo = { ...mockGraphQLTodo, todoTitle: 'New Todo', priority: 'LOW', progress: 0 };

      mockGqlMutation.mockResolvedValue({
        __typename: 'CreateTodoPayload',
        todoEdge: { node: newGraphQLTodo },
      });

      const result = await todoServiceGraphQL.createTodo(createInput);

      // スネークケース→キャメルケースに変換して送信
      expect(mockGqlMutation).toHaveBeenCalledWith(
        'CREATE_TODO',
        {
          input: {
            todoTitle: 'New Todo',
            priority: 'LOW',
            progress: 0,
          },
        },
        'createTodo'
      );
      expect(result.todo_title).toBe('New Todo');
      expect(result.priority).toBe('LOW');
      expect(result.progress).toBe(0);
    });

    it('__typenameがCreateTodoPayload以外のとき ValidationErrorメッセージでスローする', async () => {
      mockGqlMutation.mockResolvedValue({
        __typename: 'ValidationError',
        message: 'タイトルは必須です',
      });

      await expect(todoServiceGraphQL.createTodo(createInput)).rejects.toThrow(
        'タイトルは必須です'
      );
    });

    it('__typenameがValidationError以外の未知のエラーのとき汎用メッセージでスローする', async () => {
      mockGqlMutation.mockResolvedValue({
        __typename: 'UnknownError',
      });

      await expect(todoServiceGraphQL.createTodo(createInput)).rejects.toThrow(
        '作成に失敗しました'
      );
    });

    it('gqlMutationが失敗したときエラーをスローする', async () => {
      mockGqlMutation.mockRejectedValue(new Error('Server Error'));

      await expect(todoServiceGraphQL.createTodo(createInput)).rejects.toThrow(
        'Server Error'
      );
    });
  });

  /* --------------------
     updateTodo
  -------------------- */

  describe('updateTodo', () => {
    it('idをRelayGlobalIDに変換してUPDATE_TODOを呼び、統一型を返す', async () => {
      const updateInput = { id: 1, progress: 100 };
      const updatedGraphQLTodo = { ...mockGraphQLTodo, progress: 100 };

      mockGqlMutation.mockResolvedValue({
        __typename: 'UpdateTodoPayload',
        todo: updatedGraphQLTodo,
      });

      const result = await todoServiceGraphQL.updateTodo(updateInput);

      expect(mockGqlMutation).toHaveBeenCalledWith(
        'UPDATE_TODO',
        {
          id: makeGlobalId(1),      // btoa('TodoType:1')
          input: { progress: 100 }, // undefinedのフィールドは含まれない
        },
        'updateTodo'
      );
      expect(result.id).toBe(1);
      expect(result.progress).toBe(100);
    });

    it('undefinedのフィールドはinputに含まれない', async () => {
      const updateInput = {
        id: 1,
        todo_title: 'Updated Title',
        // priority と progress は undefined
      };

      mockGqlMutation.mockResolvedValue({
        __typename: 'UpdateTodoPayload',
        todo: { ...mockGraphQLTodo, todoTitle: 'Updated Title' },
      });

      await todoServiceGraphQL.updateTodo(updateInput);

      // inputにはtodoTitleのみ含まれる
      expect(mockGqlMutation).toHaveBeenCalledWith(
        'UPDATE_TODO',
        {
          id: makeGlobalId(1),
          input: { todoTitle: 'Updated Title' },
        },
        'updateTodo'
      );
    });

    it('複数フィールドを同時に更新できる', async () => {
      const updateInput = {
        id: 2,
        todo_title: 'Updated',
        priority: 'LOW' as const,
        progress: 75,
      };

      mockGqlMutation.mockResolvedValue({
        __typename: 'UpdateTodoPayload',
        todo: { ...mockGraphQLTodo2, todoTitle: 'Updated', priority: 'LOW', progress: 75 },
      });

      await todoServiceGraphQL.updateTodo(updateInput);

      expect(mockGqlMutation).toHaveBeenCalledWith(
        'UPDATE_TODO',
        {
          id: makeGlobalId(2),
          input: { todoTitle: 'Updated', priority: 'LOW', progress: 75 },
        },
        'updateTodo'
      );
    });

    it('__typenameがUpdateTodoPayload以外のとき汎用メッセージでスローする', async () => {
      mockGqlMutation.mockResolvedValue({
        __typename: 'ValidationError',
        message: 'Invalid input',
      });

      await expect(
        todoServiceGraphQL.updateTodo({ id: 1, progress: 100 })
      ).rejects.toThrow('更新に失敗しました');
    });

    it('gqlMutationが失敗したときエラーをスローする', async () => {
      mockGqlMutation.mockRejectedValue(new Error('Update failed'));

      await expect(
        todoServiceGraphQL.updateTodo({ id: 1, progress: 100 })
      ).rejects.toThrow('Update failed');
    });
  });

  /* --------------------
     deleteTodo
  -------------------- */

  describe('deleteTodo', () => {
    it('idをRelayGlobalIDに変換してDELETE_TODOを呼ぶ', async () => {
      mockGqlMutation.mockResolvedValue({
        __typename: 'DeleteTodoPayload',
        deletedId: makeGlobalId(1),
      });

      await todoServiceGraphQL.deleteTodo(1);

      expect(mockGqlMutation).toHaveBeenCalledWith(
        'DELETE_TODO',
        { id: makeGlobalId(1) },
        'deleteTodo'
      );
      expect(mockGqlMutation).toHaveBeenCalledTimes(1);
    });

    it('戻り値はundefined', async () => {
      mockGqlMutation.mockResolvedValue({
        __typename: 'DeleteTodoPayload',
        deletedId: makeGlobalId(1),
      });

      await expect(todoServiceGraphQL.deleteTodo(1)).resolves.toBeUndefined();
    });

    it('__typenameがNotFoundErrorのとき該当メッセージでスローする', async () => {
      mockGqlMutation.mockResolvedValue({
        __typename: 'NotFoundError',
        message: 'Not found',
      });

      await expect(todoServiceGraphQL.deleteTodo(999)).rejects.toThrow(
        '対象のTodoが見つかりません'
      );
    });

    it('__typenameがNotFoundError以外の失敗のとき汎用メッセージでスローする', async () => {
      mockGqlMutation.mockResolvedValue({
        __typename: 'InternalError',
      });

      await expect(todoServiceGraphQL.deleteTodo(1)).rejects.toThrow(
        '削除に失敗しました'
      );
    });

    it('gqlMutationが失敗したときエラーをスローする', async () => {
      mockGqlMutation.mockRejectedValue(new Error('Delete failed'));

      await expect(todoServiceGraphQL.deleteTodo(1)).rejects.toThrow('Delete failed');
    });
  });

  /* --------------------
     getTodoStats
  -------------------- */

  describe('getTodoStats', () => {
    it('GET_TODO_STATSを呼び、priority/count形式に変換して返す', async () => {
      mockGqlRequest.mockResolvedValue({
        priorityStats: [
          { priority: 'HIGH', count: 5 },
          { priority: 'MEDIUM', count: 3 },
          { priority: 'LOW', count: 2 },
        ],
      });

      const result = await todoServiceGraphQL.getTodoStats();

      expect(mockGqlRequest).toHaveBeenCalledWith('GET_TODO_STATS');
      expect(result).toEqual([
        { priority: 'HIGH', count: 5 },
        { priority: 'MEDIUM', count: 3 },
        { priority: 'LOW', count: 2 },
      ]);
    });

    it('空配列のとき空配列を返す', async () => {
      mockGqlRequest.mockResolvedValue({ priorityStats: [] });

      const result = await todoServiceGraphQL.getTodoStats();

      expect(result).toEqual([]);
    });

    it('gqlRequestが失敗したときエラーをスローする', async () => {
      mockGqlRequest.mockRejectedValue(new Error('Stats Error'));

      await expect(todoServiceGraphQL.getTodoStats()).rejects.toThrow('Stats Error');
    });
  });

  /* --------------------
     getProgressStats
  -------------------- */

  describe('getProgressStats', () => {
    it('GET_PROGRESS_STATSを呼び、スネークケースのキーに変換して返す', async () => {
      // GraphQL側はキャメルケース
      mockGqlRequest.mockResolvedValue({
        progressStats: {
          range020: 5,
          range2140: 3,
          range4160: 7,
          range6180: 4,
          range81100: 2,
        },
      });

      const result = await todoServiceGraphQL.getProgressStats();

      expect(mockGqlRequest).toHaveBeenCalledWith('GET_PROGRESS_STATS');
      // 統一型はスネークケース
      expect(result).toEqual({
        range_0_20: 5,
        range_21_40: 3,
        range_41_60: 7,
        range_61_80: 4,
        range_81_100: 2,
      });
    });

    it('全カウントが0のとき正しく処理される', async () => {
      mockGqlRequest.mockResolvedValue({
        progressStats: {
          range020: 0,
          range2140: 0,
          range4160: 0,
          range6180: 0,
          range81100: 0,
        },
      });

      const result = await todoServiceGraphQL.getProgressStats();

      Object.values(result).forEach((count) => {
        expect(count).toBe(0);
      });
    });

    it('gqlRequestが失敗したときエラーをスローする', async () => {
      mockGqlRequest.mockRejectedValue(new Error('Progress Error'));

      await expect(todoServiceGraphQL.getProgressStats()).rejects.toThrow(
        'Progress Error'
      );
    });
  });

  /* --------------------
     graphqlToTodo（型変換の境界値）
  -------------------- */

  describe('graphqlToTodo（Relay GlobalID変換の検証）', () => {
    it('RelayGlobalIDが整数IDに正しく変換される', async () => {
      mockGqlRequest.mockResolvedValue({
        todos: [{ ...mockGraphQLTodo, id: makeGlobalId(42) }],
      });

      const result = await todoServiceGraphQL.getTodos();

      expect(result[0].id).toBe(42);
      expect(typeof result[0].id).toBe('number');
    });

    it('大きなIDも正しく変換される', async () => {
      mockGqlRequest.mockResolvedValue({
        todos: [{ ...mockGraphQLTodo, id: makeGlobalId(99999) }],
      });

      const result = await todoServiceGraphQL.getTodos();

      expect(result[0].id).toBe(99999);
    });

    it('userフィールドは空文字になる（GraphQLにはuserがないため）', async () => {
      mockGqlRequest.mockResolvedValue({
        todos: [mockGraphQLTodo],
      });

      const result = await todoServiceGraphQL.getTodos();

      expect(result[0].user).toBe('');
    });

    it('todoTitleがtodo_titleに変換される', async () => {
      mockGqlRequest.mockResolvedValue({
        todos: [{ ...mockGraphQLTodo, todoTitle: 'キャメルケースのタイトル' }],
      });

      const result = await todoServiceGraphQL.getTodos();

      expect(result[0].todo_title).toBe('キャメルケースのタイトル');
      expect(result[0]).not.toHaveProperty('todoTitle');
    });
  });
});