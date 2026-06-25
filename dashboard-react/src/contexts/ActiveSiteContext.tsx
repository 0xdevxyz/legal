'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getTrackedWebsites, TrackedWebsite } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useDashboardStore } from '@/stores/dashboard';

interface ActiveSiteContextValue {
  sites: TrackedWebsite[];
  activeSite: TrackedWebsite | null;
  setActiveSite: (site: TrackedWebsite) => void;
  isLoading: boolean;
  refresh: () => Promise<void>;
}

const ActiveSiteContext = createContext<ActiveSiteContextValue | null>(null);

const STORAGE_KEY = 'complyo_active_site_id';

export function ActiveSiteProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [sites, setSites] = useState<TrackedWebsite[]>([]);
  const [activeSite, setActiveSiteState] = useState<TrackedWebsite | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const restoreLockFromPrimary = useDashboardStore(s => s.restoreLockFromPrimary);
  const setCurrentWebsite = useDashboardStore(s => s.setCurrentWebsite);

  // Agentur/Expert verwalten mehrere Seiten → kein Single-Domain-Lock.
  const isAgency = user?.plan_type === 'agency' || user?.plan_type === 'expert';

  const load = useCallback(async () => {
    if (!user) return;
    setIsLoading(true);
    try {
      const data = await getTrackedWebsites();
      setSites(data);

      const savedId = localStorage.getItem(STORAGE_KEY);
      const saved = data.find(s => String(s.id) === savedId);
      const primary = data.find(s => s.is_primary) ?? data[0] ?? null;
      setActiveSiteState(saved ?? primary);

      // Optimization lock NUR für Einzel-Seiten-Pläne aus der Primärseite
      // wiederherstellen. Agenturen optimieren jede Seite frei (kein Lock).
      if (!isAgency && primary?.url) {
        restoreLockFromPrimary(primary.url);
      }
    } catch {
      // Silently fail — user might not have any sites yet
    } finally {
      setIsLoading(false);
    }
  }, [user, isAgency, restoreLockFromPrimary]);

  useEffect(() => {
    load();
  }, [load]);

  // Bei Agentur folgt die analysierte/optimierte Seite dem aktiven Projekt:
  // activeSite (SiteSwitcher / ProjectsCard) → currentWebsite (Dashboard-Store).
  useEffect(() => {
    if (!isAgency || !activeSite) return;
    setCurrentWebsite({
      id: String(activeSite.id),
      url: activeSite.url,
      name: activeSite.url.replace(/^https?:\/\//, '').replace(/\/$/, ''),
      lastScan: activeSite.last_scan_date || '',
      complianceScore: activeSite.last_score ?? 0,
      status: 'completed',
    });
  }, [isAgency, activeSite, setCurrentWebsite]);

  const setActiveSite = useCallback((site: TrackedWebsite) => {
    setActiveSiteState(site);
    localStorage.setItem(STORAGE_KEY, String(site.id));
  }, []);

  return (
    <ActiveSiteContext.Provider value={{ sites, activeSite, setActiveSite, isLoading, refresh: load }}>
      {children}
    </ActiveSiteContext.Provider>
  );
}

export function useActiveSite() {
  const ctx = useContext(ActiveSiteContext);
  if (!ctx) throw new Error('useActiveSite must be used within ActiveSiteProvider');
  return ctx;
}
