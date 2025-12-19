import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/hooks/use-session-store';

export const Header = () => {
  const session = useAuthStore((state) => state.user);

  return (
    <header className="text-center px-5 pt-5">
      <h1 className="text-3xl font-bold text-gray-900 mb-5 dark:text-white">Django + React ⚛️ + shadcn/ui</h1>

      <nav className="flex justify-center gap-2">
        <Button variant="ghost" asChild>
          <Link to="/">Home</Link>
        </Button>
        <Button variant="ghost" asChild>
          <Link to="/about">About</Link>
        </Button>
        {session && (
          <>
            <Button variant="ghost" asChild>
              <Link to="/dashboard">ダッシュボード</Link>
            </Button>
          </>
        )}
        {!session && (
          <>
            <Button variant="ghost" asChild>
              <Link to="/login">ログイン</Link>
            </Button>
            <Button variant="ghost" asChild>
              <Link to="/register">新規登録</Link>
            </Button>
          </>
        )}
      </nav>
    </header>
  );
};
