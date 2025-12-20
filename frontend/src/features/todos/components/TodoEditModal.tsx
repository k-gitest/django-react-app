import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import type { Todo } from '../types';
import type { TodoFormValues } from '../schemas';
import { TodoForm } from './TodoForm';
import { useTodos } from '../hooks/useTodos';

interface TodoEditModalProps {
  todo: Todo | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const TodoEditModal = ({ todo, open, onOpenChange }: TodoEditModalProps) => {
  const { updateTodo } = useTodos();

  if (!todo) return null;

  const handleSubmit = async (values: TodoFormValues) => {
    await updateTodo({ id: todo.id, data: values });
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>タスクを編集</DialogTitle>
        </DialogHeader>
        <TodoForm 
          defaultValues={{
            todo_title: todo.todo_title,
            priority: todo.priority,
            progress: todo.progress,
          }}
          onSubmit={handleSubmit}
          submitLabel="変更を保存"
        />
      </DialogContent>
    </Dialog>
  );
};