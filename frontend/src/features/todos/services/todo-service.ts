import { apiClient } from '@/lib/api-client';
import type { CreateTodoInput, Todo, UpdateTodoInput } from '../types';

type TodoStatsResponse = {
  priority: string;
  count: number;
}[];

type ProgressStatsResponse = Record<string, number>;

export const todoService = {
  getTodos: async (): Promise<Todo[]> => {
    return await apiClient.get('todos/').json();
  },

  createTodo: async (data: CreateTodoInput): Promise<Todo> => {
    return await apiClient.post('todos/', { json: data }).json();
  },

  updateTodo: async (id: number, data: UpdateTodoInput): Promise<Todo> => {
    return await apiClient.patch(`todos/${id}/`, { json: data }).json();
  },

  deleteTodo: async (id: number): Promise<void> => {
    await apiClient.delete(`todos/${id}/`);
  },

  getTodoStats: async (): Promise<TodoStatsResponse> => {
    return await apiClient.get('todos/stats/').json();
  },

  getProgressStats: async (): Promise<ProgressStatsResponse> => {
    return await apiClient.get('todos/progress-stats/').json();
  },
};