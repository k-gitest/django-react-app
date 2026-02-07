import * as rest from './todo-service';
import * as graphql from './todo-service-graphql';

/**
 * 💡 サービス切り替えスイッチ
 * true にしたメソッドは GraphQL、false は REST が使われます。
 */
const useGraphQL = {
  getTodos: true,
  createTodo: false,
  updateTodo: true,
  deleteTodo: true,
  getTodoStats: false,
  getProgressStats: false,
};

export const todoService = {
  // Todo情報取得
  getTodos: useGraphQL.getTodos ? graphql.todoServiceGraphQL.getTodos : rest.todoService.getTodos,

  // Todo作成
  createTodo: useGraphQL.createTodo ? graphql.todoServiceGraphQL.createTodo : rest.todoService.createTodo,

  // 更新
  updateTodo: useGraphQL.updateTodo ? graphql.todoServiceGraphQL.updateTodo : rest.todoService.updateTodo,

  // 削除
  deleteTodo: useGraphQL.deleteTodo ? graphql.todoServiceGraphQL.deleteTodo : rest.todoService.deleteTodo,

  // 統計情報取得
  getTodoStats: useGraphQL.getTodoStats ? graphql.todoServiceGraphQL.getTodoStats : rest.todoService.getTodoStats,
  
  // 進捗統計情報取得
  getProgressStats: useGraphQL.getProgressStats ? graphql.todoServiceGraphQL.getProgressStats : rest.todoService.getProgressStats,
};

export const { getTodos, createTodo, updateTodo, deleteTodo, getTodoStats, getProgressStats } = todoService;
