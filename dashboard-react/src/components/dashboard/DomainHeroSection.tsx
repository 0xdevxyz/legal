'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Search, TrendingUp, Bot, Globe, RefreshCw, Lock, Info, X, Zap, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useDashboardStore } from '@/stores/dashboard';
import { analyzeWebsite, getTrackedWebsites, apiClient } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/Toast';
import { useAuth } from '@/contexts/AuthContext';
import { useQueryClient } from '@tanstack/react-query';
import ScanProgressPanel from './ScanProgressPanel';

interface DomainHeroSectionProps {
  onAnalyze?: (url: string) => void;
}

export const DomainHeroSection: React.FC<DomainHeroSectionProps> = ({
  onAnalyze
}) => {
  const { currentWebsite, updateMetrics, setCurrentWebsite, isInOptimizationMode, lockedOptimizationUrl, pendingRescanContext, setPendingRescanContext, analysisData } = useDashboardStore();
  const { showToast } = useToast();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  // Agentur/Expert: kein Single-Domain-Lock-Hinweis (jede Seite frei optimierbar).
  const isAgency = user?.plan_type === 'agency' || user?.plan_type === 'expert';
  const [url, setUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [scanToken, setScanToken] = useState<string | null>(null);
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
        return;
      }
      
      // Website aus der DB laden (Quelle der Wahrheit, /api/v2/websites).
      // Die Scan-/Analyse-Daten lädt WebsiteAnalysis separat über /api/scans/latest
      // (DB) in den Store — es gibt bewusst kein localStorage-Caching mehr.
      try {
        const websites = await getTrackedWebsites();
        if (websites && websites.length > 0) {
          const latestWebsite = websites.find(w => w.is_primary) ?? websites[0];
          setCurrentWebsite({
            id: String(latestWebsite.id),
            url: latestWebsite.url,
            name: latestWebsite.url,
            lastScan: latestWebsite.last_scan_date || latestWebsite.last_scan || new Date().toISOString(),
            complianceScore: latestWebsite.last_score ?? latestWebsite.compliance_score ?? 0,
            status: 'completed' as const
          });
          // Kein totalScore hier: das ist der Score DIESER einen Seite und
          // gehoert an currentWebsite (oben gesetzt), nicht in die
          // Portfolio-Kachel. Die Anzahl kommt aus der Liste, die wir
          // gerade geladen haben — die deckt sich mit dem Server.
          updateMetrics({ websites: websites.length });
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
      // Client erzeugt das Fortschritts-Token — es muss VOR der Anfrage
      // existieren, damit das Panel vom ersten Moment an pollen kann.
      const token =
        typeof crypto !== 'undefined' && 'randomUUID' in crypto
          ? crypto.randomUUID()
          : `scan-${Date.now()}-${Math.floor(Math.random() * 1e6)}`;
      setScanToken(token);
      const result = await analyzeWebsite(domain, legalUpdateId, token);

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

      // Die Kennzahlen-Kacheln zeigen das GESAMTE Portfolio (alle getrackten
      // Websites). Ein einzelner Scan darf sie deshalb nicht ueberschreiben —
      // genau das setzte hier frueher `websites: 1` und liess die Anzeige bei
      // 1/25 stehen, obwohl sechs Seiten getrackt sind. Stattdessen den
      // Server erneut fragen: der neue Scan steckt bereits in der Historie.
      queryClient.invalidateQueries({ queryKey: ['dashboard-metrics'] });

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

  /**
   * Überschrift und Standzeile.
   *
   * Die Aufgabe bleibt konstant ("Lücken schließen"), damit der Einstieg bei
   * jedem Besuch derselbe ist. Nur die zweite Zeile bewegt sich — sie nennt
   * die Zahl, um die es geht. Sind keine Lücken mehr offen, kippt auch die
   * Überschrift: eine Aufforderung zu etwas bereits Erledigtem wäre falsch.
   */
  const opener = (() => {
    if (!currentWebsite) {
      return {
        titel: 'Schließen Sie Ihre Compliance-Lücken',
        stand: 'Fangen Sie mit einer Prüfung an',
      };
    }

    const domain = currentWebsite.name || currentWebsite.url;

    // Solange die Analyse noch nicht da ist, wäre die Issue-Liste leer — daraus
    // "nichts offen" zu machen, wäre eine Falschaussage in der größten Schrift
    // der Seite. Ohne Daten also nur die Domain nennen.
    if (!Array.isArray(analysisData?.issues)) {
      return {
        titel: 'Schließen Sie Ihre Compliance-Lücken',
        stand: `${domain} — Ergebnis wird geladen`,
      };
    }

    const issues = analysisData!.issues as any[];
    const kritisch = issues.filter((i) => i?.severity === 'critical').length;
    const offen = issues.length;

    if (offen === 0) {
      return {
        titel: 'Ihre Compliance-Lücken sind geschlossen',
        stand: `${domain} — nichts offen`,
      };
    }
    if (kritisch > 0) {
      return {
        titel: 'Schließen Sie Ihre Compliance-Lücken',
        stand: `${kritisch} ${kritisch === 1 ? 'kritische Lücke' : 'kritische Lücken'} auf ${domain}`,
      };
    }
    return {
      titel: 'Schließen Sie Ihre Compliance-Lücken',
      stand: `${offen} ${offen === 1 ? 'offener Punkt' : 'offene Punkte'} auf ${domain}`,
    };
  })();

  return (
    // min-h-full statt h-full, damit die Karte darunter mitwachsen darf,
    // wenn der Inhalt mehr Platz braucht als die Nachbarspalte hergibt.
    <div className="min-h-full">
      {/* Hero Section */}
      {/* min-h-full statt h-full: die Karte fuellt die Zeile, darf aber ueber
          sie hinauswachsen. Mit h-full und overflow-hidden verschwand der
          Inhalt, sobald links mehr stand als rechts Platz war — bei einer
          Fehlermeldung fiel die Ueberschrift oben aus dem Bild. */}
      <div className="relative min-h-full glass-strong rounded-3xl p-8 lg:p-12">
        {/* Die Farbverlaeufe brauchen den Beschnitt, damit sie an den runden
            Ecken enden — der Inhalt darueber nicht. */}
        <div className="absolute inset-0 rounded-3xl overflow-hidden pointer-events-none">
          <div className="absolute inset-0 bg-gradient-to-br from-[#25bac8]/10 via-transparent to-[#25bac8]/5 opacity-70"></div>
          <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-[#25bac8]/[0.04] to-transparent"></div>
        </div>

        <div className="relative grid lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] gap-8 lg:gap-10 items-start">
          {/* Left: Domain Input & Info */}
          <div className="space-y-6">
            <div
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold mb-4"
              style={{ background: 'var(--lime-dim)', color: 'var(--lime)' }}
            >
              <Bot className="w-3.5 h-3.5" /> KI-geprüft
            </div>
            {/* Der Opener nennt die Aufgabe, die zweite Zeile den Stand.
                "auf 100% optimieren" stand hier fest verdrahtet: ein Versprechen,
                das das Produkt bewusst nicht gibt (Teile der WCAG brauchen
                menschliches Urteil) und das bei einem Score von 17 zynisch wirkt.
                "Lücken schließen" ist dagegen einlösbar — und wenn keine mehr
                offen ist, sagt die Überschrift genau das. */}
            <h1
              className="text-3xl lg:text-4xl font-black text-gray-900 dark:text-white mb-4 leading-[1.12] tracking-tight"
              style={{ textWrap: 'balance' } as React.CSSProperties}
            >
              {opener.titel}
            </h1>
            {/* Die Standzeile ist Beiwerk, keine zweite Ueberschrift. Frueher
                stand sie fast so gross wie die Ueberschrift und schob den
                eigentlichen Inhalt aus der Karte. */}
            <p
              className="text-lg lg:text-xl font-semibold mb-5 leading-snug"
              style={{ color: 'var(--lime)', textWrap: 'balance' } as React.CSSProperties}
            >
              {opener.stand}
            </p>
            <p className="text-lg text-gray-600 dark:text-zinc-300 leading-relaxed">
              {currentWebsite
                ? 'Jeder Punkt unten ist im Browser nachgemessen, mit Fundstelle und Rechtsgrundlage. Was sich nicht automatisch prüfen lässt, steht als Anleitung dabei.'
                : 'Wir prüfen DSGVO, Cookies, Rechtstexte und Barrierefreiheit im echten Browser — und zeigen jede Fundstelle, statt nur eine Zahl.'}
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
                    <p className="text-xs text-gray-600 dark:text-zinc-400">
                      <strong className="text-emerald-400">{lockedOptimizationUrl}</strong> — 
                      <span className="text-zinc-500 ml-1">Alle KI-Fixes und Optimierungen sind für diese Seite personalisiert.</span>
                    </p>
                  </div>
                  {/* Kein Entsperren-Button - nur Support-Hinweis */}
                  <div className="text-right flex-shrink-0">
                    <p className="text-[10px] text-zinc-500">Änderung nur via</p>
                    <a 
                      href="mailto:support@complyo.de?subject=Website-Änderung"
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
                      className="flex-shrink-0 ml-1 p-1 rounded-lg text-zinc-500 hover:text-zinc-300 hover:bg-gray-200/50 dark:hover:bg-zinc-700/50 transition-colors"
                      aria-label="Hinweis schließen"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
                <div className="flex flex-col sm:flex-row sm:flex-wrap gap-3 w-full">
                <div className="flex-1 min-w-[16rem] relative group">
                  <Globe className="absolute left-5 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-600 dark:text-zinc-400 group-focus-within:text-[#25bac8] transition-colors" />
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

              {/* Live-Ansicht: die realen Pruefgruppen statt Spinner-Blackbox */}
              {isAnalyzing && <ScanProgressPanel url={url.trim() || currentWebsite?.url || ''} token={scanToken} />}

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
                <div className="glass-card rounded-2xl p-4 border border-gray-200/50 dark:border-zinc-700/50 animate-fade-in">
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
                      className="text-gray-700 dark:text-zinc-300 hover:text-gray-900 dark:hover:text-white hover:bg-white/5 rounded-xl disabled:opacity-50"
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
          {/* Oben ausgerichtet: mittig zentriert hing die Vorschau neben dem
              Eingabefeld, waehrend die Ueberschrift darueber ins Leere lief. */}
          <div className="flex items-start justify-center lg:pt-2">
            <div className="relative w-56 h-56 lg:w-72 lg:h-72" aria-hidden="true">
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
              {/* Website-Vorschau: der echte Screenshot der analysierten Site.
                  Der Deko-Haken bleibt nur als Fallback, solange kein Bild da
                  ist — eine Vorschau der EIGENEN Seite sagt "wir haben deine
                  Website wirklich angesehen", ein Icon sagt nichts. */}
              <HeroVorschau url={currentWebsite?.url} />
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
              <h4 className="text-gray-900 dark:text-white font-semibold text-sm">Vier Säulen geprüft</h4>
              <p className="text-xs text-gray-500 dark:text-zinc-400 mt-0.5">DSGVO, Cookies, Rechtstexte, BFSG</p>
            </div>
          </div>
          <div className="flex items-center gap-4 p-4 rounded-2xl glass-card hover:glass-strong transition-all group">
            <div className="p-3.5 rounded-xl group-hover:scale-110 transition-transform" style={{ background: 'var(--lime-dim)' }}>
              <Bot className="w-6 h-6 text-[#25bac8]" />
            </div>
            <div>
              <h4 className="text-gray-900 dark:text-white font-semibold text-sm">Risiko-Radar</h4>
              <p className="text-xs text-gray-500 dark:text-zinc-400 mt-0.5">Meldet neue Pflichten</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};


/**
 * Screenshot der analysierten Website im Hero — geladen ueber das Backend
 * (Auth-Header noetig, daher Blob statt <img src>); Fallback ist der
 * bisherige Schild-Haken.
 */
const HeroVorschau: React.FC<{ url?: string | null }> = ({ url }) => {
  const [bild, setBild] = useState<string | null>(null);

  useEffect(() => {
    let aktiv = true;
    let objektUrl: string | null = null;
    setBild(null);
    if (!url) return;
    apiClient
      .get('/api/v2/site-screenshot', { params: { url }, responseType: 'blob' })
      .then((r) => {
        if (!aktiv) return;
        objektUrl = URL.createObjectURL(r.data as Blob);
        setBild(objektUrl);
      })
      .catch(() => {
        /* kein Screenshot -> Fallback bleibt stehen */
      });
    return () => {
      aktiv = false;
      if (objektUrl) URL.revokeObjectURL(objektUrl);
    };
  }, [url]);

  if (!bild) {
    return (
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="p-7 rounded-[2rem] bg-white/50 dark:bg-zinc-900/50 backdrop-blur-md border border-white/[0.06] shadow-2xl">
          <ShieldCheck className="w-16 h-16 lg:w-20 lg:h-20" style={{ color: 'var(--lime)' }} strokeWidth={1.5} />
        </div>
      </div>
    );
  }

  return (
    <div className="absolute inset-0 flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-2xl overflow-hidden border dark:border-white/10 border-gray-200 shadow-2xl bg-white">
        {/* Browser-Rahmen, damit das Bild als Website lesbar ist */}
        <div className="flex items-center gap-1.5 px-3 py-2 dark:bg-zinc-800 bg-gray-100 border-b dark:border-zinc-700 border-gray-200">
          <span className="w-2.5 h-2.5 rounded-full bg-red-400" />
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
          <span className="w-2.5 h-2.5 rounded-full bg-green-400" />
          <span className="ml-2 text-[10px] truncate dark:text-zinc-400 text-gray-500">{url}</span>
        </div>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={bild} alt={`Vorschau von ${url}`} className="w-full h-auto" />
      </div>
    </div>
  );
};
