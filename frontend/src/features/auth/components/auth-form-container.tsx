import { useAuth } from '@/features/auth/hooks/use-auth';
import { AccountForm } from './auth-form';
import type { AccountFormType } from '@/features/auth/types/auth';

export const AuthFormContainer = ({ type }: { type: AccountFormType }) => {
  const { signIn, signUp, signInMutation, signUpMutation } = useAuth();

  // 1. type に基づいて「実行する関数」と「状態」を選択
  const isLogin = type === 'login';
  const submitFn = isLogin ? signIn : signUp;
  const isPending = isLogin ? signInMutation.isPending : signUpMutation.isPending;
  const label = isLogin ? 'ログイン' : '登録';

  return (
    <AccountForm 
      submitLabel={label} 
      onSubmit={submitFn} 
      isLoading={isPending} 
    />
  );
};