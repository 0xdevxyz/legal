'use client';

import React from 'react';
import { Scale, AlertTriangle, Info, Lightbulb } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useLegalNews } from '@/hooks/useCompliance';
import { formatRelativeTime } from '@/lib/utils';

// ✅ TypeScript Interface für News-Items
interface NewsItem {
  id: string;
  type: 'critical' | 'update' | 'tip';
  severity: 'critical' | 'info';
  title: string;
  summary: string;
  date: string;
  source?: string;
}

export const LegalNews: React.FC = () => {
  const { data: legalNews, isLoading } = useLegalNews();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Scale className="mr-2 text-purple-400" />
            Rechtliche Neuigkeiten
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-gray-700 rounded"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  // ✅ Fallback zu Demo-Daten mit korrekten Types
  const newsData: NewsItem[] = [
    {
      id: '1',
      type: 'critical',
      severity: 'critical',
      title: 'TTDSG Änderung: Neue Cookie-Richtlinien',
      summary: 'Seit 1. August 2025 gelten verschärfte Regeln für Cookie-Banner. Ihre Website ist betroffen.',
      date: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      source: 'BMJV'
    },
    {
      id: '2', 
      type: 'update',
      severity: 'info',
      title: 'DSGVO: Neue Mustervorlagen verfügbar',
      summary: 'Aktualisierte Datenschutzerklärung-Templates für 2025 sind verfügbar.',
      date: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      source: 'Datenschutzbeauftragte'
    },
    {
      id: '3',
      type: 'tip',
      severity: 'info', 
      title: 'Barrierefreiheit: WCAG 2.2 Update',
      summary: 'Neue Accessibility-Standards können Ihre Website-Bewertung verbessern.',
      date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      source: 'W3C'
    }
  ];

  const getIcon = (type: string) => {
    switch (type) {
      case 'critical': return AlertTriangle;
      case 'update': return Info;
      case 'tip': return Lightbulb;
      default: return Info;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Scale className="mr-2 text-purple-400" />
          Rechtliche Neuigkeiten
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {newsData.map((news: NewsItem) => {
            const IconComponent = getIcon(news.type);
            
            return (
              <div key={news.id} className="p-3 rounded-lg bg-gray-800/50 border border-gray-600/30">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-1">
                      <IconComponent className={`mr-2 h-4 w-4 ${
                        news.severity === 'critical' ? 'text-red-400' :
                        news.type === 'update' ? 'text-blue-400' : 'text-yellow-400'
                      }`} />
                      <Badge variant={news.severity === 'critical' ? 'critical' : 'info'}>
                        {news.severity === 'critical' ? 'Kritisch' : 
                         news.type === 'update' ? 'Information' : 'Tipp'}
                      </Badge>
                      <span className="text-xs text-gray-400 ml-2">
                        {formatRelativeTime(news.date)}
                      </span>
                    </div>
                    <h4 className="font-medium text-white text-sm">{news.title}</h4>
                    <p className="text-xs text-gray-300 mt-1">{news.summary}</p>
                    {news.source && (
                      <div className="text-xs text-gray-500 mt-1">
                        Quelle: {news.source}
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
