import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { TodoForm } from './TodoForm';
import type { TodoFormValues } from '../schemas';

interface TodoCreateFormProps {
  onSubmit: (values: TodoFormValues) => void | Promise<void>;
  isLoading?: boolean;
}

/**
 * Todo作成ダイアログ
 * 
 * DialogとTodoFormを統合したコンポーネント
 * - Dialog の開閉状態を管理
 * - フォーム送信後にDialogを閉じる
 */
export const TodoCreateForm = ({ onSubmit, isLoading }: TodoCreateFormProps) => {
  const [open, setOpen] = useState(false);

  const handleSubmit = async (values: TodoFormValues) => {
    await onSubmit(values);
    setOpen(false); // フォーム送信成功後にDialogを閉じる
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" /> 新規タスク追加
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>新しいタスクを作成</DialogTitle>
        </DialogHeader>
        {/* 共通のTodoFormを使用 */}
        <TodoForm
          onSubmit={handleSubmit}
          submitLabel={isLoading ? "作成中..." : "タスクを作成"}
          isLoading={isLoading}
        />
      </DialogContent>
    </Dialog>
  );
};