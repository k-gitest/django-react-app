import { useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { useAuthStore } from './use-session-store';

export const useAuthUser = () => {
  const { user, isAuthenticated, isLoading } = useAuth0();
  const setUser = useAuthStore((state) => state.setUser);
  const setInitialized = useAuthStore((state) => state.setInitialized);

  useEffect(() => {
    if (!isLoading) {
      setInitialized(true);
      if (isAuthenticated && user) {
        setUser({
          id: user.sub!,
          email: user.email!,
          first_name: user.given_name || '',
          last_name: user.family_name || '',
        });
      } else {
        setUser(null);
      }
    }
  }, [isLoading, isAuthenticated, user, setUser, setInitialized]);

  return { isLoading };
};