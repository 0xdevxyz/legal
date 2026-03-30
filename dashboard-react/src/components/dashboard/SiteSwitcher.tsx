'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Globe, ChevronDown, Plus, Check, Loader2 } from 'lucide-react';
import { useActiveSite } from '@/contexts/ActiveSiteContext';
import { saveTrackedWebsite, TrackedWebsite } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

export function SiteSwitcher() {
  const { sites, activeSite, setActiveSite, isLoading, refresh } = useActiveSite();
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [adding, setAdding] = useState(false);
  const [newUrl, setNewUrl] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
        setAdding(false);
        setError('');
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Nur für Agentur-User sichtbar
  if (user?.plan_type !== 'agency') return null;

  const displayUrl = activeSite
    ? activeSite.url.replace(/^https?:\/\//, '').replace(/\/$/, '')
    : '—';

  const planLimit = user?.plan_limits?.websites_max ?? 25;
  const atLimit = planLimit !== -1 && sites.length >= planLimit;

  const handleAdd = async () => {
    if (!newUrl.trim()) return;
    setSaving(true);
    setError('');
    try {
      let url = newUrl.trim();
      if (!/^https?:\/\//i.test(url)) url = 'https://' + url;
      const site = await saveTrackedWebsite(url, 0);
      await refresh();
      setActiveSite(site);
      setAdding(false);
      setNewUrl('');
      setOpen(false);
    } catch (err: any) {
      setError(err.message ?? 'Fehler beim Hinzufügen');
    } finally {
      setSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-xl glass-card text-sm text-gray-400">
        <Loader2 size={14} className="animate-spin" />
        <span>Lädt…</span>
      </div>
    );
  }

  return (
    <div ref={ref} className="relative">
      {/* Trigger */}
      <button
        onClick={() => { setOpen(o => !o); setAdding(false); setError(''); }}
        className="flex items-center gap-2 px-3 py-2 rounded-xl glass-card hover:glass-strong transition-all duration-200 text-sm max-w-[220px]"
        aria-label="Website wechseln"
      >
        <Globe size={14} className="text-purple-400 shrink-0" />
        <span className="truncate text-gray-200">{displayUrl}</span>
        <ChevronDown size={14} className={`text-gray-400 shrink-0 transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute left-0 top-full mt-2 w-72 rounded-xl glass-strong border border-white/10 shadow-2xl z-50 overflow-hidden">
          {/* Site List */}
          <div className="max-h-56 overflow-y-auto">
            {sites.length === 0 && (
              <p className="px-4 py-3 text-sm text-gray-400">Noch keine Website hinzugefügt.</p>
            )}
            {sites.map((site) => {
              const label = site.url.replace(/^https?:\/\//, '').replace(/\/$/, '');
              const isActive = activeSite?.id === site.id;
              return (
                <button
                  key={site.id}
                  onClick={() => { setActiveSite(site); setOpen(false); }}
                  className={`w-full flex items-center gap-3 px-4 py-3 text-sm text-left transition-colors duration-150 hover:bg-white/5 ${isActive ? 'bg-purple-500/10' : ''}`}
                >
                  <Globe size={13} className="text-gray-400 shrink-0" />
                  <span className="truncate flex-1 text-gray-200">{label}</span>
                  {isActive && <Check size={13} className="text-purple-400 shrink-0" />}
                  {site.last_score != null && (
                    <span className={`text-xs font-medium shrink-0 ${site.last_score >= 80 ? 'text-green-400' : site.last_score >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
                      {site.last_score}%
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Add Site */}
          <div className="border-t border-white/10">
            {!adding ? (
              <button
                onClick={() => { if (!atLimit) setAdding(true); }}
                disabled={atLimit}
                className={`w-full flex items-center gap-2 px-4 py-3 text-sm transition-colors duration-150 ${atLimit ? 'text-gray-500 cursor-not-allowed' : 'text-purple-400 hover:bg-white/5'}`}
              >
                <Plus size={14} className="shrink-0" />
                <span>{atLimit ? `Limit erreicht (${planLimit} Websites)` : 'Website hinzufügen'}</span>
              </button>
            ) : (
              <div className="p-3 space-y-2">
                <label htmlFor="site-switcher-url" className="sr-only">Website-URL</label>
                <input
                  id="site-switcher-url"
                  autoFocus
                  type="url"
                  placeholder="https://beispiel.de"
                  value={newUrl}
                  onChange={e => setNewUrl(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') handleAdd(); if (e.key === 'Escape') { setAdding(false); setError(''); } }}
                  className="w-full px-3 py-2 text-sm rounded-lg bg-white/5 border border-white/10 text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500"
                />
                {error && <p className="text-xs text-red-400">{error}</p>}
                <div className="flex gap-2">
                  <button
                    onClick={handleAdd}
                    disabled={saving || !newUrl.trim()}
                    className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 text-xs rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white transition-colors"
                  >
                    {saving ? <Loader2 size={12} className="animate-spin" /> : null}
                    Hinzufügen
                  </button>
                  <button
                    onClick={() => { setAdding(false); setError(''); }}
                    className="px-3 py-1.5 text-xs rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 transition-colors"
                  >
                    Abbrechen
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
