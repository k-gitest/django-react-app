export type Priority = 'LOW' | 'MEDIUM' | 'HIGH';

export interface Todo {
  id: number;
  todo_title: string;
  priority: Priority;
  progress: number;
  user: string; // ユーザーのemail
  created_at: string;
  updated_at: string;
}

export type CreateTodoInput = Pick<Todo, 'todo_title' | 'priority' | 'progress'>;
export type UpdateTodoInput = Partial<CreateTodoInput>;