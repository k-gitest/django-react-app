import { useCallback } from 'react';
import { graphql } from 'react-relay';
import { useRelayMutation } from '@/hooks/useRelayMutation';
import { TodoCreateForm } from './TodoCreateForm';
import type { TodoCreateFormRelayContainerMutation } from '@/__generated__/TodoCreateFormRelayContainerMutation.graphql';
import type { TodoFormValues } from '../schemas';

const CreateTodoMutation = graphql`
  mutation TodoCreateFormRelayContainerMutation($input: TodoCreateInput!) {
    createTodo(input: $input) {
      __typename
      ... on TodoType {
        id
        todoTitle
        progress
        priority
      }
      ... on ValidationError {
        message
      }
    }
  }
`;

export const TodoCreateFormRelayContainer = () => {
  const { execute, isInFlight } = useRelayMutation<TodoCreateFormRelayContainerMutation>(CreateTodoMutation);

  const handleCreateSubmit = useCallback(
    async (values: TodoFormValues): Promise<void> => {
      await execute({
        variables: {
          input: {
            todoTitle: values.todo_title,
            priority: values.priority,
            progress: values.progress,
          },
        },
        updater: (store) => {
          // 1. サーバーから返ってきた 'createTodo' の結果（新しく作られたデータ）を取得
          const payload = store.getRootField('createTodo');
          if (!payload) return;

          // 2. 作成成功時の型（TodoType）を特定する
          const newTodo = payload.getLinkedRecord('... on TodoType'); 
          // もし Union 型でないなら payload そのものが TodoType です
          const itemToAdd = newTodo || payload;

          // 3. ルート（Query）にある現在の 'todos' 配列を取得
          const root = store.getRoot();
          const currentTodos = root.getLinkedRecords('todos') || [];

          // 4. 新しい配列を作成（先頭に追加する場合）してセット
          // これにより TodoList が再描画されます
          root.setLinkedRecords([itemToAdd, ...currentTodos], 'todos');
        },
        errorContext: 'タスクの作成に失敗しました',
      });
    },
    [execute]
  );

  return (
    <TodoCreateForm
      onSubmit={handleCreateSubmit}
      isLoading={isInFlight}
    />
  );
};