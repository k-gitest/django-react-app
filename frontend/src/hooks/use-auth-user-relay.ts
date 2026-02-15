import { graphql } from 'react-relay';
import { useEffect, useState } from 'react';
import { useRelayEnvironment, fetchQuery } from 'react-relay';
import { useAuthStore } from './use-session-store';
import type { useAuthUserRelayQuery } from '@/__generated__/useAuthUserRelayQuery.graphql';

const MeQuery = graphql`
  query useAuthUserRelayQuery {
    me {
      __typename
      ... on UserType {
        id
        email
        firstName
        lastName
        isStaff
      }
    }
  }
`;

export const useAuthUserRelay = () => {
  const environment = useRelayEnvironment();
  const [isLoading, setIsLoading] = useState(true);
  
  // ZustandのStore
  const { user, isInitialized, setUser, setInitialized, logout } = useAuthStore();

  useEffect(() => {
    // 1. fetchQuery を使って命令的にデータを取得（Suspenseを起動させない）
    const disposable = fetchQuery<useAuthUserRelayQuery>(
      environment,
      MeQuery,
      {},
      { fetchPolicy: 'network-only' } // 認証チェックは常に最新を追いたい場合
    ).subscribe({
      next: (data) => {
        if (data?.me?.__typename === 'UserType') {
          const u = data.me;
          // 2. Zustand Storeを更新（既存のAuthFlowと同じ）
          setUser({
            id: parseInt(atob(String(u.id)).split(':')[1], 10),
            email: u.email,
            first_name: u.firstName,
            last_name: u.lastName,
            is_staff: u.isStaff,
          });
        } else {
          logout();
        }
      },
      error: (err: Error) => {
        console.error('Relay Auth Check Error:', err);
        logout();
        setInitialized(true);
        setIsLoading(false);
      },
      complete: () => {
        setInitialized(true);
        setIsLoading(false);
      }
    });

    return () => disposable.unsubscribe();
  }, [environment, setUser, setInitialized, logout]);

  // 3. 既存の useAuthUser と同じ形式を返す
  return {
    isLoading,
    user,
    isInitialized,
    // 必要なら error も追加
  };
};