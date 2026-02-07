import { useTodos } from '../hooks/useTodos';
import { TodoItem } from './TodoItem';
// import { Spinner } from '@/components/ui/spinner';
// import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
// import { Terminal } from 'lucide-react';
import { useState, useCallback } from 'react';
import { TodoEditModal } from './TodoEditModal';
import type { Todo } from '../types';
import type { TodoFormValues } from '../schemas';

export const TodoList = ({ showActions = true, limit }: { showActions?: boolean; limit?: number; }) => {
  const { todos, updateTodo, deleteTodo } = useTodos();
	const [editingTodo, setEditingTodo] = useState<Todo | null>(null);

  /*
  const handleToggleComplete = useCallback(async (todo: Todo) => {
    const newProgress = todo.progress === 100 ? 0 : 100;
    await updateTodo({ id: todo.id, data: { progress: newProgress } });
  }, [updateTodo]);
  */

  const handleToggleComplete = useCallback(async (id: number | string, currentProgress: number) => {
    const newProgress = currentProgress === 100 ? 0 : 100;
    await updateTodo({ id: Number(id), progress: newProgress });
  }, [updateTodo]);

	const handleEdit = useCallback((todo: Todo) => {
    setEditingTodo(todo);
  }, []);

  const handleDelete = useCallback(async (id: number) => {
    if (window.confirm('本当にこのタスクを削除しますか？')) {
      await deleteTodo(id);
    }
  }, [deleteTodo]);

  const handleUpdateSubmit = useCallback(async (values: TodoFormValues) => {
    if (!editingTodo) return;
    await updateTodo({ id: editingTodo.id, ...values });
  }, [editingTodo, updateTodo]);

  const handleModalClose = useCallback((open: boolean) => {
    if (!open) {
      setEditingTodo(null);
    }
  }, []);

  // APIレスポンスが「配列そのまま」の場合と「{ data: [] }」の場合を許容し、
  // 取得失敗時は空配列をデフォルトにする（データの正規化）
  const safeTodos: Todo[] = Array.isArray(todos) ? todos : (todos?.data ?? []);
  const displayTodos = limit ? safeTodos.slice(0, limit) : safeTodos;

  /*
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-40">
        <Spinner />
      </div>
    );
  }

  if (isError) {
    return (
      <Alert variant="destructive">
        <Terminal className="h-4 w-4" />
        <AlertTitle>エラー</AlertTitle>
        <AlertDescription>タスクの読み込みに失敗しました。</AlertDescription>
      </Alert>
    );
  }
  */

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
            title={todo.todo_title}
            priority={todo.priority ?? 'MEDIUM'}
            progress={todo.progress ?? 0}
            updatedAt={todo.updated_at}
            showActions={showActions}
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
          title={editingTodo.todo_title}
          priority={editingTodo.priority ?? 'MEDIUM'}
          progress={editingTodo.progress ?? 0}
          open={true}
          onOpenChange={handleModalClose}
          onSubmit={handleUpdateSubmit}
        />
      )}
		</>
  );
};