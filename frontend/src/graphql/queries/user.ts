import { gql } from 'graphql-request';
import { USER_FRAGMENT } from '../fragments/user';

/**
 * 現在のログインユーザー情報取得
 */
export const GET_ME = gql`
  ${USER_FRAGMENT}
  query GetMe {
    me {
      ...UserFields
    }
  }
`;