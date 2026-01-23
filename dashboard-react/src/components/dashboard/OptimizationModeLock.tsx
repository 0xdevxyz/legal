'use client';

import React, { useState, useEffect } from 'react';
import { Lock, Unlock, Globe, ArrowRight, AlertTriangle, CheckCircle, Sparkles, Zap, Info } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useDashboardStore } from '@/stores/dashboard';
import { useRouter } from 'next/navigation';

interface OptimizationModeLockProps {
  onLock?: (url: string) => void;
  onUnlock?: () => void;
}

export const OptimizationModeLock: React.FC<OptimizationModeLockProps> = ({
  onLock,
  onUnlock
}) => {
  const router = useRouter();
  const { 
    currentWebsite,
    analysisData,
    lockedOptimizationUrl,
    isInOptimizationMode,
    lockForOptimization,
    unlockOptimization
  } = useDashboardStore();
  
  const [showConfirm, setShowConfirm] = useState(false);

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

  const handleUnlock = () => {
    unlockOptimization();
    
    if (onUnlock) {
      onUnlock();
    }
  };

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

  // Bereits im Optimierungsmodus und andere Seite wird angezeigt
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
                  Optimierungen sind nur für <strong className="text-emerald-400">{lockedOptimizationUrl}</strong> verfügbar.
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={handleUnlock}
                className="gap-2 border-zinc-600 hover:bg-zinc-800"
              >
                <Unlock className="w-4 h-4" />
                Entsperren & wechseln
              </Button>
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
                  <h3 className="text-lg font-bold text-white">Optimierungsmodus aktiv</h3>
                  <Badge variant="success" className="text-xs">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Gelockt
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
            
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={handleUnlock}
                className="gap-2 border-zinc-600 hover:bg-zinc-800"
              >
                <Unlock className="w-4 h-4" />
                Entsperren
              </Button>
            </div>
          </div>
          
          {/* Quick Actions for optimization */}
          <div className="mt-4 pt-4 border-t border-emerald-500/20">
            <p className="text-xs text-zinc-400 mb-3">Schnelle Optimierungs-Aktionen:</p>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" variant="secondary" className="gap-2">
                <Sparkles className="w-3 h-3" />
                KI-Optimierung starten
              </Button>
              <Button 
                size="sm" 
                variant="ghost" 
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
              <div className="p-2 bg-amber-500/20 rounded-lg flex-shrink-0">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <h3 className="font-bold text-white mb-1">Seite für Optimierung sperren?</h3>
                <p className="text-sm text-zinc-300 mb-3">
                  Wenn Sie <strong className="text-blue-400">{currentWebsite.url}</strong> für die Optimierung sperren:
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
                  <li className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                    Optimierungen für andere Seiten erst nach Entsperren
                  </li>
                </ul>
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
                className="gap-2 bg-emerald-500 hover:bg-emerald-600"
              >
                <Lock className="w-4 h-4" />
                Seite sperren & optimieren
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default OptimizationModeLock;
