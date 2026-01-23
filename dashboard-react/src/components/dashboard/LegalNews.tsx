'use client';

import React, { useState, useEffect } from 'react';
import { 
  Scale, AlertTriangle, Info, Lightbulb, Bell, Newspaper, ChevronRight, 
  ExternalLink, X, Clock, Search, Shield, FileText, Eye, Zap,
  TrendingUp, Archive, ThumbsUp, ThumbsDown, AlertCircle
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useRouter } from 'next/navigation';
import { LegalArchiveModal } from './LegalArchiveModal';
import { SkeletonLegalNews } from '@/components/ui/Skeleton';

// TypeScript Interfaces
interface AIClassification {
  action_required: boolean;
  confidence?: string;
  impact_score?: number;
  primary_action?: {
    action_type: string;
    button_text: string;
    button_color: string;
    icon: string;
  };
  recommended_actions?: Array<{
    action_type: string;
    title: string;
    description: string;
    button_text: string;
    button_color: string;
    icon: string;
  }>;
  reasoning?: string;
  user_impact?: string;
  consequences_if_ignored?: string;
  classification_id?: number;
}

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
  
  // KI-Klassifizierung
  classification?: AIClassification;
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
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'updates' | 'news'>('updates'); // KI-Updates per Default
  const [legalUpdates, setLegalUpdates] = useState<LegalUpdate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [newsData, setNewsData] = useState<NewsItem[]>([]);
  const [selectedArticle, setSelectedArticle] = useState<NewsItem | null>(null);
  const [showArticleModal, setShowArticleModal] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null); // ✅ Fehlerstatus für API
  const [showArchive, setShowArchive] = useState(false);
  const [selectedUpdate, setSelectedUpdate] = useState<LegalUpdate | null>(null);

  useEffect(() => {
    fetchLegalUpdates();
    fetchRSSNews();
  }, []);

  // KI-gesteuerte Aktionen
  const handlePrimaryAction = async (update: LegalUpdate, event?: React.MouseEvent) => {
    // Verhindere Standard-Navigation
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    
    if (!update.classification?.primary_action) {
      // Fallback: Zeige Details
      setSelectedUpdate(update);
      return;
    }
    
    const action = update.classification.primary_action;
    const startTime = Date.now();
    
    // ✅ PRÜFE: Hat User eine Website?
    if ((action as any).has_website === false && action.action_type !== 'info_only' && action.action_type !== 'information_only') {
      // Zeige Warnung + Details
      const message = `⚠️ Keine Website hinterlegt\n\n${update.title}\n\nUm diese Gesetzesänderung auf Ihre Website anzuwenden, müssen Sie zunächst eine Website scannen.\n\n📋 Details:\n${update.classification.reasoning || 'Keine Details verfügbar'}\n\nMöchten Sie jetzt eine Website scannen?`;
      
      if (confirm(message)) {
        window.location.href = '/';
      } else {
        // Zeige trotzdem Details-Modal
        setSelectedUpdate(update);
      }
      return;
    }
    
    // ✅ ZEIGE DETAILS + AKTION
    // Zeige Details-Modal mit reasoning, user_impact, consequences
    const detailsMessage = `📋 ${update.title}\n\n${(action as any).description || ''}\n\n⏱️ Dauer: ${(action as any).estimated_time || 'N/A'}\n\n🤔 Begründung:\n${update.classification.reasoning || 'Keine Details'}\n\n👤 Auswirkungen:\n${update.classification.user_impact || 'Keine Angaben'}\n\n${update.classification.consequences_if_ignored ? `⚠️ Folgen bei Ignorierung:\n${update.classification.consequences_if_ignored}` : ''}\n\nMöchten Sie fortfahren?`;
    
    if (!confirm(detailsMessage)) {
      return;
    }
    
    // Track Feedback (impliziter Click)
    trackFeedback(update, 'implicit_click', 'click_primary_button', startTime);
    
    console.log('🔍 Action triggered:', action.action_type, 'für Update:', update.title);
    
    // Führe Aktion aus
    switch (action.action_type) {
      case 'scan_website':
        // ✅ ECHTE SCAN-INTEGRATION: Navigiere zur Hauptseite mit Scan-Trigger
        const scanUrl = `/?trigger_scan=true&legal_update_id=${update.id}&legal_context=${encodeURIComponent(update.title)}`;
        window.location.href = scanUrl;
        break;
        
      case 'update_cookie_banner':
        // ✅ KI-ANALYSE: Starte Cookie-Compliance Analyse
        const cookieAnalysisUrl = `/?trigger_scan=true&focus=cookies&legal_update_id=${update.id}&legal_context=${encodeURIComponent(update.title)}&ai_analysis=cookie_banner`;
        // Zeige Hinweis BEVOR der Scan startet
        if (confirm(`🍪 Cookie-Banner KI-Analyse\n\nWegen: ${update.title}\n\nDie KI wird Ihren Cookie-Banner analysieren und konkrete Verbesserungsvorschläge machen.\n\nMöchten Sie die Analyse jetzt starten?`)) {
          window.location.href = cookieAnalysisUrl;
        }
        break;
        
      case 'review_policy':
      case 'update_privacy_policy':
        // ✅ Trigger Scan mit Fokus auf Datenschutz
        const privacyUrl = `/?trigger_scan=true&focus=datenschutz&legal_update_id=${update.id}&legal_context=${encodeURIComponent(update.title)}`;
        window.location.href = privacyUrl;
        break;
        
      case 'update_impressum':
        // ✅ Trigger Scan mit Fokus auf Impressum
        const impressumUrl = `/?trigger_scan=true&focus=impressum&legal_update_id=${update.id}&legal_context=${encodeURIComponent(update.title)}`;
        window.location.href = impressumUrl;
        break;
        
      case 'check_accessibility':
        // ✅ DIREKT ZUM ACCESSIBILITY WIDGET (Tool ist bereits implementiert!)
        // Scroll zum Widget falls auf der Seite, sonst navigiere zur Hauptseite
        const accessibilityWidget = document.querySelector('[data-widget="accessibility"]') || document.getElementById('accessibility-widget');
        if (accessibilityWidget) {
          accessibilityWidget.scrollIntoView({ behavior: 'smooth', block: 'center' });
          setTimeout(() => {
            alert(`♿ Barrierefreiheit-Widget\n\nWegen: ${update.title}\n\nIhr Accessibility-Widget (unten rechts) hilft Ihnen, WCAG 2.1 AA-konform zu werden.\n\nDas Widget ist bereits aktiv und behebt automatisch viele Barrierefreiheits-Probleme!`);
          }, 500);
        } else {
          // Falls nicht auf Seite, navigiere zur Hauptseite und zeige Widget-Hinweis
          alert(`♿ Barrierefreiheit-Tool\n\nWegen: ${update.title}\n\nIhr Accessibility-Widget (unten rechts auf der Hauptseite) hilft Ihnen WCAG-konform zu werden!`);
          window.location.href = '/';
        }
        break;
        
      case 'contact_support':
      case 'consult_legal':
        window.open('mailto:support@complyo.tech?subject=Rechtsberatung: ' + update.title, '_blank');
        break;
        
      case 'info_only':
        // Nur Details zeigen
        setSelectedUpdate(update);
        break;
        
      default:
        console.log('⚠️ Unbekannter Action-Type:', action.action_type);
        setSelectedUpdate(update);
    }
  };
  
  const trackFeedback = async (
    update: LegalUpdate, 
    feedbackType: string, 
    userAction?: string,
    startTime?: number
  ) => {
    // Skip if no classification_id (required by backend)
    if (!update.classification?.classification_id) {
      return;
    }

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';
      const timeToAction = startTime ? Math.floor((Date.now() - startTime) / 1000) : null;
      
      await fetch(`${API_URL}/api/legal-ai/feedback`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          update_id: String(update.id),
          classification_id: update.classification.classification_id,
          feedback_type: feedbackType,
          user_action: userAction,
          time_to_action: timeToAction,
          context_data: {
            severity: update.severity,
            update_type: update.update_type
          }
        })
      });
    } catch (error) {
      // Silent fail - nicht kritisch
      console.debug('Feedback tracking skipped:', error);
    }
  };
  
  const handleFeedback = async (update: LegalUpdate, helpful: boolean) => {
    await trackFeedback(
      update, 
      helpful ? 'explicit_helpful' : 'explicit_not_helpful'
    );
    
    // UI-Feedback
    alert(helpful ? '✅ Danke für Ihr Feedback!' : '📝 Danke! Wir werden das verbessern.');
  };
  
  const getActionIcon = (iconName: string) => {
    const icons: Record<string, any> = {
      Search, Shield, FileText, Eye, Zap, AlertTriangle, Scale, Info, Lightbulb
    };
    return icons[iconName] || Info;
  };
  
  const handleStartScan = () => {
    // Navigiere zur Hauptseite wo der User eine neue Analyse starten kann
    window.location.href = '/';
  };

  const fetchLegalUpdates = async () => {
    setLoadError(null);
    
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

      // ✅ Lade ALLE Updates (include_info_only=true), damit auch News ohne action_required sichtbar sind
      const response = await fetch(`${API_URL}/api/legal-ai/updates?limit=10&include_info_only=true`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.ok) {
        const updates = await response.json();
        
        console.log('📥 Legal Updates geladen:', updates?.length || 0);
        
        // Parse Classification-Daten
        const parsedUpdates = (updates || []).map((update: any) => ({
          ...update,
          severity: update.severity || (update.action_required ? 'warning' : 'info'),
          classification: update.primary_action ? {
            action_required: update.action_required,
            confidence: update.confidence,
            impact_score: update.impact_score,
            primary_action: update.primary_action,
            recommended_actions: update.recommended_actions,
            reasoning: update.reasoning,
            user_impact: update.user_impact,
            consequences_if_ignored: update.consequences_if_ignored,
            classification_id: update.classification_id
          } : null
        }));
        
        setLegalUpdates(parsedUpdates);
      } else {
        console.error('❌ Legal Updates API Fehler:', response.status, response.statusText);
        setLoadError(`API-Fehler: ${response.status} ${response.statusText}`);
        setLegalUpdates([]);
      }
    } catch (error) {
      console.error('❌ Fehler beim Laden der Gesetzesänderungen:', error);
      setLoadError('Verbindung zur API fehlgeschlagen. Bitte später erneut versuchen.');
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
          <SkeletonLegalNews />
        </CardContent>
        <CardContent>
          <SkeletonLegalNews />
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
          // Gesetzesänderungen Tab mit KI-Klassifizierung
          legalUpdates.length > 0 ? (
            <div className="space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {legalUpdates.map((update) => {
                const badge = getSeverityBadge(update.severity);
                const classification = update.classification;
                const primaryAction = classification?.primary_action;
                const ActionIcon = primaryAction ? getActionIcon(primaryAction.icon) : AlertTriangle;
                
                // Dynamische Button-Farbe basierend auf KI
                const buttonColorMap: Record<string, string> = {
                  'red': 'bg-red-600 hover:bg-red-700 border-red-500',
                  'orange': 'bg-orange-600 hover:bg-orange-700 border-orange-500',
                  'blue': 'bg-blue-600 hover:bg-blue-700 border-blue-500',
                  'gray': 'bg-gray-600 hover:bg-gray-700 border-gray-500',
                  'green': 'bg-green-600 hover:bg-green-700 border-green-500'
                };
                const buttonColor = primaryAction ? buttonColorMap[primaryAction.button_color] || buttonColorMap['blue'] : buttonColorMap['red'];
                
                return (
                  <div
                    key={update.id}
                    className={`p-4 rounded-lg border transition-all hover:shadow-lg ${
                      update.action_required
                        ? 'bg-gradient-to-br from-red-500/10 to-orange-500/5 border-red-500/30 hover:border-red-500/50'
                        : 'bg-gradient-to-br from-gray-800 to-gray-900 border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2 flex-wrap">
                          <span className={`px-2 py-1 rounded-md text-xs font-bold border ${badge.color}`}>
                            {badge.icon} {update.severity.toUpperCase()}
                          </span>
                          {update.action_required && (
                            <span className="px-2 py-1 rounded-md text-xs font-bold bg-red-500 text-white animate-pulse">
                              Aktion erforderlich
                            </span>
                          )}
                          {classification?.confidence && (
                            <span className={`px-2 py-1 rounded-md text-xs font-semibold ${
                              classification.confidence === 'high' ? 'bg-green-500/20 text-green-400' :
                              classification.confidence === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                              'bg-gray-500/20 text-gray-400'
                            }`}>
                              🤖 {classification.confidence === 'high' ? 'Sehr sicher' : 
                                  classification.confidence === 'medium' ? 'Mittel' : 'Niedrig'}
                            </span>
                          )}
                        </div>
                        <h4 className="text-white font-bold text-sm leading-tight mb-1">
                          {update.title}
                        </h4>
                        <span className="text-xs text-gray-500">
                          {update.update_type.replace('_', ' ')} • {formatDate(update.published_at)}
                        </span>
                      </div>
                    </div>

                    {/* Description */}
                    <p className="text-gray-400 text-xs leading-relaxed mb-3">
                      {update.description.substring(0, 150)}{update.description.length > 150 ? '...' : ''}
                    </p>
                    
                    {/* KI-Impact-Score */}
                    {classification?.impact_score && (
                      <div className="mb-3 flex items-center gap-2">
                        <div className="flex-1 bg-gray-700 rounded-full h-2 overflow-hidden">
                          <div 
                            className={`h-full transition-all ${
                              classification.impact_score >= 8 ? 'bg-red-500' :
                              classification.impact_score >= 6 ? 'bg-orange-500' :
                              classification.impact_score >= 4 ? 'bg-yellow-500' :
                              'bg-blue-500'
                            }`}
                            style={{ width: `${(classification.impact_score / 10) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-400 font-semibold">
                          {classification.impact_score.toFixed(1)}/10
                        </span>
                      </div>
                    )}
                    
                    {/* KI-User-Impact */}
                    {classification?.user_impact && (
                      <div className="mb-3 p-2 bg-blue-500/10 border border-blue-500/30 rounded-md">
                        <p className="text-xs text-blue-300 leading-relaxed">
                          💡 <strong>Bedeutung:</strong> {classification.user_impact.substring(0, 120)}...
                        </p>
                      </div>
                    )}

                    {/* KI-Gesteuerter Action Button */}
                    {primaryAction && (
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          handlePrimaryAction(update, e);
                        }}
                        className={`w-full ${buttonColor} text-white text-xs font-bold py-2.5 px-4 rounded-lg transition-all flex items-center justify-center gap-2 border-2 shadow-lg hover:shadow-xl`}
                      >
                        <ActionIcon className="w-4 h-4" />
                        {primaryAction.button_text}
                      </button>
                    )}
                    
                    {/* Fallback für Updates ohne Klassifizierung */}
                    {!primaryAction && update.action_required && (
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStartScan();
                        }}
                        className="w-full bg-red-600 hover:bg-red-700 text-white text-xs font-bold py-2.5 px-4 rounded-lg transition-all flex items-center justify-center gap-2"
                      >
                        <Search className="w-4 h-4" />
                        Jetzt neu scannen
                      </button>
                    )}
                    
                    {/* Feedback Buttons (nur anzeigen wenn klassifiziert) */}
                    {classification && (
                      <div className="mt-2 flex items-center justify-between gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedUpdate(update);
                          }}
                          className="flex-1 text-xs text-gray-400 hover:text-white transition py-1.5 px-2 rounded hover:bg-gray-700"
                        >
                          <Eye className="w-3 h-3 inline mr-1" />
                          Details
                        </button>
                        <div className="flex gap-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleFeedback(update, true);
                            }}
                            className="text-xs text-green-400 hover:text-green-300 transition p-1.5 rounded hover:bg-green-500/10"
                            title="Hilfreich"
                          >
                            <ThumbsUp className="w-3 h-3" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleFeedback(update, false);
                            }}
                            className="text-xs text-red-400 hover:text-red-300 transition p-1.5 rounded hover:bg-red-500/10"
                            title="Nicht hilfreich"
                          >
                            <ThumbsDown className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
              </div>
              
              {/* Archiv-Link */}
              <div className="text-center pt-2">
                <button
                  onClick={() => setShowArchive(true)}
                  className="text-sm text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-2 mx-auto"
                >
                  <Archive className="w-4 h-4" />
                  Archiv anzeigen (ältere Änderungen)
                </button>
              </div>
            </div>
          ) : loadError ? (
            // ✅ Fehlermeldung bei API-Problemen
            <div className="text-center py-8">
              <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
              <p className="text-red-400 font-medium mb-2">
                Fehler beim Laden der Gesetzesänderungen
              </p>
              <p className="text-gray-500 text-sm mb-4">
                {loadError}
              </p>
              <button
                onClick={fetchLegalUpdates}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm transition-colors"
              >
                Erneut versuchen
              </button>
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

      {/* Update Detail Modal (KI-Klassifizierung) */}
      {selectedUpdate && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
          onClick={() => setSelectedUpdate(null)}
        >
          <div 
            className="bg-gray-800 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl border border-gray-700"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between p-6 border-b border-gray-700 bg-gradient-to-r from-purple-900/30 to-blue-900/30">
              <div className="flex-1 pr-4">
                <div className="flex items-center gap-2 mb-3">
                  {selectedUpdate.classification?.confidence && (
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      selectedUpdate.classification.confidence === 'high' ? 'bg-green-500/20 text-green-300 border border-green-500' :
                      selectedUpdate.classification.confidence === 'medium' ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500' :
                      'bg-gray-500/20 text-gray-300 border border-gray-500'
                    }`}>
                      🤖 KI-Konfidenz: {selectedUpdate.classification.confidence === 'high' ? 'Sehr hoch' : 
                          selectedUpdate.classification.confidence === 'medium' ? 'Mittel' : 'Niedrig'}
                    </span>
                  )}
                  {selectedUpdate.classification?.impact_score && (
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-orange-500/20 text-orange-300 border border-orange-500">
                      Impact: {selectedUpdate.classification.impact_score.toFixed(1)}/10
                    </span>
                  )}
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  {selectedUpdate.title}
                </h2>
                <div className="flex items-center gap-4 text-sm text-gray-400">
                  <span className="flex items-center gap-1">
                    <Scale className="w-4 h-4" />
                    {selectedUpdate.update_type.replace('_', ' ')}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {formatDate(selectedUpdate.published_at)}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedUpdate(null)}
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X className="w-6 h-6 text-gray-400" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-250px)] space-y-4">
              {/* Beschreibung */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Beschreibung</h3>
                <p className="text-gray-300 leading-relaxed">
                  {selectedUpdate.description}
                </p>
              </div>
              
              {/* KI-Analyse: User-Impact */}
              {selectedUpdate.classification?.user_impact && (
                <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-blue-400" />
                    Was bedeutet das für Sie?
                  </h3>
                  <p className="text-gray-300 text-sm leading-relaxed">
                    {selectedUpdate.classification.user_impact}
                  </p>
                </div>
              )}
              
              {/* KI-Analyse: Reasoning */}
              {selectedUpdate.classification?.reasoning && (
                <div className="p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                  <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-purple-400" />
                    KI-Analyse
                  </h3>
                  <p className="text-gray-300 text-sm leading-relaxed">
                    {selectedUpdate.classification.reasoning}
                  </p>
                </div>
              )}
              
              {/* Konsequenzen */}
              {selectedUpdate.classification?.consequences_if_ignored && (
                <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                  <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-red-400" />
                    Bei Nicht-Umsetzung
                  </h3>
                  <p className="text-gray-300 text-sm leading-relaxed">
                    {selectedUpdate.classification.consequences_if_ignored}
                  </p>
                </div>
              )}
              
              {/* Empfohlene Aktionen */}
              {selectedUpdate.classification?.recommended_actions && selectedUpdate.classification.recommended_actions.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-white mb-3">Empfohlene Aktionen</h3>
                  <div className="space-y-2">
                    {selectedUpdate.classification.recommended_actions.map((action, idx) => {
                      const Icon = getActionIcon(action.icon);
                      return (
                        <div key={idx} className="p-3 bg-gray-700/50 rounded-lg border border-gray-600 hover:border-gray-500 transition-all">
                          <div className="flex items-start gap-3">
                            <div className={`p-2 rounded-lg ${
                              action.button_color === 'red' ? 'bg-red-500/20 text-red-400' :
                              action.button_color === 'orange' ? 'bg-orange-500/20 text-orange-400' :
                              action.button_color === 'blue' ? 'bg-blue-500/20 text-blue-400' :
                              'bg-gray-500/20 text-gray-400'
                            }`}>
                              <Icon className="w-5 h-5" />
                            </div>
                            <div className="flex-1">
                              <h4 className="text-white font-semibold text-sm mb-1">{action.title}</h4>
                              <p className="text-gray-400 text-xs mb-2">{action.description}</p>
                              <button 
                                className={`text-xs px-3 py-1 rounded ${
                                  action.button_color === 'red' ? 'bg-red-600 hover:bg-red-700' :
                                  action.button_color === 'orange' ? 'bg-orange-600 hover:bg-orange-700' :
                                  action.button_color === 'blue' ? 'bg-blue-600 hover:bg-blue-700' :
                                  'bg-gray-600 hover:bg-gray-700'
                                } text-white transition`}
                              >
                                {action.button_text}
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between p-6 border-t border-gray-700 bg-gray-800/50">
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-400">War diese KI-Analyse hilfreich?</span>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      handleFeedback(selectedUpdate, true);
                      setSelectedUpdate(null);
                    }}
                    className="px-3 py-1.5 bg-green-500/20 text-green-300 hover:bg-green-500/30 rounded-md transition text-sm flex items-center gap-1"
                  >
                    <ThumbsUp className="w-3 h-3" />
                    Ja
                  </button>
                  <button
                    onClick={() => {
                      handleFeedback(selectedUpdate, false);
                      setSelectedUpdate(null);
                    }}
                    className="px-3 py-1.5 bg-red-500/20 text-red-300 hover:bg-red-500/30 rounded-md transition text-sm flex items-center gap-1"
                  >
                    <ThumbsDown className="w-3 h-3" />
                    Nein
                  </button>
                </div>
              </div>
              <button
                onClick={() => setSelectedUpdate(null)}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Schließen
              </button>
            </div>
          </div>
        </div>
      )}

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
      
      {/* Archiv Modal */}
      <LegalArchiveModal 
        isOpen={showArchive}
        onClose={() => setShowArchive(false)}
      />
    </Card>
  );
};
