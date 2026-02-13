import type { TodoListRelayContainerQuery } from '@/__generated__/TodoListRelayContainerQuery.graphql';
import { useRelayLazyLoadQuery } from '@/hooks/useRelayLazyLoadQuery';
import { graphql } from 'react-relay';
import { TodoItemRelayContainer } from './TodoItemRelayContainer';

const TodoListQuery = graphql`
  query TodoListRelayContainerQuery {
    todos {
      id
      ...TodoItemRelayContainer_todo
    }
  }
`;

export const TodoList = ({ showActions = true, limit }: { showActions?: boolean; limit?: number }) => {
  const data = useRelayLazyLoadQuery<TodoListRelayContainerQuery>(TodoListQuery, {});

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
          <TodoItemRelayContainer
            key={todo.id}
            todoRef={todo}
            showActions={showActions}
          />
        ))}
      </div>
    </>
  );
};
