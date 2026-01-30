import { gql } from 'graphql-request';

/**
 * Todo基本フィールド
 * 再利用可能なFragment
 */
export const TODO_FRAGMENT = gql`
  fragment TodoFields on TodoType {
    id
    todoTitle
    priority
    progress
    createdAt
    updatedAt
  }
`;