import type { TodoListRelayContainerDeleteMutation } from '@/__generated__/TodoListRelayContainerDeleteMutation.graphql';
import type {
  TodoListRelayContainerQuery,
  TodoListRelayContainerQuery$data,
} from '@/__generated__/TodoListRelayContainerQuery.graphql';
import type { TodoListRelayContainerUpdateMutation } from '@/__generated__/TodoListRelayContainerUpdateMutation.graphql';
import { useRelayLazyLoadQuery } from '@/hooks/useRelayLazyLoadQuery';
import { useRelayMutation } from '@/hooks/useRelayMutation';
import { useCallback, useState } from 'react';
import { graphql } from 'react-relay';
import type { TodoFormValues } from '../schemas';
import { TodoEditModal } from './TodoEditModal';
import { TodoItem } from './TodoItem';

const TodoListQuery = graphql`
  query TodoListRelayContainerQuery {
    todos {
      id
      todoTitle
      priority
      progress
      updatedAt
    }
  }
`;

const TodoUpdateMutation = graphql`
  mutation TodoListRelayContainerUpdateMutation($id: ID!, $input: TodoUpdateInput!) {
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
  mutation TodoListRelayContainerDeleteMutation($id: ID!) {
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

type TodoNode = TodoListRelayContainerQuery$data['todos'][number];

export const TodoList = ({ showActions = true, limit }: { showActions?: boolean; limit?: number }) => {
  const { execute: updateTodo, isInFlight: isUpdating } =
    useRelayMutation<TodoListRelayContainerUpdateMutation>(TodoUpdateMutation);
  const { execute: deleteTodo, isInFlight: isDeleting } =
    useRelayMutation<TodoListRelayContainerDeleteMutation>(TodoDeleteMutation);
  const data = useRelayLazyLoadQuery<TodoListRelayContainerQuery>(TodoListQuery, {});

  const [editingTodo, setEditingTodo] = useState<TodoNode | null>(null);

  const handleToggleComplete = useCallback(
    async (id: number | string, currentProgress: number) => {
      const newProgress = currentProgress === 100 ? 0 : 100;
      await updateTodo({
        variables: {
          id: String(id),
          input: { progress: newProgress },
        },
      });
    },
    [updateTodo],
  );

  const handleEdit = useCallback((todo: TodoNode) => {
    setEditingTodo(todo);
  }, []);

  const handleDelete = useCallback(
    async (id: string) => {
      if (window.confirm('本当にこのタスクを削除しますか？')) {
        await deleteTodo({
          variables: { id: String(id) }, // RelayのIDは文字列(GlobalID)として扱うのが無難です
        });
      }
    },
    [deleteTodo],
  );

  const handleUpdateSubmit = useCallback(
    async (values: TodoFormValues) => {
      if (!editingTodo) return;
      await updateTodo({
        variables: {
          id: String(editingTodo.id),
          input: {
            todoTitle: values.todo_title, // スキーマに合わせてマッピング
            priority: values.priority,
            progress: values.progress,
          },
        },
      });
    },
    [editingTodo, updateTodo],
  );

  const handleModalClose = useCallback((open: boolean) => {
    if (!open) {
      setEditingTodo(null);
    }
  }, []);

  // APIレスポンスが「配列そのまま」の場合と「{ data: [] }」の場合を許容し、
  // 取得失敗時は空配列をデフォルトにする（データの正規化）
  const safeTodos = data?.todos ?? [];
  const displayTodos = limit ? safeTodos.slice(0, limit) : safeTodos;

  if (safeTodos.length === 0) {
    return <p className="text-center text-gray-500">まだタスクがありません。新しいタスクを追加しましょう！</p>;
  }

  return (
    <>
      <div className="space-y-4">
        {displayTodos.map((todo) => (
          <TodoItem
            key={todo.id}
            id={todo.id}
            title={todo.todoTitle}
            priority={(todo.priority as 'LOW' | 'MEDIUM' | 'HIGH') ?? 'MEDIUM'}
            progress={todo.progress ?? 0}
            updatedAt={todo.updatedAt}
            showActions={showActions}
            disabled={isUpdating || isDeleting}
            onToggleComplete={() => handleToggleComplete(todo.id, todo.progress ?? 0)}
            onEdit={() => handleEdit(todo)}
            onDelete={() => handleDelete(todo.id)}
          />
        ))}
      </div>
      {/* ✅ 編集モードの時だけモーダルをレンダリング */}
      {showActions && editingTodo && (
        <TodoEditModal
          id={editingTodo.id}
          title={editingTodo.todoTitle}
          priority={(editingTodo.priority as "LOW" | "MEDIUM" | "HIGH") ?? 'MEDIUM'}
          progress={editingTodo.progress ?? 0}
          open={true}
          onOpenChange={handleModalClose}
          onSubmit={handleUpdateSubmit}
          isSubmitting={isUpdating}
        />
      )}
    </>
  );
};
