'use client';

import React, { useState } from 'react';
import { Building2, Download, ChevronDown, ChevronUp, Mail, Loader2 } from 'lucide-react';
import type { AgencyClient } from '@/lib/agency-api';
import { downloadClientReport } from '@/lib/agency-api';

interface ClientGroupProps {
  client: AgencyClient;
}

export function ClientGroup({ client }: ClientGroupProps) {
  const [expanded, setExpanded] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = async () => {
    setDownloading(true);
    setError(null);
    try {
      await downloadClientReport(client.client_name);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? err?.message ?? 'Download fehlgeschlagen');
    } finally {
      setDownloading(false);
    }
  };

  const rate = (client.acceptance_rate * 100).toFixed(1);
  const rateColor =
    client.acceptance_rate >= 0.6 ? 'text-green-400'
      : client.acceptance_rate >= 0.3 ? 'text-orange-400'
      : 'text-zinc-500';

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
      <div className="px-6 py-4 flex items-center justify-between gap-4">
        <button
          onClick={() => setExpanded(v => !v)}
          className="flex items-center gap-3 flex-1 text-left"
          aria-expanded={expanded}
        >
          <div className="p-2 bg-blue-500/20 rounded-lg flex-shrink-0">
            <Building2 className="w-5 h-5 text-blue-400" />
          </div>
          <div className="min-w-0">
            <h3 className="text-white font-semibold truncate">{client.client_name}</h3>
            {client.client_email && (
              <p className="text-zinc-500 text-xs flex items-center gap-1 mt-0.5">
                <Mail className="w-3 h-3" /> {client.client_email}
              </p>
            )}
          </div>
          {expanded
            ? <ChevronUp className="w-4 h-4 text-zinc-400" />
            : <ChevronDown className="w-4 h-4 text-zinc-400" />}
        </button>
        <div className="flex items-center gap-4 flex-shrink-0">
          <div className="text-right hidden sm:block">
            <p className="text-xs text-zinc-500">Sites</p>
            <p className="text-white font-semibold">{client.site_count}</p>
          </div>
          <div className="text-right hidden sm:block">
            <p className="text-xs text-zinc-500">Acceptance</p>
            <p className={`font-semibold ${rateColor}`}>{rate}%</p>
          </div>
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white text-sm font-semibold rounded-lg transition-colors"
            aria-label={`PDF herunterladen fuer ${client.client_name}`}
          >
            {downloading
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Download className="w-4 h-4" />}
            PDF herunterladen
          </button>
        </div>
      </div>
      {error && (
        <div className="px-6 pb-3 -mt-2 text-red-400 text-xs">{error}</div>
      )}
      {expanded && (
        <div className="px-6 pb-4 border-t border-zinc-800 pt-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-zinc-500">Sites</p>
            <p className="text-white font-semibold">{client.site_count}</p>
          </div>
          <div>
            <p className="text-xs text-zinc-500">Impressionen (30d)</p>
            <p className="text-white font-semibold">{client.total_impressions.toLocaleString('de-DE')}</p>
          </div>
          <div>
            <p className="text-xs text-zinc-500">Akzeptiert</p>
            <p className="text-white font-semibold">{client.total_accepted.toLocaleString('de-DE')}</p>
          </div>
          <div>
            <p className="text-xs text-zinc-500">Acceptance Rate</p>
            <p className={`font-semibold ${rateColor}`}>{rate}%</p>
          </div>
        </div>
      )}
    </div>
  );
}
