import { createBrowserRouter, RouterProvider, createRoutesFromElements, Route, Outlet } from 'react-router-dom';
import { Layout } from '@/components/layout/layout';
import { AuthLayout } from '@/components/layout/auth/auth-layout';
import Home from '@/pages/HomePage';
import About from '@/pages/AboutPage';
import Register from '@/pages/RegisterPage';
import Login from '@/pages/LoginPage';
import Auth from '@/pages/Auth';
import Dashboard from '@/pages/Dashboard';
import NotFound from '@/pages/Not-Found';
import { AuthGuard } from '@/routes/auth-guard';
import { GuestGuard } from '@/routes/guest-guard';
import { PageAsyncBoundary } from '@/components/async-boundary';

const LayoutWrapper = () => {
  return (
    <Layout>
      <PageAsyncBoundary>
        <Outlet />
      </PageAsyncBoundary>
    </Layout>
  );
};

const AuthLayoutWrapper = () => {
  return (
    <AuthLayout>
      <PageAsyncBoundary>
        <Outlet />
      </PageAsyncBoundary>
    </AuthLayout>
  );
};

/* pages内コンポーネントを非同期のlazyとする場合
import { LazyPages } from './lazy-pages';
// 使い方
<Route path="/" element={<LazyPages.Home />} />
<Route path="/about" element={<LazyPages.About />} />
*/

const router = createBrowserRouter(
  createRoutesFromElements(
    <>
      <Route element={<LayoutWrapper />}>
        {/* Public routes */}
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />

        {/* new password redirect routes */}
        <Route path="/pass" element={<Auth />} />

        {/* Guest routes with GuestGuard */}
        <Route element={<GuestGuard />}>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Route>

        {/* Not found route */}
        <Route path="*" element={<NotFound />} />
      </Route>
      <Route element={<AuthLayoutWrapper />}>
        {/* Protected routes */}
        <Route element={<AuthGuard />}>
          <Route path="/dashboard" element={<Dashboard />} />
        </Route>
      </Route>
    </>,
  ),
);

export const Router = () => {
  return <RouterProvider router={router} />;
};
