import { gqlRequest, gqlMutation } from '@/lib/graphql-client';
import {
  GET_TODOS,
  GET_TODO_STATS,
  GET_PROGRESS_STATS,
} from '@/graphql/queries/todo';
import {
  CREATE_TODO,
  UPDATE_TODO,
  DELETE_TODO,
} from '@/graphql/mutations/todo';
import type {
  GetTodosQuery,
  GetTodoStatsQuery,
  GetProgressStatsQuery,
  CreateTodoMutation,
  UpdateTodoMutation,
  DeleteTodoMutation,
  TodoCreateInput,
  TodoUpdateInput,
  TodoType,
  PriorityEnum,
} from '@/graphql/types';
import type { CreateTodoInput, Todo, UpdateTodoInput } from '../types/index';

/**
 * GraphQL API実装
 * 
 * 責務:
 * - GraphQL型 ⇔ 統一型（Todo）の変換
 * - Relay GlobalID ⇔ 整数IDの変換
 */
export const todoServiceGraphQL = {
  getTodos: async (): Promise<Todo[]> => {
    const data = await gqlRequest<GetTodosQuery>(GET_TODOS);
    return data.todos.map(graphqlToTodo);
  },

  createTodo: async (input: CreateTodoInput): Promise<Todo> => {
    const graphqlInput: TodoCreateInput = {
      todoTitle: input.todo_title,
      // input.priority が string なら PriorityEnum 型へ適切にアサーション
      priority: input.priority as PriorityEnum,
      progress: input.progress,
    };

    const result = await gqlMutation<CreateTodoMutation, 'createTodo'>(
      CREATE_TODO,
      { input: graphqlInput },
      'createTodo'
    );


    // ✅ 型ガード: まず __typename で「成功時」であることを確定させる
    if (result.__typename === 'CreateTodoPayload') {
      // 成功時、result は CreateTodoPayload 型として扱えるので node にアクセス可能
      const node = result.todoEdge.node;
      // node を TodoType として扱う
      return graphqlToTodo(node as unknown as TodoType);
    }
    
    // ❌ 失敗時（ValidationErrorなど）
    throw new Error(result.__typename === 'ValidationError' ? result.message : '作成に失敗しました');

  },

  updateTodo: async (input: UpdateTodoInput): Promise<Todo> => {
    const graphqlInput: TodoUpdateInput = {};
    if (input.todo_title !== undefined) graphqlInput.todoTitle = input.todo_title;
    if (input.priority !== undefined) {
      graphqlInput.priority = input.priority as PriorityEnum;
    }
    if (input.progress !== undefined) graphqlInput.progress = input.progress;

    const globalId = btoa(`TodoType:${input.id}`);

    const result = await gqlMutation<UpdateTodoMutation, 'updateTodo'>(
      UPDATE_TODO,
      { id: globalId, input: graphqlInput },
      'updateTodo'
    );

    // ✅ 型ガード: UpdateTodoPayload であることを確認
    if (result.__typename === 'UpdateTodoPayload') {
      // payload の中の todo プロパティが Node 本体
      return graphqlToTodo(result.todo as unknown as TodoType);
    }

    throw new Error('更新に失敗しました');
  },

  deleteTodo: async (id: number): Promise<void> => {
    const globalId = btoa(`TodoType:${id}`);

    const result = await gqlMutation<DeleteTodoMutation, 'deleteTodo'>(
      DELETE_TODO,
      { id: globalId },
      'deleteTodo'
    );

    // ✅ 追加：明示的に成功(Payload)を確認する
    if (result.__typename !== 'DeleteTodoPayload') {
      // 失敗時（NotFoundError や InternalError）はエラーを投げる
      throw new Error(
        result.__typename === 'NotFoundError' ? '対象のTodoが見つかりません' : '削除に失敗しました'
      );
    }
    
    // ここまで来れば、result.__typename === 'DeleteTodoPayload' なので確実に成功
  },

  getTodoStats: async (): Promise<Array<{ priority: string; count: number }>> => {
    const data = await gqlRequest<GetTodoStatsQuery>(GET_TODO_STATS);

    return data.priorityStats.map((stat) => ({
      priority: stat.priority,
      count: stat.count,
    }));
  },

  getProgressStats: async (): Promise<Record<string, number>> => {
    const data = await gqlRequest<GetProgressStatsQuery>(GET_PROGRESS_STATS);
    const stats = data.progressStats;

    return {
      range_0_20: stats.range020,
      range_21_40: stats.range2140,
      range_41_60: stats.range4160,
      range_61_80: stats.range6180,
      range_81_100: stats.range81100,
    };
  },
};

/**
 * GraphQL型 → 統一型（Todo）に変換
 */
function graphqlToTodo(graphqlTodo: TodoType): Todo {
  // Relay GlobalID → 整数IDに変換
  const decodedId = atob(graphqlTodo.id);
  const id = parseInt(decodedId.split(':')[1], 10);

  return {
    id,
    todo_title: graphqlTodo.todoTitle,
    priority: graphqlTodo.priority as Todo['priority'],
    progress: graphqlTodo.progress,
    user: '',
    created_at: graphqlTodo.createdAt,
    updated_at: graphqlTodo.updatedAt,
  };
}