import { useCallback } from 'react';
import { useTodos } from '@/features/todos/hooks/useTodos';
import type { TodoFormValues } from '@/features/todos/schemas';
import { TodoIndexView } from './TodoIndexView';

export const TodoIndexContainer = () => {
  const { createTodo } = useTodos();

  const handleCreateSubmit = useCallback(async (values: TodoFormValues) => {
    await createTodo(values);
  }, [createTodo]);

  return <TodoIndexView onCreateSubmit={handleCreateSubmit} />;
};

export const TodoIndex = TodoIndexContainer;