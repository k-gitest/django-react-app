import { gql } from 'graphql-request';
import { TODO_FRAGMENT } from '../fragments/todo';

/**
 * Todo作成
 */
export const CREATE_TODO = gql`
  ${TODO_FRAGMENT}
  mutation CreateTodo($input: TodoCreateInput!) {
    createTodo(input: $input) {
      __typename
      ... on TodoType {
        ...TodoFields
      }
      ... on ValidationError {
        category
        message
        field
        code
      }
      ... on ConflictError {
        category
        message
        code
      }
      ... on InternalError {
        category
        message
        code
      }
    }
  }
`;

/**
 * Todo更新
 */
export const UPDATE_TODO = gql`
  ${TODO_FRAGMENT}
  mutation UpdateTodo($id: GlobalID!, $input: TodoUpdateInput!) {
    updateTodo(id: $id, input: $input) {
      __typename
      ... on TodoType {
        ...TodoFields
      }
      ... on ValidationError {
        category
        message
        field
        code
      }
      ... on NotFoundError {
        category
        message
        code
      }
      ... on InternalError {
        category
        message
        code
      }
    }
  }
`;

/**
 * Todo削除
 */
export const DELETE_TODO = gql`
  mutation DeleteTodo($id: GlobalID!) {
    deleteTodo(id: $id) {
      __typename
      ... on Success {
        message
        success
      }
      ... on NotFoundError {
        category
        message
        code
      }
      ... on InternalError {
        category
        message
        code
      }
    }
  }
`;

/**
 * 一括ベクトルインデックス登録
 */
export const BULK_INDEX_TODOS = gql`
  mutation BulkIndexTodos {
    bulkIndexTodos {
      __typename
      ... on Success {
        message
        success
      }
      ... on ExternalServiceError {
        category
        message
        code
      }
      ... on InternalError {
        category
        message
        code
      }
    }
  }
`;