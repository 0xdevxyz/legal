'use client';

import React, { useState } from 'react';
import { Clock, TrendingUp, TrendingDown, Globe, ChevronRight } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { useScanHistory } from '@/hooks/useCompliance';
import { formatRelativeTime } from '@/lib/utils';

interface ScanHistoryPanelProps {
  limit?: number;
  onSelectScan?: (scanId: string) => void;
}

export const ScanHistoryPanel: React.FC<ScanHistoryPanelProps> = ({ 
  limit = 5,
  onSelectScan 
}) => {
  const { data: scanHistory = [], isLoading } = useScanHistory(limit);
  const [expandedScan, setExpandedScan] = useState<string | null>(null);

  if (isLoading) {
    return (
      <Card className="bg-gray-800/70 border-gray-700">
        <CardContent className="py-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full" />
            <span className="ml-3 text-gray-400">Lade Scan-Historie...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!scanHistory || scanHistory.length === 0) {
    return null;
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getScoreTrend = (currentScore: number, previousScore?: number) => {
    if (!previousScore) return null;
    
    const diff = currentScore - previousScore;
    if (diff > 0) {
      return (
        <span className="flex items-center text-green-400 text-sm ml-2">
          <TrendingUp className="w-4 h-4 mr-1" />
          +{diff}
        </span>
      );
    } else if (diff < 0) {
      return (
        <span className="flex items-center text-red-400 text-sm ml-2">
          <TrendingDown className="w-4 h-4 mr-1" />
          {diff}
        </span>
      );
    }
    return null;
  };

  return (
    <Card className="bg-gray-800/70 border-gray-700">
      <CardHeader>
        <CardTitle className="flex items-center text-lg text-white">
          <Clock className="w-5 h-5 mr-2 text-blue-400" />
          Letzte Scans
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {scanHistory.map((scan: any, index: number) => {
            const isExpanded = expandedScan === scan.scan_id;
            const previousScan = scanHistory[index + 1];

            return (
              <div
                key={scan.scan_id}
                className="bg-gray-900/50 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-all cursor-pointer"
                onClick={() => {
                  if (onSelectScan) {
                    onSelectScan(scan.scan_id);
                  }
                  setExpandedScan(isExpanded ? null : scan.scan_id);
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Globe className="w-4 h-4 text-blue-400" />
                      <span className="text-white font-medium truncate max-w-[300px]">
                        {scan.url}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-gray-400">
                        {formatRelativeTime(scan.scan_timestamp)}
                      </span>
                      
                      <div className="flex items-center">
                        <span className="text-gray-400 mr-1">Score:</span>
                        <span className={`font-bold ${getScoreColor(scan.compliance_score)}`}>
                          {scan.compliance_score}/100
                        </span>
                        {getScoreTrend(scan.compliance_score, previousScan?.compliance_score)}
                      </div>
                      
                      {scan.critical_issues > 0 && (
                        <span className="text-red-400 font-medium">
                          🔴 {scan.critical_issues} Kritisch
                        </span>
                      )}
                      
                      {scan.warning_issues > 0 && (
                        <span className="text-yellow-400 font-medium">
                          ⚠️ {scan.warning_issues} Warnungen
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <ChevronRight 
                    className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                  />
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-gray-700">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-400">Gesamtrisiko:</span>
                        <div className="text-red-400 font-bold">
                          {new Intl.NumberFormat('de-DE', { 
                            style: 'currency', 
                            currency: 'EUR' 
                          }).format(scan.total_risk_euro || 0)}
                        </div>
                      </div>
                      
                      <div>
                        <span className="text-gray-400">Issues gesamt:</span>
                        <div className="text-white font-bold">
                          {scan.total_issues}
                        </div>
                      </div>
                    </div>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onSelectScan) {
                          onSelectScan(scan.scan_id);
                        }
                      }}
                      className="mt-3 w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                      Scan laden
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

