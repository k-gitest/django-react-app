import { useCallback } from 'react';
import { useMutation, graphql } from 'react-relay';
import { TodoIndexView } from './TodoIndexView';
import type { TodoIndexRelayContainerMutation } from '@/__generated__/TodoIndexRelayContainerMutation.graphql';
import type { TodoFormValues } from '@/features/todos/schemas';

// Mutationの定義
const CreateTodoMutation = graphql`
  mutation TodoIndexRelayContainerMutation($input: TodoCreateInput!) {
    createTodo(input: $input) {
      __typename
      ... on TodoType {
        id
        todoTitle # スキーマに合わせて修正
        progress  # completed の代わりに progress を使用
        priority
      }
      ... on ValidationError {
        message
      }
      # 必要に応じて他のエラー型も追加
    }
  }
`;

export const TodoIndexContainer = () => {
  const [commit] = useMutation<TodoIndexRelayContainerMutation>(CreateTodoMutation);

  // 1. async を付与し、明示的に Promise<void> を返すようにする
  const handleCreateSubmit = useCallback(async (values: TodoFormValues): Promise<void> => {
    // 2. Promise<void> を明示的に指定してインスタンス化
    return new Promise<void>((resolve, reject) => {
      commit({
        variables: {
          input: {
            todoTitle: values.todo_title,
            priority: values.priority,
            progress: values.progress,
          },
        },
        onCompleted: (_, errors) => {
          if (errors) {
            return reject(errors);
          }
          // 3. resolve() を引数なしで呼ぶ
          resolve();
        },
        onError: (err) => reject(err),
      });
    });
  }, [commit]);

  return (
    <TodoIndexView 
      onCreateSubmit={handleCreateSubmit} 
      // isLoading={isInFlight} // View側にisLoadingプロパティがあれば
    />
  );
};

export const TodoIndex = TodoIndexContainer;