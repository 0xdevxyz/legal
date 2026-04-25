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

      // Optimization lock aus DB-Primärseite wiederherstellen (überlebt Cache-Leerung)
      if (primary?.url) {
        restoreLockFromPrimary(primary.url);
      }
    } catch {
      // Silently fail — user might not have any sites yet
    } finally {
      setIsLoading(false);
    }
  }, [user, restoreLockFromPrimary]);

  useEffect(() => {
    load();
  }, [load]);

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
