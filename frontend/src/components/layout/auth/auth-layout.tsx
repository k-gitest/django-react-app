import type { ReactNode } from 'react';
import { AuthMainWrapper } from '@/components/layout/auth/auth-main-wrapper';
import { AuthHeader } from '@/components/layout/auth/auth-header';
import { Toaster } from '@/components/ui/sonner';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

export const AuthLayout = ({ children }: { children: ReactNode }) => {
  return (
    <>
      <AuthHeader />
      <nav className="flex justify-center gap-2">
        <Button variant="ghost" asChild>
          <Link to="/dashboard">Home</Link>
        </Button>
        <Button variant="ghost" asChild>
          <Link to="/todo">Todo</Link>
        </Button>
      </nav>
      <AuthMainWrapper>{children}</AuthMainWrapper>
      <Toaster />
    </>
  );
};
