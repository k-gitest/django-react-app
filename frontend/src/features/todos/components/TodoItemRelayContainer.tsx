import { graphql, useFragment } from 'react-relay';
import { TodoItem } from './TodoItem';
import { isPriority } from '@/lib/utils';
import { useRelayMutation } from '@/hooks/useRelayMutation';
import { useCallback } from 'react';
import { useExclusiveModal, useUIStore } from '@/hooks/useExclusiveModal';
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
  //const [isEditOpen, setIsEditOpen] = useState(false);
  const { isOpen, open, close } = useExclusiveModal();

  const { execute: updateTodo, isInFlight: isUpdating } =
    useRelayMutation<TodoItemRelayContainerUpdateMutation>(TodoUpdateMutation);
  const { execute: deleteTodo, isInFlight: isDeleting } =
    useRelayMutation<TodoItemRelayContainerDeleteMutation>(TodoDeleteMutation);

  const handleToggle = useCallback(async () => {
    const nextProgress = todo.progress === 100 ? 0 : 100;

    try {
      await updateTodo({
        variables: {
          id: todo.id,
          input: { progress: nextProgress },
        },
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
    } catch (error) {
      if (import.meta.env.DEV) console.error(error);
    }
  }, [todo.id, todo.todoTitle, todo.priority, todo.progress, updateTodo]);

  const handleDelete = useCallback(async () => {
    if (!window.confirm('本当に削除しますか？')) return;

    try {
      await deleteTodo({
        variables: {
          id: todo.id,
          connections: ['client:root:__TodoList_todosConnection_connection'],
        },
        optimisticUpdater: (store) => {
          store.delete(todo.id);
        },
        errorContext: 'Todo削除',
      });
    } catch (error) {
      if (import.meta.env.DEV) console.error(error);
    }
  }, [todo.id, deleteTodo]);

  // 編集開始ハンドラ (排他制御付き)
  /*
  const handleEditOpen = useCallback(() => {
    open(); // 内部で isAnyModalOpen をチェック
  }, [open]);
  */

  const isLockedByOther = useUIStore(
    (state) => state.currentModalId !== null && !isOpen
  );

  const isDisabled = isUpdating || isDeleting || isLockedByOther;

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
        disabled={isDisabled}
        onEdit={open}
        onDelete={handleDelete}
        onToggleComplete={handleToggle}
      />
      {isOpen && (
        <TodoEditModalRelayContainer
          todoRef={todo}
          onClose={close}
        />
      )}
    </>
  );
};