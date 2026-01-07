'use client';

import React, { useState, useEffect } from 'react';
import { Search, TrendingUp, Bot, Globe, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useDashboardStore } from '@/stores/dashboard';
import { analyzeWebsite, getTrackedWebsites } from '@/lib/api';

interface DomainHeroSectionProps {
  onAnalyze?: (url: string) => void;
}

export const DomainHeroSection: React.FC<DomainHeroSectionProps> = ({
  onAnalyze
}) => {
  const { currentWebsite, metrics, updateMetrics, setCurrentWebsite } = useDashboardStore();
  const [url, setUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<{
    message: string;
    details?: string;
    suggestions?: string[];
  } | null>(null);

  const score = currentWebsite?.complianceScore ?? metrics.totalScore ?? 0;

  // ✅ AUTO-TRIGGER SCAN bei URL-Parametern (von Legal Updates)
  useEffect(() => {
    const checkAutoTrigger = () => {
      // ✅ SSR-Check
      if (typeof window === 'undefined' || typeof document === 'undefined') return;
      
      const params = new URLSearchParams(window.location.search);
      const triggerScan = params.get('trigger_scan');
      const legalUpdateId = params.get('legal_update_id');
      const legalContext = params.get('legal_context');
      const focus = params.get('focus');
      
      if (triggerScan === 'true') {
        console.log('🔍 Auto-Trigger Scan von Legal Update:', {
          legalUpdateId,
          legalContext,
          focus
        });
        
        // Zeige Hinweis
        const contextMsg = legalContext ? `\n\nWegen Gesetzesänderung: "${decodeURIComponent(legalContext)}"` : '';
        const focusMsg = focus ? `\n\nFokus: ${focus}` : '';
        
        alert(`🔍 Website-Scan wird vorbereitet...${contextMsg}${focusMsg}\n\nBitte geben Sie Ihre Website-URL ein und starten Sie den Scan.`);
        
        // URL-Parameter entfernen (damit nicht bei jedem Reload getriggert wird)
        window.history.replaceState({}, document.title, window.location.pathname);
        
        // Scroll zur URL-Eingabe
        const urlInput = document.querySelector('input[type="text"]') as HTMLInputElement;
        if (urlInput) {
          urlInput.focus();
          urlInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    };
    
    checkAutoTrigger();
  }, []);

  // ✅ Load saved website on mount (nur wenn noch keine Website im Store ist)
  useEffect(() => {
    const loadSavedWebsite = async () => {
      // ✅ Nur laden wenn noch keine Website im Store ist
      if (currentWebsite?.url) {
        console.log('✅ Website bereits im Store geladen:', currentWebsite.url);
        return;
      }
      
      try {
        const websites = await getTrackedWebsites();
        if (websites && websites.length > 0) {
          const latestWebsite = websites[0]; // Get most recent website
          console.log('✅ Lade gespeicherte Website:', latestWebsite.url);
          setCurrentWebsite({
            id: String(latestWebsite.id),
            url: latestWebsite.url,
            name: latestWebsite.url,
            lastScan: latestWebsite.last_scan || new Date().toISOString(),
            complianceScore: latestWebsite.compliance_score || 0,
            status: 'completed' as const
          });
          updateMetrics({
            totalScore: latestWebsite.compliance_score || 0,
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

  const handleAnalyze = async (forceUrl?: string) => {
    // ✅ FIX: Nutze entweder übergebene URL, url State, oder currentWebsite.url
    const urlToUse = forceUrl || url.trim() || currentWebsite?.url;
    
    if (!urlToUse) {
      setError('Bitte geben Sie eine Domain ein');
      return;
    }

    setError(null);
    setErrorDetails(null);
    setIsAnalyzing(true);

    try {
      // Normalize URL
      let normalizedUrl = urlToUse;
      if (!normalizedUrl.startsWith('http://') && !normalizedUrl.startsWith('https://')) {
        normalizedUrl = 'https://' + normalizedUrl;
      }

      const urlObj = new URL(normalizedUrl);
      const domain = urlObj.hostname;

      // Call API
      const result = await analyzeWebsite(domain);

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
            suggestions: errorDetail.suggestions
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


  const getScoreColor = (score: number): string => {
    if (score >= 90) return 'text-green-400';
    if (score >= 70) return 'text-yellow-400';
    if (score >= 50) return 'text-orange-400';
    return 'text-red-400';
  };

  const getScoreGradient = (score: number): string => {
    if (score >= 90) return 'from-green-500 to-emerald-600';
    if (score >= 70) return 'from-yellow-500 to-orange-500';
    if (score >= 50) return 'from-orange-500 to-red-500';
    return 'from-red-500 to-red-700';
  };

  return (
    <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Hero Section */}
      <div className="relative glass-strong rounded-3xl p-8 lg:p-14 overflow-hidden">
        {/* Animated Background Gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-sky-500/10 via-purple-500/10 to-indigo-500/10 opacity-50"></div>
        <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-sky-500/5 to-transparent animate-gradient bg-[length:200%_200%]"></div>
        
        <div className="relative grid lg:grid-cols-2 gap-10 items-center">
          {/* Left: Domain Input & Info */}
          <div className="space-y-6">
            <h1 className="text-4xl lg:text-5xl font-bold text-white mb-6 leading-tight tracking-tight">
              Website-Compliance
              <span className="block mt-2 bg-gradient-to-r from-sky-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
                auf 100% optimieren
              </span>
            </h1>
            <p className="text-lg text-zinc-300 leading-relaxed">
              KI-gestützte Analyse & automatische Optimierung für DSGVO, BFSG & TTDSG
            </p>

            {/* Domain Input */}
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="flex-1 relative group">
                  <Globe className="absolute left-5 top-1/2 transform -translate-y-1/2 h-5 w-5 text-zinc-400 group-focus-within:text-sky-400 transition-colors" />
                  <input
                    type="text"
                    value={url}
                    onChange={(e) => {
                      setUrl(e.target.value);
                      setError(null);
                      setErrorDetails(null);
                    }}
                    onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
                    placeholder="ihre-domain.de eingeben"
                    className="w-full pl-14 pr-5 py-4 bg-zinc-900/50 backdrop-blur-sm border-2 border-zinc-700/50 rounded-2xl text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-sky-500/50 focus:border-sky-500/50 text-lg transition-all"
                    disabled={isAnalyzing}
                  />
                </div>
                <Button
                  size="lg"
                  onClick={handleAnalyze}
                  disabled={isAnalyzing || !url.trim()}
                  className="bg-gradient-to-r from-sky-500 to-purple-500 hover:from-sky-600 hover:to-purple-600 text-white font-semibold px-8 py-6 text-lg shadow-lg shadow-sky-500/25 hover:shadow-xl hover:shadow-sky-500/40 transition-all rounded-2xl disabled:opacity-40"
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
                      <h3 className="text-red-200 font-semibold mb-1">Website nicht erreichbar</h3>
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
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-500/20 to-purple-500/20 flex items-center justify-center">
                        <Globe className="w-5 h-5 text-sky-400" />
                      </div>
                      <div>
                        <p className="text-xs text-zinc-400 mb-0.5">Aktuell analysiert</p>
                        <p className="text-sm font-semibold text-white">{currentWebsite.name}</p>
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

          {/* Right: Score Display & CTA */}
          <div className="flex flex-col items-center justify-center">
            {currentWebsite ? (
              <>
                {/* Score Display */}
                <div className="relative mb-10">
                  {/* Circular Progress mit Glassmorphism */}
                  <div className="relative w-72 h-72">
                    {/* Glow Effect */}
                    <div className="absolute inset-0 bg-gradient-to-br from-sky-500/20 to-purple-500/20 rounded-full blur-2xl"></div>
                    
                    <svg className="w-full h-full transform -rotate-90 relative z-10">
                      {/* Background Circle */}
                      <circle
                        cx="144"
                        cy="144"
                        r="120"
                        stroke="rgba(255,255,255,0.05)"
                        strokeWidth="20"
                        fill="none"
                      />
                      {/* Progress Circle */}
                      <circle
                        cx="144"
                        cy="144"
                        r="120"
                        stroke="url(#scoreGradient)"
                        strokeWidth="20"
                        fill="none"
                        strokeDasharray={`${(score / 100) * 753.98} 753.98`}
                        strokeLinecap="round"
                        className="transition-all duration-1000 ease-out drop-shadow-lg"
                      />
                      <defs>
                        <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor={score >= 90 ? '#10B981' : score >= 70 ? '#FBBF24' : '#EF4444'} />
                          <stop offset="100%" stopColor={score >= 90 ? '#059669' : score >= 70 ? '#F97316' : '#DC2626'} />
                        </linearGradient>
                      </defs>
                    </svg>

                    {/* Score Number */}
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <div className="text-xs text-zinc-500 uppercase tracking-wider mb-2">
                        {currentWebsite.url}
                      </div>
                      <div className={`text-7xl font-black ${getScoreColor(score)} tracking-tight`}>
                        {score}
                      </div>
                      <div className="text-2xl text-zinc-400 font-light">/100</div>
                      <div className="text-sm text-zinc-500 mt-1 font-medium">Compliance-Score</div>
                    </div>
                  </div>
                </div>

                {/* Score Info Text */}
                {score < 100 ? (
                  <p className="text-sm text-zinc-400 mt-5 text-center">
                    Noch <strong className="text-white font-semibold">{100 - score} Punkte</strong> bis zum Abmahnschutz
                  </p>
                ) : (
                  <div className="flex items-center gap-2 text-green-400 mt-5">
                    <TrendingUp className="w-5 h-5" />
                    <p className="text-sm font-semibold">100% Compliance erreicht!</p>
                  </div>
                )}
              </>
            ) : (
              /* Empty State */
              <div className="text-center py-12">
                <div className="w-56 h-56 mx-auto mb-8 relative">
                  <div className="absolute inset-0 bg-gradient-to-br from-sky-500/10 to-purple-500/10 rounded-full animate-pulse"></div>
                  <div className="absolute inset-6 bg-gradient-to-br from-sky-500/5 to-purple-500/5 rounded-full animate-pulse delay-75"></div>
                  <div className="absolute inset-12 bg-gradient-to-br from-sky-500/5 to-purple-500/5 rounded-full animate-pulse delay-150"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="p-6 bg-zinc-900/50 rounded-full backdrop-blur-sm">
                      <Globe className="w-20 h-20 text-zinc-600" />
                    </div>
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">
                  Bereit für Ihre erste Analyse?
                </h3>
                <p className="text-zinc-400 text-sm">
                  Geben Sie oben eine Domain ein, um zu starten
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Features Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-10 pt-8 border-t border-white/5">
          <div className="flex items-center gap-4 p-4 rounded-2xl glass-card hover:glass-strong transition-all group">
            <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 p-3.5 rounded-xl group-hover:scale-110 transition-transform">
              <TrendingUp className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <h4 className="text-white font-semibold text-sm">KI-gestützt</h4>
              <p className="text-xs text-zinc-400 mt-0.5">Automatische Optimierung</p>
            </div>
          </div>
          <div className="flex items-center gap-4 p-4 rounded-2xl glass-card hover:glass-strong transition-all group">
            <div className="bg-gradient-to-br from-sky-500/20 to-blue-500/20 p-3.5 rounded-xl group-hover:scale-110 transition-transform">
              <Globe className="w-6 h-6 text-sky-400" />
            </div>
            <div>
              <h4 className="text-white font-semibold text-sm">20+ Prüfpunkte</h4>
              <p className="text-xs text-zinc-400 mt-0.5">DSGVO, BFSG, TTDSG</p>
            </div>
          </div>
          <div className="flex items-center gap-4 p-4 rounded-2xl glass-card hover:glass-strong transition-all group">
            <div className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 p-3.5 rounded-xl group-hover:scale-110 transition-transform">
              <Bot className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h4 className="text-white font-semibold text-sm">Abmahnschutz</h4>
              <p className="text-xs text-zinc-400 mt-0.5">Bei 100% Compliance</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

