import { apiClient } from '@/lib/auth-client';
import type { Todo, CreateTodoInput, UpdateTodoInput } from '../types';

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
};