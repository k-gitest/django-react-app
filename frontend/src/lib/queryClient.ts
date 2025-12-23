import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// ブラウザの window オブジェクトにフラグがあるか確認
const isE2E = typeof window !== 'undefined' && window.__IS_E2E_TESTING__ === true;

const queryClient = new QueryClient({
  //グローバルオプション設定
  defaultOptions: {
    queries: {
      retry: isE2E ? 0 : 3,
      //retryDelay: isE2E ? 0 : (attempt) => Math.min(1000 * 2 ** attempt, 30000),
    },
  },
});

export { queryClient, QueryClientProvider };
