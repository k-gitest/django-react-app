import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { todoSchema, type TodoFormValues } from '../schemas';
import { Button } from '@/components/ui/button';
import { FormWrapper, FormInput, FormSelect } from '@/components/form/form-parts';
import { FormField, FormItem, FormLabel, FormControl } from '@/components/ui/form';
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
    <FormWrapper onSubmit={onSubmit} form={form}>
      {/* FormInputを使用（元はFormField + Input） */}
      <FormInput 
        label="タイトル" 
        name="todo_title"
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
      />

      {/* Sliderは特殊なのでFormFieldのまま */}
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
    </FormWrapper>
  );
};