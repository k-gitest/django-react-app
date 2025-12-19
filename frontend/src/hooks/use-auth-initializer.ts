import { fetchMe } from '@/features/auth/services/auth-service';
import { useEffect } from 'react';
import { useAuthStore } from './use-session-store';

/**
 * アプリ起動時に認証状態を初期化するフック
 * Cookieベースの認証なので、サーバーにユーザー情報を問い合わせる
 */
export const useAuthInitializer = () => {
  const { setUser, logout, setInitialized, isInitialized } = useAuthStore();

  useEffect(() => {
    // 既に初期化済みの場合はスキップ
    if (isInitialized) {
      return;
    }

    const fetchUserData = async () => {
      try {
        // Cookieが有効であればユーザー情報を取得できる
        const fetchedUser = await fetchMe();
        setUser(fetchedUser);
      } catch (error) {
        if(import.meta.env.DEV){
          // 認証エラー（Cookieが無効または期限切れ）
          console.log('認証が必要です', error);
        }
        logout();
      } finally {
        // 成功・失敗に関わらず初期化完了
        setInitialized(true);
      }
    };

    fetchUserData();
  }, [isInitialized, setUser, logout, setInitialized]);
  // ⚠️ userは依存配列に入れない（無限ループ防止）
};