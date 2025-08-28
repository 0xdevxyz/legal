'use client';

import React from 'react';
import { Globe, RefreshCw, AlertTriangle, AlertCircle, CheckCircle, Bot, UserCheck } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useDashboardStore } from '@/stores/dashboard';
import { useStartAIFix, useBookExpert } from '@/hooks/useCompliance';
import { formatRelativeTime } from '@/lib/utils';

export const WebsiteAnalysis: React.FC = () => {
  const { currentWebsite, analysisData } = useDashboardStore();
  const startAIFix = useStartAIFix();
  const bookExpert = useBookExpert();

  const handleRescan = () => {
    console.log('Rescanning website...');
  };

  const handleAIFix = (issueId: string) => {
    startAIFix.mutate(issueId);
  };

  const handleBookExpert = (issueId: string) => {
    bookExpert.mutate(issueId);
  };

  if (!currentWebsite) return null;

  const mockFindings = [
    {
      id: 'impressum',
      status: 'error' as const,
      severity: 'critical' as const,
      title: 'Impressum unvollständig',
      description: 'Das Impressum entspricht nicht den Anforderungen des TMG §5. Fehlende Angaben: Registergericht, Handelsregisternummer, Umsatzsteuer-ID.',
      abmahn_risiko_euro: '2.000€ - 5.000€',
      fix_available: true,
      icon: AlertTriangle
    },
    {
      id: 'cookies',
      status: 'warning' as const,
      severity: 'medium' as const,
      title: 'Cookie-Banner nicht DSGVO-konform',
      description: 'Der Cookie-Banner erfüllt nicht die DSGVO-Anforderungen. Fehlende Opt-out-Möglichkeiten für nicht-essenzielle Cookies.',
      abmahn_risiko_euro: '1.000€ - 3.000€',
      fix_available: true,
      icon: AlertCircle
    },
    {
      id: 'datenschutz',
      status: 'success' as const,
      severity: 'low' as const,
      title: 'Datenschutzerklärung vollständig',
      description: 'Die Datenschutzerklärung entspricht den DSGVO-Anforderungen und ist vollständig.',
      abmahn_risiko_euro: '0€',
      fix_available: false,
      icon: CheckCircle
    }
  ];

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center">
            <Globe className="mr-2 text-blue-400" />
            Aktuelle Website-Analyse
          </CardTitle>
          <div className="text-sm text-gray-400">
            Zuletzt gescannt: {formatRelativeTime(currentWebsite.lastScan)}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="bg-gray-800/50 rounded-lg p-4 mb-4 border border-gray-600/30">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-400">Analysierte Website:</div>
              <div className="text-lg font-semibold text-blue-400">{currentWebsite.url}</div>
            </div>
            <Button 
              variant="secondary" 
              onClick={handleRescan}
              className="flex items-center"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Erneut scannen
            </Button>
          </div>
        </div>

        <div className="space-y-4">
          {mockFindings.map((finding) => {
            const IconComponent = finding.icon;
            const badgeVariant = finding.status === 'error' ? 'critical' : 
                                finding.status === 'warning' ? 'warning' : 'success';

            return (
              <div
                key={finding.id}
                className={`rounded-lg p-4 border ${
                  finding.status === 'error' 
                    ? 'bg-red-900/30 border-red-500/50' 
                    : finding.status === 'warning'
                    ? 'bg-yellow-900/30 border-yellow-500/50'
                    : 'bg-green-900/30 border-green-500/50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <IconComponent className={`mr-2 h-5 w-5 ${
                        finding.status === 'error' ? 'text-red-400' :
                        finding.status === 'warning' ? 'text-yellow-400' : 'text-green-400'
                      }`} />
                      <Badge variant={badgeVariant}>
                        {finding.severity === 'critical' ? 'Kritisches Problem' :
                         finding.severity === 'medium' ? 'Verbesserung erforderlich' : 'OK'}
                      </Badge>
                    </div>
                    
                    <h3 className="font-semibold mb-2 text-white">{finding.title}</h3>
                    <p className="text-sm text-gray-300 mb-3">{finding.description}</p>
                    
                    {finding.abmahn_risiko_euro !== '0€' && (
                      <div className={`rounded p-3 mb-3 ${
                        finding.status === 'error' ? 'bg-red-800/30' : 'bg-yellow-800/30'
                      }`}>
                        <div className="text-sm font-semibold text-gray-300">Abmahnrisiko:</div>
                        <div className={`text-lg font-bold ${
                          finding.status === 'error' ? 'text-red-400' : 'text-yellow-400'
                        }`}>
                          {finding.abmahn_risiko_euro}
                        </div>
                      </div>
                    )}
                    
                    {finding.fix_available && (
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          onClick={() => handleAIFix(finding.id)}
                          isLoading={startAIFix.isPending}
                        >
                          <Bot className="mr-1 h-4 w-4" />
                          KI-Fix starten
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleBookExpert(finding.id)}
                          isLoading={bookExpert.isPending}
                        >
                          <UserCheck className="mr-1 h-4 w-4" />
                          Experte beauftragen
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};
