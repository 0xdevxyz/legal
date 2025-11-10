'use client';

import React, { useState, useEffect } from 'react';
import { Scale, AlertTriangle, Info, Lightbulb, Bell, Newspaper, ChevronRight, ExternalLink, X, Clock } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

// TypeScript Interfaces
interface LegalUpdate {
  id: number;
  update_type: string;
  title: string;
  description: string;
  severity: 'info' | 'warning' | 'critical';
  action_required: boolean;
  published_at: string;
  effective_date?: string;
  url?: string;
}

interface NewsItem {
  id: string;
  type: 'critical' | 'update' | 'tip';
  severity: 'critical' | 'info';
  title: string;
  summary: string;
  date: string;
  source?: string;
  url?: string;
}

export const LegalNews: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'updates' | 'news'>('news'); // Standardmäßig RSS-News anzeigen
  const [legalUpdates, setLegalUpdates] = useState<LegalUpdate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [newsData, setNewsData] = useState<NewsItem[]>([]);
  const [selectedArticle, setSelectedArticle] = useState<NewsItem | null>(null);
  const [showArticleModal, setShowArticleModal] = useState(false);

  useEffect(() => {
    fetchLegalUpdates();
    fetchRSSNews();
  }, []);

  const fetchLegalUpdates = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

      const response = await fetch(`${API_URL}/api/legal/updates?limit=10`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();

        if (data.success && data.updates && data.updates.length > 0) {
          setLegalUpdates(data.updates);
          console.log('✅ Gesetzesänderungen geladen:', data.updates.length);
        } else {
          console.log('⚠️ Keine Gesetzesänderungen gefunden');
          setLegalUpdates([]);
        }
      } else {
        console.error('❌ Legal Updates API Fehler:', response.status, response.statusText);
        setLegalUpdates([]);
      }
    } catch (error) {
      console.error('❌ Fehler beim Laden der Gesetzesänderungen:', error);
      setLegalUpdates([]);
    }
  };

  const fetchRSSNews = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

      const response = await fetch(`${API_URL}/api/legal/news?limit=6`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();

        if (data.success && data.news && data.news.length > 0) {
          // Konvertiere Backend-Format zu Frontend-Format
          const formattedNews = data.news.map((item: any) => ({
            id: String(item.id) || String(Math.random()),
            type: item.news_type || 'update',
            severity: item.severity || 'info',
            title: item.title,
            summary: item.summary,
            date: item.published_date || new Date().toISOString(),
            source: item.source,
            url: item.url
          }));

          setNewsData(formattedNews);
        } else {

        }
      } else {
        console.error('❌ RSS API Fehler:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('❌ Fehler beim Laden der RSS-News:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // newsData wird jetzt über API geladen (siehe fetchRSSNews)

  const handleArticleClick = (article: NewsItem) => {

    setSelectedArticle(article);
    setShowArticleModal(true);
  };

  const closeArticleModal = () => {
    setShowArticleModal(false);
    setTimeout(() => setSelectedArticle(null), 300); // Cleanup nach Animation
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'critical': return AlertTriangle;
      case 'update': return Info;
      case 'tip': return Lightbulb;
      default: return Info;
    }
  };

  const getSeverityBadge = (severity: string) => {
    const configs = {
      critical: { color: 'bg-red-500/20 text-red-400 border-red-500', icon: '🚨' },
      warning: { color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500', icon: '⚠️' },
      info: { color: 'bg-blue-500/20 text-blue-400 border-blue-500', icon: 'ℹ️' }
    };
    return configs[severity as keyof typeof configs] || configs.info;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffHours < 24) return `vor ${diffHours}h`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `vor ${diffDays}d`;
    return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' });
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-xl">
              <Scale className="w-6 h-6 text-purple-400" />
            </div>
            <span>Rechtliche Updates</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-20 bg-zinc-800/50 rounded-xl"></div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-3">
          <div className="p-2.5 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-xl">
            <Scale className="w-6 h-6 text-purple-400" />
          </div>
          <span>Rechtliche Updates & News</span>
        </CardTitle>
        
        {/* Tabs */}
        <div className="flex gap-3 mt-5">
          <button
            onClick={() => setActiveTab('updates')}
            className={`flex-1 px-5 py-3 rounded-xl text-sm font-semibold transition-all duration-300 ${
              activeTab === 'updates'
                ? 'bg-purple-500/15 text-purple-400 border-2 border-purple-500/50 shadow-lg shadow-purple-500/10'
                : 'glass-card text-zinc-400 hover:glass-strong hover:text-white'
            }`}
          >
            <Bell className="w-4 h-4 inline mr-2" />
            Gesetzesänderungen
            {legalUpdates.filter(u => u.action_required).length > 0 && (
              <span className="ml-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full font-bold">
                {legalUpdates.filter(u => u.action_required).length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('news')}
            className={`flex-1 px-5 py-3 rounded-xl text-sm font-semibold transition-all duration-300 ${
              activeTab === 'news'
                ? 'bg-sky-500/15 text-sky-400 border-2 border-sky-500/50 shadow-lg shadow-sky-500/10'
                : 'glass-card text-zinc-400 hover:glass-strong hover:text-white'
            }`}
          >
            <Newspaper className="w-4 h-4 inline mr-2" />
            Allgemeine News
            {newsData.length > 0 && (
              <span className="ml-2 bg-sky-500 text-white text-xs px-2 py-1 rounded-full font-bold">
                {newsData.length}
              </span>
            )}
          </button>
        </div>
      </CardHeader>

      <CardContent>
        {activeTab === 'updates' ? (
          // Gesetzesänderungen Tab
          legalUpdates.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {legalUpdates.map((update) => {
              const badge = getSeverityBadge(update.severity);
              return (
                <div
                  key={update.id}
                  className={`p-4 rounded-lg border transition-all hover:bg-gray-700/50 cursor-pointer ${
                    update.action_required
                      ? 'bg-red-500/10 border-red-500/30'
                      : 'bg-gray-800 border-gray-700'
                  }`}
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${badge.color}`}>
                          {badge.icon} {update.severity.toUpperCase()}
                        </span>
                        {update.action_required && (
                          <span className="px-2 py-0.5 rounded text-xs font-semibold bg-red-500 text-white">
                            Aktion erforderlich
                          </span>
                        )}
                        <span className="px-2 py-0.5 rounded text-xs bg-gray-700 text-gray-400">
                          {update.update_type.toUpperCase()}
                        </span>
                      </div>
                      <h4 className="text-white font-semibold text-sm leading-tight">
                        {update.title}
                      </h4>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0 ml-2" />
                  </div>

                  {/* Description */}
                  <p className="text-gray-400 text-xs leading-relaxed mb-2">
                    {update.description}
                  </p>

                  {/* Footer */}
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{formatDate(update.published_at)}</span>
                    {update.effective_date && (
                      <span>Gilt ab: {new Date(update.effective_date).toLocaleDateString('de-DE')}</span>
                    )}
                  </div>

                  {/* Action Button */}
                  {update.action_required && (
                    <button className="mt-3 w-full bg-red-600 hover:bg-red-700 text-white text-xs font-semibold py-2 px-4 rounded-lg transition">
                      Jetzt neu scannen
                    </button>
                  )}
                </div>
              );
            })}
            </div>
          ) : (
            <div className="text-center py-8">
              <Bell className="w-12 h-12 text-gray-600 mx-auto mb-3" />
              <p className="text-gray-400 text-sm">
                Keine aktuellen Gesetzesänderungen
              </p>
              <p className="text-gray-500 text-xs mt-1">
                Sie werden benachrichtigt, sobald es neue Updates gibt
              </p>
            </div>
          )
        ) : (
          // Allgemeine News Tab
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {newsData.map((item) => {
            const Icon = getIcon(item.type);
            const badge = getSeverityBadge(item.severity);

            return (
              <div
                key={item.id}
                onClick={() => handleArticleClick(item)}
                className="bg-gray-800 hover:bg-gray-700 p-4 rounded-lg border border-gray-700 transition-all cursor-pointer group"
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${badge.color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-1">
                      <h4 className="text-white font-semibold text-sm leading-tight group-hover:text-blue-400 transition-colors">
                        {item.title}
                      </h4>
                      <ChevronRight className="w-4 h-4 text-gray-500 group-hover:text-blue-400 transition-colors flex-shrink-0 ml-2" />
                    </div>
                    <p className="text-gray-400 text-xs leading-relaxed mb-2">
                      {item.summary}
                    </p>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>{item.source}</span>
                      <span>{formatDate(item.date)}</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
          </div>
        )}
      </CardContent>

      {/* Article Detail Modal */}
      {showArticleModal && selectedArticle && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
          onClick={closeArticleModal}
        >
          <div 
            className="bg-gray-800 rounded-xl max-w-3xl w-full max-h-[90vh] overflow-hidden shadow-2xl border border-gray-700"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between p-6 border-b border-gray-700">
              <div className="flex-1 pr-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getSeverityBadge(selectedArticle.severity).color}`}>
                    {selectedArticle.severity.toUpperCase()}
                  </span>
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-gray-700 text-gray-300 border border-gray-600">
                    {selectedArticle.type.toUpperCase()}
                  </span>
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  {selectedArticle.title}
                </h2>
                <div className="flex items-center gap-4 text-sm text-gray-400">
                  <span className="flex items-center gap-1">
                    <Newspaper className="w-4 h-4" />
                    {selectedArticle.source}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {formatDate(selectedArticle.date)}
                  </span>
                </div>
              </div>
              <button
                onClick={closeArticleModal}
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X className="w-6 h-6 text-gray-400" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
              <div className="prose prose-invert max-w-none">
                <p className="text-gray-300 text-base leading-relaxed mb-4">
                  {selectedArticle.summary}
                </p>
                
                {/* Optional: Full content if available */}
                {(selectedArticle as any).content && (
                  <div className="text-gray-400 text-sm leading-relaxed mt-4">
                    {(selectedArticle as any).content}
                  </div>
                )}

                {/* Compliance-Relevanz Box */}
                <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
                    <Scale className="w-5 h-5 text-blue-400" />
                    Relevanz für Ihre Compliance
                  </h3>
                  <p className="text-gray-400 text-sm">
                    Diese Nachricht kann Auswirkungen auf Ihre Website-Compliance haben. 
                    Prüfen Sie, ob Ihre Seite die genannten Anforderungen erfüllt.
                  </p>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between p-6 border-t border-gray-700 bg-gray-800/50">
              <button
                onClick={closeArticleModal}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Schließen
              </button>
              {selectedArticle.url && (
                <a
                  href={selectedArticle.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg transition-colors flex items-center gap-2"
                  onClick={(e) => e.stopPropagation()}
                >
                  Zum Original-Artikel
                  <ExternalLink className="w-4 h-4" />
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};
