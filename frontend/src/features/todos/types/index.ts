import type { ApiRes, ApiReq } from '@/types/api-utils';

// 一覧取得の型。配列なので [number] で中身を抜く
export type Todo = ApiRes<'/api/v1/todos/', 'get'> extends Array<infer T> ? T : never;

// 新規作成時の入力型
export type CreateTodoInput = ApiReq<'/api/v1/todos/', 'post'>;

// 更新時の入力型（PATCHなので一部の項目だけでもOKな型が自動で手に入る）
export type UpdateTodoInput = ApiReq<'/api/v1/todos/{id}/', 'patch'>;

export type Priority = 'LOW' | 'MEDIUM' | 'HIGH';

/*
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

*/