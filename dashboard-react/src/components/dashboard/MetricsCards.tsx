'use client';

import React from 'react';
import { TrendingUp, Globe, AlertTriangle, BarChart3 } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { useDashboardStore } from '@/stores/dashboard';

export const MetricsCards: React.FC = () => {
  const { metrics } = useDashboardStore();

  const metricCards = [
    {
      title: 'Gesamt-Score',
      value: metrics.totalScore,
      change: '+2.3% diese Woche',
      changeType: 'positive' as const,
      icon: TrendingUp,
      color: 'text-green-400',
      bgColor: 'bg-green-500/20'
    },
    {
      title: 'Websites',
      value: metrics.websites,
      change: '3 aktive Scans',
      changeType: 'neutral' as const,
      icon: Globe,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20'
    },
    {
      title: 'Kritische Issues',
      value: metrics.criticalIssues,
      change: 'Sofortige Beachtung',
      changeType: 'negative' as const,
      icon: AlertTriangle,
      color: 'text-red-400',
      bgColor: 'bg-red-500/20'
    },
    {
      title: 'Scans verfügbar',
      value: `${metrics.scansUsed}/${metrics.scansAvailable}`,
      change: `${Math.round((metrics.scansUsed / metrics.scansAvailable) * 100)}% genutzt`,
      changeType: 'neutral' as const,
      icon: BarChart3,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/20'
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
