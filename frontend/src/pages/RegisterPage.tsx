import { AuthFormContainer } from '@/features/auth/components/auth-form-container';
//import { AuthFormRelayContainer as AuthFormContainer } from '@/features/auth/components/AuthFormRelayContainer';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { MainWrapper } from '@/components/layout/main-wrapper';
import { PageAsyncBoundary } from '@/components/async-boundary';

const Register = () => {
  return (
    <MainWrapper>
      <PageAsyncBoundary pageName="新規登録">
        <div className="flex justify-center">
          <AuthFormContainer type="register" />
        </div>
      </PageAsyncBoundary>

      <div className="flex justify-center p-4">
        <p>
          既に登録している方は
          <Button variant="ghost">
            <Link to="/login">ログインページ</Link>
          </Button>
          からログインしてください
        </p>
      </div>
    </MainWrapper>
  );
};

export default Register;
