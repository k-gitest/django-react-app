import { useTodos } from '../hooks/useTodos';
import { TodoItem } from './TodoItem';
import { Spinner } from '@/components/ui/spinner';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Terminal } from 'lucide-react';
import { useState } from 'react';
import { TodoEditModal } from './TodoEditModal';
import type { Todo } from '../types';

export const TodoList = () => {
  const { todos, isLoading, isError, updateTodo, deleteTodo } = useTodos();
	const [editingTodo, setEditingTodo] = useState<Todo | null>(null);

  const handleToggleComplete = async (todo: typeof todos[number]) => {
    const newProgress = todo.progress === 100 ? 0 : 100;
    await updateTodo({ id: todo.id, data: { progress: newProgress } });
  };

	/*
  const handleEdit = (todo: typeof todos[number]) => {
    // 編集モーダルなどを開くロジックをここに実装
    console.log('Edit todo:', todo);
    alert(`TODO: ${todo.todo_title} を編集`);
  };
	*/

  const handleDelete = async (id: number) => {
    if (window.confirm('本当にこのタスクを削除しますか？')) {
      await deleteTodo(id);
    }
  };

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
				{todos.map((todo) => (
					<TodoItem
						key={todo.id}
						todo={todo}
						onToggleComplete={handleToggleComplete}
						onEdit={(t) => setEditingTodo(t)} // 編集対象をセット
						onDelete={handleDelete}
					/>
				))}
			</div>
			<TodoEditModal 
					todo={editingTodo} 
					open={!!editingTodo} 
					onOpenChange={(open) => !open && setEditingTodo(null)} 
				/>
		</>
  );
};