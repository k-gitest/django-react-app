import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { useTodos } from '../hooks/useTodos';
import { TodoForm } from './TodoForm';
import type { TodoFormValues } from '../schemas';

/**
 * Todo作成ダイアログ
 * 
 * DialogとTodoFormを統合したコンポーネント
 * - Dialog の開閉状態を管理
 * - フォーム送信後にDialogを閉じる
 */
export const TodoCreateForm = () => {
  const [open, setOpen] = useState(false);
  const { createTodo } = useTodos();

  const handleSubmit = async (values: TodoFormValues) => {
    await createTodo(values);
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
          submitLabel="タスクを作成"
        />
      </DialogContent>
    </Dialog>
  );
};