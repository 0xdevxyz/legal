'use client';

export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'
export const runtime = 'nodejs'

import { useEffect, useState } from 'react'
import { DashboardHeader } from '@/components/dashboard/DashboardHeader'
import { DomainHeroSection } from '@/components/dashboard/DomainHeroSection'
import { WebsiteAnalysis } from '@/components/dashboard/WebsiteAnalysis'
import { LegalNews } from '@/components/dashboard/LegalNews'
import { CookieComplianceWidget } from '@/components/dashboard/CookieComplianceWidget'
import { PlanGuard } from '@/components/guards/PlanGuard'
import { OnboardingWizard } from '@/components/onboarding/OnboardingWizard'
// NEU: AI Compliance Card
import { AIComplianceCard } from '@/components/dashboard/AIComplianceCard'
// NEU: Kurzwahl-Leiste für gelockte Seiten
import { OptimizationQuickNav } from '@/components/dashboard/OptimizationQuickNav'
import { useAuth } from '@/contexts/AuthContext'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { AccessibilityWidget } from '@/components/accessibility/AccessibilityWidget'

export default function Page() {
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [isClient, setIsClient] = useState(false);
  const { user } = useAuth(); // NEU: User für AI Compliance Card

  useEffect(() => {
    setIsClient(true);
    const hasCompleted = localStorage.getItem('complyo_onboarding_completed');
    if (!hasCompleted) {
      setShowOnboarding(true);
    }
  }, []);

  if (!isClient) {
    return null; // Prevent hydration mismatch
  }

  if (showOnboarding) {
    return <OnboardingWizard onComplete={() => setShowOnboarding(false)} />;
  }

  return (
    <PlanGuard requiredPlan="ai">
      <ErrorBoundary componentName="Dashboard Page">
        {/* Accessibility Widget - lädt dynamisch basierend auf analysierter Website */}
        <AccessibilityWidget />
        
        {/* ✅ Kurzwahl-Leiste: Schneller Rückweg zur Optimierung wenn andere Seite analysiert wird */}
        <OptimizationQuickNav />
        
        <div className="min-h-screen">
          {/* Header */}
          <DashboardHeader />
          
          {/* Main Content Area - Semantisches HTML für Barrierefreiheit */}
          <main role="main" aria-label="Hauptinhalt">
            {/* Hero Section: Domain Input + Score + KI-CTA */}
            <section aria-label="Website-Analyse">
              <DomainHeroSection />
            </section>
            
            {/* Main Content Grid */}
            <section aria-label="Dashboard Übersicht" className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                {/* Left Column - AI Compliance Sidebar (schmaler) */}
                <aside className="lg:col-span-1" aria-label="AI Compliance Informationen">
                  <ErrorBoundary componentName="AIComplianceCard">
                    <AIComplianceCard user={user || undefined} />
                  </ErrorBoundary>
                </aside>
                
                {/* Right Column - Main Content */}
                <div className="lg:col-span-3 space-y-8">
                  {/* Website Compliance-Analyse */}
                  <section aria-label="Website Compliance-Analyse">
                    <ErrorBoundary componentName="WebsiteAnalysis">
                      <WebsiteAnalysis />
                    </ErrorBoundary>
                  </section>
                  
                  {/* Legal News */}
                  <section aria-label="Aktuelle Rechtsänderungen">
                    <ErrorBoundary componentName="LegalNews">
                      <LegalNews />
                    </ErrorBoundary>
                  </section>
                  
                  {/* Cookie-Compliance Management */}
                  <section aria-label="Cookie-Compliance Verwaltung">
                    <ErrorBoundary componentName="CookieComplianceWidget">
                      <CookieComplianceWidget />
                    </ErrorBoundary>
                  </section>
                </div>
              </div>
            </section>
          </main>
        </div>
      </ErrorBoundary>
    </PlanGuard>
  )
}
