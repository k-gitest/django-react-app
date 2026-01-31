import { gql } from 'graphql-request';
import { USER_FRAGMENT } from '../fragments/user';

/**
 * ユーザー登録
 */
export const REGISTER = gql`
  ${USER_FRAGMENT}
  mutation Register($input: RegisterInput!) {
    register(input: $input) {
      __typename
      ... on AuthPayload {
        user {
          ...UserFields
        }
        message
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
        conflictingField
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
 * ログイン
 */
export const LOGIN = gql`
  ${USER_FRAGMENT}
  mutation Login($input: LoginInput!) {
    login(input: $input) {
      __typename
      ... on AuthPayload {
        user {
          ...UserFields
        }
        message
      }
      ... on ValidationError {
        category
        message
        field
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
 * ログアウト
 */
export const LOGOUT = gql`
  mutation Logout {
    logout {
      __typename
      ... on Success {
        message
        success
      }
      ... on AuthenticationError {
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