import './App.css';
import type { ReactNode } from 'react';
import { Router } from '@/routes/router';
import { queryClient, QueryClientProvider } from '@/lib/queryClient';
import { RelayEnvironmentProvider } from 'react-relay';
import { relayEnvironment } from '@/lib/relayEnvironment';
import { GlobalAsyncBoundary } from './components/async-boundary';

interface AppProps {
  children?: ReactNode;
}

export default function App({ children }: AppProps) {
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