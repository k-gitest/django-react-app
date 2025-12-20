import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { todoSchema, type TodoFormValues } from '../schemas';
import { useTodos } from '../hooks/useTodos';
import { Button } from '@/components/ui/button';
import { FormWrapper, FormInput, FormSelect } from '@/components/form/form-parts';
import { FormField, FormItem, FormLabel, FormControl } from '@/components/ui/form';
import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Plus } from 'lucide-react';

export const TodoCreateForm = () => {
  const [open, setOpen] = useState(false);
  const { createTodo } = useTodos();

  const form = useForm<TodoFormValues>({
    resolver: zodResolver(todoSchema),
    defaultValues: {
      todo_title: '',
      priority: 'MEDIUM',
      progress: 0,
    },
  });

  const onSubmit = async (values: TodoFormValues) => {
    try {
      await createTodo(values);
      form.reset();
      setOpen(false);
    } catch (error) {
      console.error('Failed to create todo:', error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="mb-4">
          <Plus className="mr-2 h-4 w-4" /> 新規タスク追加
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>新しいタスクを作成</DialogTitle>
        </DialogHeader>
        {/* FormWrapperを使用（元はForm） */}
        <FormWrapper onSubmit={onSubmit} form={form}>
          {/* FormInputを使用（元はFormField + Input） */}
          <FormInput
            label="タイトル"
            name="todo_title"
            placeholder="例: レポートを作成する"
          />
          
          {/* FormSelectを使用（元はFormField + Select） */}
          <FormSelect
            label="優先度"
            name="priority"
            options={[
              { value: 'LOW', label: '低' },
              { value: 'MEDIUM', label: '中' },
              { value: 'HIGH', label: '高' },
            ]}
            placeholder="優先度を選択"
          />

          {/* Input type="number" は特殊なのでFormFieldのまま */}
          <FormField
            control={form.control}
            name="progress"
            render={({ field }) => (
              <FormItem>
                <FormLabel>進捗 ({field.value}%)</FormLabel>
                <FormControl>
                  <input 
                    type="number" 
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    min={0}
                    max={100}
                    value={field.value}
                    onChange={e => field.onChange(parseInt(e.target.value) || 0)} 
                  />
                </FormControl>
              </FormItem>
            )}
          />

          <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting ? '保存中...' : 'タスクを保存'}
          </Button>
        </FormWrapper>
      </DialogContent>
    </Dialog>
  );
};