'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from '@/components/dashboard/Sidebar';
import AuthGuard from '@/components/auth/AuthGuard';

const AUTH_ROUTES = ['/login', '/register', '/auth/callback', '/privacy'];

interface SidebarLayoutProps {
  children: React.ReactNode;
}

/**
 * App shell — left icon rail + glass-tile content over a compliance-themed
 * background. Name kept as SidebarLayout for backwards-compatible imports.
 */
export const SidebarLayout: React.FC<SidebarLayoutProps> = ({ children }) => {
  const pathname = usePathname();
  const isAuthPage = AUTH_ROUTES.some((route) => pathname?.startsWith(route));

  if (isAuthPage) {
    return <>{children}</>;
  }

  return (
    <AuthGuard>
      {/* Fixed compliance background sitting behind the whole shell */}
      <div className="app-backdrop" aria-hidden />

      <div className="app-shell">
        <Sidebar />
        <div className="app-content">{children}</div>
      </div>
    </AuthGuard>
  );
};
