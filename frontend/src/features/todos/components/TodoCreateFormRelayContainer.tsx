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