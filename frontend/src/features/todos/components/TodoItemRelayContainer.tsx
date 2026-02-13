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
      ... on TodoType {
        id
        todoTitle
        priority
        progress
      }
      ... on ValidationError {
        message
      }
    }
  }
`;

const TodoDeleteMutation = graphql`
  mutation TodoItemRelayContainerDeleteMutation($id: ID!) {
    deleteTodo(id: $id) {
      __typename
      ... on Success {
        message
        success
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
    await updateTodo({
      variables: {
        id: todo.id,
        input: { progress: todo.progress === 100 ? 0 : 100 }
      }
    });
  };

  const handleDelete = async () => {
    if (window.confirm('本当に削除しますか？')) {
      await deleteTodo({
        variables: { id: todo.id },
        updater: (store) => {
          store.delete(todo.id);
        },
      });
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