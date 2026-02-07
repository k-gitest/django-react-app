import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
//import type { Todo } from '../types';
import type { TodoFormValues } from '../schemas';
import { TodoForm } from './TodoForm';
//import { useTodos } from '../hooks/useTodos';

/*
interface TodoEditModalProps {
  todo: Todo | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}
*/

interface TodoEditModalProps {
  id: number | string;
  title: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  progress: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (values: TodoFormValues) => void | Promise<void>;
}

export const TodoEditModal = ({ 
  //id, 
  title, 
  priority, 
  progress, 
  open, 
  onOpenChange, 
  onSubmit  
}: TodoEditModalProps) => {
  //const { updateTodo } = useTodos();

  //if (!id) return null;

  const handleSubmit = async (values: TodoFormValues) => {
    await onSubmit(values);
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
            todo_title: title,
            priority: priority,
            progress: progress,
          }}
          onSubmit={handleSubmit}
          submitLabel="変更を保存"
        />
      </DialogContent>
    </Dialog>
  );
};