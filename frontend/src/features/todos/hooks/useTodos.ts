import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { todoService } from '../services/todo-service';
import type { UpdateTodoInput } from '../types';

export const TODO_QUERY_KEY = ['todos'] as const;

export const useTodos = () => {
  const queryClient = useQueryClient();

  // 一覧取得
  const todosQuery = useQuery({
    queryKey: TODO_QUERY_KEY,
    queryFn: todoService.getTodos,
  });

  // 作成
  const createMutation = useMutation({
    mutationFn: todoService.createTodo,
    onSuccess: () => {
      // キャッシュを無効化して再取得、または直接更新
      queryClient.invalidateQueries({ queryKey: TODO_QUERY_KEY });
    },
  });

  // 更新
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateTodoInput }) =>
      todoService.updateTodo(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TODO_QUERY_KEY });
    },
  });

  // 削除
  const deleteMutation = useMutation({
    mutationFn: todoService.deleteTodo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TODO_QUERY_KEY });
    },
  });

  return {
    todos: todosQuery.data ?? [],
    isLoading: todosQuery.isLoading,
    isError: todosQuery.isError,
    createTodo: createMutation.mutateAsync,
    updateTodo: updateMutation.mutateAsync,
    deleteTodo: deleteMutation.mutateAsync,
  };
};