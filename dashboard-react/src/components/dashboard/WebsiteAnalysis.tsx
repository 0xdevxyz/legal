'use client';

import React, { useState, useRef, useEffect as useEffectAlias } from 'react';
import { Globe, RefreshCw, AlertTriangle, AlertCircle, CheckCircle, Bot, Download, Eye, Shield, FileText, Cookie, ChevronDown, ListChecks } from 'lucide-react';
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
  // Reale Pläne (single/pro/agency/expert/update) auf Fix-Zugriffsstufen abbilden:
  // expert = Done-for-you (Service buchen), jeder andere bezahlte Plan = Self-Service KI-Fixes, sonst free.
  const planType: 'free' | 'paid' | 'expert' =
    rawPlanType === 'expert' ? 'expert'
    : rawPlanType !== 'free' ? 'paid'
    : 'free';

  // Agentur/Expert: jede getrackte Seite ist voll optimierbar → kein Single-Lock.
  const isAgency = rawPlanType === 'agency' || rawPlanType === 'expert';

  const isCurrentSiteLocked = isAgency || (isInOptimizationMode &&
    lockedOptimizationUrl &&
    currentWebsite?.url &&
    (currentWebsite.url === lockedOptimizationUrl ||
     currentWebsite.url.includes(lockedOptimizationUrl) ||
     lockedOptimizationUrl.includes(currentWebsite.url)));

  const isAnalysisOnly = !isAgency && !!(isInOptimizationMode && lockedOptimizationUrl && !isCurrentSiteLocked);
  
  // ✅ PERSISTENCE: Lade letzte Scan-Ergebnisse beim Mount
  const { data: latestScanData, isLoading: isLoadingLatestScan } = useLatestScan();
  const { data: activeJobs = [] } = useActiveFixJobs();
  
  // ✅ FIX: Zuerst aus Store lesen, dann ggf. neu laden
  const { data: fetchedAnalysisData, refetch, isLoading } = useComplianceAnalysis(
    currentWebsite?.url || null // ← CRITICAL FIX: null statt undefined
  );
  
  // Priorität: DB (latestScan) > Fetched > Store (localStorage-Cache).
  // Bei Agentur NICHT den global letzten Scan bevorzugen — sonst überschreibt er
  // beim Seitenwechsel die per-Domain-Analyse der aktiven Seite.
  const analysisData = isAgency
    ? (fetchedAnalysisData || storedAnalysisData)
    : (latestScanData || fetchedAnalysisData || storedAnalysisData);
  
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
        // Objekt-Issue (von Check-Modulen): id sicherstellen.
        // Manche Check-Module (z. B. Cookie/AGB) liefern keine id mit — ohne id
        // bricht der KI-Fix mit "Ungültige Issue-ID" ab. Fallback wie im Backend:
        // Slug aus Kategorie + Titel.
        const obj = issue as ComplianceIssue;
        if (!obj.id || typeof obj.id !== 'string') {
          const cat = (obj.category || 'compliance').toLowerCase();
          const slug = (obj.title || obj.description || '')
            .toLowerCase()
            .replace(/[^a-z0-9\s]/g, '')
            .split(/\s+/)
            .filter(Boolean)
            .slice(0, 4)
            .join('-');
          obj.id = `${cat}-${slug}`.slice(0, 50) || `issue-${index}`;
        }
        return obj;
      })
    : [];
  
  const complianceScore = analysisData?.compliance_score ?? currentWebsite?.complianceScore ?? 0;
  const totalRisk = analysisData?.total_risk_euro || (analysisData as any)?.estimated_risk_euro || '0€';

  // 4 Säulen (SSOT v3.0 — identisch zum Backend ScoreCalculator):
  //  - Sicherheit (CSP/HSTS/Header) = DSGVO Art. 32 → fällt in "gdpr"
  //  - Shop-Pflichttexte (Widerruf, Preisangaben) → fallen in "legal"
  const pillars = [
    {
      id: 'accessibility',
      name: 'Barrierefreiheit',
      icon: Eye,
      color: 'blue',
      description: 'WCAG 2.1 AA Konformität',
      keywords: ['accessibility', 'wcag', 'aria', 'barrierefreiheit', 'barriere', 'alt-text', 'alt_text', 'kontrast', 'contrast', 'tastat']
    },
    {
      id: 'gdpr',
      name: 'Datenschutz',
      icon: Shield,
      color: 'green',
      description: 'DSGVO inkl. technischer Sicherheit (Art. 32)',
      keywords: ['gdpr', 'dsgvo', 'datenschutz', 'privacy', 'personenbezogen', 'avv',
        'security', 'sicherheit', 'csp', 'content-security', 'hsts', 'x-frame', 'header', 'ssl', 'tls']
    },
    {
      id: 'legal',
      name: 'Rechtssichere Texte',
      icon: FileText,
      color: 'purple',
      description: 'Impressum, AGB, Widerruf, Preisangaben, Shop',
      keywords: ['impressum', 'agb', 'legal', 'rechtlich', 'tmg', 'uwg', 'widerruf',
        'preisangaben', 'preis', 'pangv', 'shop', 'kontakt', 'contact', 'social']
    },
    {
      id: 'cookies',
      name: 'Cookie Compliance',
      icon: Cookie,
      color: 'orange',
      description: 'Cookie-Banner & Consent',
      keywords: ['cookie', 'consent', 'tracking', 'tcf', 'ttdsg']
    }
  ];

  const categorizeIssue = (issue: ComplianceIssue): string => {
    // Reihenfolge der Säulen = Priorität (erste Übereinstimmung gewinnt),
    // damit z.B. "tracking" zuerst Cookies und nicht versehentlich Legal trifft.
    const ordered = ['accessibility', 'cookies', 'gdpr', 'legal'];

    // 1. PRIMÄR: nur über das category-Feld zuordnen — identisch zum Backend
    //    (ScoreCalculator.categorize). So kann ein Wort wie "Inhalt" nicht über den
    //    Teilstring "alt" ein Datenschutz-Issue fälschlich in Barrierefreiheit kippen.
    const cat = (issue.category || '').toLowerCase();
    if (cat) {
      for (const id of ordered) {
        const pillar = pillars.find(p => p.id === id);
        if (pillar && pillar.keywords.some(keyword => cat.includes(keyword))) {
          return pillar.id;
        }
      }
    }

    // 2. FALLBACK (nur für Legacy-String-Issues ohne brauchbares category-Feld):
    //    Titel/Beschreibung heranziehen.
    const text = `${issue.title} ${issue.description}`.toLowerCase();
    for (const id of ordered) {
      const pillar = pillars.find(p => p.id === id);
      if (pillar && pillar.keywords.some(keyword => text.includes(keyword))) {
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
      // Fallback: identische Formel wie Backend ScoreCalculator (SSOT v3.0)
      // Säule = max(0, 100 - (critical*25 + warning*8))
      const criticalCount = pillarIssues.filter(i => i.severity === 'critical').length;
      const warningCount = pillarIssues.filter(i => i.severity === 'warning').length;

      score = Math.max(0, 100 - (criticalCount * 25 + warningCount * 8));
    }

    // ✅ v4.0 evidenz-basiert: Status vom Backend übernehmen, sonst aus Score ableiten.
    // 'unverified' = konnte nicht geprüft werden → NIE als grün/bestanden darstellen.
    const criticalCount = pillarIssues.filter(i => i.severity === 'critical').length;
    const status: string =
      backendPillarScore?.status ||
      (criticalCount > 0 ? 'non_compliant' : pillarIssues.length > 0 ? 'partial' : 'compliant');

    return {
      ...pillar,
      issues: pillarIssues,
      score: Math.round(score),
      status,
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
        <div className="glass-strong rounded-2xl p-6 border-2 border-[#25bac8]/30 mb-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-4 flex-1">
              <div className="p-3 rounded-xl" style={{ background: 'var(--lime-dim)' }}>
                <Globe className="w-8 h-8" style={{ color: 'var(--lime)' }} />
              </div>
              <div className="flex-1">
                <div className="text-xs font-semibold mb-1 uppercase tracking-wider" style={{ color: 'var(--lime)' }}>📊 Analysierte Website</div>
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
            <div className="p-2.5 rounded-xl" style={{ background: 'var(--lime-dim)' }}>
              <AlertTriangle className="w-6 h-6" style={{ color: 'var(--lime)' }} />
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
                <span className="w-1 h-6 rounded-full" style={{ background: 'var(--lime)' }}></span>
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
                        <div className="p-3 rounded-xl" style={{ background: 'var(--lime-dim)' }}>
                          <Icon className="w-6 h-6" style={{ color: 'var(--lime)' }} />
                        </div>
                        <div className="text-left">
                          <h4 className="text-lg font-bold text-white flex items-center gap-2 flex-wrap">
                            {pillar.name}
                            {/* ✅ v4.0: evidenz-basierter Status-Badge */}
                            {(() => {
                              const cfg: Record<string, { label: string; cls: string }> = {
                                compliant:     { label: '✓ Bestanden',    cls: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' },
                                partial:       { label: 'Teilweise',      cls: 'bg-amber-500/15 text-amber-400 border border-amber-500/30' },
                                non_compliant: { label: '✗ Nicht erfüllt', cls: 'bg-red-500/15 text-red-400 border border-red-500/30' },
                                unverified:    { label: '? Ungeprüft',    cls: 'bg-zinc-500/15 text-zinc-300 border border-zinc-500/40' },
                              };
                              const s = cfg[(pillar as any).status] || cfg.compliant;
                              return (
                                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${s.cls}`}>
                                  {s.label}
                                </span>
                              );
                            })()}
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
                        {/* Score ring (ORION) */}
                        {(() => {
                          const r = 26;
                          const circ = 2 * Math.PI * r;
                          const isUnverified = (pillar as any).status === 'unverified';
                          const pct = Math.max(0, Math.min(100, pillar.score));
                          // Ungeprüft: voller neutraler Ring, kein irreführender 0%-Wert
                          const off = isUnverified ? 0 : circ - (pct / 100) * circ;
                          const ringColor = isUnverified
                            ? '#71717a' // zinc-500
                            : pillar.score >= 80 ? '#25bac8' : pillar.score >= 60 ? '#eab308' : '#ef4444';
                          return (
                            <div className="relative w-[68px] h-[68px] flex-shrink-0">
                              <svg className="w-full h-full -rotate-90" viewBox="0 0 68 68">
                                <circle cx="34" cy="34" r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="6" />
                                <circle
                                  cx="34" cy="34" r={r} fill="none"
                                  stroke={ringColor} strokeWidth="6" strokeLinecap="round"
                                  strokeDasharray={circ} strokeDashoffset={off}
                                  style={{ transition: 'stroke-dashoffset 0.8s ease' }}
                                />
                              </svg>
                              <div className="absolute inset-0 flex flex-col items-center justify-center">
                                {isUnverified ? (
                                  <span className="text-2xl font-black text-zinc-300 leading-none" title="Konnte nicht geprüft werden">?</span>
                                ) : (
                                  <>
                                    <span className="text-lg font-black text-white leading-none">{pillar.score}</span>
                                    <span className="text-[9px] text-zinc-500 leading-none mt-0.5">/100</span>
                                  </>
                                )}
                              </div>
                            </div>
                          );
                        })()}

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
