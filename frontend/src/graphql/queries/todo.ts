import { gql } from 'graphql-request';
import { TODO_FRAGMENT } from '../fragments/todo';

/**
 * Todo一覧取得
 */
export const GET_TODOS = gql`
  ${TODO_FRAGMENT}
  query GetTodos {
    todos {
      ...TodoFields
    }
  }
`;

/**
 * Todo個別取得
 */
export const GET_TODO = gql`
  ${TODO_FRAGMENT}
  query GetTodo($id: ID!) {
    todo(id: $id) {
      ...TodoFields
    }
  }
`;

/**
 * 優先度別統計
 */
export const GET_TODO_STATS = gql`
  query GetTodoStats {
    priorityStats {
      priority
      count
    }
  }
`;

/**
 * 進捗統計
 */
export const GET_PROGRESS_STATS = gql`
  query GetProgressStats {
    progressStats {
      range020
      range2140
      range4160
      range6180
      range81100
    }
  }
`;

/**
 * セマンティック検索
 */
export const SEARCH_TODOS = gql`
  query SearchTodos($input: TodoSearchInput!) {
    searchTodos(input: $input) {
      id
      todoTitle
      priority
      progress
      score
    }
  }
`;