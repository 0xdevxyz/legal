'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Search, TrendingUp, Bot, Globe, RefreshCw, Lock, Info, X, Zap, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useDashboardStore } from '@/stores/dashboard';
import { analyzeWebsite, getTrackedWebsites } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/Toast';
import { useAuth } from '@/contexts/AuthContext';

interface DomainHeroSectionProps {
  onAnalyze?: (url: string) => void;
}

export const DomainHeroSection: React.FC<DomainHeroSectionProps> = ({
  onAnalyze
}) => {
  const { currentWebsite, updateMetrics, setCurrentWebsite, isInOptimizationMode, lockedOptimizationUrl, pendingRescanContext, setPendingRescanContext } = useDashboardStore();
  const { showToast } = useToast();
  const { user } = useAuth();
  // Agentur/Expert: kein Single-Domain-Lock-Hinweis (jede Seite frei optimierbar).
  const isAgency = user?.plan_type === 'agency' || user?.plan_type === 'expert';
  const [url, setUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoTriggerInfo, setAutoTriggerInfo] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<{
    message: string;
    details?: string;
    suggestions?: string[];
    reason?: string;
  } | null>(null);
  // v4.0: Hinweis auf erstem Screen (Platzhalter/Baustelle/Grundsystem)
  const [scanNotice, setScanNotice] = useState<{ text: string; cms?: string | null } | null>(null);

  // Store-Listener: Rescan-Kontext von Legal News empfangen
  useEffect(() => {
    if (!pendingRescanContext) return;

    const focusLabel: Record<string, string> = {
      cookies: 'Cookies',
      datenschutz: 'Datenschutz',
      impressum: 'Impressum',
      barrierefreiheit: 'Barrierefreiheit',
    };
    const focusPart = pendingRescanContext.focus_category
      ? ` — Fokus: ${focusLabel[pendingRescanContext.focus_category] ?? pendingRescanContext.focus_category}`
      : '';
    setAutoTriggerInfo(
      `Scan gestartet wegen: "${pendingRescanContext.legal_update_title}"${focusPart}`
    );

    if (currentWebsite?.url) {
      handleAnalyze(currentWebsite.url, pendingRescanContext.legal_update_id);
    }

    setPendingRescanContext(null);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingRescanContext]);

  // ✅ HINWEIS: Auto-Analyse wurde entfernt.
  // "Zurück zur Optimierung" lädt jetzt gespeicherte Daten direkt in den Store
  // statt eine neue Analyse zu starten. Siehe OptimizationQuickNav.tsx und OptimizationModeLock.tsx

  // ✅ Load saved website on mount (nur wenn noch keine Website im Store ist)
  useEffect(() => {
    const loadSavedWebsite = async () => {
      // ✅ Nur laden wenn noch keine Website im Store ist
      if (currentWebsite?.url) {
        console.log('✅ Website bereits im Store geladen:', currentWebsite.url);
        return;
      }
      
      // 1. Versuche localStorage zu laden (nach Refresh)
      if (typeof localStorage !== 'undefined') {
        const savedWebsite = localStorage.getItem('complyo_current_website');
        const savedAnalysis = localStorage.getItem('complyo_last_analysis');
        
        if (savedWebsite) {
          try {
            const website = JSON.parse(savedWebsite);
            const analysisData = savedAnalysis ? JSON.parse(savedAnalysis) : null;
            
            console.log('✅ Lade Website aus localStorage nach Refresh:', website.url);
            setCurrentWebsite(website);
            
            if (analysisData) {
              const { setAnalysisData } = useDashboardStore.getState();
              setAnalysisData(analysisData);
              console.log('✅ Lade Analysedaten aus localStorage');
            }
            return; // Early exit — keine API-Abfrage nötig
          } catch (e) {
            console.error('localStorage parse error:', e);
          }
        }
      }
      
      // 2. Fallback: API abfragen
      try {
        const websites = await getTrackedWebsites();
        if (websites && websites.length > 0) {
          const latestWebsite = websites.find(w => w.is_primary) ?? websites[0];
          console.log('✅ Lade gespeicherte Website:', latestWebsite.url);
          setCurrentWebsite({
            id: String(latestWebsite.id),
            url: latestWebsite.url,
            name: latestWebsite.url,
            lastScan: latestWebsite.last_scan_date || latestWebsite.last_scan || new Date().toISOString(),
            complianceScore: latestWebsite.last_score ?? latestWebsite.compliance_score ?? 0,
            status: 'completed' as const
          });
          updateMetrics({
            totalScore: latestWebsite.last_score ?? latestWebsite.compliance_score ?? 0,
            websites: websites.length
          });
        }
      } catch (error) {
        console.error('Failed to load saved website:', error);
        // Silent fail - user can still scan new websites
      }
    };
    
    loadSavedWebsite();
  }, [currentWebsite?.url, setCurrentWebsite, updateMetrics]);

  const handleAnalyze = async (forceUrl?: string, legalUpdateId?: number) => {
    // FIX: Nutze entweder übergebene URL, url State, oder currentWebsite.url
    const urlToUse = forceUrl || url.trim() || currentWebsite?.url;
    
    if (!urlToUse) {
      setError('Bitte geben Sie eine Domain ein');
      return;
    }

    setError(null);
    setErrorDetails(null);
    setScanNotice(null);
    setIsAnalyzing(true);

    try {
      // Normalize URL - Type-safe check
      if (typeof urlToUse !== 'string') {
        setError('Ungültige URL');
        setIsAnalyzing(false);
        return;
      }
      
      let normalizedUrl = String(urlToUse).trim();
      if (!normalizedUrl) {
        setError('Bitte geben Sie eine Domain ein');
        setIsAnalyzing(false);
        return;
      }
      
      if (typeof normalizedUrl !== 'string' || (!normalizedUrl.startsWith('http://') && !normalizedUrl.startsWith('https://'))) {
        normalizedUrl = 'https://' + normalizedUrl;
      }

      const urlObj = new URL(normalizedUrl);
      const domain = urlObj.hostname;

      // Call API
      const result = await analyzeWebsite(domain, legalUpdateId);

      // Update store with website
      setCurrentWebsite({
        id: Date.now().toString(),
        url: domain,
        name: domain,
        lastScan: new Date().toISOString(),
        complianceScore: result.compliance_score || 0,
        status: 'completed' as const
      });

      // Update store with analysis data (Issues)
      const { setAnalysisData } = useDashboardStore.getState();
      setAnalysisData(result);

      // ✅ v4.0: Hinweis bei nicht-produktiven Seiten (Platzhalter/Baustelle) auf erstem Screen
      if ((result as any)?.scan_notice) {
        setScanNotice({ text: (result as any).scan_notice, cms: (result as any).detected_cms });
      } else {
        setScanNotice(null);
      }

      // Update metrics
      const criticalCount = Array.isArray(result.issues)
        ? result.issues.filter((issue: any) => {
            if (typeof issue === 'string') {
              return issue.toLowerCase().includes('fehlt') || 
                     issue.toLowerCase().includes('nicht gefunden') ||
                     issue.toLowerCase().includes('kritisch');
            }
            return issue.severity === 'critical';
          }).length
        : 0;

      updateMetrics({
        totalScore: result.compliance_score || 0,
        criticalIssues: criticalCount,
        websites: 1
      });

      // Call optional callback
      if (onAnalyze) {
        onAnalyze(domain);
      }

      setUrl('');
    } catch (err: any) {
      console.error('Analysis failed:', err);
      
      // ✅ Parse detailed error from backend
      if (err?.response?.data?.detail) {
        const errorDetail = err.response.data.detail;
        
        // Check if it's a structured error (object with message, details, suggestions)
        if (typeof errorDetail === 'object' && errorDetail.message) {
          setError(errorDetail.message);
          setErrorDetails({
            message: errorDetail.message,
            details: errorDetail.details,
            suggestions: errorDetail.suggestions,
            reason: errorDetail.reason,
          });
        } else if (typeof errorDetail === 'string') {
          setError(errorDetail);
        } else {
          setError('Website konnte nicht analysiert werden');
        }
      } else {
        setError(err instanceof Error ? err.message : 'Analyse fehlgeschlagen');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };


  return (
    <div className="h-full">
      {/* Hero Section */}
      <div className="relative h-full glass-strong rounded-3xl p-8 lg:p-12 overflow-hidden">
        {/* Animated Background Gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-[#25bac8]/10 via-transparent to-[#25bac8]/5 opacity-70"></div>
        <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-[#25bac8]/[0.04] to-transparent"></div>

        <div className="relative grid lg:grid-cols-2 gap-10 items-center">
          {/* Left: Domain Input & Info */}
          <div className="space-y-6">
            <div
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold mb-4"
              style={{ background: 'var(--lime-dim)', color: 'var(--lime)' }}
            >
              <Bot className="w-3.5 h-3.5" /> KI-geprüft
            </div>
            <h1 className="text-4xl lg:text-5xl font-black text-gray-900 dark:text-white mb-5 leading-[1.05] tracking-tight">
              Website-Compliance
              <span className="block mt-2" style={{ color: 'var(--lime)' }}>
                auf 100% optimieren
              </span>
            </h1>
            <p className="text-lg text-gray-600 dark:text-zinc-300 leading-relaxed">
              KI-gestützte Analyse & automatische Optimierung für DSGVO, BFSG & TTDSG
            </p>

            {/* Domain Input */}
            <div className="space-y-4">
              {/* ✅ Hinweis: Website ist dauerhaft verknüpft - KEIN Entsperren möglich */}
              {!isAgency && isInOptimizationMode && lockedOptimizationUrl && (
                <div className="flex items-center gap-3 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl">
                  <Lock className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold text-emerald-300">Ihre registrierte Website:</span>
                      <Badge variant="success" className="text-xs">Dauerhaft verknüpft</Badge>
                    </div>
                    <p className="text-xs text-zinc-400">
                      <strong className="text-emerald-400">{lockedOptimizationUrl}</strong> — 
                      <span className="text-zinc-500 ml-1">Alle KI-Fixes und Optimierungen sind für diese Seite personalisiert.</span>
                    </p>
                  </div>
                  {/* Kein Entsperren-Button - nur Support-Hinweis */}
                  <div className="text-right flex-shrink-0">
                    <p className="text-[10px] text-zinc-500">Änderung nur via</p>
                    <a 
                      href="mailto:support@complyo.tech?subject=Website-Änderung"
                      className="text-xs text-blue-400 hover:text-blue-300"
                    >
                      Support
                    </a>
                  </div>
                </div>
              )}
              
              <div className="flex flex-col sm:flex-row gap-3">
                {autoTriggerInfo && (
                  <div className="w-full flex items-start gap-3 glass-card border border-sky-500/30 rounded-2xl px-4 py-3 mb-1 animate-fade-in">
                    <div className="flex-shrink-0 p-1.5 bg-sky-500/20 rounded-lg mt-0.5">
                      <Zap className="w-3.5 h-3.5 text-sky-400" />
                    </div>
                    <p className="text-sm text-sky-300 flex-1 leading-snug">{autoTriggerInfo}</p>
                    <button
                      onClick={() => setAutoTriggerInfo(null)}
                      className="flex-shrink-0 ml-1 p-1 rounded-lg text-zinc-500 hover:text-zinc-300 hover:bg-zinc-700/50 transition-colors"
                      aria-label="Hinweis schließen"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
                <div className="flex flex-col sm:flex-row gap-3 w-full">
                <div className="flex-1 relative group">
                  <Globe className="absolute left-5 top-1/2 transform -translate-y-1/2 h-5 w-5 text-zinc-400 group-focus-within:text-[#25bac8] transition-colors" />
                  <label htmlFor="website-url-input" className="sr-only">Website-URL eingeben</label>
                  <input
                    type="text"
                    id="website-url-input"
                    value={url}
                    onChange={(e) => {
                      setUrl(e.target.value);
                      setError(null);
                      setErrorDetails(null);
                    }}
                    onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
                    placeholder="ihre-domain.de eingeben"
                    aria-label="Website-URL zur Compliance-Analyse eingeben"
                    className="w-full pl-14 pr-5 py-4 bg-white dark:bg-zinc-900/50 backdrop-blur-sm border-2 border-gray-200 dark:border-zinc-700/50 rounded-2xl text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-[#25bac8]/50 focus:border-[#25bac8]/50 text-lg transition-all shadow-sm dark:shadow-none"
                    disabled={isAnalyzing}
                  />
                </div>
                <Button
                  size="lg"
                  onClick={() => handleAnalyze()}
                  disabled={isAnalyzing || !url.trim()}
                  className="bg-[#25bac8] hover:bg-[#45d6e2] text-zinc-950 font-bold px-8 py-6 text-lg shadow-lg shadow-[#25bac8]/25 hover:shadow-xl hover:shadow-[#25bac8]/30 transition-all rounded-2xl disabled:opacity-40"
                >
                  {isAnalyzing ? (
                    <>
                      <RefreshCw className="mr-2 h-5 w-5 animate-spin" />
                      Analysiere...
                    </>
                  ) : (
                    <>
                      <Search className="mr-2 h-5 w-5" />
                      Analysieren
                    </>
                  )}
                </Button>
              </div>
              </div>

              {/* ✅ v4.0: Hinweis bei Platzhalter-/Baustellenseiten (Scan erfolgreich, aber nicht produktiv) */}
              {scanNotice && (
                <div className="bg-amber-500/10 backdrop-blur-sm border border-amber-500/30 rounded-2xl p-5 animate-slide-down">
                  <div className="flex items-start gap-3">
                    <div className="bg-amber-500/20 rounded-xl p-2 flex-shrink-0">
                      <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M5 19h14a2 2 0 001.84-2.75L13.74 4a2 2 0 00-3.48 0L3.16 16.25A2 2 0 005 19z" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h3 className="text-amber-200 font-semibold mb-1 flex items-center gap-2 flex-wrap">
                        Aktuell nicht vollständig prüfbar
                        {scanNotice.cms && (
                          <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-100">
                            Grundsystem: {scanNotice.cms}
                          </span>
                        )}
                      </h3>
                      <p className="text-amber-100/90 text-sm leading-relaxed">{scanNotice.text}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Error Message */}
              {error && (
                <div className="bg-red-500/10 backdrop-blur-sm border border-red-500/30 rounded-2xl p-5 animate-slide-down">
                  <div className="flex items-start gap-3">
                    <div className="bg-red-500/20 rounded-xl p-2 flex-shrink-0">
                      <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h3 className="text-red-200 font-semibold mb-1">
                        {errorDetails?.reason === 'maintenance' ? 'Aktuell nicht prüfbar (Wartung)'
                          : errorDetails?.reason === 'blocked' ? 'Zugriff blockiert'
                          : errorDetails?.reason === 'not_found' ? 'Seite nicht gefunden'
                          : 'Website nicht erreichbar'}
                      </h3>
                      <p className="text-red-300/80 text-sm mb-3">{error}</p>
                      
                      {errorDetails && (
                        <>
                          {errorDetails.details && (
                            <div className="bg-red-900/30 rounded-lg p-3 mb-3">
                              <p className="text-red-100 text-sm font-mono">{errorDetails.details}</p>
                            </div>
                          )}
                          
                          {errorDetails.suggestions && errorDetails.suggestions.length > 0 && (
                            <div>
                              <p className="text-red-100 font-medium mb-2 text-sm">💡 Lösungsvorschläge:</p>
                              <ul className="space-y-1">
                                {errorDetails.suggestions.map((suggestion, idx) => (
                                  <li key={idx} className="text-red-200 text-sm flex items-start">
                                    <span className="mr-2">•</span>
                                    <span>{suggestion}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Current Website Info */}
              {currentWebsite && !isAnalyzing && (
                <div className="glass-card rounded-2xl p-4 border border-zinc-700/50 animate-fade-in">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'var(--lime-dim)' }}>
                        <Globe className="w-5 h-5" style={{ color: 'var(--lime)' }} />
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 dark:text-zinc-400 mb-0.5">Aktuell analysiert</p>
                        <p className="text-sm font-semibold text-gray-900 dark:text-white">{currentWebsite.name}</p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleAnalyze(currentWebsite?.url)}
                      disabled={isAnalyzing || !currentWebsite?.url}
                      className="text-zinc-300 hover:text-white hover:bg-white/5 rounded-xl disabled:opacity-50"
                    >
                      <RefreshCw className={`w-4 h-4 mr-2 ${isAnalyzing ? 'animate-spin' : ''}`} />
                      {isAnalyzing ? 'Scanne...' : 'Erneut scannen'}
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right: compliance visual — score lives in the ComplianceGauge cluster.
              [3D-VISUAL-SLOT] replaced by a generated lime-glass render in phase 4. */}
          <div className="flex items-center justify-center">
            <div className="relative w-64 h-64 lg:w-80 lg:h-80" aria-hidden="true">
              {/* lime glow */}
              <div className="absolute inset-0 rounded-full blur-3xl" style={{ background: 'rgba(37,186,200,0.14)' }} />
              {/* core gradient orb */}
              <div
                className="absolute inset-6 rounded-full"
                style={{ background: 'radial-gradient(circle at 35% 30%, rgba(37,186,200,0.45), rgba(37,186,200,0.05) 58%, transparent 72%)' }}
              />
              {/* concentric rings */}
              <div className="absolute inset-2 rounded-full border border-[#25bac8]/25 animate-pulse" />
              <div className="absolute inset-12 rounded-full border border-[#25bac8]/15 animate-pulse" style={{ animationDelay: '0.2s' }} />
              <div className="absolute inset-20 rounded-full border border-[#25bac8]/10 animate-pulse" style={{ animationDelay: '0.4s' }} />
              {/* center mark */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="p-7 rounded-[2rem] bg-zinc-900/50 backdrop-blur-md border border-white/[0.06] shadow-2xl">
                  <ShieldCheck className="w-16 h-16 lg:w-20 lg:h-20" style={{ color: 'var(--lime)' }} strokeWidth={1.5} />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Features Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-10 pt-8 border-t border-white/5">
          <div className="flex items-center gap-4 p-4 rounded-2xl glass-card hover:glass-strong transition-all group">
            <div className="p-3.5 rounded-xl group-hover:scale-110 transition-transform" style={{ background: 'var(--lime-dim)' }}>
              <TrendingUp className="w-6 h-6 text-[#25bac8]" />
            </div>
            <div>
              <h4 className="text-gray-900 dark:text-white font-semibold text-sm">KI-gestützt</h4>
              <p className="text-xs text-gray-500 dark:text-zinc-400 mt-0.5">Automatische Optimierung</p>
            </div>
          </div>
          <div className="flex items-center gap-4 p-4 rounded-2xl glass-card hover:glass-strong transition-all group">
            <div className="p-3.5 rounded-xl group-hover:scale-110 transition-transform" style={{ background: 'var(--lime-dim)' }}>
              <Globe className="w-6 h-6 text-[#25bac8]" />
            </div>
            <div>
              <h4 className="text-gray-900 dark:text-white font-semibold text-sm">20+ Prüfpunkte</h4>
              <p className="text-xs text-gray-500 dark:text-zinc-400 mt-0.5">DSGVO, BFSG, TTDSG</p>
            </div>
          </div>
          <div className="flex items-center gap-4 p-4 rounded-2xl glass-card hover:glass-strong transition-all group">
            <div className="p-3.5 rounded-xl group-hover:scale-110 transition-transform" style={{ background: 'var(--lime-dim)' }}>
              <Bot className="w-6 h-6 text-[#25bac8]" />
            </div>
            <div>
              <h4 className="text-gray-900 dark:text-white font-semibold text-sm">Risiko-Radar</h4>
              <p className="text-xs text-gray-500 dark:text-zinc-400 mt-0.5">Bei 100% Compliance</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

