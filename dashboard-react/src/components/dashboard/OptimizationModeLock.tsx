'use client';

import React, { useState, useEffect } from 'react';
import { Lock, Globe, ArrowRight, AlertTriangle, CheckCircle, Sparkles, Zap, Info, Loader2 } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useDashboardStore } from '@/stores/dashboard';
import { useRouter } from 'next/navigation';
import { getTrackedWebsites } from '@/lib/api';

interface OptimizationModeLockProps {
  onLock?: (url: string) => void;
  // onUnlock entfernt - Website-Verknüpfung ist DAUERHAFT
}

export const OptimizationModeLock: React.FC<OptimizationModeLockProps> = ({
  onLock
}) => {
  const router = useRouter();
  const { 
    currentWebsite,
    analysisData,
    lockedOptimizationUrl,
    isInOptimizationMode,
    lockForOptimization,
    setCurrentWebsite,
    updateMetrics
    // unlockOptimization entfernt - NICHT mehr verfügbar
  } = useDashboardStore();
  
  const [showConfirm, setShowConfirm] = useState(false);
  const [isLoadingBack, setIsLoadingBack] = useState(false);

  // Restore from localStorage on mount
  useEffect(() => {
    if (typeof localStorage !== 'undefined') {
      const savedUrl = localStorage.getItem('complyo_locked_optimization_url');
      const savedMode = localStorage.getItem('complyo_optimization_mode');
      
      if (savedUrl && savedMode === 'true' && !isInOptimizationMode) {
        lockForOptimization(savedUrl);
      }
    }
  }, []);

  const handleLock = () => {
    if (!currentWebsite?.url) return;
    
    lockForOptimization(currentWebsite.url);
    setShowConfirm(false);
    
    if (onLock) {
      onLock(currentWebsite.url);
    }
  };

  // ⛔ handleUnlock ENTFERNT - Website-Verknüpfung ist DAUERHAFT
  // Änderungen nur über Support-Ticket: support@complyo.tech

  // Prüfe ob aktuelle Website die gelockte ist
  const isCurrentSiteLocked = isInOptimizationMode && 
    lockedOptimizationUrl && 
    currentWebsite?.url && 
    (currentWebsite.url === lockedOptimizationUrl || 
     currentWebsite.url.includes(lockedOptimizationUrl) ||
     lockedOptimizationUrl.includes(currentWebsite.url));

  // Don't show if no website is analyzed
  if (!currentWebsite?.url || !analysisData) {
    return null;
  }

  // ✅ Funktion: Zurück zur Optimierung - Lädt gespeicherte Daten, KEINE neue Analyse
  const handleBackToOptimization = async () => {
    if (!lockedOptimizationUrl) return;
    
    setIsLoadingBack(true);
    
    try {
      // Lade gespeicherte Website-Daten vom Backend
      const websites = await getTrackedWebsites();
      
      // Finde die gelockte Website
      const lockedWebsite = websites.find(w => 
        w.url === lockedOptimizationUrl ||
        w.url.includes(lockedOptimizationUrl) ||
        lockedOptimizationUrl.includes(w.url)
      );
      
      if (lockedWebsite) {
        // ✅ Setze die gespeicherten Daten direkt in den Store
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
      
      // Navigiere zur Hauptseite (ohne URL-Parameter = zeigt gespeicherte Daten)
      router.push('/');
    } catch (error) {
      console.error('Fehler beim Laden der Website-Daten:', error);
      // Fallback: Navigiere trotzdem zur Hauptseite
      router.push('/');
    } finally {
      setIsLoadingBack(false);
    }
  };

  // Bereits im Optimierungsmodus und andere Seite wird angezeigt
  // → Info-Meldung mit prominentem "Zurück zur Optimierung" Button
  if (isInOptimizationMode && lockedOptimizationUrl && !isCurrentSiteLocked) {
    return (
      <Card className="mb-6 bg-gradient-to-r from-amber-500/10 to-orange-500/10 border-amber-500/30">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-amber-500/20 rounded-xl">
                <Info className="w-6 h-6 text-amber-400" />
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-lg font-bold text-white">Nur Analyse-Modus</h3>
                  <Badge variant="warning" className="text-xs">
                    Keine Optimierung möglich
                  </Badge>
                </div>
                <p className="text-sm text-zinc-400">
                  Sie analysieren: <strong className="text-white">{currentWebsite.url}</strong>
                </p>
                <p className="text-xs text-zinc-500 mt-1">
                  Optimierungen sind nur für Ihre registrierte Website verfügbar.
                </p>
              </div>
            </div>
            
            {/* ✅ PROMINENTER "Zurück zur Optimierung" Button */}
            <Button
              onClick={handleBackToOptimization}
              disabled={isLoadingBack}
              className="gap-2 bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-600 hover:to-green-600 text-white font-semibold shadow-lg shadow-emerald-500/25 disabled:opacity-70"
              size="lg"
            >
              {isLoadingBack ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <ArrowRight className="w-5 h-5 rotate-180" />
              )}
              {isLoadingBack ? 'Lädt Daten...' : 'Zurück zur Optimierung'}
            </Button>
          </div>
          
          {/* ✅ Kurzwahl-Leiste */}
          <div className="mt-4 pt-4 border-t border-amber-500/20">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-emerald-400" />
                <span className="text-sm text-zinc-400">
                  Ihre Seite: <strong className="text-emerald-400">{lockedOptimizationUrl}</strong>
                </span>
              </div>
              
              <div className="flex gap-2">
                <Button 
                  size="sm" 
                  variant="ghost" 
                  className="gap-2 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                  onClick={handleBackToOptimization}
                  disabled={isLoadingBack}
                >
                  {isLoadingBack ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
                  KI-Optimierung
                </Button>
                <Button 
                  size="sm" 
                  variant="ghost" 
                  className="gap-2 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
                  onClick={() => router.push('/cookie-compliance')}
                >
                  <Zap className="w-3 h-3" />
                  Cookies
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Im Optimierungsmodus und die richtige Seite wird angezeigt
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
            
            {/* Kein Entsperren-Button mehr - Hinweis auf Support */}
            <div className="text-right">
              <p className="text-xs text-zinc-500">
                Änderungen nur via Support
              </p>
              <a 
                href="mailto:support@complyo.tech?subject=Website-Änderung"
                className="text-xs text-blue-400 hover:text-blue-300 underline"
              >
                support@complyo.tech
              </a>
            </div>
          </div>
          
          {/* Quick Actions for optimization */}
          <div className="mt-4 pt-4 border-t border-emerald-500/20">
            <p className="text-xs text-zinc-400 mb-3">Schnelle Optimierungs-Aktionen:</p>
            <div className="flex flex-wrap gap-2">
              <Button 
                size="sm" 
                variant="secondary" 
                className="gap-2"
                onClick={() => router.push('/cookie-compliance')}
              >
                <Zap className="w-3 h-3" />
                Cookie-Compliance
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Noch nicht im Optimierungsmodus - Übergangs-Prompt anzeigen
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
                
                {/* Wichtiger Warnhinweis */}
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mt-3">
                  <p className="text-sm text-red-300 font-semibold mb-1">
                    ⚠️ Diese Entscheidung ist dauerhaft!
                  </p>
                  <p className="text-xs text-red-300/80">
                    Die Verknüpfung kann <strong>nicht selbstständig</strong> rückgängig gemacht werden. 
                    Änderungen sind nur über ein <strong>Support-Ticket</strong> möglich.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex gap-3 justify-end">
              <Button
                variant="ghost"
                onClick={() => setShowConfirm(false)}
              >
                Abbrechen
              </Button>
              <Button
                onClick={handleLock}
                className="gap-2 bg-red-500 hover:bg-red-600"
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
