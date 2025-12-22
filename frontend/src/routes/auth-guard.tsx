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

  // 「ロード中」かつ「一度も初期化されていない」間は、絶対に Navigate させない
  if (isLoading && !isInitialized) {
    return <div className="h-screen flex items-center justify-center">Loading...</div>;
  }

  // 「ロードが終わり」、かつ「ユーザーがいない」ことが確定してから初めてログインへ飛ばす
  if (!isLoading && isInitialized && !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 認証済みの場合、子要素をレンダリング
  return <Outlet />;
};