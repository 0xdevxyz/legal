'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/lib/api';
import {
  BookOpen,
  Search,
  ExternalLink,
  Loader2,
  AlertTriangle,
  ScrollText,
  Newspaper,
} from 'lucide-react';

interface LawPage {
  id: string;
  title: string;
  law_areas: string[];
  affected_checks: string[];
  tags: string[];
  obsidian_deep_link?: string;
}

interface UpdateItem {
  id: string;
  title: string;
  date: string;
  category: string;
  law_areas: string[];
  impact: 'high' | 'medium' | 'low' | '';
  source_type: string;
  source_url: string;
  tags: string[];
}

interface SearchResult {
  id?: string;
  title?: string;
  score?: number;
  snippet?: string;
  text?: string;
  summary?: string;
  [k: string]: unknown;
}

const impactStyle: Record<string, string> = {
  high: 'bg-red-500/15 text-red-400 border border-red-500/30',
  medium: 'bg-amber-500/15 text-amber-400 border border-amber-500/30',
  low: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
};

function Chip({ children, tone = 'default' }: { children: React.ReactNode; tone?: 'default' | 'area' }) {
  const cls =
    tone === 'area'
      ? 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/25'
      : 'dark:bg-zinc-700/60 bg-gray-200 dark:text-gray-300 text-gray-700';
  return <span className={`text-[11px] px-2 py-0.5 rounded ${cls}`}>{children}</span>;
}

export default function KnowledgePage() {
  const [query, setQuery] = useState('');
  const [submitted, setSubmitted] = useState('');

  const lawsQuery = useQuery({
    queryKey: ['knowledge', 'laws'],
    queryFn: async () => {
      const { data } = await apiClient.get('/api/knowledge/laws');
      return (data?.laws ?? []) as LawPage[];
    },
    staleTime: 5 * 60_000,
    retry: false,
  });

  const updatesQuery = useQuery({
    queryKey: ['knowledge', 'updates'],
    queryFn: async () => {
      const { data } = await apiClient.get('/api/knowledge/updates?limit=20');
      return (data?.updates ?? []) as UpdateItem[];
    },
    staleTime: 5 * 60_000,
    retry: false,
  });

  const searchQuery = useQuery({
    queryKey: ['knowledge', 'search', submitted],
    queryFn: async () => {
      const { data } = await apiClient.get(`/api/knowledge/search?q=${encodeURIComponent(submitted)}`);
      return (data?.results ?? []) as SearchResult[];
    },
    enabled: submitted.trim().length >= 2,
    retry: false,
  });

  const onSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(query.trim());
  };

  return (
    <div className="px-4 sm:px-6 py-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-3 mb-2">
        <BookOpen className="w-6 h-6 text-indigo-400" />
        <h1 className="text-2xl font-bold dark:text-white text-gray-900">Rechts-Wissen</h1>
      </div>
      <p className="dark:text-gray-400 text-gray-600 mb-6 text-sm">
        Gesetzes-Stammdaten und aktuelle Rechts-Updates aus dem Complyo-Knowledge-Vault.
      </p>

      {/* Search */}
      <form onSubmit={onSearch} className="mb-8">
        <div className="relative max-w-xl">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={'Wissensdatenbank durchsuchen (z. B. „Cookie-Einwilligung")…'}
            className="w-full pl-9 pr-24 py-2.5 rounded-lg text-sm dark:bg-zinc-800 bg-gray-100 dark:text-white text-gray-900 border dark:border-zinc-700 border-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
          />
          <button
            type="submit"
            className="absolute right-1.5 top-1/2 -translate-y-1/2 px-3 py-1.5 rounded-md text-sm font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition"
          >
            Suchen
          </button>
        </div>
      </form>

      {/* Search results */}
      {submitted.trim().length >= 2 && (
        <section className="mb-10">
          <h2 className="text-sm font-semibold uppercase tracking-wider dark:text-zinc-400 text-gray-500 mb-3">
            Suchergebnisse für „{submitted}"
          </h2>
          {searchQuery.isLoading ? (
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin" /> Suche läuft…
            </div>
          ) : searchQuery.isError ? (
            <div className="flex items-center gap-2 text-sm text-amber-400">
              <AlertTriangle className="w-4 h-4" /> Volltextsuche derzeit nicht verfügbar.
            </div>
          ) : (searchQuery.data?.length ?? 0) === 0 ? (
            <p className="text-sm text-gray-400">Keine Treffer.</p>
          ) : (
            <div className="space-y-2">
              {searchQuery.data!.map((r, i) => (
                <div
                  key={r.id ?? i}
                  className="dark:bg-zinc-800/60 bg-gray-100 rounded-lg p-4 border dark:border-zinc-700/50 border-gray-200"
                >
                  <p className="font-semibold dark:text-white text-gray-900 text-sm">
                    {r.title ?? r.id ?? `Treffer ${i + 1}`}
                  </p>
                  {(r.snippet || r.text || r.summary) && (
                    <p className="text-xs dark:text-gray-400 text-gray-600 mt-1 line-clamp-3 whitespace-pre-line">
                      {r.snippet ?? r.text ?? r.summary}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Updates */}
      <section className="mb-10">
        <div className="flex items-center gap-2 mb-3">
          <Newspaper className="w-4 h-4 text-indigo-400" />
          <h2 className="text-sm font-semibold uppercase tracking-wider dark:text-zinc-400 text-gray-500">
            Aktuelle Rechts-Updates
          </h2>
        </div>
        {updatesQuery.isLoading ? (
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Loader2 className="w-4 h-4 animate-spin" /> Lädt…
          </div>
        ) : updatesQuery.isError ? (
          <div className="flex items-center gap-2 text-sm text-amber-400">
            <AlertTriangle className="w-4 h-4" /> Updates konnten nicht geladen werden.
          </div>
        ) : (updatesQuery.data?.length ?? 0) === 0 ? (
          <p className="text-sm dark:text-gray-400 text-gray-600">
            Noch keine Updates erfasst. Der tägliche Knowledge-Updater befüllt diesen Bereich automatisch.
          </p>
        ) : (
          <div className="space-y-3">
            {updatesQuery.data!.map((u) => (
              <div
                key={u.id}
                className="dark:bg-zinc-800/60 bg-gray-100 rounded-lg p-4 border dark:border-zinc-700/50 border-gray-200"
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="font-semibold dark:text-white text-gray-900">{u.title}</p>
                  {u.impact && (
                    <span className={`text-[11px] px-2 py-0.5 rounded shrink-0 ${impactStyle[u.impact] ?? ''}`}>
                      {u.impact}
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-2 mt-2">
                  {u.date && <span className="text-xs text-gray-500">{u.date}</span>}
                  {u.law_areas?.map((a) => (
                    <Chip key={a} tone="area">
                      {a}
                    </Chip>
                  ))}
                  {u.tags?.slice(0, 4).map((t) => (
                    <Chip key={t}>{t}</Chip>
                  ))}
                </div>
                {u.source_url && (
                  <a
                    href={u.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 mt-2"
                  >
                    Quelle <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Laws */}
      <section>
        <div className="flex items-center gap-2 mb-3">
          <ScrollText className="w-4 h-4 text-indigo-400" />
          <h2 className="text-sm font-semibold uppercase tracking-wider dark:text-zinc-400 text-gray-500">
            Gesetze & Rechtsgrundlagen
          </h2>
        </div>
        {lawsQuery.isLoading ? (
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <Loader2 className="w-4 h-4 animate-spin" /> Lädt…
          </div>
        ) : lawsQuery.isError ? (
          <div className="flex items-center gap-2 text-sm text-amber-400">
            <AlertTriangle className="w-4 h-4" /> Gesetze konnten nicht geladen werden.
          </div>
        ) : (lawsQuery.data?.length ?? 0) === 0 ? (
          <p className="text-sm dark:text-gray-400 text-gray-600">Keine Gesetzes-Seiten im Vault.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {lawsQuery.data!.map((law) => (
              <div
                key={law.id}
                className="dark:bg-zinc-800/60 bg-gray-100 rounded-lg p-5 border dark:border-zinc-700/50 border-gray-200 flex flex-col gap-3"
              >
                <h3 className="font-semibold dark:text-white text-gray-900 leading-snug">{law.title}</h3>
                {law.law_areas?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {law.law_areas.map((a) => (
                      <Chip key={a} tone="area">
                        {a}
                      </Chip>
                    ))}
                  </div>
                )}
                {law.affected_checks?.length > 0 && (
                  <p className="text-xs dark:text-gray-400 text-gray-600">
                    Betrifft Checks:{' '}
                    <span className="dark:text-gray-300 text-gray-700">
                      {law.affected_checks.join(', ')}
                    </span>
                  </p>
                )}
                {law.tags?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-auto">
                    {law.tags.slice(0, 5).map((t) => (
                      <Chip key={t}>{t}</Chip>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
