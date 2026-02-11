import { useCallback } from 'react';
import { useTodos } from '@/features/todos/hooks/useTodos';
import { TodoCreateForm } from './TodoCreateForm';
import type { TodoFormValues } from '@/features/todos/schemas';

export const TodoCreateFormContainer = () => {
  const { createTodo, createMutation } = useTodos();

  const handleCreateSubmit = useCallback(async (values: TodoFormValues) => {
    await createTodo(values);
  }, [createTodo]);

  return (
    <TodoCreateForm onSubmit={handleCreateSubmit} isLoading={createMutation.isPending} />
  );
};