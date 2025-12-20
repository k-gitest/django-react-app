import { todoService } from '../services/todo-service';
import type { UpdateTodoInput, Todo, CreateTodoInput } from '../types';
import { useApiQuery, useApiMutation } from '@/hooks/use-tanstack-query';
import { queryClient } from '@/lib/queryClient';
import { ApiError } from '@/errors/api-error';

export const TODO_QUERY_KEY = ['todos'] as const;

export const useTodos = () => {
  // 一覧取得
  const todosQuery = useApiQuery<Todo[]>({
    queryKey: TODO_QUERY_KEY,
    queryFn: todoService.getTodos,
  });

  // 作成
  const createMutation = useApiMutation<Todo, Error | ApiError, { data: CreateTodoInput }>({
    mutationFn: ({ data }) => todoService.createTodo(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TODO_QUERY_KEY });
    },
    onError: (err) => {
      // エラーは既に errorHandler で処理済み
      // 個別の処理が必要な場合のみここに記述
      if (err instanceof ApiError && err.status === 400) {
        // バリデーションエラーの追加処理
      }
    },
  });

  // 更新
  const updateMutation = useApiMutation<Todo, Error | ApiError, { id: number; data: UpdateTodoInput }>({
    mutationFn: ({ id, data }) => todoService.updateTodo(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TODO_QUERY_KEY });
    },
    onError: (err) => {
      // エラーは既に errorHandler で処理済み
      if (err instanceof ApiError && err.status === 404) {
        // Todo が見つからない場合の追加処理
      }
    },
  });

  // 削除
  const deleteMutation = useApiMutation<void, Error | ApiError, { id: number }>({
    mutationFn: ({ id }) => todoService.deleteTodo(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TODO_QUERY_KEY });
    },
    onError: (err) => {
      // エラーは既に errorHandler で処理済み
      if (err instanceof ApiError && err.status === 404) {
        // Todo が見つからない場合の追加処理
      }
    },
  });

  // メソッド実装
  const createTodo = async (data: CreateTodoInput) => {
    return createMutation.mutateAsync({ data });
  };

  const updateTodo = async (id: number, data: UpdateTodoInput) => {
    return updateMutation.mutateAsync({ id, data });
  };

  const deleteTodo = async (id: number) => {
    return deleteMutation.mutateAsync({ id });
  };

  return {
    // データ
    todos: todosQuery.data ?? [],
    isLoading: todosQuery.isLoading,
    isError: todosQuery.isError,
    
    // メソッド
    createTodo,
    updateTodo,
    deleteTodo,
    
    // Mutation オブジェクト（ローディング状態などを取得する場合）
    createMutation,
    updateMutation,
    deleteMutation,
  };
};