import { todoService } from '../services/index';
import type { Todo, CreateTodoInput } from '../types';
import { useApiMutation } from '@/hooks/use-tanstack-query';
import { useApiSuspenseQuery } from '@/hooks/use-suspense-query';
import { queryClient } from '@/lib/queryClient';
import { ApiError } from '@/errors/api-error';

export const TODO_QUERY_KEY = ['todos'] as const;

export const useTodos = () => {
  type GetRes = Awaited<ReturnType<typeof todoService.getTodos>>;
  type CreateRes = Awaited<ReturnType<typeof todoService.createTodo>>;
  type UpdateRes = Awaited<ReturnType<typeof todoService.updateTodo>>;
  type DeleteRes = Awaited<ReturnType<typeof todoService.deleteTodo>>;

  type CreateReq = Parameters<typeof todoService.createTodo>[0];
  type UpdateReq = Parameters<typeof todoService.updateTodo>[0];
  type DeleteReq = Parameters<typeof todoService.deleteTodo>[0];

  //type Todo = NonNullable<GetRes['data']>[number];

  // 一覧取得
  /*
  const todosQuery = useApiQuery<Todo[]>({
    queryKey: TODO_QUERY_KEY,
    queryFn: todoService.getTodos,
  });
  */
  const todosQuery = useApiSuspenseQuery<GetRes>({
    queryKey: TODO_QUERY_KEY,
    queryFn: todoService.getTodos,
    staleTime: 1000 * 5, // 5秒間はデータを新鮮とみなす（頻繁な再ロードによるSuspense化を防止）
  });

  // 作成
  const createMutation = useApiMutation<CreateRes, Error | ApiError, CreateReq, { previousTodos: Todo[] | undefined }>({
    mutationFn: ( data ) => todoService.createTodo(data),
    onMutate: async ( data ) => {
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
  const updateMutation = useApiMutation<UpdateRes, Error | ApiError, UpdateReq, { previousTodos: Todo[] | undefined }>({
    mutationFn: (data) => todoService.updateTodo(data),
    onMutate: async (data) => {
      await queryClient.cancelQueries({ queryKey: TODO_QUERY_KEY });
      const previousTodos = queryClient.getQueryData<Todo[]>(TODO_QUERY_KEY);

      queryClient.setQueryData<Todo[]>(TODO_QUERY_KEY, (old = []) => {
        return old.map((todo) =>
          todo.id === data.id
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
  const deleteMutation = useApiMutation<DeleteRes, Error | ApiError, DeleteReq, { previousTodos: Todo[] | undefined }>({
    mutationFn: ( id ) => todoService.deleteTodo(id),
    onMutate: async ( id ) => {
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
    return createMutation.mutateAsync( data );
  };

  /*
  const updateTodo = async (data: UpdateTodoInput) => {
    return updateMutation.mutateAsync(data);
  };
  */
  const updateTodo = updateMutation.mutateAsync;

  const deleteTodo = async (id: number) => {
    return deleteMutation.mutateAsync( id );
  };

  return {
    // データ
    todos: todosQuery.data ?? [],
    //isLoading: todosQuery.isLoading,
    //isError: todosQuery.isError,

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