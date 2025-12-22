import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/hooks/use-session-store';
import { useAuthUser } from '@/hooks/use-auth-user';

export const GuestGuard = () => {
  const { isLoading } = useAuthUser(); // 現在の認証状況を確認
  const user = useAuthStore((state) => state.user);
  const isInitialized = useAuthStore((state) => state.isInitialized);

  // 1. まだ認証チェックが終わっていない場合はローディングを表示
  // これがないと、一瞬ログイン画面が見えた後にリダイレクトされるちらつきが起きます
  if (isLoading && !isInitialized) {
    return <div className="h-screen flex items-center justify-center">Loading...</div>;
  }

  // ロードが終わり、ユーザーがいることが確定した時のみリダイレクト
  if (!isLoading && isInitialized && user) {
    return <Navigate to="/dashboard" replace />;
  }

  // セッションがない（未ログイン）の場合、子要素をレンダリング
  return <Outlet />;
};
