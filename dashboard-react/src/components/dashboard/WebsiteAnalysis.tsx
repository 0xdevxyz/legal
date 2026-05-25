'use client';

import React, { useState, useRef, useEffect as useEffectAlias } from 'react';
import { Globe, RefreshCw, AlertTriangle, AlertCircle, CheckCircle, Bot, Download, Eye, Shield, FileText, Cookie, ChevronDown, ListChecks, Lock } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useQueryClient } from '@tanstack/react-query';
import { useDashboardStore } from '@/stores/dashboard';
import { useStartAIFix, useBookExpert, useComplianceAnalysis, useLatestScan, useActiveFixJobs } from '@/hooks/useCompliance';
import { formatRelativeTime } from '@/lib/utils';
import { SkeletonWebsiteAnalysis } from '@/components/ui/Skeleton';
import { ScoreAnimation, SuccessAnimation } from '@/components/ui/SuccessAnimation';
import type { ComplianceIssue } from '@/types/api';
import { ComplianceIssueCard } from './ComplianceIssueCard';
import { ComplianceIssueGroup } from './ComplianceIssueGroup';
import { ActiveJobsPanel } from './ActiveJobsPanel';
import { useAuth } from '@/contexts/AuthContext';
import { WidgetIntegrationCard } from '@/components/accessibility';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import TCFComplianceWidget from './TCFComplianceWidget';
import { generateSiteId, isScanHash } from '@/lib/siteIdUtils';
import { OptimizationModeLock } from './OptimizationModeLock';
import { ComplianceWizard } from './ComplianceWizard';
import QuickWins from './QuickWins';
import apiClient from '@/lib/api';

export const WebsiteAnalysis: React.FC = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const { currentWebsite, analysisData: storedAnalysisData, setAnalysisData, isInOptimizationMode, lockedOptimizationUrl } = useDashboardStore();
  const [expandedPillar, setExpandedPillar] = useState<string | null>(null);
  const [showScoreAnimation, setShowScoreAnimation] = useState(false);
  const [previousScore, setPreviousScore] = useState<number | null>(null);
  const [showWizard, setShowWizard] = useState(false);
  const pillarRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const rawPlanType = user?.plan_type || 'free';
  const planType: 'free' | 'ai' | 'expert' = (['free','ai','expert'].includes(rawPlanType) ? rawPlanType : 'free') as 'free' | 'ai' | 'expert';

  const isCurrentSiteLocked = isInOptimizationMode &&
    lockedOptimizationUrl &&
    currentWebsite?.url &&
    (currentWebsite.url === lockedOptimizationUrl ||
     currentWebsite.url.includes(lockedOptimizationUrl) ||
     lockedOptimizationUrl.includes(currentWebsite.url));

  const isAnalysisOnly = !!(isInOptimizationMode && lockedOptimizationUrl && !isCurrentSiteLocked);
  
  // ✅ PERSISTENCE: Lade letzte Scan-Ergebnisse beim Mount
  const { data: latestScanData, isLoading: isLoadingLatestScan } = useLatestScan();
  const { data: activeJobs = [] } = useActiveFixJobs();
  
  // ✅ FIX: Zuerst aus Store lesen, dann ggf. neu laden
  const { data: fetchedAnalysisData, refetch, isLoading } = useComplianceAnalysis(
    currentWebsite?.url || null // ← CRITICAL FIX: null statt undefined
  );
  
  // Priorität: DB (latestScan) > Fetched > Store (localStorage-Cache)
  const analysisData = latestScanData || fetchedAnalysisData || storedAnalysisData;
  
  // ✅ DEBUG: Log final analysisData
  React.useEffect(() => {
    console.log('📊 Final analysisData:', {
      hasData: !!analysisData,
      url: analysisData?.url,
      issues: analysisData?.issues?.length,
      issue_groups: analysisData?.issue_groups?.length,
      grouping_stats: analysisData?.grouping_stats,
      source: storedAnalysisData ? 'store' : fetchedAnalysisData ? 'fetched' : latestScanData ? 'latest' : 'none'
    });
    
    // 🔍 DEBUG: Log issue_groups im Detail
    if (analysisData?.issue_groups) {
      console.log('🎯 Issue Groups gefunden:', analysisData.issue_groups);
    } else {
      console.warn('⚠️ Keine issue_groups in analysisData!', analysisData);
    }
  }, [analysisData, storedAnalysisData, fetchedAnalysisData, latestScanData]);
  
  // ✅ FIX: Gesamter Loading-State berücksichtigt auch latestScan
  const isActuallyLoading = isLoading || (isLoadingLatestScan && !fetchedAnalysisData && !storedAnalysisData);
  
  // Wenn neue Daten vom Hook kommen, in Store speichern
  React.useEffect(() => {
    if (fetchedAnalysisData) {
      setAnalysisData(fetchedAnalysisData);
    }
  }, [fetchedAnalysisData, setAnalysisData]);
  
  // ✅ PERSISTENCE: Letzte Scan-Ergebnisse beim Mount in Store laden
  React.useEffect(() => {
    console.log('🔍 PERSISTENCE DEBUG:', {
      hasLatestScanData: !!latestScanData,
      hasStoredData: !!storedAnalysisData,
      hasFetchedData: !!fetchedAnalysisData,
      latestScanUrl: latestScanData?.url,
      latestScanIssues: latestScanData?.issues?.length
    });
    
    if (latestScanData && !storedAnalysisData && !fetchedAnalysisData) {
      console.log('✅ Loading latest scan into store:', latestScanData.url);
      setAnalysisData(latestScanData);
      
      // ✅ WICHTIG: Auch die Website-URL im Store setzen, damit der Score angezeigt wird
      const { setCurrentWebsite, updateMetrics } = useDashboardStore.getState();
      setCurrentWebsite({
        id: latestScanData.scan_id || Date.now().toString(),
        url: latestScanData.url,
        name: latestScanData.url,
        lastScan: latestScanData.scan_timestamp || new Date().toISOString(),
        complianceScore: latestScanData.compliance_score || 0,
        status: 'completed' as const
      });
      
      // Metrics aktualisieren
      const criticalCount = Array.isArray(latestScanData.issues)
        ? latestScanData.issues.filter((issue: any) => {
            if (typeof issue === 'string') {
              return issue.toLowerCase().includes('fehlt') || 
                     issue.toLowerCase().includes('nicht gefunden');
            }
            return issue.severity === 'critical';
          }).length
        : 0;
      
      updateMetrics({
        totalScore: latestScanData.compliance_score || 0,
        criticalIssues: criticalCount,
        websites: 1
      });
    }
  }, [latestScanData, storedAnalysisData, fetchedAnalysisData, setAnalysisData]);
  
  const startAIFix = useStartAIFix();
  const bookExpert = useBookExpert();

  const handleRescan = async () => {
    if (!currentWebsite?.url) {

      return;
    }

    try {
      // Cache komplett leeren vor dem Rescan
      const { setAnalysisData } = useDashboardStore.getState();
      setAnalysisData(undefined as any);
      
      // React Query Cache für diese URL invalidieren
      await queryClient.invalidateQueries({ queryKey: ['compliance-analysis', currentWebsite.url] });
      await queryClient.invalidateQueries({ queryKey: ['latest-scan'] });
      
      const result = await refetch();
      
      // Update Dashboard Store mit den Ergebnissen
      if (result.data) {
        const { setAnalysisData, updateMetrics } = useDashboardStore.getState();
        setAnalysisData(result.data);
        
        // Metrics aktualisieren
        const criticalCount = Array.isArray(result.data.issues)
          ? result.data.issues.filter((issue: any) => {
              if (typeof issue === 'string') {
                return issue.toLowerCase().includes('fehlt') || 
                       issue.toLowerCase().includes('nicht gefunden');
              }
              return issue.severity === 'critical';
            }).length
          : 0;
        
        const newScore = result.data.compliance_score || 0;
        const oldScore = useDashboardStore.getState().metrics.totalScore || 0;
        
        updateMetrics({
          totalScore: newScore,
          criticalIssues: criticalCount,
          scansUsed: (useDashboardStore.getState().metrics.scansUsed || 0) + 1
        });
        
        // ✅ Success-Animation bei Score-Verbesserung
        if (newScore > oldScore && newScore >= 100) {
          setPreviousScore(oldScore);
          setShowScoreAnimation(true);
        }
      }
    } catch (error) {
      console.error('Rescan failed:', error);
    }
  };

  const handleAIFix = (category: string) => {
    if (!analysisData || !analysisData.scan_id) return;

    startAIFix.mutate({ scanId: analysisData.scan_id, categories: [category] });
  };

  const handleBookExpert = (issueId: string) => {

    bookExpert.mutate(issueId);
  };

  const handleNavigateToPillar = (pillarId: string) => {
    setExpandedPillar(pillarId);
    setTimeout(() => {
      const el = pillarRefs.current[pillarId];
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);
  };

  // ✅ Echte API-Daten verwenden und Issues konvertieren
  const rawIssues = analysisData?.issues || [];
  
  // Konvertiere String-Issues zu strukturierten Objects
  const findings: ComplianceIssue[] = Array.isArray(rawIssues) 
    ? rawIssues.map((issue: any, index: number) => {
        if (typeof issue === 'string') {
          // String-Issue zu Object konvertieren
          const severity = issue.toLowerCase().includes('kritisch') || 
                          issue.toLowerCase().includes('fehlt') ||
                          issue.toLowerCase().includes('nicht gefunden')
            ? 'critical'
            : issue.toLowerCase().includes('empfehlung') 
            ? 'info'
            : 'warning';
          
          // Category aus Text ableiten (✅ MIT BARRIEREFREIHEIT!)
          let category = 'compliance';
          if (issue.includes('Impressum')) category = 'impressum';
          if (issue.includes('Datenschutz')) category = 'datenschutz';
          if (issue.includes('Cookie')) category = 'cookies';
          if (issue.includes('E-Mail')) category = 'contact';
          if (issue.toLowerCase().includes('barrierefreiheit') || 
              issue.toLowerCase().includes('accessibility') ||
              issue.toLowerCase().includes('wcag') ||
              issue.toLowerCase().includes('alt-text') ||
              issue.toLowerCase().includes('kontrast') ||
              issue.toLowerCase().includes('aria')) {
            category = 'barrierefreiheit';
          }
          
          return {
            id: `issue-${index}`,
            category,
            severity,
            title: issue.substring(0, 100),
            description: issue,
            risk_euro: severity === 'critical' ? 5000 : severity === 'warning' ? 1000 : 0,
            recommendation: 'Bitte korrigieren Sie diesen Punkt',
            legal_basis: severity === 'critical' ? 'DSGVO, TMG, TTDSG' : 'Best Practice',
            auto_fixable: category === 'impressum' || category === 'datenschutz' || category === 'cookies'
          } as ComplianceIssue;
        }
        return issue as ComplianceIssue;
      })
    : [];
  
  const complianceScore = analysisData?.compliance_score ?? currentWebsite?.complianceScore ?? 0;
  const totalRisk = analysisData?.total_risk_euro || (analysisData as any)?.estimated_risk_euro || '0€';

  // Gruppiere Issues nach Kategorien (4 Säulen)
  const pillars = [
    {
      id: 'accessibility',
      name: 'Barrierefreiheit',
      icon: Eye,
      color: 'blue',
      description: 'WCAG 2.1 AA Konformität',
      keywords: ['accessibility', 'wcag', 'barrierefreiheit', 'alt', 'kontrast', 'tastat']
    },
    {
      id: 'gdpr',
      name: 'DSGVO',
      icon: Shield,
      color: 'green',
      description: 'Datenschutz-Compliance',
      keywords: ['gdpr', 'dsgvo', 'datenschutz', 'privacy', 'personenbezogen']
    },
    {
      id: 'legal',
      name: 'Rechtssichere Texte',
      icon: FileText,
      color: 'purple',
      description: 'Impressum, AGB, Widerrufsrecht',
      keywords: ['impressum', 'agb', 'legal', 'widerruf', 'rechtlich', 'tmg']
    },
    {
      id: 'cookies',
      name: 'Cookie Compliance',
      icon: Cookie,
      color: 'orange',
      description: 'Cookie-Banner & Consent',
      keywords: ['cookie', 'consent', 'tracking', 'ttdsg']
    },
    {
      id: 'security',
      name: 'Sicherheits-Header',
      icon: Lock,
      color: 'red',
      description: 'CSP, HSTS & HTTP-Header',
      keywords: ['security', 'csp', 'content-security-policy', 'hsts', 'x-frame', 'header', 'strict-transport']
    }
  ];

  const categorizeIssue = (issue: ComplianceIssue): string => {
    const text = `${issue.title} ${issue.description} ${issue.category}`.toLowerCase();

    for (const pillar of pillars) {
      if (pillar.keywords.some(keyword => text.includes(keyword))) {
        return pillar.id;
      }
    }

    return 'legal'; // Default für TMG/UWG-Issues ohne explizites Keyword
  };

  // ✅ NEU: Verwende Backend-Säulen-Scores (wenn vorhanden), sonst Fallback
  const groupedIssues = pillars.map(pillar => {
    const pillarIssues = findings.filter(issue => categorizeIssue(issue) === pillar.id);
    
    // Prüfe ob Backend pillar_scores liefert
    const backendPillarScore = (analysisData as any)?.pillar_scores?.find(
      (p: any) => p.pillar === pillar.id
    );
    
    let score = 100; // Default wenn keine Issues
    
    if (backendPillarScore) {
      // ✅ BESTE OPTION: Backend-Score verwenden!
      score = backendPillarScore.score;

    } else if (pillarIssues.length > 0) {
      // Fallback: Client-seitige Berechnung mit VERSCHÄRFTER Formel
      const criticalCount = pillarIssues.filter(i => i.severity === 'critical').length;
      const warningCount = pillarIssues.filter(i => i.severity === 'warning').length;
      
      // WICHTIG: Verschärfte Formel wie Backend!
      // CRITICAL = -60, WARNING = -15, max 40 bei critical > 0
      score = 100 - (criticalCount * 60 + warningCount * 15);
      if (criticalCount > 0) {
        score = Math.min(score, 40);
      }
      score = Math.max(0, score);
    }
    
    return {
      ...pillar,
      issues: pillarIssues,
      score: Math.round(score)
    };
  });

  // Auto-expand: Säule mit den meisten Critical Issues beim ersten Laden öffnen
  useEffectAlias(() => {
    if (!analysisData || expandedPillar !== null) return;
    const mostCritical = groupedIssues
      .filter(p => p.issues.length > 0)
      .sort((a, b) => {
        const aCrit = a.issues.filter(i => i.severity === 'critical').length;
        const bCrit = b.issues.filter(i => i.severity === 'critical').length;
        if (bCrit !== aCrit) return bCrit - aCrit;
        return b.issues.length - a.issues.length;
      })[0];
    if (mostCritical) {
      setExpandedPillar(mostCritical.id);
    }
  }, [analysisData]);

  useEffectAlias(() => {
    const handler = () => {
      const firstCriticalPillar = groupedIssues.find(p =>
        p.issues.some(i => i.severity === 'critical')
      );
      const targetPillar = firstCriticalPillar || groupedIssues.find(p => p.issues.length > 0);
      if (targetPillar) {
        setExpandedPillar(targetPillar.id);
        setTimeout(() => {
          const el = pillarRefs.current[targetPillar.id];
          if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
      }
    };
    window.addEventListener('complyo:scroll-to-first-critical', handler);
    return () => window.removeEventListener('complyo:scroll-to-first-critical', handler);
  }, [groupedIssues]);

  useEffectAlias(() => {
    const handler = (e: Event) => {
      const pillarId = (e as CustomEvent).detail?.pillarId;
      if (pillarId) {
        setExpandedPillar(pillarId);
        setTimeout(() => {
          const el = pillarRefs.current[pillarId];
          if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
      }
    };
    window.addEventListener('complyo:scroll-to-pillar', handler);
    return () => window.removeEventListener('complyo:scroll-to-pillar', handler);
  }, []);

  return (
    <div className="space-y-6">
      {/* ✅ PROMINENTER WEBSITE-BANNER - IMMER SICHTBAR */}
      {currentWebsite && (
        <div className="glass-strong rounded-2xl p-6 border-2 border-orange-500/30 mb-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-4 flex-1">
              <div className="p-3 bg-orange-500/15 rounded-xl">
                <Globe className="w-8 h-8 text-orange-400" />
              </div>
              <div className="flex-1">
                <div className="text-xs font-semibold text-sky-400 mb-1 uppercase tracking-wider">📊 Analysierte Website</div>
                <div className="text-2xl font-bold text-white mb-1">{currentWebsite.name || currentWebsite.url}</div>
                <div className="flex items-center gap-3 text-sm text-zinc-400">
                  <span className="font-mono bg-zinc-900/70 px-3 py-1 rounded-lg border border-zinc-700">{currentWebsite.url}</span>
                  <span className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                    {formatRelativeTime(currentWebsite.lastScan)}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="flex gap-2 flex-wrap">
              <Button
                variant="secondary"
                size="sm"
                onClick={handleRescan}
                disabled={isActuallyLoading || !currentWebsite.url}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${isActuallyLoading ? 'animate-spin' : ''}`} />
                {isActuallyLoading ? 'Analysiere...' : 'Neu scannen'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  if (analysisData && analysisData.scan_id) {
                    try {
                      const response = await apiClient.get(
                        `/api/v2/reports/${analysisData.scan_id}/download`,
                        { responseType: 'blob' }
                      );
                      const blob = response.data;
                      const url = window.URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `complyo-report-${analysisData.scan_id}.pdf`;
                      document.body.appendChild(a);
                      a.click();
                      window.URL.revokeObjectURL(url);
                      document.body.removeChild(a);
                    } catch {
                      showToast('PDF-Download fehlgeschlagen. Bitte versuchen Sie es erneut.', 'error');
                    }
                  }
                }}
                disabled={!analysisData || !analysisData.scan_id}
              >
                <Download className="mr-2 h-4 w-4" />
                PDF
              </Button>
            </div>
          </div>
        </div>
      )}

        {/* ✅ NEU: Optimierungsmodus-Übergang */}
      {currentWebsite && analysisData && (
        <ErrorBoundary componentName="OptimizationModeLock">
          <OptimizationModeLock hasInteracted={expandedPillar !== null} />
        </ErrorBoundary>
      )}

    <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-sky-500/20 to-purple-500/20 rounded-xl">
              <AlertTriangle className="w-6 h-6 text-sky-400" />
            </div>
            <span>Compliance-Analyse</span>
            {isInOptimizationMode && lockedOptimizationUrl && (
              <Badge variant="success" className="ml-2">
                Optimierungsmodus
              </Badge>
            )}
            {!isActuallyLoading && findings.length > 0 && (
              <Button
                size="sm"
                variant="outline"
                className="ml-auto gap-2"
                onClick={() => setShowWizard(true)}
              >
                <ListChecks className="w-4 h-4" />
                Schritt-für-Schritt beheben
              </Button>
            )}
          </CardTitle>
        </CardHeader>

        <CardContent>

        {/* ✅ LOADING STATE mit Skeleton Screens */}
        {isActuallyLoading && (
          <SkeletonWebsiteAnalysis />
        )}
        
        {/* ✅ Success-Animationen */}
        {showScoreAnimation && previousScore !== null && (
          <ScoreAnimation
            oldScore={previousScore}
            newScore={complianceScore}
            show={showScoreAnimation}
            onComplete={() => {
              setShowScoreAnimation(false);
              setPreviousScore(null);
            }}
          />
        )}

        {/* ✅ AKTIVE FIX-JOBS */}
        {activeJobs.length > 0 && (
          <div className="mb-6">
            <ActiveJobsPanel jobs={activeJobs} />
          </div>
        )}

        {/* ✅ 4-SÄULEN COMPLIANCE-ANALYSE */}
        {!isActuallyLoading && findings.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <span className="w-1 h-6 bg-gradient-to-b from-sky-500 to-purple-500 rounded-full"></span>
                Compliance-Analyse nach Kategorien
              </h3>
            </div>

            {/* Quick Wins — direkte Navigation zu Säulen */}
            <div className="mb-6">
              <QuickWins issues={findings} onNavigateToPillar={handleNavigateToPillar} />
            </div>
            
            {/* Akkordion-Karten mit Score */}
            <div className="space-y-4">
              {groupedIssues.map((pillar) => {
                const Icon = pillar.icon;
                const issueCount = pillar.issues.length;
                const criticalCount = pillar.issues.filter(i => i.severity === 'critical').length;
                const isExpanded = expandedPillar === pillar.id;
                
                if (!Icon) {
                  return null;
                }
                
                return (
                  <div 
                    key={pillar.id}
                    ref={(el) => { pillarRefs.current[pillar.id] = el; }}
                    className="glass-card rounded-2xl overflow-hidden border border-zinc-800/50 hover:border-zinc-700/70 transition-all"
                  >
                    {/* Header - Klickbar */}
                    <button
                      onClick={() => setExpandedPillar(isExpanded ? null : pillar.id)}
                      className="w-full p-6 flex items-center justify-between hover:bg-white/[0.02] transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-xl bg-gradient-to-br ${
                          pillar.color === 'blue'   ? 'from-sky-500/20 to-blue-500/20' :
                          pillar.color === 'green'  ? 'from-green-500/20 to-emerald-500/20' :
                          pillar.color === 'purple' ? 'from-purple-500/20 to-pink-500/20' :
                          pillar.color === 'red'    ? 'from-red-500/20 to-rose-500/20' :
                          'from-orange-500/20 to-red-500/20'
                        }`}>
                          <Icon className={`w-6 h-6 ${
                            pillar.color === 'blue'   ? 'text-sky-400' :
                            pillar.color === 'green'  ? 'text-green-400' :
                            pillar.color === 'purple' ? 'text-purple-400' :
                            pillar.color === 'red'    ? 'text-red-400' :
                            'text-orange-400'
                          }`} />
                        </div>
                        <div className="text-left">
                          <h4 className="text-lg font-bold text-white flex items-center gap-2">
                            {pillar.name}
                            {issueCount > 0 && (
                              <Badge variant={criticalCount > 0 ? 'critical' : 'warning'}>
                                {issueCount} Issue{issueCount !== 1 ? 's' : ''}
                              </Badge>
                            )}
                          </h4>
                          <p className="text-sm text-zinc-400 mt-0.5">{pillar.description}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-4">
                        {/* Score */}
                        <div className="text-right">
                          <div className={`text-3xl font-bold ${
                            pillar.score >= 80 ? 'text-green-400' : 
                            pillar.score >= 60 ? 'text-yellow-400' : 
                            'text-red-400'
                          }`}>
                            {pillar.score}
                          </div>
                          <div className="text-xs text-zinc-500">/100</div>
                        </div>
                        
                        {/* Chevron */}
                        <ChevronDown className={`w-5 h-5 text-zinc-400 transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`} />
                      </div>
                    </button>

                    {/* Ausklappbare Details */}
                    {isExpanded && issueCount > 0 && (
                      <div className="border-t border-zinc-800/50 p-6 bg-black/20 animate-slide-down">
                        <div className="space-y-4">
                          {/* ✨ NEU: Gruppierte Issues (wenn vorhanden) */}
                          {(() => {
                            const issueGroups = (analysisData as any)?.issue_groups || [];
                            const ungroupedIssues = (analysisData as any)?.ungrouped_issues || [];
                            
                            // 🔍 DEBUG: Log für diese Säule
                            console.log(`🔧 Rendering pillar: ${pillar.id}`, {
                              totalGroups: issueGroups.length,
                              groups: issueGroups,
                              pillarIssues: pillar.issues.length
                            });
                            
                            // Filtere Gruppen für diese Säule
                            const pillarGroups = issueGroups.filter((group: any) => 
                              group.category === pillar.id || 
                              (pillar.id === 'gdpr' && group.category === 'datenschutz') ||
                              (pillar.id === 'legal' && group.category === 'impressum')
                            );
                            
                            console.log(`📦 Filtered groups for ${pillar.id}:`, pillarGroups.length, pillarGroups);
                            
                            // Filtere ungrouped Issues für diese Säule
                            const pillarUngrouped = pillar.issues.filter((issue: any) => {
                              // Prüfe ob Issue nicht in einer Gruppe ist
                              const inGroup = issueGroups.some((group: any) => {
                                const groupIssueIds = [
                                  ...(group.sub_issues || []).map((si: any) => si.id),
                                  group.parent_issue?.id
                                ].filter(Boolean);
                                return groupIssueIds.includes(issue.id);
                              });
                              return !inGroup;
                            });
                            
                            return (
                              <>
                                {/* Analyse-Modus Banner pro Säule */}
                                {isAnalysisOnly && (
                                  <div className="flex items-center justify-between gap-3 px-4 py-2.5 mb-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                                    <span className="text-xs text-amber-300">
                                      Analyse-Modus — Optimierungen sind nur für <strong className="text-white">{lockedOptimizationUrl}</strong> verfügbar
                                    </span>
                                    <button
                                      onClick={() => {
                                        if (typeof window !== 'undefined') {
                                          window.dispatchEvent(new CustomEvent('complyo:back-to-optimization'));
                                        }
                                      }}
                                      className="text-xs text-amber-300 hover:text-white underline whitespace-nowrap"
                                    >
                                      Zurück zur Optimierung
                                    </button>
                                  </div>
                                )}

                                {/* Zeige gruppierte Issues */}
                                {pillarGroups.map((group: any, idx: number) => (
                                  <ErrorBoundary key={`group-${group.group_id}-${idx}`} componentName={`ComplianceIssueGroup (${group.title})`}>
                                    <ComplianceIssueGroup
                                      group={group}
                                      planType={planType}
                                      websiteUrl={analysisData?.url}
                                      scanId={analysisData?.scan_id}
                                      onStartFix={handleAIFix}
                                      isAnalysisOnly={isAnalysisOnly}
                                    />
                                  </ErrorBoundary>
                                ))}
                                
                                {/* Zeige ungrouped Issues */}
                                {pillarUngrouped.map((issue: any, idx: number) => (
                                  <ErrorBoundary key={`eb-${issue.id}-${idx}`} componentName={`ComplianceIssueCard (${issue.title})`}>
                                    <ComplianceIssueCard
                                      key={`${issue.id}-${idx}`}
                                      issue={issue}
                                      planType={planType}
                                      scanId={analysisData?.scan_id}
                                      websiteUrl={analysisData?.url}
                                      onStartFix={handleAIFix}
                                      isAnalysisOnly={isAnalysisOnly}
                                    />
                                  </ErrorBoundary>
                                ))}
                              </>
                            );
                          })()}
                          
                          {/* 🚀 BARRIEREFREIHEIT: Eine einzige, klare Widget-Karte (nicht doppelt!) */}
                          {pillar.id === 'accessibility' && analysisData && (
                            <div className="mt-6">
                              {/* ✅ EINZIGE Widget-Integration Card - mit korrektem Status */}
                              <ErrorBoundary componentName="WidgetIntegrationCard">
                                <WidgetIntegrationCard
                                  siteId={(() => {
                                    // ✅ FIX: Generiere Site-ID aus URL statt Scan-Hash zu verwenden
                                    const currentSiteId = analysisData.site_id || analysisData.scan_id || '';
                                    
                                    // Wenn site_id ein Scan-Hash ist, generiere aus URL
                                    if (isScanHash(currentSiteId) || !currentSiteId) {
                                      return generateSiteId(analysisData.url || currentWebsite?.url || '');
                                    }
                                    
                                    return currentSiteId;
                                  })()}
                                  websiteUrl={analysisData.url}
                                  isWidgetActive={analysisData.has_accessibility_widget === true}
                                />
                              </ErrorBoundary>
                            </div>
                          )}
                          
                          {/* 🍪 NEU: Cookie/TCF-Spezifische Komponenten */}
                          {pillar.id === 'cookies' && analysisData && analysisData.tcf_data && (
                            <div className="mt-6">
                              <ErrorBoundary componentName="TCFComplianceWidget">
                                <TCFComplianceWidget
                                  scanId={analysisData.scan_id || analysisData.site_id}
                                  tcfData={analysisData.tcf_data}
                                />
                              </ErrorBoundary>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                    
                    {/* Leerer Zustand wenn keine Issues */}
                    {isExpanded && issueCount === 0 && (
                      <div className="border-t border-zinc-800/50 p-6 bg-black/20 text-center">
                        <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
                        <p className="text-zinc-300 font-medium">Keine Issues gefunden</p>
                        <p className="text-zinc-500 text-sm mt-1">Diese Kategorie ist vollständig compliant! 🎉</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ✅ EMPTY STATE - Nur anzeigen wenn wirklich keine Daten */}
        {!currentWebsite && !analysisData && !isActuallyLoading && (
          <div className="text-center py-8">
            <Globe className="mx-auto mb-4 h-12 w-12 text-gray-400" />
            <p className="text-gray-300 mb-4">Keine Website analysiert</p>
            <p className="text-gray-400 text-sm">Geben Sie eine Website-URL ein, um eine Compliance-Analyse zu starten.</p>
          </div>
        )}

        {/* ✅ NO FINDINGS STATE */}
        {currentWebsite && !isActuallyLoading && findings.length === 0 && analysisData && (
          <div className="text-center py-8">
            <CheckCircle className="mx-auto mb-4 h-12 w-12 text-green-400" />
            <p className="text-gray-300 mb-2">Analyse abgeschlossen</p>
            <p className="text-gray-400 text-sm">
              {complianceScore >= 80 
                ? 'Ihre Website ist gut konfiguriert!' 
                : 'Es wurden einige Bereiche zur Verbesserung identifiziert.'}
            </p>
          </div>
        )}
      </CardContent>
    </Card>

    {showWizard && (
      <ErrorBoundary componentName="ComplianceWizard">
        <ComplianceWizard
          issues={findings}
          groups={(analysisData as any)?.issue_groups || []}
          planType={planType}
          websiteUrl={analysisData?.url}
          scanId={analysisData?.scan_id}
          onClose={() => setShowWizard(false)}
          onComplete={() => setShowWizard(false)}
        />
      </ErrorBoundary>
    )}
    </div>
  );
};
