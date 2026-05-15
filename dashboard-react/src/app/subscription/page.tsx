'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import {
  Shield, Eye, FileText, BarChart3, CreditCard, ExternalLink,
  Loader2, AlertCircle, CheckCircle, Zap, Star, Building2, X
} from 'lucide-react';
import { getAccessToken } from '@/lib/auth-helper';
import apiClient from '@/lib/api';

const PLAN_LABELS: Record<string, string> = {
  free: 'Kostenlos', single: 'Einzelne Säule', pro: 'Pro-Paket',
  agency: 'Agentur', expert: 'Expertenservice', update: 'Updateservice',
};

const MODULE_META: Record<string, { label: string; icon: React.ElementType }> = {
  cookie:        { label: 'Cookie & DSGVO',   icon: Shield },
  accessibility: { label: 'Barrierefreiheit', icon: Eye },
  legal_texts:   { label: 'Rechtliche Texte', icon: FileText },
  monitoring:    { label: 'Monitoring',        icon: BarChart3 },
};

const PLANS = [
  {
    id: 'single',
    name: 'Einzelne Säule',
    price: 19,
    period: 'Monat',
    description: 'Eine Compliance-Säule für Ihre Website',
    icon: Shield,
    color: 'blue',
    features: [
      '1 Compliance-Modul nach Wahl',
      'Unbegrenzte Scans',
      'KI-gestützte Fixes',
      'PDF-Export',
      'E-Mail Support',
    ],
  },
  {
    id: 'pro',
    name: 'Pro-Paket',
    price: 49,
    period: 'Monat',
    description: 'Alle 4 Säulen für vollständige Compliance',
    icon: Zap,
    color: 'orange',
    highlight: true,
    features: [
      'Alle 4 Compliance-Module',
      'Unbegrenzte KI-Fixes',
      'Schritt-für-Schritt Anleitungen',
      'Score-Verlauf & Reports',
      'eRecht24 Integration',
      'PDF/Excel Export',
      'Prioritäts-Support',
    ],
  },
  {
    id: 'agency',
    name: 'Agentur',
    price: 299,
    period: 'Monat',
    description: 'Für Agenturen mit mehreren Websites',
    icon: Building2,
    color: 'purple',
    features: [
      'Alle Pro-Features',
      'Bis zu 25 Websites',
      'Agentur-Dashboard',
      'White-Label Option',
      'Dedicated Account Manager',
      'SLA Garantie',
    ],
  },
];

interface SubStatus {
  has_subscription: boolean;
  plan: string;
  status: string;
  modules: { id: string; name: string }[];
}

export default function SubscriptionPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [sub, setSub] = useState<SubStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [portalLoading, setPortalLoading] = useState(false);
  const [upgradeLoading, setUpgradeLoading] = useState<string | null>(null);
  const [showPlans, setShowPlans] = useState(false);

  useEffect(() => {
    apiClient.get('/api/payment/subscription-status')
      .then(res => {
        setSub(res.data);
        if (!res.data.has_subscription) setShowPlans(true);
      })
      .catch((err) => {
        const msg = err.response?.data?.detail || 'Abonnement-Status konnte nicht geladen werden.';
        setError(msg);
      })
      .finally(() => setLoading(false));
  }, []);

  const handlePortal = async () => {
    setPortalLoading(true);
    try {
      const res = await apiClient.post('/api/stripe/create-portal-session', {
        return_url: `${window.location.origin}/subscription`,
      });
      if (res.data.portal_url) {
        window.location.href = res.data.portal_url;
      } else {
        setError('Stripe-Portal konnte nicht geöffnet werden.');
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Fehler beim Öffnen des Stripe-Portals.';
      setError(msg);
    } finally {
      setPortalLoading(false);
    }
  };

  const handleUpgrade = async (planId: string) => {
    setUpgradeLoading(planId);
    setError('');
    try {
      const res = await apiClient.post('/api/stripe/create-checkout', {
        plan: planId,
        billing_period: 'monthly',
        success_url: `${window.location.origin}/subscription?success=true`,
        cancel_url: `${window.location.origin}/subscription`,
      });
      if (res.data.checkout_url) {
        window.location.href = res.data.checkout_url;
      } else {
        setError(res.data.detail || 'Checkout konnte nicht gestartet werden.');
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Fehler beim Starten des Checkouts.';
      setError(msg);
    } finally {
      setUpgradeLoading(null);
    }
  };

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-zinc-950">
        <Loader2 className="w-8 h-8 animate-spin text-orange-400" />
      </main>
    );
  }

  const planLabel = PLAN_LABELS[sub?.plan ?? user?.plan_type ?? 'free'] ?? 'Unbekannt';
  const activeModuleIds = sub?.modules?.map(m => m.id) ?? user?.active_modules ?? [];
  const isFreePlan = !sub?.has_subscription || sub?.plan === 'free';

  const colorMap: Record<string, string> = {
    blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/40',
    orange: 'from-orange-500/20 to-orange-600/10 border-orange-500/60',
    purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/40',
  };
  const btnMap: Record<string, string> = {
    blue: 'bg-blue-600 hover:bg-blue-700',
    orange: 'bg-orange-500 hover:bg-orange-600',
    purple: 'bg-purple-600 hover:bg-purple-700',
  };

  return (
    <main role="main" aria-label="Abonnement-Verwaltung" className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-4xl mx-auto px-4 py-10">

        <div className="mb-8">
          <h1 className="text-2xl font-bold">Abo & Rechnung</h1>
          <p className="text-zinc-400 text-sm mt-1">Verwalten Sie Ihr Abonnement und Ihre Zahlungsmethoden.</p>
        </div>

        {error && (
          <div className="mb-6 flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}

        {/* Current Plan Card */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 mb-6">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <p className="text-xs uppercase tracking-widest text-zinc-500 mb-1">Ihr aktueller Plan</p>
              <h2 className="text-xl font-bold text-white">{planLabel}</h2>
            </div>
            <div className="flex items-center gap-3 flex-wrap">
              {sub?.has_subscription && (
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  sub.status === 'active' ? 'bg-green-900/60 text-green-300 border border-green-700' :
                  sub.status === 'trialing' ? 'bg-blue-900/60 text-blue-300 border border-blue-700' :
                  'bg-red-900/60 text-red-300 border border-red-700'
                }`}>
                  {sub.status === 'active' ? 'Aktiv' :
                   sub.status === 'trialing' ? 'Testphase' :
                   sub.status === 'past_due' ? 'Zahlung ausstehend' : sub.status}
                </span>
              )}
              {isFreePlan && (
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-zinc-800 text-zinc-400 border border-zinc-700">
                  Kostenlos
                </span>
              )}
            </div>
          </div>

          {/* Active Modules */}
          {!isFreePlan && (
            <div className="mt-5">
              <p className="text-xs text-zinc-500 uppercase tracking-wider mb-3">Aktive Module</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {Object.entries(MODULE_META).map(([id, { label, icon: Icon }]) => {
                  const active = activeModuleIds.includes(id);
                  return (
                    <div key={id} className={`flex items-center gap-2 p-3 rounded-lg border text-sm ${
                      active
                        ? 'border-green-700/50 bg-green-900/10 text-green-300'
                        : 'border-zinc-800 text-zinc-600'
                    }`}>
                      <Icon className="w-4 h-4 shrink-0" />
                      <span className="text-xs">{label}</span>
                      {active && <CheckCircle className="w-3 h-3 ml-auto shrink-0" />}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="mt-6 flex flex-wrap gap-3">
            {sub?.has_subscription ? (
              <>
                <button
                  onClick={handlePortal}
                  disabled={portalLoading}
                  className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed px-4 py-2.5 rounded-lg text-sm font-medium transition-colors border border-zinc-700"
                >
                  {portalLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CreditCard className="w-4 h-4" />}
                  Zahlung & Rechnungen
                  <ExternalLink className="w-3.5 h-3.5 opacity-50" />
                </button>
                <button
                  onClick={() => setShowPlans(s => !s)}
                  className="flex items-center gap-2 bg-orange-500 hover:bg-orange-600 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors"
                >
                  <Zap className="w-4 h-4" />
                  Plan upgraden
                </button>
              </>
            ) : (
              <button
                onClick={() => setShowPlans(true)}
                className="flex items-center gap-2 bg-orange-500 hover:bg-orange-600 px-5 py-2.5 rounded-lg text-sm font-bold transition-colors"
              >
                <Zap className="w-4 h-4" />
                Plan auswählen & upgraden
              </button>
            )}
          </div>
        </div>

        {/* Plan Selection */}
        {showPlans && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Pläne vergleichen</h2>
              {sub?.has_subscription && (
                <button onClick={() => setShowPlans(false)} className="text-zinc-500 hover:text-zinc-300">
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {PLANS.map(plan => {
                const isCurrentPlan = (sub?.plan ?? user?.plan_type ?? 'free') === plan.id;
                const Icon = plan.icon;
                return (
                  <div key={plan.id} className={`relative rounded-xl border bg-gradient-to-br p-5 flex flex-col ${colorMap[plan.color]}`}>
                    {plan.highlight && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                        <span className="bg-orange-500 text-white text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1">
                          <Star className="w-3 h-3" /> Beliebteste
                        </span>
                      </div>
                    )}

                    <div className="mb-4">
                      <Icon className={`w-7 h-7 mb-3 ${
                        plan.color === 'orange' ? 'text-orange-400' :
                        plan.color === 'blue' ? 'text-blue-400' : 'text-purple-400'
                      }`} />
                      <h3 className="font-bold text-white text-base">{plan.name}</h3>
                      <p className="text-zinc-400 text-xs mt-0.5">{plan.description}</p>
                    </div>

                    <div className="mb-5">
                      <span className="text-3xl font-bold text-white">{plan.price}€</span>
                      <span className="text-zinc-400 text-sm">/{plan.period}</span>
                    </div>

                    <ul className="space-y-2 mb-6 flex-1">
                      {plan.features.map(f => (
                        <li key={f} className="flex items-start gap-2 text-sm text-zinc-300">
                          <CheckCircle className="w-4 h-4 text-green-400 shrink-0 mt-0.5" />
                          {f}
                        </li>
                      ))}
                    </ul>

                    <button
                      onClick={() => !isCurrentPlan && handleUpgrade(plan.id)}
                      disabled={isCurrentPlan || upgradeLoading === plan.id}
                      className={`w-full py-2.5 rounded-lg text-sm font-semibold transition-colors flex items-center justify-center gap-2 ${
                        isCurrentPlan
                          ? 'bg-zinc-700 text-zinc-400 cursor-default'
                          : `${btnMap[plan.color]} text-white`
                      } disabled:opacity-60`}
                    >
                      {upgradeLoading === plan.id
                        ? <Loader2 className="w-4 h-4 animate-spin" />
                        : isCurrentPlan
                        ? <><CheckCircle className="w-4 h-4" /> Aktueller Plan</>
                        : <><Zap className="w-4 h-4" /> Jetzt upgraden</>
                      }
                    </button>
                  </div>
                );
              })}
            </div>

            <p className="text-center text-xs text-zinc-600 mt-2">
              Alle Pläne beinhalten eine 14-Tage Kündigungsfrist · Zahlung via Stripe · SSL-verschlüsselt
            </p>
          </div>
        )}

        <button
          onClick={() => router.push('/')}
          className="mt-8 text-zinc-500 hover:text-zinc-300 text-sm transition-colors"
        >
          ← Zurück zum Dashboard
        </button>
      </div>
    </main>
  );
}
