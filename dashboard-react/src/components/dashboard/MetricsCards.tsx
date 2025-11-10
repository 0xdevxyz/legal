'use client';

import React, { useEffect } from 'react';
import { TrendingUp, Globe, AlertTriangle, BarChart3, Sparkles } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { useDashboardStore } from '@/stores/dashboard';
import { useDashboardMetrics } from '@/hooks/useMetrics';

export const MetricsCards: React.FC = () => {
  const { updateMetrics } = useDashboardStore();
  const { metrics: apiMetrics, isLoading } = useDashboardMetrics();
  
  // Update store when API data arrives
  useEffect(() => {
    if (apiMetrics) {
      updateMetrics({
        totalScore: apiMetrics.totalScore,
        websites: apiMetrics.websites,
        criticalIssues: apiMetrics.criticalIssues,
        scansAvailable: apiMetrics.scansAvailable,
        scansUsed: apiMetrics.scansUsed
      });
    }
  }, [apiMetrics, updateMetrics]);
  
  // Use API metrics if available, otherwise fall back to store
  const { metrics } = useDashboardStore();

  // Hole Limits aus API-Metriken
  const aiFixesUsed = apiMetrics?.aiFixesUsed ?? 0;
  const aiFixesMax = apiMetrics?.aiFixesMax ?? 1;
  const websitesMax = apiMetrics?.websitesMax ?? 3;

  // Berechne Trend-Anzeigen
  const getScoreTrendDisplay = () => {
    const trend = apiMetrics?.scoreTrend;
    if (trend === null || trend === undefined) {
      return { text: 'Keine Vergleichsdaten', type: 'neutral' as const };
    }
    if (trend > 0) {
      return { text: `+${trend}% diese Woche`, type: 'positive' as const };
    } else if (trend < 0) {
      return { text: `${trend}% diese Woche`, type: 'negative' as const };
    }
    return { text: 'Unverändert', type: 'neutral' as const };
  };

  const getCriticalTrendDisplay = () => {
    const trend = apiMetrics?.criticalTrend;
    if (trend === null || trend === undefined) {
      return { text: 'Sofortige Beachtung', type: 'negative' as const };
    }
    if (trend > 0) {
      return { text: `+${trend} seit letzter Woche`, type: 'negative' as const };
    } else if (trend < 0) {
      return { text: `${trend} seit letzter Woche`, type: 'positive' as const };
    }
    return { text: 'Unverändert', type: 'neutral' as const };
  };

  const scoreTrend = getScoreTrendDisplay();
  const criticalTrend = getCriticalTrendDisplay();

  const metricCards = [
    {
      title: 'Gesamt-Score',
      value: metrics.totalScore,
      change: scoreTrend.text,
      changeType: scoreTrend.type,
      icon: TrendingUp,
      color: 'text-green-400',
      bgColor: 'bg-green-500/20'
    },
    {
      title: 'Analysen',
      value: `${metrics.websites}/${websitesMax}`,
      change: `${websitesMax - metrics.websites} verfügbar`,
      changeType: metrics.websites >= websitesMax ? 'negative' as const : 'neutral' as const,
      icon: Globe,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20'
    },
    {
      title: 'KI-Optimierungen',
      value: `${aiFixesUsed}/${aiFixesMax}`,
      change: aiFixesUsed >= aiFixesMax ? 'Limit erreicht' : `${aiFixesMax - aiFixesUsed} verfügbar`,
      changeType: aiFixesUsed >= aiFixesMax ? 'negative' as const : 'positive' as const,
      icon: Sparkles,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/20'
    },
    {
      title: 'Kritische Issues',
      value: metrics.criticalIssues,
      change: criticalTrend.text,
      changeType: criticalTrend.type,
      icon: AlertTriangle,
      color: 'text-red-400',
      bgColor: 'bg-red-500/20'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      {metricCards.map((metric, index) => {
        const IconComponent = metric.icon;
        
        return (
          <Card key={index} hover className="relative overflow-hidden">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm mb-1">{metric.title}</p>
                <p className="text-3xl font-bold text-white mb-1">{metric.value}</p>
                <p className={`text-sm ${
                  metric.changeType === 'positive' ? 'text-green-400' :
                  metric.changeType === 'negative' ? 'text-red-400' : 'text-gray-400'
                }`}>
                  {metric.change}
                </p>
              </div>
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${metric.bgColor}`}>
                <IconComponent className={`h-6 w-6 ${metric.color}`} />
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
};
