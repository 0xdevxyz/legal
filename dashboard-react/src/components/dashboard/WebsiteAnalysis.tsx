'use client';

import React, { useState } from 'react';
import { Globe, RefreshCw, AlertTriangle, AlertCircle, CheckCircle, Bot, Download, Eye, Shield, FileText, Cookie, ChevronDown } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useDashboardStore } from '@/stores/dashboard';
import { useStartAIFix, useBookExpert, useComplianceAnalysis, useLatestScan, useActiveFixJobs } from '@/hooks/useCompliance';
import { formatRelativeTime } from '@/lib/utils';
import type { ComplianceIssue } from '@/types/api';
import { ComplianceIssueCard } from './ComplianceIssueCard';
import { ActiveJobsPanel } from './ActiveJobsPanel';
import { useAuth } from '@/contexts/AuthContext';

export const WebsiteAnalysis: React.FC = () => {
  const { user } = useAuth();
  const { currentWebsite, analysisData: storedAnalysisData, setAnalysisData } = useDashboardStore();
  const [expandedPillar, setExpandedPillar] = useState<string | null>(null);
  
  // Get plan type from user, default to 'free'
  const planType: 'free' | 'ai' | 'expert' = user?.plan_type || 'free';
  
  // ✅ PERSISTENCE: Lade letzte Scan-Ergebnisse beim Mount
  const { data: latestScanData, isLoading: isLoadingLatestScan } = useLatestScan();
  const { data: activeJobs = [] } = useActiveFixJobs();
  
  // ✅ FIX: Zuerst aus Store lesen, dann ggf. neu laden
  const { data: fetchedAnalysisData, refetch, isLoading } = useComplianceAnalysis(
    currentWebsite?.url || null // ← CRITICAL FIX: null statt undefined
  );
  
  // Priorität: Store > Fetched > Latest Scan (beim Mount)
  const analysisData = storedAnalysisData || fetchedAnalysisData || latestScanData;
  
  // ✅ DEBUG: Log final analysisData
  React.useEffect(() => {
    console.log('📊 Final analysisData:', {
      hasData: !!analysisData,
      url: analysisData?.url,
      issues: analysisData?.issues?.length,
      source: storedAnalysisData ? 'store' : fetchedAnalysisData ? 'fetched' : latestScanData ? 'latest' : 'none'
    });
  }, [analysisData, storedAnalysisData, fetchedAnalysisData, latestScanData]);
  
  // ✅ FIX: Gesamter Loading-State berücksichtigt auch latestScan
  const isActuallyLoading = isLoading || (isLoadingLatestScan && !storedAnalysisData && !fetchedAnalysisData);
  
  // Wenn neue Daten vom Hook kommen, in Store speichern
  React.useEffect(() => {
    if (fetchedAnalysisData && !storedAnalysisData) {

      setAnalysisData(fetchedAnalysisData);
    }
  }, [fetchedAnalysisData, storedAnalysisData, setAnalysisData]);
  
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
    }
  }, [latestScanData, storedAnalysisData, fetchedAnalysisData, setAnalysisData]);
  
  const startAIFix = useStartAIFix();
  const bookExpert = useBookExpert();

  const handleRescan = async () => {
    if (!currentWebsite?.url) {

      return;
    }

    try {
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
        
        updateMetrics({
          totalScore: result.data.compliance_score || 0,
          criticalIssues: criticalCount,
          scansUsed: (useDashboardStore.getState().metrics.scansUsed || 0) + 1
        });
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
          
          // Category aus Text ableiten
          let category = 'compliance';
          if (issue.includes('Impressum')) category = 'impressum';
          if (issue.includes('Datenschutz')) category = 'datenschutz';
          if (issue.includes('Cookie')) category = 'cookies';
          if (issue.includes('E-Mail')) category = 'contact';
          
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
    }
  ];

  const categorizeIssue = (issue: ComplianceIssue): string => {
    const text = `${issue.title} ${issue.description} ${issue.category}`.toLowerCase();
    
    for (const pillar of pillars) {
      if (pillar.keywords.some(keyword => text.includes(keyword))) {
        return pillar.id;
      }
    }
    
    return 'legal'; // Default
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

  return (
    <div className="space-y-6">
      {/* ✅ PROMINENTER WEBSITE-BANNER - IMMER SICHTBAR */}
      {currentWebsite && (
        <div className="glass-strong rounded-2xl p-6 border-2 border-sky-500/30 shadow-glow-blue sticky top-20 z-40 mb-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-4 flex-1">
              <div className="p-3 bg-gradient-to-br from-sky-500 to-purple-500 rounded-xl shadow-lg">
                <Globe className="w-8 h-8 text-white" />
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
                onClick={() => {
                  if (analysisData && analysisData.scan_id) {
                    window.open(`/api/v2/reports/${analysisData.scan_id}/download`, '_blank');
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

      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-sky-500/20 to-purple-500/20 rounded-xl">
              <AlertTriangle className="w-6 h-6 text-sky-400" />
            </div>
            <span>Compliance-Analyse</span>
          </CardTitle>
        </CardHeader>

        <CardContent>
          {/* ✅ METRIKEN ÜBERSICHT */}
          {currentWebsite && (
            <div className="glass-card rounded-xl p-6 mb-6 border border-zinc-700/50">
              {/* Website-Anzeige */}
              <div className="mb-4 pb-4 border-b border-zinc-800">
                <div className="text-xs text-zinc-500 uppercase tracking-wider mb-1">Analysierte Website</div>
                <div className="text-lg font-semibold text-white flex items-center gap-2">
                  <Globe className="w-4 h-4 text-indigo-400" />
                  {currentWebsite.url}
                </div>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-zinc-900/50 rounded-xl p-4 border border-zinc-800">
                  <div className="text-xs text-zinc-400 mb-2 font-semibold uppercase tracking-wider">Compliance-Score</div>
                  <div className={`text-3xl font-bold ${complianceScore >= 80 ? 'text-green-400' : complianceScore >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {complianceScore}<span className="text-lg text-zinc-500">/100</span>
                  </div>
                </div>
                
                <div className="bg-zinc-900/50 rounded-xl p-4 border border-zinc-800">
                  <div className="text-xs text-zinc-400 mb-2 font-semibold uppercase tracking-wider">Geschätztes Risiko</div>
                  <div className="text-3xl font-bold text-red-400">
                    {typeof totalRisk === 'string' ? totalRisk : new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(totalRisk)}
                  </div>
                </div>
                
                <div className="bg-zinc-900/50 rounded-xl p-4 border border-zinc-800">
                  <div className="text-xs text-zinc-400 mb-2 font-semibold uppercase tracking-wider">Gefundene Issues</div>
                  <div className="text-3xl font-bold text-orange-400">
                    {findings.length}
                  </div>
                </div>
              </div>
            </div>
          )}

        {/* ✅ LOADING STATE */}
        {isActuallyLoading && (
          <div className="text-center py-12">
            <div className="relative mx-auto mb-6 w-16 h-16">
              <div className="absolute inset-0 border-4 border-zinc-800 rounded-full"></div>
              <div className="absolute inset-0 border-4 border-t-sky-500 border-r-purple-500 border-b-transparent border-l-transparent rounded-full animate-spin"></div>
            </div>
            <p className="text-white font-semibold text-lg mb-2">
              {isLoadingLatestScan && !isLoading ? 'Lade letzte Scan-Ergebnisse...' : 'Daten werden geladen...'}
            </p>
            {currentWebsite && (
              <p className="text-zinc-400 text-sm">
                Analysiere: <span className="text-sky-400 font-medium">{currentWebsite.name}</span>
              </p>
            )}
          </div>
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
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <span className="w-1 h-6 bg-gradient-to-b from-sky-500 to-purple-500 rounded-full"></span>
              Compliance-Analyse nach Kategorien
            </h3>
            
            {/* Akkordion-Karten mit Score */}
            <div className="space-y-4">
              {groupedIssues.map((pillar) => {
                const Icon = pillar.icon;
                const issueCount = pillar.issues.length;
                const criticalCount = pillar.issues.filter(i => i.severity === 'critical').length;
                const isExpanded = expandedPillar === pillar.id;
                
                return (
                  <div 
                    key={pillar.id} 
                    className="glass-card rounded-2xl overflow-hidden border border-zinc-800/50 hover:border-zinc-700/70 transition-all"
                  >
                    {/* Header - Klickbar */}
                    <button
                      onClick={() => setExpandedPillar(isExpanded ? null : pillar.id)}
                      className="w-full p-6 flex items-center justify-between hover:bg-white/[0.02] transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-xl bg-gradient-to-br ${
                          pillar.color === 'blue' ? 'from-sky-500/20 to-blue-500/20' :
                          pillar.color === 'green' ? 'from-green-500/20 to-emerald-500/20' :
                          pillar.color === 'purple' ? 'from-purple-500/20 to-pink-500/20' :
                          'from-orange-500/20 to-red-500/20'
                        }`}>
                          <Icon className={`w-6 h-6 ${
                            pillar.color === 'blue' ? 'text-sky-400' :
                            pillar.color === 'green' ? 'text-green-400' :
                            pillar.color === 'purple' ? 'text-purple-400' :
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
                          {pillar.issues.map((issue, idx) => (
                            <ComplianceIssueCard
                              key={`${issue.id}-${idx}`}
                              issue={issue}
                              planType={planType}
                              scanId={analysisData?.scan_id}
                              websiteUrl={analysisData?.url}
                              onStartFix={handleAIFix}
                            />
                          ))}
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
    </div>
  );
};
