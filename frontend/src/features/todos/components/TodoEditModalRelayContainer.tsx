import { graphql, useFragment } from 'react-relay';
import { TodoEditModal } from './TodoEditModal';
import { isPriority } from '@/lib/utils';
import { useRelayMutation } from '@/hooks/useRelayMutation';
import type { TodoEditModalRelayContainer_todo$key } from '@/__generated__/TodoEditModalRelayContainer_todo.graphql';
import type { TodoUpdateInput, TodoEditModalRelayContainerUpdateMutation } from '@/__generated__/TodoEditModalRelayContainerUpdateMutation.graphql';

const TodoEditModalFragment = graphql`
  fragment TodoEditModalRelayContainer_todo on TodoType {
    id
    todoTitle
    priority
    progress
  }
`;

const TodoUpdateMutation = graphql`
  mutation TodoEditModalRelayContainerUpdateMutation($id: ID!, $input: TodoUpdateInput!) {
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

interface Props {
  todoRef: TodoEditModalRelayContainer_todo$key;
  onClose: () => void;
}

export const TodoEditModalRelayContainer = ({ todoRef, ...props }: Props) => {
  const todo = useFragment<TodoEditModalRelayContainer_todo$key>(TodoEditModalFragment, todoRef);

  const { execute: updateTodo, isInFlight: isUpdating } =
      useRelayMutation<TodoEditModalRelayContainerUpdateMutation>(TodoUpdateMutation);

  const handleSave = async (formValues: { todo_title: string; priority: string; progress: number }) => {
    // スキーマの型に合わせてオブジェクトを構成
    const input: TodoUpdateInput = {
      todoTitle: formValues.todo_title,
      priority: isPriority(formValues.priority) ? formValues.priority : 'MEDIUM',
      progress: formValues.progress,
    };

    await updateTodo({
      variables: {
        id: todo.id,
        input,
      },
    });
    props.onClose(); // 成功時に閉じる
  };

  // onOpenChangeをbooleanで受け取り、falseの時だけonCloseを呼ぶ
  const handleOpenChange = (open: boolean) => {
    if (!open) {
      props.onClose();
    }
  };

  const priority = isPriority(todo.priority) ? todo.priority : 'MEDIUM';

  return (
    <TodoEditModal
			id={todo.id}
      open={true}
      title={todo.todoTitle}
      priority={priority}
      progress={todo.progress ?? 0}
      onOpenChange={handleOpenChange}
      onSubmit={handleSave}
      isSubmitting={isUpdating}
    />
  );
};