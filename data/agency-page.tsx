'use client';

import React, { useState, useEffect } from 'react';
import apiClient from '@/lib/api';

interface SiteStat {
  site_id: string;
  total_impressions: number;
  acceptance_rate: number;
}

interface AgencyStats {
  total_sites: number;
  total_impressions: number;
  overall_acceptance_rate: number;
  sites: SiteStat[];
}

export default function AgencyPage() {
  const [stats, setStats] = useState<AgencyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient
      .get<AgencyStats>('/api/cookie-compliance/agency/stats')
      .then((res) => {
        setStats(res.data);
      })
      .catch((err) => {
        setError(err?.message ?? 'Fehler beim Laden der Statistiken.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-900 flex items-center justify-center">
        <p className="text-gray-400 text-lg">Lade Statistiken...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-zinc-900 flex items-center justify-center">
        <p className="text-red-400 text-lg">{error}</p>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="min-h-screen bg-zinc-900 flex items-center justify-center">
        <p className="text-gray-500 text-lg">Keine Daten verfügbar.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-900 text-white p-8">
      <h1 className="text-2xl font-bold mb-8 text-white">Agency Dashboard</h1>

      {/* Aggregated stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-10">
        <div className="bg-zinc-800 rounded-lg p-6">
          <p className="text-gray-400 text-sm mb-1">Verwaltete Sites</p>
          <p className="text-3xl font-semibold text-white">{stats.total_sites}</p>
        </div>
        <div className="bg-zinc-800 rounded-lg p-6">
          <p className="text-gray-400 text-sm mb-1">Impressionen gesamt</p>
          <p className="text-3xl font-semibold text-white">
            {stats.total_impressions.toLocaleString('de-DE')}
          </p>
        </div>
        <div className="bg-zinc-800 rounded-lg p-6">
          <p className="text-gray-400 text-sm mb-1">Gesamte Akzeptanzrate</p>
          <p className="text-3xl font-semibold text-white">
            {(stats.overall_acceptance_rate * 100).toFixed(1)} %
          </p>
        </div>
      </div>

      {/* Per-site list */}
      <h2 className="text-lg font-semibold mb-4 text-gray-200">Sites im Überblick</h2>

      {stats.sites.length === 0 ? (
        <div className="bg-zinc-800 rounded-lg p-6 text-gray-500">
          Keine Sites gefunden.
        </div>
      ) : (
        <div className="bg-zinc-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-zinc-700 text-gray-300 text-left">
                <th className="px-6 py-3 font-medium">Site ID</th>
                <th className="px-6 py-3 font-medium text-right">Impressionen</th>
                <th className="px-6 py-3 font-medium text-right">Akzeptanzrate</th>
              </tr>
            </thead>
            <tbody>
              {stats.sites.map((site, i) => (
                <tr
                  key={site.site_id}
                  className={i % 2 === 0 ? 'bg-zinc-800' : 'bg-zinc-700/50'}
                >
                  <td className="px-6 py-4 text-white font-mono">{site.site_id}</td>
                  <td className="px-6 py-4 text-gray-300 text-right">
                    {site.total_impressions.toLocaleString('de-DE')}
                  </td>
                  <td className="px-6 py-4 text-gray-300 text-right">
                    {(site.acceptance_rate * 100).toFixed(1)} %
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
