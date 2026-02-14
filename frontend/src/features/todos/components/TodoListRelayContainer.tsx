import type { TodoListRelayContainerQuery } from '@/__generated__/TodoListRelayContainerQuery.graphql';
import { useRelayLazyLoadQuery } from '@/hooks/useRelayLazyLoadQuery';
import { graphql } from 'react-relay';
import { TodoItemRelayContainer } from './TodoItemRelayContainer';

const TodoListQuery = graphql`
  query TodoListRelayContainerQuery($first: Int = 100) {
    todosConnection(first: $first)
    @connection(key: "TodoList_todosConnection") {
      edges {
        node {
          id
          ...TodoItemRelayContainer_todo
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
      totalCount
    }
  }
`;

export const TodoList = ({ showActions = true, limit }: { showActions?: boolean; limit?: number }) => {
  const data = useRelayLazyLoadQuery<TodoListRelayContainerQuery>(TodoListQuery, { first: 100, });

  // APIレスポンスが「配列そのまま」の場合と「{ data: [] }」の場合を許容し、
  // 取得失敗時は空配列をデフォルトにする（データの正規化）
  const edges = data.todosConnection?.edges ?? [];
  const totalCount = data.todosConnection?.totalCount ?? 0;
  const safeTodos = edges.map((edge) => edge.node);
  const displayTodos = limit ? safeTodos.slice(0, limit) : safeTodos;

  if (safeTodos.length === 0) {
    return <p className="text-center text-gray-500">まだタスクがありません。新しいタスクを追加しましょう！</p>;
  }

  return (
    <>
      <div className="space-y-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">タスク一覧</h2>
          <span className="text-sm text-muted-foreground">全{totalCount}件</span>
        </div>
        
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
