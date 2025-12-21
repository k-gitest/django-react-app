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
  const createMutation = useApiMutation<Todo, Error | ApiError, { data: CreateTodoInput }, { previousTodos: Todo[] | undefined }>({
    mutationFn: ({ data }) => todoService.createTodo(data),
    onMutate: async ({ data }) => {
      // 1. 進行中のクエリをキャンセル
      await queryClient.cancelQueries({ queryKey: TODO_QUERY_KEY });

      // 2. 現在のキャッシュを保存（ロールバック用）
      const previousTodos = queryClient.getQueryData<Todo[]>(TODO_QUERY_KEY);

      // 3. 楽観的更新: 仮のIDで即座に追加
      queryClient.setQueryData<Todo[]>(TODO_QUERY_KEY, (old = []) => {
        const optimisticTodo: Todo = {
          id: Date.now(), // 仮ID（サーバーから正式なIDが返る）
          ...data,
          user: '', // ダミー値
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        return [...old, optimisticTodo];
      });

      return { previousTodos };
    },
    onError: (err, _variables, context) => {
      // エラーは既に errorHandler で処理済み
      // 4. エラー時: ロールバック
      if (context?.previousTodos) {
        queryClient.setQueryData(TODO_QUERY_KEY, context.previousTodos);
      }

      if (err instanceof ApiError && err.status === 400) {
        // バリデーションエラーの追加処理
        // 個別の処理が必要な場合のみここに記述
      }
    },
    onSettled: () => {
      // 5. 最後に: サーバーと同期（正式なIDを取得）
      queryClient.invalidateQueries({ queryKey: TODO_QUERY_KEY });
    },
  });

  // 更新
  const updateMutation = useApiMutation<Todo, Error | ApiError, { id: number; data: UpdateTodoInput }, { previousTodos: Todo[] | undefined }>({
    mutationFn: ({ id, data }) => todoService.updateTodo(id, data),
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: TODO_QUERY_KEY });
      const previousTodos = queryClient.getQueryData<Todo[]>(TODO_QUERY_KEY);

      queryClient.setQueryData<Todo[]>(TODO_QUERY_KEY, (old = []) => {
        return old.map((todo) =>
          todo.id === id
            ? { ...todo, ...data, updated_at: new Date().toISOString() }
            : todo
        );
      });

      return { previousTodos };
    },
    onError: (err, _variables, context) => {
      // エラーは既に errorHandler で処理済み
      if (context?.previousTodos) {
        queryClient.setQueryData(TODO_QUERY_KEY, context.previousTodos);
      }

      if (err instanceof ApiError && err.status === 404) {
        // Todo が見つからない場合の追加処理
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: TODO_QUERY_KEY });
    },
  });

  // 削除
  const deleteMutation = useApiMutation<void, Error | ApiError, { id: number }, { previousTodos: Todo[] | undefined }>({
    mutationFn: ({ id }) => todoService.deleteTodo(id),
    onMutate: async ({ id }) => {
      await queryClient.cancelQueries({ queryKey: TODO_QUERY_KEY });
      const previousTodos = queryClient.getQueryData<Todo[]>(TODO_QUERY_KEY);

      queryClient.setQueryData<Todo[]>(TODO_QUERY_KEY, (old = []) => {
        return old.filter((todo) => todo.id !== id);
      });

      return { previousTodos };
    },
    onError: (err, _variables, context) => {
      // エラーは既に errorHandler で処理済み
      if (context?.previousTodos) {
        queryClient.setQueryData(TODO_QUERY_KEY, context.previousTodos);
      }

      if (err instanceof ApiError && err.status === 404) {
        // Todo が見つからない場合の追加処理
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: TODO_QUERY_KEY });
    },
  });

  // メソッド実装
  const createTodo = async (data: CreateTodoInput) => {
    return createMutation.mutateAsync({ data });
  };

  const updateTodo = async ({ id, data }: { id: number; data: UpdateTodoInput }) => {
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