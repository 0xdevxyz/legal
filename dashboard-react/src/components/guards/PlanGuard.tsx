'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Shield, Sparkles, Crown } from 'lucide-react';

interface PlanGuardProps {
  children: React.ReactNode;
  requiredPlan?: 'ai' | 'expert';
  fallback?: React.ReactNode;
}

export const PlanGuard: React.FC<PlanGuardProps> = ({ 
  children, 
  requiredPlan = 'ai',
  fallback 
}) => {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  // Zeige Loading State
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // User nicht eingeloggt
  if (!user) {
    if (typeof window !== 'undefined') {
      router.push('/login');
    }
    return null;
  }

  // Prüfe Plan-Zugriff
  const userPlan = user.plan_type || 'free';
  
  const planHierarchy: Record<string, number> = {
    'free': 0,
    'ai': 1,
    'expert': 2
  };

  const hasAccess = planHierarchy[userPlan] >= planHierarchy[requiredPlan];
  
  // Free-User haben Zugriff, aber mit Limits (1 Fix gratis)
  const isFreeUser = userPlan === 'free';

  // Free-User: Zeige Freemium-Hinweis (kein Hard-Block!)
  // Sie bekommen 1 Fix gratis, dann Paywall im ComplianceIssueCard
  
  // Kein Zugriff - zeige Upgrade-Screen (nur für AI/Expert erforderlich)
  if (!hasAccess && !isFreeUser) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center p-4">
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-2xl p-8">
          <div className="text-center">
            {requiredPlan === 'ai' && (
              <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-100 rounded-full mb-6">
                <Sparkles className="w-10 h-10 text-blue-600" />
              </div>
            )}
            {requiredPlan === 'expert' && (
              <div className="inline-flex items-center justify-center w-20 h-20 bg-purple-100 rounded-full mb-6">
                <Crown className="w-10 h-10 text-purple-600" />
              </div>
            )}
            
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              {requiredPlan === 'ai' ? 'AI Plan erforderlich' : 'Expert Plan erforderlich'}
            </h1>
            
            <p className="text-lg text-gray-600 mb-8">
              Diese Funktion ist nur für {requiredPlan === 'ai' ? 'AI' : 'Expert'}-Plan Nutzer verfügbar.
            </p>

            <div className="bg-blue-50 rounded-lg p-6 mb-8">
              <h3 className="font-semibold text-gray-900 mb-3">Was Sie mit dem {requiredPlan === 'ai' ? 'AI' : 'Expert'} Plan erhalten:</h3>
              <ul className="text-left space-y-2 text-gray-700">
                {requiredPlan === 'ai' && (
                  <>
                    <li className="flex items-start gap-2">
                      <span className="text-green-600 mt-1">✓</span>
                      <span>KI-gestützte Compliance-Analysen</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-600 mt-1">✓</span>
                      <span>Unbegrenzte KI-Fix-Generierung</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-600 mt-1">✓</span>
                      <span>Code-Snippets für Ihre Website</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-600 mt-1">✓</span>
                      <span>Schritt-für-Schritt Anleitungen</span>
                    </li>
                  </>
                )}
                {requiredPlan === 'expert' && (
                  <>
                    <li className="flex items-start gap-2">
                      <span className="text-green-600 mt-1">✓</span>
                      <span>Unbegrenzte Website-Analysen</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-600 mt-1">✓</span>
                      <span>Unbegrenzte KI-Fixes</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-600 mt-1">✓</span>
                      <span>Vollständige Dokument-Generierung</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-600 mt-1">✓</span>
                      <span>Prioritäts-Support</span>
                    </li>
                  </>
                )}
              </ul>
            </div>

            <div className="flex gap-4 justify-center">
              <button
                onClick={() => router.push('/ai-compliance/upgrade')}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-3 rounded-lg font-semibold transition-all shadow-lg hover:shadow-xl"
              >
                Jetzt upgraden
              </button>
              <button
                onClick={() => {
                  if (typeof window !== 'undefined' && window.history.length > 1) {
                    window.history.back();
                  } else {
                    router.push('/');
                  }
                }}
                className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-8 py-3 rounded-lg font-semibold transition-all"
              >
                Zurück
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // User hat Zugriff
  return <>{children}</>;
};

// Export auch einen Hook für programmatische Checks
export const usePlanAccess = () => {
  const { user } = useAuth();
  
  const checkAccess = (requiredPlan: 'ai' | 'expert' = 'ai'): boolean => {
    if (!user) return false;
    
    const userPlan = user.plan_type || 'free';
    const planHierarchy: Record<string, number> = {
      'free': 0,
      'ai': 1,
      'expert': 2
    };
    
    return planHierarchy[userPlan] >= planHierarchy[requiredPlan];
  };

  return {
    hasAIAccess: checkAccess('ai'),
    hasExpertAccess: checkAccess('expert'),
    checkAccess
  };
};

