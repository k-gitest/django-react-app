import { Link } from 'react-router-dom';
import { useAuthStore } from '@/hooks/use-session-store';
//import { useProfile } from '@/features/profile/hooks/use-profile-queries-tanstack';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/features/auth/hooks/use-auth';

export const AuthHeader = () => {
  const user = useAuthStore((state) => state.user);
  const { signOut, signOutMutation } = useAuth();
  
  /* profileテーブルから取得出来る準備ができたら開放
  const { useGetProfile } = useProfile();
  const { data } = useGetProfile(userId); // ユーザーIDに基づいたプロフィール取得は維持
*/

  const signOutClick = async () => {
    try {
      await signOut();
    } catch (error) {
      if (import.meta.env.DEV) {
        console.error('ログアウトエラー:', error);
      }
    }
  };

  return (
    <header className="text-center px-5 pt-5">
      <div className="flex justify-between">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          <Link to="/dashboard">⚛️ + ⚡</Link>
        </h1>
        
        {/* ユーザー情報が表示可能であれば、ログアウトボタンを表示 */}
        {user && (
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600 dark:text-gray-300">
              {user.email} としてログイン中
            </span>
            <Button 
              variant="default"
              onClick={signOutClick}
              disabled={signOutMutation.isPending} // ← ローディング中は無効化
              className='cursor-pointer'
            >
              {signOutMutation.isPending ? 'ログアウト中...' : 'ログアウト'}
            </Button>
          </div>
        )}
      </div>
    </header>
  );
};