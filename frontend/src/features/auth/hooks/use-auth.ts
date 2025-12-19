// hooks/use-auth.ts
import { ApiError } from '@/errors/api-error';
import {
  loginService,
  logoutService,
  signupService,
} from '@/features/auth/services/auth-service';
import type { Account, TokenResponse } from '@/features/auth/types/auth';
import { useAuthStore } from '@/hooks/use-session-store';
import { useApiMutation } from '@/hooks/use-tanstack-query';
import { useNavigate } from 'react-router-dom';
import { queryClient } from '@/lib/queryClient';

/**
 * 認証関連の操作を提供するカスタムフック
 * 
 * 【改善ポイント】
 * - 個別の try-catch を削除
 * - エラーハンドリングは errorHandler に集約
 * - onError では状態更新のみ実行
 */
export const useAuth = () => {
  const navigate = useNavigate();
  const { logout } = useAuthStore();

  // 成功時の型
  type SuccessType = TokenResponse;
  // エラー時の型
  type ErrorType = Error | ApiError;

  // --- 1. サインアップ用 ---
  const signUpMutation = useApiMutation<SuccessType, ErrorType, { data: Account }>({
    mutationFn: ({ data }) => signupService(data),
    onSuccess: async () => {
      // サインアップ成功後、ユーザー情報を取得
      // ※ signupService が既にuser情報を返している場合は
      //    response.user を直接使用することも可能
      await queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      navigate('/dashboard');
    },
    onError: (err) => {
      // エラーは既に errorHandler で処理済み
      // 個別の処理が必要な場合のみここに記述
      
      // 例: 特定のエラーコードで追加処理
      if (err instanceof ApiError && err.status === 400) {
        // バリデーションエラーの場合の追加処理
        // フィールドエラーの表示などはフォームコンポーネントで処理
      }
    },
  });

  // --- 2. サインイン用 ---
  const signInMutation = useApiMutation<SuccessType, ErrorType, { data: Account }>({
    mutationFn: ({ data }) => loginService(data),
    onSuccess: async (data) => {
      // 単純に以下のinvalidateだと結構待つので先にレスポンスからユーザー情報をセットする
      // await queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });

      // 1. ログインAPIのレスポンス(data)に含まれるユーザー情報を即座にStoreにセット
      // これにより、AuthGuardが「userがいる」と即座に判断できるようになります
      if(data.user){
        useAuthStore.getState().setUser(data.user); 
        // 2. キャッシュも手動で更新（これによりinvalidateの再取得待ちを防ぐ）
        queryClient.setQueryData(['auth', 'me'], data.user);
      }
      // userの有無に関わらず、ログイン処理自体は成功しているので
      // 初期化完了フラグを立ててガードを通す
      useAuthStore.getState().setInitialized(true);

      // 3. 裏側で念のため無効化はしておく（awaitしない）
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      
      navigate('/dashboard');
    },
    onError: (err) => {
      // エラーは既に errorHandler で処理済み
      // 個別の処理が必要な場合のみここに記述
      
      if (err instanceof ApiError && err.status === 401) {
        // 認証失敗時の追加処理（既にトーストは表示済み）
        // 例: ログイン試行回数をカウントするなど
      }
    },
  });

  // --- 3. サインアウト用 ---
  const signOutMutation = useApiMutation<void, ErrorType>({
    mutationFn: logoutService,
    onSuccess: () => {
      // ログアウト成功時
      queryClient.clear();
      logout();
      navigate('/login');
    },
    onError: (err) => {
      // エラーは既に errorHandler で処理済み
      
      // ログアウトAPIが失敗しても、クライアント側の状態は削除する
      // （サーバー側のトークン無効化は失敗したが、ユーザー体験を優先）
      logout();
      navigate('/login');
      
      // エラーログ（開発環境のみ）
      if (import.meta.env.DEV) {
        console.warn('ログアウトAPIは失敗しましたが、クライアント側の状態をクリアしました:', err);
      }
    },
  });

  // --- 各メソッド実装 ---
  const signUp = async (data: Account) => {
    return signUpMutation.mutateAsync({ data });
  };

  const signIn = async (data: Account) => {
    return signInMutation.mutateAsync({ data });
  };

  const signOut = async () => {
    return signOutMutation.mutateAsync();
  };

  return {
    // メソッド
    signUp,
    signIn,
    signOut,
    
    // Mutation オブジェクト（ローディング状態などを取得する場合）
    signUpMutation,
    signInMutation,
    signOutMutation,
  };
};