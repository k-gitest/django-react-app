import { gql } from 'graphql-request';
import { TODO_FRAGMENT } from '../fragments/todo';

/**
 * Todo作成
 * CreateTodoPayload > todoEdge > node の階層に変更
 */
export const CREATE_TODO = gql`
  ${TODO_FRAGMENT}
  mutation CreateTodo($input: TodoCreateInput!) {
    createTodo(input: $input) {
      __typename
      ... on CreateTodoPayload {
        todoEdge {
          node {
            ...TodoFields
          }
        }
      }
      ... on ValidationError {
        message
        field
      }
      ... on InternalError {
        message
      }
    }
  }
`;

/**
 * Todo更新
 * UpdateTodoPayload > todo の階層に変更
 */
export const UPDATE_TODO = gql`
  ${TODO_FRAGMENT}
  mutation UpdateTodo($id: ID!, $input: TodoUpdateInput!) {
    updateTodo(id: $id, input: $input) {
      __typename
      ... on UpdateTodoPayload {
        todo {
          ...TodoFields
        }
      }
      ... on ValidationError {
        message
        field
      }
      ... on NotFoundError {
        message
      }
      ... on InternalError {
        message
      }
    }
  }
`;

/**
 * Todo削除
 * DeleteTodoPayload を使用。Success型は消えたので削除。
 */
export const DELETE_TODO = gql`
  mutation DeleteTodo($id: ID!) {
    deleteTodo(id: $id) {
      __typename
      ... on DeleteTodoPayload {
        deletedTodoId
        message
      }
      ... on NotFoundError {
        message
      }
      ... on InternalError {
        message
      }
    }
  }
`;

/**
 * 一括ベクトルインデックス登録
 * 戻り値が Success 型のままならそのままでOK
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
        message
      }
      ... on InternalError {
        message
      }
    }
  }
`;