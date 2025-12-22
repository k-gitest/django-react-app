import { useTodos } from '../hooks/useTodos';
import { TodoItem } from './TodoItem';
import { Spinner } from '@/components/ui/spinner';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Terminal } from 'lucide-react';
import { useState, useCallback } from 'react';
import { TodoEditModal } from './TodoEditModal';
import type { Todo } from '../types';

export const TodoList = ({ showActions = true, limit }: { showActions?: boolean; limit?: number; }) => {
  const { todos, isLoading, isError, updateTodo, deleteTodo } = useTodos();
	const [editingTodo, setEditingTodo] = useState<Todo | null>(null);

  const handleToggleComplete = useCallback(async (todo: Todo) => {
    const newProgress = todo.progress === 100 ? 0 : 100;
    await updateTodo({ id: todo.id, data: { progress: newProgress } });
  }, [updateTodo]);

	const handleEdit = useCallback((todo: Todo) => {
    setEditingTodo(todo);
  }, []);

  const handleDelete = useCallback(async (id: number) => {
    if (window.confirm('本当にこのタスクを削除しますか？')) {
      await deleteTodo(id);
    }
  }, [deleteTodo]);

  const handleModalClose = useCallback((open: boolean) => {
    if (!open) {
      setEditingTodo(null);
    }
  }, []);

  const displayTodos = limit ? todos.slice(0, limit) : todos;

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

  if (todos.length === 0) {
    return <p className="text-center text-gray-500">まだタスクがありません。新しいタスクを追加しましょう！</p>;
  }

  return (
    <>
			<div className="space-y-4">
				{displayTodos.map((todo) => (
					<TodoItem
						key={todo.id}
						todo={todo}
            showActions={showActions}
						onToggleComplete={handleToggleComplete}
						onEdit={handleEdit}
						onDelete={handleDelete}
					/>
				))}
			</div>
			{/* ✅ 編集モードの時だけモーダルをレンダリング（微塵の無駄も省く） */}
      {showActions && (
        <TodoEditModal 
          todo={editingTodo} 
          open={!!editingTodo} 
          onOpenChange={handleModalClose} 
        />
      )}
		</>
  );
};