import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/hooks/use-session-store';
import { useAuthUser } from '@/hooks/use-auth-user';

/**
 * 認証ガード（Cookie専用）
 * user情報の有無で認証状態を判定
 */
export const AuthGuard = () => {
  const { isLoading } = useAuthUser(); // ここで認証チェックが走る
  const user = useAuthStore((state) => state.user);
  const isInitialized = useAuthStore((state) => state.isInitialized);
  const location = useLocation();

  // 1. 初回のデータ取得中（初期化中）はローディング
  if ( isLoading && !isInitialized) {
    return <div className="h-screen flex items-center justify-center">Loading...</div>;
  }

  // 2. 取得が終わった結果、ユーザーがいなければログインへ
  if (!user) {
    return <Navigate drop-shadow to="/login" state={{ from: location }} replace />;
  }

  // 認証済みの場合、子要素をレンダリング
  return <Outlet />;
};