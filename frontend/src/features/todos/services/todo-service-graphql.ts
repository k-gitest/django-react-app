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
} from '@/graphql/types';
import type { CreateTodoInput, Todo, UpdateTodoInput } from '../types/index';

/**
 * GraphQL API実装
 * 外部には公開しない（todo-service.ts経由で使用）
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
      priority: input.priority as any,
      progress: input.progress,
    };

    const todo = await gqlMutation<CreateTodoMutation, 'createTodo'>(
      CREATE_TODO,
      { input: graphqlInput },
      'createTodo'
    );

    return graphqlToTodo(todo as TodoType);
  },

  updateTodo: async (id: number, input: UpdateTodoInput): Promise<Todo> => {
    const graphqlInput: any = {};
    if (input.todo_title !== undefined) {
      graphqlInput.todoTitle = input.todo_title;
    }
    if (input.priority !== undefined) {
      graphqlInput.priority = input.priority;
    }
    if (input.progress !== undefined) {
      graphqlInput.progress = input.progress;
    }

    const globalId = btoa(`TodoType:${id}`);

    const todo = await gqlMutation<UpdateTodoMutation, 'updateTodo'>(
      UPDATE_TODO,
      { id: globalId, input: graphqlInput },
      'updateTodo'
    );

    return graphqlToTodo(todo as TodoType);
  },

  deleteTodo: async (id: number): Promise<void> => {
    const globalId = btoa(`TodoType:${id}`);

    await gqlMutation<DeleteTodoMutation, 'deleteTodo'>(
      DELETE_TODO,
      { id: globalId },
      'deleteTodo'
    );
  },

  getTodoStats: async (): Promise
    Array< { priority: string; count: number } >
  > => {
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
    priority: graphqlTodo.priority as any,
    progress: graphqlTodo.progress,
    user: '',
    created_at: graphqlTodo.createdAt,
    updated_at: graphqlTodo.updatedAt,
  };
}