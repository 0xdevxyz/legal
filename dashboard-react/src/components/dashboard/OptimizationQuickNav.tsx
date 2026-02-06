'use client';

import React, { useState } from 'react';
import { Lock, ArrowRight, Sparkles, Settings, Home, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useDashboardStore } from '@/stores/dashboard';
import { useRouter, usePathname } from 'next/navigation';
import { getTrackedWebsites } from '@/lib/api';

/**
 * OptimizationQuickNav
 * 
 * Persistente Kurzwahl-Leiste, die am oberen Rand angezeigt wird,
 * wenn eine Website gelockt ist. Ermöglicht schnellen Zugriff auf:
 * - Zurück zur Optimierung (gelockte Seite mit gespeicherten Stats)
 * - Cookie-Compliance
 * - Dashboard Home
 */
export const OptimizationQuickNav: React.FC = () => {
  const router = useRouter();
  const pathname = usePathname();
  const [isLoading, setIsLoading] = useState(false);
  const { 
    currentWebsite,
    lockedOptimizationUrl,
    isInOptimizationMode,
    setCurrentWebsite,
    updateMetrics
  } = useDashboardStore();

  // Prüfe ob aktuelle Website die gelockte ist
  const isCurrentSiteLocked = isInOptimizationMode && 
    lockedOptimizationUrl && 
    currentWebsite?.url && 
    (currentWebsite.url === lockedOptimizationUrl || 
     currentWebsite.url.includes(lockedOptimizationUrl) ||
     lockedOptimizationUrl.includes(currentWebsite.url));

  // Zeige nur wenn:
  // 1. Im Optimierungsmodus
  // 2. Eine URL gelockt ist
  // 3. NICHT auf der gelockten Seite (oder auf einer Unterseite)
  const showQuickNav = isInOptimizationMode && 
    lockedOptimizationUrl && 
    !isCurrentSiteLocked;

  if (!showQuickNav) {
    return null;
  }

  // ✅ Lade gespeicherte Website-Daten und zeige Optimierungsansicht
  const handleBackToOptimization = async () => {
    setIsLoading(true);
    
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
        
        // Navigiere zur Hauptseite (ohne URL-Parameter = keine neue Analyse)
        router.push('/');
      } else {
        // Fallback: Navigiere trotzdem zur Hauptseite
        router.push('/');
      }
    } catch (error) {
      console.error('Fehler beim Laden der Website-Daten:', error);
      // Fallback: Navigiere zur Hauptseite
      router.push('/');
    } finally {
      setIsLoading(false);
    }
  };

  // Extrahiere Domain für kompakte Anzeige
  const getShortDomain = (url: string) => {
    try {
      const domain = new URL(url.startsWith('http') ? url : `https://${url}`).hostname;
      return domain.replace('www.', '');
    } catch {
      return url;
    }
  };

  return (
    <div className="sticky top-0 z-50 bg-gradient-to-r from-emerald-900/95 to-green-900/95 backdrop-blur-sm border-b border-emerald-500/30 shadow-lg">
      <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-12 gap-4">
          {/* Left: Locked Website Info */}
          <div className="flex items-center gap-3 min-w-0">
            <div className="flex items-center gap-2 text-emerald-300">
              <Lock className="w-4 h-4 flex-shrink-0" />
              <span className="text-sm font-medium hidden sm:inline">Ihre Seite:</span>
            </div>
            <span className="text-sm font-bold text-white truncate max-w-[200px]">
              {getShortDomain(lockedOptimizationUrl)}
            </span>
          </div>

          {/* Center: Status Info (optional auf breiteren Screens) */}
          <div className="hidden md:flex items-center gap-2 text-xs text-emerald-300/70">
            <span>Sie analysieren eine andere Seite</span>
          </div>

          {/* Right: Quick Actions */}
          <div className="flex items-center gap-2">
            {/* Zurück zur Optimierung - HAUPT-BUTTON */}
            <Button
              onClick={handleBackToOptimization}
              size="sm"
              disabled={isLoading}
              className="gap-2 bg-white text-emerald-900 hover:bg-emerald-50 font-semibold shadow-md disabled:opacity-70"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <ArrowRight className="w-4 h-4 rotate-180" />
              )}
              <span className="hidden sm:inline">{isLoading ? 'Lädt...' : 'Zurück zur Optimierung'}</span>
              <span className="sm:hidden">{isLoading ? '...' : 'Optimierung'}</span>
            </Button>

            {/* Cookie-Compliance Link */}
            <Button
              onClick={() => router.push('/cookie-compliance')}
              size="sm"
              variant="ghost"
              className="gap-1.5 text-emerald-200 hover:text-white hover:bg-emerald-800/50"
            >
              <Settings className="w-4 h-4" />
              <span className="hidden lg:inline">Cookies</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OptimizationQuickNav;
