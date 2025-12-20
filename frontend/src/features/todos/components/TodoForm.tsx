import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { todoSchema, type TodoFormValues } from '../schemas';
import { Button } from '@/components/ui/button';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';

interface TodoFormProps {
  defaultValues: TodoFormValues;
  onSubmit: (values: TodoFormValues) => Promise<void>;
  submitLabel: string;
}

export const TodoForm = ({ defaultValues, onSubmit, submitLabel }: TodoFormProps) => {
  const form = useForm<TodoFormValues>({
    resolver: zodResolver(todoSchema),
    defaultValues,
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="todo_title"
          render={({ field }) => (
            <FormItem>
              <FormLabel>タイトル</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          control={form.control}
          name="priority"
          render={({ field }) => (
            <FormItem>
              <FormLabel>優先度</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl><SelectTrigger><SelectValue /></SelectTrigger></FormControl>
                <SelectContent>
                  <SelectItem value="LOW">低</SelectItem>
                  <SelectItem value="MEDIUM">中</SelectItem>
                  <SelectItem value="HIGH">高</SelectItem>
                </SelectContent>
              </Select>
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="progress"
          render={({ field }) => (
            <FormItem>
              <FormLabel>進捗: {field.value}%</FormLabel>
              <FormControl>
                <Slider
                  min={0} max={100} step={5}
                  value={[field.value]}
                  onValueChange={(vals) => field.onChange(vals[0])}
                />
              </FormControl>
            </FormItem>
          )}
        />

        <Button type="submit" className="w-full" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? '処理中...' : submitLabel}
        </Button>
      </form>
    </Form>
  );
};
