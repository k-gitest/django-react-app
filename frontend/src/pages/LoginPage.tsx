import { AuthFormContainer } from '@/features/auth/components/auth-form-container';
//import { AuthFormRelayContainer } from '@/features/auth/components/AuthFormRelayContainer';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { MainWrapper } from '@/components/layout/main-wrapper';
import { PageAsyncBoundary } from '@/components/async-boundary';

const Login = () => {
  return (
    <MainWrapper>
      <PageAsyncBoundary pageName="ログイン">
        <div className="flex justify-center">
          <AuthFormContainer type="login" />
        </div>
      </PageAsyncBoundary>

      <div className="flex justify-center p-4">
        <p>
          登録がまだの方は
          <Button variant="ghost">
            <Link to="/register">新規登録ページ</Link>
          </Button>
          から登録してください
        </p>
      </div>
    </MainWrapper>
  );
};

export default Login;
