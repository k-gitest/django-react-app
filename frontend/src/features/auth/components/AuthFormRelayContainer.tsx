import { graphql, useMutation } from 'react-relay';
import { useNavigate } from 'react-router-dom';
import { AccountForm } from './auth-form';
import type { AccountFormType, Account } from '@/features/auth/types/auth';

// --- 自動生成される型をインポート ---
// ※ relay-compiler 実行後に生成されます
import type { 
  AuthFormRelayContainerRegisterMutation 
} from '@/__generated__/AuthFormRelayContainerRegisterMutation.graphql';

import type { 
  AuthFormRelayContainerLoginMutation 
} from '@/__generated__/AuthFormRelayContainerLoginMutation.graphql';

const RegisterMutation = graphql`
  mutation AuthFormRelayContainerRegisterMutation($input: RegisterInput!) {
    register(input: $input) {
      __typename
      ... on AuthPayload {
        user {
          id
          email
          firstName
          lastName
          isStaff
          dateJoined
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

const LoginMutation = graphql`
  mutation AuthFormRelayContainerLoginMutation($input: LoginInput!) {
    login(input: $input) {
      __typename
      ... on AuthPayload {
        user {
          id
          email
          firstName
          lastName
          isStaff
          dateJoined
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

export const AuthFormRelayContainer = ({ type }: { type: AccountFormType }) => {
  const navigate = useNavigate();
  
  // ジェネリクスに型を渡すことで、引数やレスポンスが型安全になる
  const [commitRegister, isRegisterPending] = useMutation<AuthFormRelayContainerRegisterMutation>(RegisterMutation);
  const [commitLogin, isLoginPending] = useMutation<AuthFormRelayContainerLoginMutation>(LoginMutation);

  const isLogin = type === 'login';
  const label = isLogin ? 'ログイン' : '登録';
  const isPending = isLogin ? isLoginPending : isRegisterPending;

  const handleSubmit = async (data: Account) => {
    // 共通の成功時・失敗時処理を定義
    // response は any ではなく、各 Mutation ごとの型がつきます
    const variables = {
      input: {
        email: data.email,
        password: data.password,
        passwordConfirm: data.password,
      },
    };

    if (isLogin) {
      commitLogin({
        variables,
        onCompleted: (response) => {
          // response は AuthFormRelayContainerLoginMutation$data 型になる
          if (response.login?.__typename === 'AuthPayload') {
             navigate('/dashboard');
          }
        },
        onError: (error: Error) => console.error(error),
      });
    } else {
      commitRegister({
        variables,
        onCompleted: (response) => {
          // response は AuthFormRelayContainerRegisterMutation$data 型になる
          if (response.register?.__typename === 'AuthPayload') {
             navigate('/dashboard');
          }
        },
        onError: (error: Error) => console.error(error),
      });
    }
  };

  return (
    <AccountForm
      submitLabel={label}
      onSubmit={handleSubmit}
      isLoading={isPending}
    />
  );
};