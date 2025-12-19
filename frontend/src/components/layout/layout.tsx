import type { ReactNode } from 'react';
import { MainWrapper } from '@/components/layout/main-wrapper';
import { Header } from '@/components/layout/header';
import { Footer } from '@/components/layout/footer';
import { Toaster } from '@/components/ui/sonner';

export const Layout = ({ children }: { children: ReactNode }) => {
  return (
    <>
      <Header />
      <MainWrapper>{children}</MainWrapper>
      <Footer />
      <Toaster />
    </>
  );
};
