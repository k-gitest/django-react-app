import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { useAuthStore } from '@/hooks/use-session-store';

export const ContentHome = () => {
  const user = useAuthStore((state) => state.user);
  return (
    <div className="w-full h-[calc(100vh-148px)] bg-gray-200 flex flex-col gap-6 justify-center items-center rounded-md">
      <h2 className="text-6xl">django + react APP</h2>
      <div className="flex gap-2">
        {!user && (
          <>
            <Button data-testid="register-button-content-home">
              <Link to="/register">新規登録</Link>
            </Button>
            <Button data-testid="login-button-content-home">
              <Link to="/login">ログイン</Link>
            </Button>
          </>
        )}
        {user && (
          <Button data-testid="dashboard-button-content-home">
            <Link to="/dashboard">dashboard</Link>
          </Button>
        )}
      </div>
    </div>
  );
};
