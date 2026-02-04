import { apiClient } from '@/lib/api-client';
import type { CreateTodoInput, UpdateTodoInput } from '../types';

/*
type TodoStatsResponse = {
  priority: string;
  count: number;
}[];

type ProgressStatsResponse = Record<string, number>;
*/

export const todoService = {
  getTodos: async () => {
    return await apiClient.GET('/api/v1/todos/');
  },

  createTodo: async (data: CreateTodoInput) => {
    return await apiClient.POST('/api/v1/todos/', { body: data });
  },

  updateTodo: async (data: UpdateTodoInput) => {
    const { id, ...body } = data;
    const res = await apiClient.PATCH('/api/v1/todos/{id}/', { params: { path: { id } }, body: body });
    return res;
  },

  deleteTodo: async (id: number) => {
    await apiClient.DELETE('/api/v1/todos/{id}/', { params: { path: { id } } });
  },

  getTodoStats: async () => {
    return await apiClient.GET('/api/v1/todos/stats/');
  },

  getProgressStats: async () => {
    return await apiClient.GET('/api/v1/todos/progress-stats/');
  },
};