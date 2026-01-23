'use client';

import React, { useEffect, useState } from 'react';
import {
  Users,
  Mail,
  TrendingUp,
  Shield,
  CreditCard,
  Sparkles,
  CalendarDays,
  AlertCircle,
  CheckCircle,
  Clock,
  Trash2,
  RefreshCw
} from 'lucide-react';

interface DashboardStats {
  total_leads: number;
  verified_leads: number;
  converted_leads: number;
  leads_last_24h: number;
  verification_rate: number;
  conversion_rate: number;
  gdpr_compliant: boolean;
  data_retention_days: number;
  storage_type: string;
}

interface Lead {
  id: string;
  email: string;
  name: string;
  company?: string;
  status: string;
  email_verified: boolean;
  created_at: string;
  verified_at?: string;
  url_analyzed?: string;
}

interface AdminOverview {
  overview: DashboardStats;
  lead_sources: Record<string, number>;
  recent_activity: number;
  status_breakdown: Record<string, number>;
  system_status: {
    storage_type: string;
    gdpr_compliant: boolean;
    email_service: string;
    pdf_generation: string;
  };
}

const moduleTiles = [
  {
    icon: Users,
    title: 'Creator CRM',
    description: 'Tagge Leads, sende Segment-Mails und visualisiere Funnel-Etappen.'
  },
  {
    icon: Sparkles,
    title: 'AI Marketing',
    description: 'alfi AI schreibt E-Mails, Upsells und Launch-Storys für dich.'
  },
  {
    icon: CreditCard,
    title: 'Payments & Reports',
    description: 'Abrechnung, Gebührenübersicht und Umsatz-Insights in einem Panel.'
  },
  {
    icon: CalendarDays,
    title: 'Termine & Coaching',
    description: 'Buchungslinks, Erinnerungen und Coachings mit Zahlungsabwicklung.'
  }
];

const AdminDashboard: React.FC = () => {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('all');

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';
  const ADMIN_API_KEY = 'admin_complyo_2025';

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [overviewResponse, leadsResponse] = await Promise.all([
        fetch(`${API_BASE}/api/admin/dashboard/overview?api_key=${ADMIN_API_KEY}`),
        fetch(`${API_BASE}/api/admin/leads?api_key=${ADMIN_API_KEY}&limit=50`)
      ]);

      if (overviewResponse.ok) {
        const overviewData = await overviewResponse.json();
        setOverview(overviewData);
      }

      if (leadsResponse.ok) {
        const leadsData = await leadsResponse.json();
        setLeads(leadsData.leads);
      }
    } catch (err) {
      console.error('Dashboard loading error:', err);
      setError('Fehler beim Laden der Daten. Bitte später erneut versuchen.');
    } finally {
      setLoading(false);
    }
  };

  const resendVerification = async (leadId: string) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/admin/leads/${leadId}/resend-verification?api_key=${ADMIN_API_KEY}`,
        { method: 'POST' }
      );

      if (response.ok) {
        alert('Verification E-Mail erneut gesendet');
        loadDashboardData();
      } else {
        alert('Fehler beim Senden der E-Mail');
      }
    } catch (err) {
      alert('Fehler beim Senden der E-Mail');
    }
  };

  const deleteLead = async (leadId: string) => {
    if (!confirm('Lead wirklich löschen? (DSGVO-Recht auf Löschung)')) return;
    const reason = prompt('Grund für die Löschung:') || 'Admin deletion';
    try {
      const response = await fetch(
        `${API_BASE}/api/admin/leads/${leadId}?api_key=${ADMIN_API_KEY}&reason=${encodeURIComponent(reason)}`,
        { method: 'DELETE' }
      );

      if (response.ok) {
        alert('Lead gelöscht');
        loadDashboardData();
      } else {
        alert('Fehler beim Löschen');
      }
    } catch (err) {
      alert('Fehler beim Löschen');
    }
  };

  const filteredLeads = selectedStatus === 'all'
    ? leads
    : leads.filter((lead) => {
        if (selectedStatus === 'verified') return lead.email_verified;
        if (selectedStatus === 'unverified') return !lead.email_verified;
        if (selectedStatus === 'converted') return lead.status === 'converted';
        return true;
      });

  const getStatusBadge = (status: string, verified: boolean) => {
    if (status === 'converted') {
      return <span className="rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-semibold text-emerald-300">Konvertiert</span>;
    }
    if (verified) {
      return <span className="rounded-full bg-sky-500/20 px-3 py-1 text-xs font-semibold text-sky-200">Verifiziert</span>;
    }
    return <span className="rounded-full bg-yellow-500/20 px-3 py-1 text-xs font-semibold text-yellow-200">Ausstehend</span>;
  };

  if (loading && !overview) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-400 mx-auto mb-4" />
          <p className="text-white/70">Lade das Creator Dashboard...</p>
        </div>
      </div>
    );
  }

  if (error && !overview) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="mx-auto mb-4 h-12 w-12 text-rose-400" />
          <p className="text-white/90">{error}</p>
          <button
            onClick={loadDashboardData}
            className="mt-4 inline-flex items-center gap-2 rounded-full bg-white px-6 py-2 text-sm font-semibold text-slate-900"
          >
            Reload
            <RefreshCw className="w-4 h-4 text-slate-900" />
          </button>
        </div>
      </div>
    );
  }

  const stats = [
    {
      label: 'Gesamt-Leads',
      value: overview?.overview.total_leads ?? '—',
      icon: Users,
      accent: 'from-cyan-500 to-blue-500'
    },
    {
      label: 'Verifiziert',
      value: overview?.overview.verified_leads ?? '—',
      icon: CheckCircle,
      accent: 'from-emerald-500 to-teal-500'
    },
    {
      label: 'Konvertiert',
      value: overview?.overview.converted_leads ?? '—',
      icon: TrendingUp,
      accent: 'from-purple-500 to-pink-500'
    },
    {
      label: 'Neue Leads (24h)',
      value: overview?.overview.leads_last_24h ?? '—',
      icon: Clock,
      accent: 'from-yellow-500 to-orange-500'
    }
  ];

  const statusBreakdown = overview?.status_breakdown ?? {};
  const leadSources = overview?.lead_sources ?? {};

  return (
    <div className="min-h-screen bg-slate-950 text-white relative overflow-hidden">
      <div className="absolute -top-20 left-1/2 h-64 w-64 -translate-x-1/2 rounded-full bg-cyan-500/40 blur-3xl" />
      <div className="absolute bottom-0 right-10 h-56 w-56 rounded-full bg-violet-500/40 blur-3xl" />

      <div className="relative mx-auto max-w-6xl px-4 pb-12 pt-10 sm:px-6 lg:px-8">
        <header className="space-y-3">
          <p className="text-xs uppercase tracking-[0.4em] text-white/60">Creator Operations</p>
          <h1 className="text-4xl font-bold leading-tight">All-in-One Command Center</h1>
          <p className="text-base text-white/70">
            Verwalte Leads, Launches, Termine und Automationen aus einem Dashboard. Die Insights sind auf Creator-Produkte und Coaching-Angebote abgestimmt.
          </p>
          <button
            onClick={loadDashboardData}
            className="inline-flex items-center gap-2 rounded-full bg-white px-5 py-3 text-sm font-semibold text-slate-900 transition hover:bg-white/90"
          >
            Aktuelle Daten laden
            <RefreshCw className="w-4 h-4 text-slate-900" />
          </button>
        </header>

        <div className="mt-8 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-xl backdrop-blur"
            >
              <div className={`inline-flex items-center justify-center rounded-2xl bg-gradient-to-br ${stat.accent} p-3 text-white`}>
                <stat.icon className="w-5 h-5" />
              </div>
              <p className="mt-4 text-3xl font-bold">{stat.value}</p>
              <p className="text-sm uppercase tracking-[0.3em] text-white/60">{stat.label}</p>
            </div>
          ))}
        </div>

        <section className="mt-10 rounded-3xl border border-white/10 bg-gradient-to-br from-white/5 to-slate-900/40 p-6 shadow-2xl">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Module & Automationen</h2>
            <p className="text-sm text-white/60">Perfekt für digitale Launches</p>
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {moduleTiles.map((tile) => (
              <div key={tile.title} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="flex items-center gap-3 text-white/70">
                  <tile.icon className="w-5 h-5 text-white" />
                  <h3 className="text-lg font-semibold text-white">{tile.title}</h3>
                </div>
                <p className="mt-3 text-sm text-white/70">{tile.description}</p>
              </div>
            ))}
          </div>
          {Object.keys(leadSources).length > 0 && (
            <div className="mt-6 flex flex-wrap gap-3">
              {Object.entries(leadSources).map(([source, count]) => (
                <span key={source} className="rounded-full border border-white/20 px-4 py-2 text-xs uppercase tracking-[0.3em] text-white/70">
                  {source} • {count}
                </span>
              ))}
            </div>
          )}
        </section>

        <section className="mt-10 rounded-3xl border border-white/10 bg-white/5 p-6 shadow-xl">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-xl font-semibold">Lead-Verwaltung</h2>
              <p className="text-sm text-white/60">Filtere Status, sende Verifikationsmails oder lösche GDPR-konform.</p>
            </div>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="min-w-[180px] rounded-full border border-white/20 bg-slate-900/60 px-4 py-2 text-sm text-white"
            >
              <option value="all">Alle Status</option>
              <option value="verified">Verifiziert</option>
              <option value="unverified">Nicht verifiziert</option>
              <option value="converted">Konvertiert</option>
            </select>
          </div>

          <div className="mt-6 overflow-x-auto">
            <table className="min-w-full divide-y divide-white/10 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-[0.3em] text-white/40">
                  <th className="px-4 py-3">Lead</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Erstellt</th>
                  <th className="px-4 py-3">Produkt</th>
                  <th className="px-4 py-3 text-center">Aktionen</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {filteredLeads.map((lead) => (
                  <tr key={lead.id} className="hover:bg-white/5">
                    <td className="px-4 py-4">
                      <div className="text-sm font-semibold">{lead.name}</div>
                      <div className="text-xs text-white/60">{lead.email}</div>
                      {lead.company && <div className="text-[11px] text-white/40">{lead.company}</div>}
                    </td>
                    <td className="px-4 py-4">{getStatusBadge(lead.status, lead.email_verified)}</td>
                    <td className="px-4 py-4 text-xs text-white/60">{new Date(lead.created_at).toLocaleDateString('de-DE')}</td>
                    <td className="px-4 py-4 text-xs text-white/60">{lead.url_analyzed || '—'}</td>
                    <td className="px-4 py-4 text-center">
                      <div className="flex items-center justify-center gap-3 text-white/70">
                        {!lead.email_verified && (
                          <button onClick={() => resendVerification(lead.id)} title="Verification erneut senden">
                            <Mail className="w-4 h-4 text-cyan-300" />
                          </button>
                        )}
                        <button onClick={() => deleteLead(lead.id)} title="Lead löschen (GDPR)">
                          <Trash2 className="w-4 h-4 text-rose-400" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filteredLeads.length === 0 && (
            <div className="mt-8 rounded-2xl bg-white/5 p-6 text-center text-sm text-white/60">
              Keine Leads für diesen Filter gefunden.
            </div>
          )}
        </section>

        <section className="mt-8 grid gap-6 md:grid-cols-2">
          <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
            <h3 className="text-lg font-semibold mb-3">System Status</h3>
            <div className="space-y-3 text-sm text-white/70">
              <div className="flex items-center justify-between">
                <span>Datenbank</span>
                <span>{overview?.system_status.storage_type || '–'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>E-Mail Service</span>
                <span>{overview?.system_status.email_service || '–'}</span>
              </div>
              <div className="flex items-center justify-between text-emerald-300">
                <span>GDPR Status</span>
                <span>{overview?.system_status.gdpr_compliant ? 'Konform' : 'Überprüfung nötig'}</span>
              </div>
            </div>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
            <h3 className="text-lg font-semibold mb-3">Status Breakdown</h3>
            <div className="space-y-4 text-xs text-white/70">
              {Object.entries(statusBreakdown).map(([key, value]) => (
                <div key={key}>
                  <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-white/50">
                    <span>{key}</span>
                    <span>{value}</span>
                  </div>
                  <div className="mt-1 h-2 rounded-full bg-white/10">
                    <div
                      className="h-2 rounded-full bg-gradient-to-r from-cyan-400 to-blue-500"
                      style={{
                        width: `${Math.min((value / Math.max(overview?.overview.total_leads || 1, 1)) * 100, 100)}%`
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default AdminDashboard;
