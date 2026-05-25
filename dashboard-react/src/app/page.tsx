'use client';

export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'
export const runtime = 'nodejs'

import { useEffect, useState } from 'react'
import { WebsiteAnalysis } from '@/components/dashboard/WebsiteAnalysis'
import { LegalNews } from '@/components/dashboard/LegalNews'
import { CookieComplianceWidget } from '@/components/dashboard/CookieComplianceWidget'
import { OnboardingWizard } from '@/components/onboarding/OnboardingWizard'
import { OptimizationQuickNav } from '@/components/dashboard/OptimizationQuickNav'
import { useAuth } from '@/contexts/AuthContext'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { AccessibilityWidget } from '@/components/accessibility/AccessibilityWidget'
import { ComplianceGauge } from '@/components/dashboard/ComplianceGauge'
import { ComplianceFlowWidget } from '@/components/dashboard/ComplianceFlowWidget'
import { MetricsCards } from '@/components/dashboard/MetricsCards'
import { DomainHeroSection } from '@/components/dashboard/DomainHeroSection'
import { AIComplianceCard } from '@/components/dashboard/AIComplianceCard'
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

          {/* Row 1: Domain input */}
          <section aria-label="Website-Analyse">
            <ErrorBoundary componentName="DomainHeroSection">
              <DomainHeroSection />
            </ErrorBoundary>
          </section>

          {/* Row 2: Compliance-Analyse (links) + Score & AI-Upgrade (rechts) */}
          <section aria-label="Compliance-Analyse" className="grid grid-cols-1 xl:grid-cols-3 gap-5">
            <div className="xl:col-span-2">
              <ErrorBoundary componentName="WebsiteAnalysis">
                <WebsiteAnalysis />
              </ErrorBoundary>
            </div>
            <div className="xl:col-span-1 flex flex-col gap-5">
              <ErrorBoundary componentName="ComplianceGauge">
                <ComplianceGauge
                  userName={user?.full_name || user?.email}
                  scoreTrend={scoreTrend}
                />
              </ErrorBoundary>
              <ErrorBoundary componentName="AIComplianceCard">
                <AIComplianceCard user={user || undefined} />
              </ErrorBoundary>
            </div>
          </section>

          {/* Row 2b: Metrics Cards (full width) */}
          <section aria-label="Metriken">
            <ErrorBoundary componentName="MetricsCards">
              <MetricsCards />
            </ErrorBoundary>
          </section>

          {/* Row 3: Compliance Flow Widget */}
          <section aria-label="Compliance Flow">
            <ErrorBoundary componentName="ComplianceFlowWidget">
              <ComplianceFlowWidget />
            </ErrorBoundary>
          </section>

          {/* Row 4: Legal News */}
          <section aria-label="Legal News">
            <ErrorBoundary componentName="LegalNews">
              <LegalNews />
            </ErrorBoundary>
          </section>

          {/* Row 5: Cookie Compliance */}
          <section aria-label="Cookie Compliance">
            <ErrorBoundary componentName="CookieComplianceWidget">
              <CookieComplianceWidget />
            </ErrorBoundary>
          </section>

        </main>
      </ErrorBoundary>
  );
}
