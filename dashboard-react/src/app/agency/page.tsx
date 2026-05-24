'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  Globe,
  Users,
  BarChart3,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Building2,
  CreditCard,
  ArrowRight,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import apiClient from '@/lib/api';
import { ClientGroup } from '@/components/agency/ClientGroup';
import { AgencyLogoUpload } from '@/components/agency/AgencyLogoUpload';
import { getAgencyClients, type AgencyClient } from '@/lib/agency-api';

interface SiteStat {
  site_id: string;
  url?: string;
  total_impressions: number;
  acceptance_rate: number;
  status?: 'active' | 'inactive' | 'warning';
}

interface AgencyStats {
  total_sites: number;
  total_impressions: number;
  overall_acceptance_rate: number;
  active_clients?: number;
  sites: SiteStat[];
}

// ─── Skeleton helpers ────────────────────────────────────────────────────────

function SkeletonBox({ className }: { className?: string }) {
  return (
    <div
      className={`animate-pulse bg-zinc-800 rounded-lg ${className ?? ''}`}
    />
  );
}

function StatCardSkeleton() {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
      <SkeletonBox className="h-4 w-24 mb-3" />
      <SkeletonBox className="h-8 w-16 mb-2" />
      <SkeletonBox className="h-3 w-20" />
    </div>
  );
}

function TableRowSkeleton() {
  return (
    <tr className="border-t border-zinc-800">
      <td className="px-6 py-4">
        <SkeletonBox className="h-4 w-40" />
      </td>
      <td className="px-6 py-4 text-right">
        <SkeletonBox className="h-4 w-20 ml-auto" />
      </td>
      <td className="px-6 py-4 text-right">
        <SkeletonBox className="h-4 w-14 ml-auto" />
      </td>
      <td className="px-6 py-4 text-right">
        <SkeletonBox className="h-6 w-16 ml-auto rounded-full" />
      </td>
    </tr>
  );
}

// ─── Stat card ────────────────────────────────────────────────────────────────

interface StatCardProps {
  label: string;
  value: string | number;
  sub: string;
  icon: React.ReactNode;
  accent: string; // Tailwind color prefix, e.g. 'blue'
}

function StatCard({ label, value, sub, icon, accent }: StatCardProps) {
  const bg: Record<string, string> = {
    blue: 'bg-blue-500/10 border-blue-500/20',
    green: 'bg-green-500/10 border-green-500/20',
    purple: 'bg-purple-500/10 border-purple-500/20',
    orange: 'bg-orange-500/10 border-orange-500/20',
  };
  const text: Record<string, string> = {
    blue: 'text-blue-400',
    green: 'text-green-400',
    purple: 'text-purple-400',
    orange: 'text-orange-400',
  };
  const iconBg: Record<string, string> = {
    blue: 'bg-blue-500/20',
    green: 'bg-green-500/20',
    purple: 'bg-purple-500/20',
    orange: 'bg-orange-500/20',
  };

  return (
    <div
      className={`border rounded-xl p-6 transition-all duration-200 hover:shadow-lg ${bg[accent] ?? 'bg-zinc-900 border-zinc-800'}`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className={`text-sm font-medium mb-1 ${text[accent] ?? 'text-zinc-400'}`}>
            {label}
          </p>
          <p className={`text-3xl font-bold ${text[accent] ?? 'text-white'}`}>{value}</p>
          <p className={`text-xs mt-1 opacity-70 ${text[accent] ?? 'text-zinc-500'}`}>{sub}</p>
        </div>
        <div className={`p-2 rounded-lg ${iconBg[accent] ?? 'bg-zinc-800'}`}>{icon}</div>
      </div>
    </div>
  );
}

// ─── Status badge ─────────────────────────────────────────────────────────────

function StatusBadge({ rate }: { rate: number }) {
  if (rate >= 0.6) {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-green-500/20 text-green-400 border border-green-500/30">
        <CheckCircle className="w-3 h-3" />
        Aktiv
      </span>
    );
  }
  if (rate >= 0.3) {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-orange-500/20 text-orange-400 border border-orange-500/30">
        <AlertCircle className="w-3 h-3" />
        Niedrig
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-zinc-700/50 text-zinc-400 border border-zinc-600/30">
      <AlertCircle className="w-3 h-3" />
      Inaktiv
    </span>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function AgencyPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [stats, setStats] = useState<AgencyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [checkoutError, setCheckoutError] = useState('');
  const [clients, setClients] = useState<AgencyClient[]>([]);
  const [clientsLoading, setClientsLoading] = useState(true);
  const [clientsError, setClientsError] = useState<string | null>(null);

  const handleActivateAgency = async () => {
    setCheckoutLoading(true);
    setCheckoutError('');
    try {
      const res = await apiClient.post('/api/stripe/create-checkout', {
        plan: 'agency',
        billing_period: 'monthly',
        success_url: `${window.location.origin}/subscription?success=true&session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${window.location.origin}/agency`,
      });
      if (res.data.checkout_url) {
        window.location.href = res.data.checkout_url;
      } else {
        setCheckoutError(res.data.detail || 'Checkout konnte nicht gestartet werden.');
      }
    } catch (err: any) {
      setCheckoutError(err.response?.data?.detail || 'Fehler beim Starten des Checkouts.');
    } finally {
      setCheckoutLoading(false);
    }
  };

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get<AgencyStats>('/api/cookie-compliance/agency/stats');
      setStats(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? err?.message ?? 'Fehler beim Laden der Statistiken.');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchClients = useCallback(async () => {
    setClientsLoading(true);
    setClientsError(null);
    try {
      const data = await getAgencyClients();
      setClients(data);
    } catch (err: any) {
      setClientsError(err?.response?.data?.detail ?? err?.message ?? 'Fehler beim Laden der Kundengruppen.');
    } finally {
      setClientsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    fetchClients();
  }, [fetchStats, fetchClients]);

  const isAgency = user?.plan_type === 'agency' || user?.plan_type === 'expert';

  // ─── Upgrade banner (no agency plan) ────────────────────────────────────────
  const UpgradeBanner = () => (
    <div className="mb-8 p-6 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-blue-500/10 border border-blue-500/30 rounded-xl">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-blue-500/20 rounded-xl flex-shrink-0">
            <Building2 className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <h3 className="text-white font-semibold text-lg mb-1">Agency Plan erforderlich</h3>
            <p className="text-zinc-400 text-sm">
              Verwalten Sie mehrere Client-Websites, erhalten Sie aggregierte Consent-Statistiken
              und nutzen Sie White-Label-Funktionen mit dem Agency Plan.
            </p>
            <ul className="mt-3 space-y-1">
              {[
                'Bis zu 50 Client-Websites verwalten',
                'Aggregierte Consent-Statistiken',
                'White-Label Cookie-Banner',
                'Prioritäts-Support',
              ].map((feat) => (
                <li key={feat} className="flex items-center gap-2 text-xs text-zinc-300">
                  <CheckCircle className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
                  {feat}
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="flex flex-col gap-2">
          {checkoutError && (
            <p className="text-red-400 text-sm">{checkoutError}</p>
          )}
          <button
            onClick={handleActivateAgency}
            disabled={checkoutLoading}
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white font-semibold rounded-lg transition-colors duration-200 whitespace-nowrap flex-shrink-0"
          >
            <CreditCard className="w-4 h-4" />
            {checkoutLoading ? 'Wird gestartet…' : 'Agency Plan aktivieren'}
            {!checkoutLoading && <ArrowRight className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );

  // ─── Loading skeleton ────────────────────────────────────────────────────────
  const LoadingSkeleton = () => (
    <div className="min-h-full bg-zinc-950 p-6 lg:p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <SkeletonBox className="h-8 w-56 mb-2" />
          <SkeletonBox className="h-4 w-80" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
          {[0, 1, 2, 3].map((i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-zinc-800">
            <SkeletonBox className="h-5 w-40" />
          </div>
          <table className="w-full">
            <tbody>
              {[0, 1, 2, 3].map((i) => (
                <TableRowSkeleton key={i} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  // ─── Error state ─────────────────────────────────────────────────────────────
  const ErrorState = () => (
    <div className="min-h-full bg-zinc-950 flex items-center justify-center p-8">
      <div className="text-center max-w-md">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-red-500/20 rounded-full mb-4">
          <AlertCircle className="w-8 h-8 text-red-400" />
        </div>
        <h2 className="text-white text-xl font-semibold mb-2">Fehler beim Laden</h2>
        <p className="text-zinc-400 text-sm mb-6">{error}</p>
        <button
          onClick={fetchStats}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-white font-medium rounded-lg transition-colors duration-200"
        >
          <RefreshCw className="w-4 h-4" />
          Erneut versuchen
        </button>
      </div>
    </div>
  );

  // ─── Empty state ─────────────────────────────────────────────────────────────
  const EmptyState = () => (
    <div className="text-center py-16">
      <div className="inline-flex items-center justify-center w-16 h-16 bg-zinc-800 rounded-full mb-4">
        <Globe className="w-8 h-8 text-zinc-500" />
      </div>
      <h3 className="text-white font-semibold text-lg mb-2">Keine Websites vorhanden</h3>
      <p className="text-zinc-500 text-sm max-w-sm mx-auto">
        Es wurden noch keine Client-Websites zu Ihrem Agency-Account hinzugefügt.
      </p>
    </div>
  );

  // ─── Render ──────────────────────────────────────────────────────────────────

  if (loading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return <ErrorState />;
  }

  const totalSites = stats?.total_sites ?? 0;
  const totalImpressions = stats?.total_impressions ?? 0;
  const overallRate = stats?.overall_acceptance_rate ?? 0;
  const activeClients = stats?.active_clients ?? stats?.sites?.filter((s) => (s.acceptance_rate ?? 0) > 0).length ?? 0;
  const sites = stats?.sites ?? [];

  return (
    <main
      role="main"
      aria-label="Agentur-Dashboard"
      className="min-h-full bg-zinc-950 text-white p-6 lg:p-8"
    >
        <div className="max-w-7xl mx-auto">
          {/* ── Header ────────────────────────────────────────────────────────── */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-1">
              <div className="p-2 bg-blue-500/20 rounded-lg">
                <Building2 className="w-5 h-5 text-blue-400" />
              </div>
              <h1 className="text-2xl font-bold text-white">Agentur-Dashboard</h1>
            </div>
            <p className="text-zinc-400 text-sm ml-[52px]">
              Übersicht aller verwalteten Client-Websites und aggregierten Consent-Metriken
            </p>
          </div>

          {/* ── Upgrade banner if no agency plan ──────────────────────────────── */}
          {!isAgency && <UpgradeBanner />}

          {/* ── Stats grid ────────────────────────────────────────────────────── */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
            <StatCard
              label="Gesamte Websites"
              value={totalSites}
              sub="Alle verwalteten Sites"
              icon={<Globe className="w-5 h-5 text-blue-400" />}
              accent="blue"
            />
            <StatCard
              label="Impressionen gesamt"
              value={totalImpressions.toLocaleString('de-DE')}
              sub="Letzte 30 Tage"
              icon={<BarChart3 className="w-5 h-5 text-purple-400" />}
              accent="purple"
            />
            <StatCard
              label="Akzeptanzrate"
              value={`${(overallRate * 100).toFixed(1)} %`}
              sub="Durchschnitt aller Sites"
              icon={<TrendingUp className="w-5 h-5 text-green-400" />}
              accent="green"
            />
            <StatCard
              label="Aktive Clients"
              value={activeClients}
              sub="Mit Consent-Aktivität"
              icon={<Users className="w-5 h-5 text-orange-400" />}
              accent="orange"
            />
          </div>

          {/* Agency logo upload (Phase 10 AGENCY-03) */}
          <div className="mb-6">
            <AgencyLogoUpload onUploaded={() => fetchClients()} />
          </div>

          {/* Per-client grouped view (Phase 10 AGENCY-02) */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-white font-semibold text-lg">Kunden-Uebersicht</h2>
              {clientsError && (
                <span className="text-red-400 text-xs">{clientsError}</span>
              )}
            </div>
            {clientsLoading ? (
              <div className="space-y-3">
                {[0, 1, 2].map(i => (
                  <div key={i} className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                    <SkeletonBox className="h-5 w-48 mb-2" />
                    <SkeletonBox className="h-3 w-32" />
                  </div>
                ))}
              </div>
            ) : clients.length === 0 ? (
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 text-center">
                <p className="text-zinc-400 text-sm">
                  Noch keine Kunden zugeordnet. Weisen Sie Ihren Sites <code>client_name</code> zu, um sie hier gruppiert zu sehen.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {clients.map(c => (
                  <ClientGroup key={c.client_name} client={c} />
                ))}
              </div>
            )}
          </div>

          {/* ── Client table ──────────────────────────────────────────────────── */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-zinc-800 flex items-center justify-between">
              <h2 className="text-white font-semibold">Client-Websites im Überblick</h2>
              <button
                onClick={fetchStats}
                className="inline-flex items-center gap-1.5 text-xs text-zinc-400 hover:text-white transition-colors duration-200"
                aria-label="Statistiken aktualisieren"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Aktualisieren
              </button>
            </div>

            {sites.length === 0 ? (
              <EmptyState />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-zinc-800 text-left">
                      <th className="px-6 py-3 text-xs font-medium text-zinc-400 uppercase tracking-wider">
                        Website
                      </th>
                      <th className="px-6 py-3 text-xs font-medium text-zinc-400 uppercase tracking-wider text-right">
                        Impressionen
                      </th>
                      <th className="px-6 py-3 text-xs font-medium text-zinc-400 uppercase tracking-wider text-right">
                        Akzeptanzrate
                      </th>
                      <th className="px-6 py-3 text-xs font-medium text-zinc-400 uppercase tracking-wider text-right">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sites.map((site, i) => {
                      const displayUrl = site.url ?? site.site_id.replace(/-/g, '.');
                      return (
                        <tr
                          key={site.site_id}
                          className="border-t border-zinc-800 hover:bg-zinc-800/50 transition-colors duration-150"
                        >
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <div className="flex-shrink-0 w-7 h-7 bg-zinc-800 rounded-md flex items-center justify-center">
                                <Globe className="w-3.5 h-3.5 text-zinc-400" />
                              </div>
                              <div>
                                <p className="text-white font-medium">{displayUrl}</p>
                                {site.url && (
                                  <p className="text-zinc-500 text-xs font-mono">{site.site_id}</p>
                                )}
                              </div>
                              <a
                                href={`https://${displayUrl}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="ml-1 text-zinc-600 hover:text-zinc-400 transition-colors duration-150"
                                aria-label={`${displayUrl} öffnen`}
                              >
                                <ExternalLink className="w-3.5 h-3.5" />
                              </a>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-zinc-300 text-right tabular-nums">
                            {site.total_impressions.toLocaleString('de-DE')}
                          </td>
                          <td className="px-6 py-4 text-zinc-300 text-right tabular-nums">
                            <span
                              className={
                                site.acceptance_rate >= 0.6
                                  ? 'text-green-400'
                                  : site.acceptance_rate >= 0.3
                                  ? 'text-orange-400'
                                  : 'text-zinc-500'
                              }
                            >
                              {(site.acceptance_rate * 100).toFixed(1)} %
                            </span>
                          </td>
                          <td className="px-6 py-4 text-right">
                            <StatusBadge rate={site.acceptance_rate} />
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </main>
  );
}
