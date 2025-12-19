import { Link } from 'react-router-dom';
//import { useEffect, useState } from 'react';
// import { errorHandler } from '@/errors/error-handler'; // エラーハンドラは残します
// import { useSignOutHandler } from '@/features/auth/hooks/use-signout-handler'; // 外部フックは削除し、storeのlogoutを使用

import { useAuthStore } from '@/hooks/use-session-store'; // 👈 新しいストアをインポート
//import { useProfile } from '@/features/profile/hooks/use-profile-queries-tanstack';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/features/auth/hooks/use-auth';

export const AuthHeader = () => {
  // 必要な状態を useAuthStore から取得
  const user = useAuthStore((state) => state.user); // 👈 ユーザー情報を直接取得
  //const logout = useAuthStore((state) => state.logout); // 👈 ログアウトアクションを取得
  const { signOut, signOutMutation } = useAuth();

  //const navigate = useNavigate();
  // isPending はログアウトフックが不要になれば、ここも不要
  //const [userId, setUserId] = useState<number | null>(null); // UserInfo.idはnumberであると仮定
  
  /* profileテーブルから取得出来る準備ができたら開放
  const { useGetProfile } = useProfile();
  const { data } = useGetProfile(userId); // ユーザーIDに基づいたプロフィール取得は維持
*/

  // ログアウトロジックの簡素化
  const signOutClick = async () => {
    try {
      await signOut(); // ← サーバー側のログアウトAPIを呼ぶ
      // navigate は useAuth の onSuccess で実行される
    } catch (error) {
      if (import.meta.env.DEV) {
        console.error('ログアウトエラー:', error);
      }
    }
  };

  // UIは認証状態に応じて表示を調整できます
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