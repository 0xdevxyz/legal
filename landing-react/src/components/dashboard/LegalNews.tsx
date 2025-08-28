'use client';

import React from 'react';
import { Newspaper, AlertTriangle, Info, Lightbulb, Bot, Download, Sparkles } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatRelativeTime } from '@/lib/utils';

export const LegalNews: React.FC = () => {
  const mockNews = [
    {
      id: '1',
      type: 'critical' as const,
      title: 'TTDSG Änderung: Neue Cookie-Richtlinien',
      description: 'Seit 1. August 2025 gelten verschärfte Regeln für Cookie-Banner. Ihre Website ist betroffen.',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      action_available: true,
      action_text: 'Automatisch anpassen',
      icon: AlertTriangle
    },
    {
      id: '2',
      type: 'info' as const,
      title: 'DSGVO: Neue Mustervorlagen verfügbar',
      description: 'Aktualisierte Datenschutzerklärung-Templates für 2025 sind verfügbar.',
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      action_available: true,
      action_text: 'Templates abrufen',
      icon: Info
    },
    {
      id: '3',
      type: 'tip' as const,
      title: 'Barrierefreiheit: WCAG 2.2 Update',
      description: 'Neue Accessibility-Standards können Ihre Website-Bewertung verbessern.',
      timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      action_available: true,
      action_text: 'Optimierung starten',
      icon: Lightbulb
    }
  ];

  const handleAction = (newsId: string, actionText: string) => {
    switch (actionText) {
      case 'Automatisch anpassen':
        console.log('Starting automatic cookie adaptation...');
        alert('Cookie-Banner wird an neue TTDSG-Richtlinien angepasst!');
        break;
      case 'Templates abrufen':
        console.log('Downloading templates...');
        alert('Templates werden vorbereitet und per E-Mail gesendet.');
        break;
      case 'Optimierung starten':
        console.log('Starting accessibility optimization...');
        alert('Barrierefreiheits-Optimierung gestartet!');
        break;
      default:
        console.log(`Action: ${actionText} for news: ${newsId}`);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Newspaper className="mr-2 text-yellow-400" />
          Rechtliche Neuigkeiten
        </CardTitle>
      </CardHeader>

      <CardContent>
        <div className="space-y-4 max-h-64 overflow-y-auto">
          {mockNews.map((news) => {
            const IconComponent = news.icon;
            const badgeVariant = news.type === 'critical' ? 'critical' : 
                                news.type === 'info' ? 'info' : 'warning';
            
            const badgeText = news.type === 'critical' ? 'Kritisch' :
                             news.type === 'info' ? 'Information' : 'Tipp';

            const ActionIcon = news.action_text === 'Automatisch anpassen' ? Bot :
                              news.action_text === 'Templates abrufen' ? Download : Sparkles;

            return (
              <div
                key={news.id}
                className={`rounded-lg p-3 border ${
                  news.type === 'critical' 
                    ? 'bg-red-900/30 border-red-500/50' 
                    : news.type === 'info'
                    ? 'bg-yellow-900/30 border-yellow-500/50'
                    : 'bg-blue-900/30 border-blue-500/50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-1">
                      <IconComponent className={`mr-2 h-4 w-4 ${
                        news.type === 'critical' ? 'text-red-400' :
                        news.type === 'info' ? 'text-yellow-400' : 'text-blue-400'
                      }`} />
                      <Badge variant={badgeVariant} className="text-xs">
                        {badgeText}
                      </Badge>
                      <span className="text-xs text-gray-400 ml-2">
                        {formatRelativeTime(news.timestamp)}
                      </span>
                    </div>
                    
                    <h4 className="font-medium mb-1 text-white text-sm">{news.title}</h4>
                    <p className="text-sm text-gray-300 mb-2">{news.description}</p>
                    
                    {news.action_available && news.action_text && (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => handleAction(news.id, news.action_text)}
                        className="text-xs px-3 py-1"
                      >
                        <ActionIcon className="mr-1 h-3 w-3" />
                        {news.action_text}
                      </Button>
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
