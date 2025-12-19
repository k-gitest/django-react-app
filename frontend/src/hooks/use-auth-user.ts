import { useApiQuery } from '@/hooks/use-tanstack-query';
import { fetchMe } from '@/features/auth/services/auth-service';
import { useAuthStore } from './use-session-store';

export const useAuthUser = () => {
  const setUser = useAuthStore((state) => state.setUser);
  const setInitialized = useAuthStore((state) => state.setInitialized);

  return useApiQuery(
    {
      queryKey: ['auth', 'me'],
      queryFn: fetchMe,
      // 認証チェックはリロード時やフォーカス時に自動で行いたいので
      // staleTime や retry の設定を調整します
      staleTime: Infinity, // ユーザー情報は頻繁に変わらないため
      retry: false,        // 401エラー時に何度もリトライさせない
    },
    {
      onSuccess: (data) => {
        setUser(data);
      },
      onError: () => {
        useAuthStore.getState().logout(); // 失敗時はクリア
      },
      onSettled: () => {
        setInitialized(true);
      },
    }
  );
};