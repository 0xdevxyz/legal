'use client';

import React, { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useComploaiGuard } from '@/hooks/useComploaiGuard';

/**
 * Hard frontend guard for the AI-Compliance feature.
 *
 * Wraps everything under /ai-compliance. Users without an active
 * `comploai_guard` add-on are redirected to the upsell page instead of
 * relying solely on the backend returning 403. The /ai-compliance/upgrade
 * route is excluded so the upsell itself stays reachable.
 */
export function ComploaiGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { hasComploaiGuard, isLoading } = useComploaiGuard();

  const isUpgradeRoute = pathname?.startsWith('/ai-compliance/upgrade');

  useEffect(() => {
    if (isUpgradeRoute) return;
    if (!isLoading && !hasComploaiGuard) {
      router.replace('/ai-compliance/upgrade');
    }
  }, [isUpgradeRoute, isLoading, hasComploaiGuard, router]);

  // The upsell page is always reachable.
  if (isUpgradeRoute) return <>{children}</>;

  // While resolving access — or while redirecting a user without the add-on —
  // show a spinner rather than flashing the gated content.
  if (isLoading || !hasComploaiGuard) {
    return (
      <div className="flex items-center justify-center min-h-screen dark:bg-zinc-900 bg-white">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[color:var(--lime)]" />
      </div>
    );
  }

  return <>{children}</>;
}
