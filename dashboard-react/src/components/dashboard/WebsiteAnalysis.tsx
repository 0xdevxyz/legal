'use client';

import React, { useState } from 'react';
import { Globe, RefreshCw, AlertTriangle, AlertCircle, CheckCircle, Bot, UserCheck, Search } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useDashboardStore } from '@/stores/dashboard';
import { useStartAIFix, useBookExpert, useComplianceAnalysis } from '@/hooks/useCompliance';
import { formatRelativeTime } from '@/lib/utils';

export const WebsiteAnalysis: React.FC = () => {
  const { currentWebsite, setCurrentWebsite } = useDashboardStore();
  const [newUrl, setNewUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  // ✅ FIX: Nur API-Call wenn URL vorhanden ist
  const { data: analysisData, refetch, isLoading } = useComplianceAnalysis(
    currentWebsite?.url || null // ← CRITICAL FIX: null statt undefined
  );
  const startAIFix = useStartAIFix();
  const bookExpert = useBookExpert();

  const handleAnalyzeNewWebsite = async () => {
  // Strenge URL-Validierung
  const trimmedUrl = newUrl?.trim();
  if (!trimmedUrl || typeof trimmedUrl !== 'string' || !isValidUrl(trimmedUrl)) {
    console.warn('Invalid URL provided:', { newUrl, trimmedUrl, type: typeof newUrl });
    return;
  }

  console.log('Starting website analysis for:', trimmedUrl);
  setIsAnalyzing(true);

  // URL normalisieren
  let normalizedUrl = trimmedUrl;
  if (!normalizedUrl.startsWith('http://') && !normalizedUrl.startsWith('https://')) {
    normalizedUrl = 'https://' + normalizedUrl;
  }

  const newWebsite = {
    id: Date.now().toString(),
    url: normalizedUrl,
    name: trimmedUrl,
    lastScan: new Date().toISOString(),
    complianceScore: 0,
    status: 'scanning' as const
  };

  setCurrentWebsite(newWebsite);
  setNewUrl('');

  try {
    await refetch();
  } catch (error) {
    console.error('Website analysis failed:', error);
  } finally {
    setIsAnalyzing(false);
  }
};

  const handleRescan = async () => {
    if (!currentWebsite?.url) {
      console.warn('🚫 No website URL to rescan');
      return;
    }
    console.log('🔄 Rescanning website:', currentWebsite.url);
    await refetch();
  };

  const handleAIFix = (issueId: string) => {
    console.log('🤖 Starting AI fix for issue:', issueId);
    startAIFix.mutate(issueId);
  };

  const handleBookExpert = (issueId: string) => {
    console.log('👨‍💼 Booking expert for issue:', issueId);
    bookExpert.mutate(issueId);
  };

  // ✅ Echte API-Daten verwenden statt mockFindings
  const findings = analysisData?.findings ? Object.values(analysisData.findings) : [];
  const complianceScore = analysisData?.compliance_score || currentWebsite?.complianceScore || 0;

  // ✅ FIX: Input validation with better UX
  const handleUrlInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setNewUrl(value);
  };

  const handleUrlInputKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAnalyzeNewWebsite();
    }
  };

  const isValidUrl = (url: string) => {
    const trimmed = url.trim();
    if (!trimmed) return false;
    
    // Basic URL validation
    const urlPattern = /^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(\/.*)?$/;
    const fullUrlPattern = /^https?:\/\/([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(\/.*)?$/;
    
    return fullUrlPattern.test(trimmed) || urlPattern.test(trimmed);
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center">
            <Globe className="mr-2 text-blue-400" />
            Website-Compliance-Analyse
          </CardTitle>
          {currentWebsite && (
            <div className="text-sm text-gray-400">
              Zuletzt gescannt: {formatRelativeTime(currentWebsite.lastScan)}
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {/* ✅ NEUE WEBSITE ANALYSIEREN - Verbessertes Eingabefeld */}
        <div className="bg-gray-800/50 rounded-lg p-4 mb-4 border border-gray-600/30">
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Website-URL eingeben (z.B. example.com oder https://example.com)"
                value={newUrl}
                onChange={handleUrlInputChange}
                onKeyPress={handleUrlInputKeyPress}
                className={`w-full p-3 bg-gray-700 border rounded-lg text-white placeholder-gray-400 focus:outline-none transition-colors ${
                  newUrl.trim() && !isValidUrl(newUrl) 
                    ? 'border-red-500 focus:border-red-400' 
                    : 'border-gray-600 focus:border-blue-500'
                }`}
                disabled={isAnalyzing}
              />
              {newUrl.trim() && !isValidUrl(newUrl) && (
                <div className="text-red-400 text-sm mt-1">
                  Bitte geben Sie eine gültige URL ein (z.B. example.com)
                </div>
              )}
            </div>
            <Button
              onClick={handleAnalyzeNewWebsite}
              disabled={!newUrl.trim() || !isValidUrl(newUrl) || isAnalyzing}
              className="flex items-center whitespace-nowrap"
            >
              <Search className="mr-2 h-4 w-4" />
              {isAnalyzing ? 'Analysiere...' : 'Analysieren'}
            </Button>
          </div>
        </div>

        {/* ✅ AKTUELLE WEBSITE ANZEIGEN */}
        {currentWebsite && (
          <div className="bg-gray-800/50 rounded-lg p-4 mb-4 border border-gray-600/30">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-400">Analysierte Website:</div>
                <div className="text-lg font-semibold text-blue-400">{currentWebsite.name || currentWebsite.url}</div>
                <div className="text-xs text-gray-500 mb-1">{currentWebsite.url}</div>
                <div className="text-sm text-gray-300">
                  Compliance-Score: <span className={`font-bold ${complianceScore >= 80 ? 'text-green-400' : complianceScore >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {complianceScore}/100
                  </span>
                </div>
              </div>
              <Button
                variant="secondary"
                onClick={handleRescan}
                disabled={isLoading || !currentWebsite.url}
                className="flex items-center"
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                {isLoading ? 'Analysiere...' : 'Erneut scannen'}
              </Button>
            </div>
          </div>
        )}

        {/* ✅ LOADING STATE */}
        {(isLoading || isAnalyzing) && (
          <div className="text-center py-8">
            <div className="animate-spin mx-auto mb-4 h-8 w-8 border-4 border-blue-400 border-t-transparent rounded-full"></div>
            <p className="text-gray-300">
              {isAnalyzing ? 'Website wird analysiert...' : 'Daten werden geladen...'}
            </p>
            {currentWebsite && (
              <p className="text-gray-400 text-sm mt-2">
                Analysiere: {currentWebsite.name}
              </p>
            )}
          </div>
        )}

        {/* ✅ ECHTE API-ERGEBNISSE ANZEIGEN */}
        {!isLoading && !isAnalyzing && findings.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white mb-4">
              Gefundene Issues ({findings.length})
            </h3>
            
            {findings.map((finding, index) => {
              const badgeVariant = finding.severity === 'critical' ? 'critical' :
                                finding.severity === 'high' ? 'warning' : 
                                finding.severity === 'medium' ? 'warning' : 'success';

              const IconComponent = finding.severity === 'critical' ? AlertTriangle :
                                  finding.severity === 'high' ? AlertCircle : CheckCircle;

              return (
                <div
                  key={finding.category || `finding-${index}`}
                  className={`rounded-lg p-4 border ${
                    finding.severity === 'critical' || finding.severity === 'high'
                      ? 'bg-red-900/30 border-red-500/50'
                      : finding.severity === 'medium'
                      ? 'bg-yellow-900/30 border-yellow-500/50'
                      : 'bg-green-900/30 border-green-500/50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <IconComponent className={`mr-2 h-5 w-5 ${
                          finding.severity === 'critical' || finding.severity === 'high' ? 'text-red-400' :
                          finding.severity === 'medium' ? 'text-yellow-400' : 'text-green-400'
                        }`} />
                        <Badge variant={badgeVariant}>
                          {finding.severity === 'critical' ? 'Kritisches Problem' :
                           finding.severity === 'high' ? 'Hohes Risiko' :
                           finding.severity === 'medium' ? 'Verbesserung erforderlich' : 'OK'}
                        </Badge>
                      </div>

                      <h3 className="font-semibold mb-2 text-white">
                        {finding.title || (finding.category ? finding.category.replace('_', ' ').toUpperCase() : 'UNBEKANNTE KATEGORIE')}
                        {finding.status === 'error' ? ' - Problem erkannt' : 
                         finding.status === 'warning' ? ' - Verbesserung möglich' : ' - Konform'}
                      </h3>
                      
                      <p className="text-sm text-gray-300 mb-3">{finding.details}</p>

                      {finding.estimated_risk && finding.estimated_risk.abmahn_risiko_euro !== '0€' && (
                        <div className={`rounded p-3 mb-3 ${
                          finding.severity === 'critical' || finding.severity === 'high' ? 'bg-red-800/30' : 'bg-yellow-800/30'
                        }`}>
                          <div className="text-sm font-semibold text-gray-300">Abmahnrisiko:</div>
                          <div className={`text-lg font-bold ${
                            finding.severity === 'critical' || finding.severity === 'high' ? 'text-red-400' : 'text-yellow-400'
                          }`}>
                            {finding.estimated_risk.abmahn_risiko_euro}
                          </div>
                        </div>
                      )}

                      {(finding.severity === 'critical' || finding.severity === 'high' || finding.severity === 'medium') && (
                        <div className="flex space-x-2">
                          <Button
                            size="sm"
                            onClick={() => handleAIFix(finding.category || 'unknown')}
                            disabled={startAIFix.isPending}
                          >
                            <Bot className="mr-1 h-4 w-4" />
                            {startAIFix.isPending ? 'Wird gestartet...' : 'KI-Fix starten'}
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleBookExpert(finding.category || 'unknown')}
                            disabled={bookExpert.isPending}
                          >
                            <UserCheck className="mr-1 h-4 w-4" />
                            {bookExpert.isPending ? 'Wird gebucht...' : 'Experte beauftragen'}
                          </Button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ✅ EMPTY STATE - Verbessert */}
        {!currentWebsite && !isLoading && !isAnalyzing && (
          <div className="text-center py-8">
            <Globe className="mx-auto mb-4 h-12 w-12 text-gray-400" />
            <p className="text-gray-300 mb-4">Keine Website analysiert</p>
            <p className="text-gray-400 text-sm">Geben Sie eine Website-URL ein, um eine Compliance-Analyse zu starten.</p>
          </div>
        )}

        {/* ✅ NO FINDINGS STATE */}
        {currentWebsite && !isLoading && !isAnalyzing && findings.length === 0 && analysisData && (
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
  );
};
