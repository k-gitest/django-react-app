import { useState } from 'react';
import { graphql, useFragment } from 'react-relay';
import { TodoItem } from './TodoItem';
import { isPriority } from '@/lib/utils';
import { useRelayMutation } from '@/hooks/useRelayMutation';
import type { TodoItemRelayContainerDeleteMutation } from '@/__generated__/TodoItemRelayContainerDeleteMutation.graphql';
import type { TodoItemRelayContainerUpdateMutation } from '@/__generated__/TodoItemRelayContainerUpdateMutation.graphql';
import type { TodoItemRelayContainer_todo$key } from '@/__generated__/TodoItemRelayContainer_todo.graphql';
import { TodoEditModalRelayContainer } from './TodoEditModalRelayContainer';

const TodoItemFragment = graphql`
  fragment TodoItemRelayContainer_todo on TodoType {
    id
    todoTitle
    priority
    progress
    updatedAt
    ...TodoEditModalRelayContainer_todo
  }
`;

const TodoUpdateMutation = graphql`
  mutation TodoItemRelayContainerUpdateMutation($id: ID!, $input: TodoUpdateInput!) {
    updateTodo(id: $id, input: $input) {
      __typename
      ... on UpdateTodoPayload {
        todo {
          id
          todoTitle
          priority
          progress
          updatedAt
        }
      }
      ... on ValidationError {
        message
        field
      }
    }
  }
`;

const TodoDeleteMutation = graphql`
  mutation TodoItemRelayContainerDeleteMutation(
    $id: ID!
    $connections: [ID!]!
  ) {
    deleteTodo(id: $id) {
      __typename
      ... on DeleteTodoPayload {
        message
        deletedTodoId @deleteEdge(connections: $connections)
      }
      ... on NotFoundError {
        category
        message
        code
      }
      ... on InternalError {
        category
        message
        code
      }
    }
  }
`;

interface Props {
  todoRef: TodoItemRelayContainer_todo$key;
  showActions?: boolean;
}

export const TodoItemRelayContainer = ({ todoRef, ...props }: Props) => {
  const todo = useFragment<TodoItemRelayContainer_todo$key>(TodoItemFragment, todoRef);
  const [isEditOpen, setIsEditOpen] = useState(false);

  const { execute: updateTodo, isInFlight: isUpdating } =
    useRelayMutation<TodoItemRelayContainerUpdateMutation>(TodoUpdateMutation);
  const { execute: deleteTodo, isInFlight: isDeleting } =
    useRelayMutation<TodoItemRelayContainerDeleteMutation>(TodoDeleteMutation);

  const handleToggle = async () => {
    const nextProgress = todo.progress === 100 ? 0 : 100;

    try {
      const response = await updateTodo({
        variables: {
          id: todo.id,
          input: { progress: nextProgress },
        },
        // ✅ 楽観的更新
        optimisticResponse: {
          updateTodo: {
            __typename: 'UpdateTodoPayload',
            todo: {
              id: todo.id,
              todoTitle: todo.todoTitle,
              priority: todo.priority,
              progress: nextProgress,
              updatedAt: new Date().toISOString(),
            },
          },
        },
        errorContext: '進捗更新',
      });

      if (response.updateTodo.__typename === 'UpdateTodoPayload') {
        //toast.success('進捗を更新しました');
      }
    } catch (error) {
      if (import.meta.env.DEV) console.error(error);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('本当に削除しますか？')) return;

    try {
      const response = await deleteTodo({
        variables: {
          id: todo.id,
          // ✅ Connection ID を渡す
          connections: ['client:root:__TodoList_todosConnection_connection'],
        },
        // ✅ 楽観的更新
        optimisticUpdater: (store) => {
          store.delete(todo.id);
        },
        errorContext: 'Todo削除',
      });

      if (response.deleteTodo.__typename === 'DeleteTodoPayload') {
        //toast.success('削除しました');
      }
    } catch (error) {
      if (import.meta.env.DEV) console.error(error);
    }
  };

  const priority = isPriority(todo.priority) ? todo.priority : 'MEDIUM';

  return (
    <>
      <TodoItem
        id={todo.id}
        title={todo.todoTitle}
        priority={priority}
        progress={todo.progress ?? 0}
        updatedAt={todo.updatedAt}
        showActions={props.showActions}
        disabled={isUpdating || isDeleting}
        onEdit={() => setIsEditOpen(true)}
        onDelete={handleDelete}
        onToggleComplete={handleToggle}
      />
      {isEditOpen && (
        <TodoEditModalRelayContainer
          todoRef={todo}
          onClose={() => setIsEditOpen(false)}
        />
      )}
    </>
  );
};