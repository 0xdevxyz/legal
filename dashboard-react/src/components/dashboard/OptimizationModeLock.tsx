'use client';

import React, { useState, useEffect } from 'react';
import { Lock, Globe, ArrowRight, AlertTriangle, CheckCircle, Info, Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useDashboardStore } from '@/stores/dashboard';
import { useRouter } from 'next/navigation';
import { getTrackedWebsites } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

interface OptimizationModeLockProps {
  onLock?: (url: string) => void;
  hasInteracted?: boolean;
}

const getShortDomain = (url: string) => {
  try {
    return new URL(url.startsWith('http') ? url : `https://${url}`).hostname.replace('www.', '');
  } catch {
    return url;
  }
};

export const OptimizationModeLock: React.FC<OptimizationModeLockProps> = ({
  onLock,
  hasInteracted = false
}) => {
  const router = useRouter();
  const { user } = useAuth();
  // Agentur/Expert verwalten mehrere Seiten → kein Single-Domain-Lock.
  const isAgency = user?.plan_type === 'agency' || user?.plan_type === 'expert';
  const {
    currentWebsite,
    analysisData,
    lockedOptimizationUrl,
    isInOptimizationMode,
    lockForOptimization,
    setCurrentWebsite,
    updateMetrics
  } = useDashboardStore();

  const [showConfirm, setShowConfirm] = useState(false);
  const [isLoadingBack, setIsLoadingBack] = useState(false);

  useEffect(() => {
    if (typeof localStorage === 'undefined') return;
    // Agentur/Expert: eventuell vorhandene Alt-Lock-Keys (z. B. nach einem
    // Upgrade vom Einzel-Plan) entfernen, damit kein Lock reaktiviert wird.
    if (isAgency) {
      localStorage.removeItem('complyo_locked_optimization_url');
      localStorage.removeItem('complyo_optimization_mode');
      return;
    }
    const savedUrl = localStorage.getItem('complyo_locked_optimization_url');
    const savedMode = localStorage.getItem('complyo_optimization_mode');
    if (savedUrl && savedMode === 'true' && !isInOptimizationMode) {
      lockForOptimization(savedUrl);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAgency]);

  const handleLock = () => {
    if (!currentWebsite?.url) return;
    lockForOptimization(currentWebsite.url);
    setShowConfirm(false);
    if (onLock) onLock(currentWebsite.url);
  };

  const isCurrentSiteLocked = isInOptimizationMode &&
    lockedOptimizationUrl &&
    currentWebsite?.url &&
    (currentWebsite.url === lockedOptimizationUrl ||
     currentWebsite.url.includes(lockedOptimizationUrl) ||
     lockedOptimizationUrl.includes(currentWebsite.url));

  // Agentur/Expert: gesamtes Single-Domain-Lock-UI ausblenden — jede Seite ist
  // frei optimierbar, ein „dauerhaft verknüpfen"-Hinweis irritiert hier nur.
  if (isAgency) {
    return null;
  }

  if (!currentWebsite?.url || !analysisData) {
    return null;
  }

  const handleBackToOptimization = async () => {
    if (!lockedOptimizationUrl) return;
    setIsLoadingBack(true);
    try {
      const websites = await getTrackedWebsites();
      const lockedWebsite = websites.find((w: any) =>
        w.url === lockedOptimizationUrl ||
        w.url.includes(lockedOptimizationUrl) ||
        lockedOptimizationUrl.includes(w.url)
      );
      if (lockedWebsite) {
        setCurrentWebsite({
          id: String(lockedWebsite.id),
          url: lockedWebsite.url,
          name: lockedWebsite.url,
          lastScan: lockedWebsite.last_scan_date || new Date().toISOString(),
          complianceScore: lockedWebsite.last_score || 0,
          status: 'completed' as const
        });
        updateMetrics({
          totalScore: lockedWebsite.last_score || 0,
          websites: websites.length
        });
      }
      router.push('/');
    } catch {
      router.push('/');
    } finally {
      setIsLoadingBack(false);
    }
  };

  // Andere Seite analysiert während eigene Seite gelockt ist → kompakter Hinweis
  if (isInOptimizationMode && lockedOptimizationUrl && !isCurrentSiteLocked) {
    return (
      <div className="flex items-center justify-between gap-3 px-4 py-2.5 mb-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
        <div className="flex items-center gap-2 min-w-0">
          <Info className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <span className="text-xs text-amber-300 truncate">
            Analyse-Modus — Fixes sind gesperrt für{' '}
            <strong className="text-white">{getShortDomain(lockedOptimizationUrl)}</strong>
          </span>
        </div>
        <button
          onClick={handleBackToOptimization}
          disabled={isLoadingBack}
          className="flex items-center gap-1.5 text-xs text-amber-300 hover:text-white whitespace-nowrap disabled:opacity-60"
        >
          {isLoadingBack ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <ArrowRight className="w-3 h-3 rotate-180" />
          )}
          Zurück zur Optimierung
        </button>
      </div>
    );
  }

  // Eigene gelockte Seite wird angezeigt
  if (isInOptimizationMode && lockedOptimizationUrl && isCurrentSiteLocked) {
    return (
      <Card className="mb-6 bg-gradient-to-r from-emerald-500/10 to-green-500/10 border-emerald-500/30">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-emerald-500/20 rounded-xl">
                <Lock className="w-6 h-6 text-emerald-400" />
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-lg font-bold text-white">Website dauerhaft verknüpft</h3>
                  <Badge variant="success" className="text-xs">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Aktiv
                  </Badge>
                </div>
                <p className="text-sm text-zinc-400">
                  Alle Optimierungen für: <strong className="text-emerald-400">{lockedOptimizationUrl}</strong>
                </p>
                <p className="text-xs text-zinc-500 mt-1">
                  KI-Fixes, Cookie-Compliance und alle Features sind für diese Seite personalisiert.
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-zinc-500">Änderungen nur via Support</p>
              <a
                href="mailto:support@complyo.tech?subject=Website-Änderung"
                className="text-xs text-blue-400 hover:text-blue-300 underline"
              >
                support@complyo.tech
              </a>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Noch nicht im Optimierungsmodus — erst nach Pillar-Interaktion anzeigen
  if (!hasInteracted) {
    return null;
  }

  return (
    <Card className="mb-6 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-blue-500/30">
      <CardContent className="pt-6">
        {!showConfirm ? (
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-500/20 rounded-xl animate-pulse">
                <Globe className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-lg font-bold text-white">Bereit zur Optimierung?</h3>
                  <Badge variant="info" className="text-xs">
                    Analyse abgeschlossen
                  </Badge>
                </div>
                <p className="text-sm text-zinc-400">
                  Sie haben <strong className="text-white">{currentWebsite.url}</strong> analysiert.
                </p>
                <p className="text-xs text-zinc-500 mt-1">
                  Sperren Sie diese Seite, um personalisierte KI-Fixes und Optimierungen zu erhalten.
                </p>
              </div>
            </div>
            <Button
              onClick={() => setShowConfirm(true)}
              className="gap-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
            >
              Zur Optimierung
              <ArrowRight className="w-4 h-4" />
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-red-500/20 rounded-lg flex-shrink-0">
                <AlertTriangle className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <h3 className="font-bold text-white mb-1">Seite dauerhaft verknüpfen?</h3>
                <p className="text-sm text-zinc-300 mb-3">
                  Wenn Sie <strong className="text-blue-400">{currentWebsite.url}</strong> als Ihre Website registrieren:
                </p>
                <ul className="text-sm text-zinc-400 space-y-2 mb-4">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                    Alle KI-Fixes werden für diese Seite personalisiert
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                    Cookie-Compliance wird für diese Domain konfiguriert
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                    Fortschritt wird gespeichert und kann fortgesetzt werden
                  </li>
                  <li className="flex items-center gap-2">
                    <Info className="w-4 h-4 text-blue-400 flex-shrink-0" />
                    Analysen anderer Seiten sind weiterhin möglich
                  </li>
                </ul>
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 mt-3">
                  <p className="text-sm text-amber-300 font-semibold mb-1">Wichtiger Hinweis</p>
                  <p className="text-xs text-amber-300/80">
                    Die Verknüpfung kann <strong>nicht selbstständig</strong> rückgängig gemacht werden.
                    Änderungen sind nur über ein <strong>Support-Ticket</strong> möglich.
                  </p>
                </div>
              </div>
            </div>
            <div className="flex gap-3 justify-end">
              <Button variant="ghost" onClick={() => setShowConfirm(false)}>
                Abbrechen
              </Button>
              <Button
                onClick={handleLock}
                className="gap-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
              >
                <Lock className="w-4 h-4" />
                Verstanden & bestätigen
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default OptimizationModeLock;
