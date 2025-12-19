import type { ReactNode } from 'react';
import { Router } from '@/routes/router';
import './App.css';
import { queryClient, QueryClientProvider } from '@/lib/queryClient';

interface AppProps {
  children?: ReactNode;
}

export default function App({ children }: AppProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <Router />
    </QueryClientProvider>
  );
}