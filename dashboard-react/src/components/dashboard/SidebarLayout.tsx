'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { TopNav } from '@/components/dashboard/TopNav';
import AuthGuard from '@/components/auth/AuthGuard';

const AUTH_ROUTES = ['/login', '/register', '/auth/callback', '/privacy'];

interface SidebarLayoutProps {
  children: React.ReactNode;
}

/**
 * App shell — ORION-style top navigation (no sidebar).
 * Name kept as SidebarLayout for backwards-compatible imports.
 */
export const SidebarLayout: React.FC<SidebarLayoutProps> = ({ children }) => {
  const pathname = usePathname();
  const isAuthPage = AUTH_ROUTES.some((route) => pathname?.startsWith(route));

  if (isAuthPage) {
    return <>{children}</>;
  }

  return (
    <AuthGuard>
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <div style={{ position: 'sticky', top: 0, zIndex: 40, flexShrink: 0 }}>
          <TopNav />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>{children}</div>
      </div>
    </AuthGuard>
  );
};
