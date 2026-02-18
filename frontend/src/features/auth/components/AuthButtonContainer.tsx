import { useAuth } from '@/features/auth/hooks/use-auth0';
import { AuthButton } from './AuthButton';

type AuthType = 'login' | 'register';

interface AuthButtonContainerProps {
  type: AuthType;
}

export function AuthButtonContainer({ type }: AuthButtonContainerProps) {
  const { signIn, signUp, isLoading } = useAuth();

  const isLogin = type === 'login';
  const handleAuth = isLogin ? signIn : signUp;
  const label = isLogin ? 'ログイン' : '新規登録';
  const description = isLogin 
    ? 'Auth0を使用して安全にログインします' 
    : 'Auth0を使用してアカウントを作成します';

  return (
    <AuthButton 
      label={label}
      description={description}
      onAuth={handleAuth}
      isLoading={isLoading}
    />
  );
}