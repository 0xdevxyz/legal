'use client';

export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'
export const runtime = 'nodejs'

import { useEffect, useState } from 'react'
import { OnboardingWizard } from '@/components/onboarding/OnboardingWizard'
import { OptimizationQuickNav } from '@/components/dashboard/OptimizationQuickNav'
import { useAuth } from '@/contexts/AuthContext'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { AccessibilityWidget } from '@/components/accessibility/AccessibilityWidget'
import { Orientierungsband } from '@/components/dashboard/Orientierungsband'
import { DashboardRaster } from '@/components/dashboard/anordnen/DashboardRaster'
import { useDashboardMetrics } from '@/hooks/useMetrics'

export default function Page() {
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [isClient, setIsClient] = useState(false);
  const { user, isLoading } = useAuth();
  const { metrics: apiMetrics } = useDashboardMetrics();

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (!isClient) return;
    if (isLoading) return;

    if (user?.onboarding_completed) {
      localStorage.setItem('complyo_onboarding_completed', 'true');
      setShowOnboarding(false);
      return;
    }

    const hasCompleted = localStorage.getItem('complyo_onboarding_completed');
    if (!hasCompleted) {
      setShowOnboarding(true);
    } else {
      setShowOnboarding(false);
    }
  }, [user, isLoading, isClient]);

  if (!isClient || isLoading) return null;

  if (showOnboarding) {
    return <OnboardingWizard onComplete={() => setShowOnboarding(false)} />;
  }

  const scoreTrend = apiMetrics?.scoreTrend ?? null;

  return (
    <ErrorBoundary componentName="Dashboard Page">
        <AccessibilityWidget />
        <OptimizationQuickNav />

        <main role="main" aria-label="Hauptinhalt" className="px-4 sm:px-6 py-6 space-y-6 max-w-[1600px] mx-auto">

          {/* Orientierung zuerst: wo stehe ich, was ist passiert, was ist der
              nächste Schritt. Steht bei JEDEM Besuch da — nicht nur beim ersten. */}
          <ErrorBoundary componentName="Orientierungsband">
            <Orientierungsband />
          </ErrorBoundary>

          {/* Alle weiteren Module sind frei anordenbar (zwei Spalten, Ziehen
              oder Pfeile, je Nutzer im Browser gespeichert). Der Katalog steht
              in components/dashboard/anordnen/modulkatalog.tsx. */}
          <DashboardRaster
            userId={user?.id}
            kontext={{ userName: user?.full_name || user?.email, planType: user?.plan_type, scoreTrend }}
          />

        </main>
      </ErrorBoundary>
  );
}
