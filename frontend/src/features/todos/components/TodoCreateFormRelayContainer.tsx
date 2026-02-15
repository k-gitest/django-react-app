import { useCallback } from 'react';
import { graphql } from 'react-relay';
import { useRelayMutation } from '@/hooks/useRelayMutation';
import { useExclusiveModal, useUIStore } from '@/hooks/useExclusiveModal';
import { TodoCreateForm } from './TodoCreateForm';
import type { TodoCreateFormRelayContainerMutation } from '@/__generated__/TodoCreateFormRelayContainerMutation.graphql';
import type { TodoFormValues } from '../schemas';

const CreateTodoMutation = graphql`
  mutation TodoCreateFormRelayContainerMutation(
    $input: TodoCreateInput!
    $connections: [ID!]!
  ) {
    createTodo(input: $input) {
      __typename
      ... on CreateTodoPayload {
        todoEdge @prependEdge(connections: $connections) {
          node {
            id
            todoTitle
            progress
            priority
            createdAt
            updatedAt
          }
        }
      }
      ... on ValidationError {
        message
        field
      }
    }
  }
`;

export const TodoCreateFormRelayContainer = () => {
  const { execute, isInFlight } = useRelayMutation<TodoCreateFormRelayContainerMutation>(CreateTodoMutation);
  const { isOpen, open, close } = useExclusiveModal();

  const handleCreateSubmit = useCallback(
    async (values: TodoFormValues): Promise<void> => {
      try {
        const response = await execute({
          variables: {
            input: {
              todoTitle: values.todo_title,
              priority: values.priority,
              progress: values.progress,
            },
            // ✅ Connection ID を渡す
            connections: ['client:root:__TodoList_todosConnection_connection'],
          },
          // ✅ 楽観的更新
          optimisticResponse: {
            createTodo: {
              __typename: 'CreateTodoPayload',
              todoEdge: {
                __typename: 'TodoEdge',
                node: {
                  __typename: 'Todo',
                  id: `temp-${Date.now()}`,
                  todoTitle: values.todo_title,
                  priority: values.priority,
                  progress: values.progress,
                  createdAt: new Date().toISOString(),
                  updatedAt: new Date().toISOString(),
                },
              },
            },
          } as TodoCreateFormRelayContainerMutation['response'],
          errorContext: 'タスクの作成に失敗しました',
        });

        if (response.createTodo.__typename === 'CreateTodoPayload') {
          close(); // ✅ 成功時のみ閉じる
          //toast.success('タスクを作成しました');
        }
      } catch (error) {
        if (import.meta.env.DEV) console.error(error);
      }
    },
    [execute, close]
  );

  const handleOpenChange = useCallback((newOpen: boolean) => {
    if (newOpen) {
      open();
    } else {
      close();
    }
  }, [open, close]);

  const isLockedByOther = useUIStore(
    (state) => state.currentModalId !== null && !isOpen
  );

  return (
    <TodoCreateForm
      open={isOpen}
      onOpenChange={handleOpenChange}
      onSubmit={handleCreateSubmit}
      isLoading={isInFlight}
      disabled={isLockedByOther}
    />
  );
};