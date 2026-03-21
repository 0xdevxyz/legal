'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { Shield, Eye, FileText, BarChart3, CreditCard, ExternalLink, Loader2, AlertCircle, CheckCircle } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

const MODULE_META: Record<string, { label: string; Icon: React.FC<{ className?: string }> }> = {
  cookie:        { label: 'Cookie & DSGVO',   Icon: ({ className }) => <Shield className={className} /> },
  accessibility: { label: 'Barrierefreiheit', Icon: ({ className }) => <Eye className={className} /> },
  legal_texts:   { label: 'Rechtliche Texte', Icon: ({ className }) => <FileText className={className} /> },
  monitoring:    { label: 'Monitoring',        Icon: ({ className }) => <BarChart3 className={className} /> },
};

const PLAN_LABELS: Record<string, string> = {
  free:     'Kostenlos',
  single:   'Einzelmodul',
  complete: 'Komplett-Paket',
  expert:   'Experten-Service',
  agency:   'Agentur',
  ai:       'KI-Automatisierung',
};

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

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) { router.push('/login'); return; }

    fetch(`${API_BASE}/api/payment/subscription-status`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(data => setSub(data))
      .catch(() => setError('Abonnement-Status konnte nicht geladen werden.'))
      .finally(() => setLoading(false));
  }, [router]);

  const handlePortal = async () => {
    setPortalLoading(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API_BASE}/api/stripe/create-portal-session`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (data.portal_url) window.location.href = data.portal_url;
      else setError('Stripe-Portal konnte nicht geöffnet werden.');
    } catch {
      setError('Fehler beim Öffnen des Stripe-Portals.');
    } finally {
      setPortalLoading(false);
    }
  };

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gray-900">
        <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
      </main>
    );
  }

  const planLabel = PLAN_LABELS[sub?.plan ?? user?.plan_type ?? 'free'] ?? sub?.plan ?? 'Unbekannt';
  const activeModuleIds = sub?.modules?.map(m => m.id) ?? user?.active_modules ?? [];

  return (
    <main role="main" aria-label="Abonnement-Verwaltung" className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-2xl mx-auto px-4 py-12">
        <h1 className="text-3xl font-bold mb-8">Abonnement</h1>

        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-500 rounded-lg flex items-center gap-3 text-red-200">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* Plan Card */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 mb-6">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div>
              <p className="text-xs uppercase tracking-widest text-gray-400 mb-1">Ihr Plan</p>
              <h2 className="text-2xl font-bold">{planLabel}</h2>
            </div>
            {sub?.has_subscription && (
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                sub.status === 'active' ? 'bg-green-900 text-green-300' :
                sub.status === 'trialing' ? 'bg-blue-900 text-blue-300' :
                'bg-red-900 text-red-300'
              }`}>
                {sub.status === 'active' ? 'Aktiv' :
                 sub.status === 'trialing' ? 'Testphase' :
                 sub.status === 'past_due' ? 'Zahlung ausstehend' : sub.status}
              </span>
            )}
          </div>

          {/* Aktive Module */}
          <div>
            <p className="text-sm text-gray-400 mb-3">Aktive Module</p>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(MODULE_META).map(([id, { label, Icon }]) => {
                const active = activeModuleIds.includes(id);
                return (
                  <div key={id} className={`flex items-center gap-2 p-3 rounded-lg border text-sm ${
                    active ? 'border-green-700 bg-green-900/20 text-green-300' : 'border-gray-700 text-gray-500'
                  }`}>
                    <Icon className="w-4 h-4 shrink-0" />
                    <span>{label}</span>
                    {active && <CheckCircle className="w-3.5 h-3.5 ml-auto" />}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Aktionen */}
        <div className="flex flex-col gap-3">
          {sub?.has_subscription ? (
            <button
              onClick={handlePortal}
              disabled={portalLoading}
              className="flex items-center justify-center gap-2 w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 py-3 rounded-lg font-medium transition-colors"
            >
              {portalLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CreditCard className="w-4 h-4" />}
              Zahlung & Rechnungen verwalten
              <ExternalLink className="w-3.5 h-3.5 ml-1 opacity-60" />
            </button>
          ) : (
            <button
              onClick={() => router.push('/register')}
              className="w-full bg-blue-600 hover:bg-blue-700 py-3 rounded-lg font-medium transition-colors"
            >
              Plan auswählen
            </button>
          )}

          <button
            onClick={() => router.push('/')}
            className="w-full bg-gray-700 hover:bg-gray-600 py-3 rounded-lg font-medium transition-colors"
          >
            Zurück zum Dashboard
          </button>
        </div>
      </div>
    </main>
  );
}
