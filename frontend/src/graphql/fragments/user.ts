import { gql } from 'graphql-request';

/**
 * User基本フィールド
 */
export const USER_FRAGMENT = gql`
  fragment UserFields on UserType {
    id
    email
    firstName
    lastName
    isStaff
    dateJoined
  }
`;