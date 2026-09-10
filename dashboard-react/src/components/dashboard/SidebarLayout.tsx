'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from '@/components/dashboard/Sidebar';
import AuthGuard from '@/components/auth/AuthGuard';
import VertragsGate from '@/components/auth/VertragsGate';
import { istOhneRahmen } from '@/lib/oeffentliche-pfade';

interface SidebarLayoutProps {
  children: React.ReactNode;
}

/**
 * App shell — left icon rail + glass-tile content over a compliance-themed
 * background. Name kept as SidebarLayout for backwards-compatible imports.
 */
export const SidebarLayout: React.FC<SidebarLayoutProps> = ({ children }) => {
  const pathname = usePathname();
  // Liste in lib/oeffentliche-pfade — sie stand hier als dritte Kopie.
  const isAuthPage = istOhneRahmen(pathname ?? '');

  if (isAuthPage) {
    return <>{children}</>;
  }

  return (
    <AuthGuard>
      {/* Bestandskonten ohne AVV-Zustimmung werden hier angehalten, bis sie
          zugestimmt haben. Innerhalb der Anmeldewache, damit oeffentliche
          Seiten nichts davon sehen. */}
      <VertragsGate>
        {/* Fixed compliance background sitting behind the whole shell */}
        <div className="app-backdrop" aria-hidden />

        <div className="app-shell">
          <Sidebar />
          <div className="app-content">{children}</div>
        </div>
      </VertragsGate>
    </AuthGuard>
  );
};
