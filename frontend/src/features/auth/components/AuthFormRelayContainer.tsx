import { graphql } from 'react-relay';
import { useNavigate } from 'react-router-dom';
import { AccountForm } from './auth-form';
import { useRelayMutation } from '@/hooks/useRelayMutation';
import { useAuthStore } from '@/hooks/use-session-store';
import { queryClient } from '@/lib/queryClient';
import type { AccountFormType, Account } from '@/features/auth/types/auth';
import type { AuthFormRelayContainerRegisterMutation } from '@/__generated__/AuthFormRelayContainerRegisterMutation.graphql';
import type { AuthFormRelayContainerLoginMutation } from '@/__generated__/AuthFormRelayContainerLoginMutation.graphql';

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

  const { execute: commitRegister, isInFlight: isRegisterPending } = useRelayMutation<AuthFormRelayContainerRegisterMutation>(RegisterMutation);
  const { execute: commitLogin, isInFlight: isLoginPending } = useRelayMutation<AuthFormRelayContainerLoginMutation>(LoginMutation);

  const isLogin = type === 'login';
  const label = isLogin ? 'ログイン' : '登録';
  const isPending = isLogin ? isLoginPending : isRegisterPending;

  const handleSubmit = async (data: Account) => {
    // 共通の成功時・失敗時処理を定義
    // response は any ではなく、各 Mutation ごとの型がつきます
    const config = {
      variables: { input: { email: data.email, password: data.password, passwordConfirm: data.password } },
      errorContext: isLogin ? 'ログインに失敗しました' : 'ユーザー登録に失敗しました'
    };

    try {
      const response = isLogin ? await commitLogin(config) : await commitRegister(config);

      // 「login か register のどちらかに入っている result」を型安全に抽出
      const result = ('login' in response ? response.login : response.register);

      if (result?.__typename === 'AuthPayload') {
        // REST/GraphQL版と同じ処理を追加
        const user = result.user;
        
        if (user) {
          // ユーザー情報を即座にStoreにセット
          useAuthStore.getState().setUser({
            id: parseInt(atob(String(user.id)).split(':')[1], 10), // Relay GlobalID → 整数ID
            email: user.email,
            first_name: user.firstName,
            last_name: user.lastName,
            is_staff: user.isStaff,
          });

          // 2. キャッシュも手動で更新
          queryClient.setQueryData(['auth', 'me'], {
            id: parseInt(atob(String(user.id)).split(':')[1], 10),
            email: user.email,
            first_name: user.firstName,
            last_name: user.lastName,
            is_staff: user.isStaff,
          });
        }

        // 3. 初期化完了フラグを立ててガードを通す
        useAuthStore.getState().setInitialized(true);

        // 4. 念のため無効化（awaitしない）
        queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });

        navigate('/dashboard');
      }
    } catch (error) {
      // errorHandlerはuseRelayMutation内部で実行されるので、ここでは何もしなくてOK
      if (import.meta.env.DEV) console.error("error: ", error)
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