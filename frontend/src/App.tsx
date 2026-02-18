import './App.css';
import { useEffect } from 'react';
import type { ReactNode } from 'react';
import { Router } from '@/routes/router';
import { queryClient, QueryClientProvider } from '@/lib/queryClient';
import { RelayEnvironmentProvider } from 'react-relay';
import { relayEnvironment } from '@/lib/relayEnvironment';
import { setAuth0TokenGetter } from './lib/authenticated-fetch';
import { useAuth0 } from '@auth0/auth0-react';
import { GlobalAsyncBoundary } from './components/async-boundary';

interface AppProps {
  children?: ReactNode;
}

export default function App({ children }: AppProps) {

  const { getAccessTokenSilently, isLoading } = useAuth0()

  useEffect(() => {
    if (!isLoading) {
      setAuth0TokenGetter(getAccessTokenSilently);
    }
  }, [getAccessTokenSilently, isLoading]);

  return (
    <QueryClientProvider client={queryClient}>
      <RelayEnvironmentProvider environment={relayEnvironment}>
        <GlobalAsyncBoundary>
          {children}
          <Router />
        </GlobalAsyncBoundary>
      </RelayEnvironmentProvider>
    </QueryClientProvider>
  );
}