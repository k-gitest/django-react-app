import { useAuth0 } from '@auth0/auth0-react';
import { useAuthStore } from '@/hooks/use-session-store';
import { useNavigate } from 'react-router-dom';
import { queryClient } from '@/lib/queryClient';

/**
 * 認証フック（Auth0統合版）
 * 
 * Django認証時代のインターフェースを維持しつつ、
 * 内部実装をAuth0に切り替え
 */
export const useAuth = () => {
  const { loginWithRedirect, logout: auth0Logout, isAuthenticated, isLoading } = useAuth0();
  const user = useAuthStore((state) => state.user);
  const zustandLogout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();

  // ログイン（Auth0リダイレクト）
  const signIn = async (returnTo?: string) => {
    try {
      await loginWithRedirect({
        appState: { returnTo: returnTo || '/dashboard' },
      });
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  // サインアップ（Auth0リダイレクト）
  const signUp = async (returnTo?: string) => {
    try {
      await loginWithRedirect({
        authorizationParams: {
          screen_hint: 'signup',  // サインアップ画面を表示
        },
        appState: { returnTo: returnTo || '/dashboard' },
      });
    } catch (error) {
      console.error('Signup failed:', error);
      throw error;
    }
  };

  // ログアウト
  const signOut = async () => {
    try {
      // 1. Zustandクリア
      zustandLogout();
      
      // 2. クエリキャッシュクリア
      queryClient.clear();
      
      // 3. Auth0ログアウト
      auth0Logout({
        logoutParams: {
          returnTo: window.location.origin,
        },
      });
    } catch (error) {
      console.error('Logout failed:', error);
      
      // ログアウト失敗してもクライアント側はクリア
      zustandLogout();
      navigate('/login');
    }
  };

  return {
    // メソッド（既存インターフェース維持）
    signIn,
    signUp,
    signOut,

    // 状態
    user,
    isAuthenticated,
    isLoading,

    // Mutation互換（既存コードとの互換性）
    signInMutation: {
      isPending: isLoading,
      isError: false,
      error: null,
    },
    signUpMutation: {
      isPending: isLoading,
      isError: false,
      error: null,
    },
    signOutMutation: {
      isPending: false,
      isError: false,
      error: null,
    },
  };
};