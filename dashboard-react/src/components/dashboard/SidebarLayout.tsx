'use client';

import React, { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from '@/components/dashboard/Sidebar';
import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import AuthGuard from '@/components/auth/AuthGuard';

const AUTH_ROUTES = ['/login', '/register', '/auth/callback', '/privacy'];

interface SidebarLayoutProps {
  children: React.ReactNode;
}

export const SidebarLayout: React.FC<SidebarLayoutProps> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);
  const pathname = usePathname();

  useEffect(() => { setMounted(true); }, []);

  const isAuthPage = AUTH_ROUTES.some(route => pathname?.startsWith(route));

  if (isAuthPage) {
    return <>{children}</>;
  }

  const sidebarWidth = collapsed ? 72 : 256;
  const topbarHeight = 64;

  return (
    <AuthGuard>
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <div style={{ width: sidebarWidth, flexShrink: 0, transition: 'width 0.25s cubic-bezier(0.4,0,0.2,1)' }}>
          <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />
        </div>

        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
          <div style={{ height: topbarHeight, flexShrink: 0, position: 'sticky', top: 0, zIndex: 39 }}>
            <DashboardHeader sidebarCollapsed={collapsed} />
          </div>

          <div style={{ flex: 1 }}>
            {children}
          </div>
        </div>
      </div>
    </AuthGuard>
  );
};
