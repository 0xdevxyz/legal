'use client';

import React, { useState } from 'react';
import { ComplianceIssue, FixResult } from '@/types/api';
import { generateFix } from '@/lib/api';
import { Copy, Check, FileText, Shield, ExternalLink, Sparkles } from 'lucide-react';
import { StripePaywallModal } from './StripePaywallModal';
import { ConfirmFixModal } from './ConfirmFixModal';
import { FixModal } from './FixModal';
import { useToast } from '@/components/ui/Toast';
import { AIFixPreview, AIFixPreviewMini } from '@/components/ai/AIFixPreview';
import { AIFixDisplay } from '@/components/ai/AIFixDisplay'; // NEW: Enhanced Fix Display
import { useCreateFixJob } from '@/hooks/useCompliance';
import { UnifiedFixButton } from './UnifiedFixButton';

const extractDomain = (url: string): string => {
  try {
    const urlObj = new URL(url.startsWith('http') ? url : `https://${url}`);
    let domain = urlObj.hostname;
    if (domain.startsWith('www.')) {
      domain = domain.substring(4);
    }
    return domain;
  } catch {
    return url;
  }
};

// 🎯 Mapping: Issue-Kategorie → Fix-Typ
const getFixTypeForIssue = (issue: ComplianceIssue): 'code' | 'text' | 'guide' => {
  const category = issue.category.toLowerCase();
  const title = issue.title.toLowerCase();
  
  // TEXT-FIX: Rechtliche Texte
  if (
    category.includes('legal') || 
    category.includes('rechtssicher') ||
    title.includes('impressum') ||
    title.includes('datenschutz') ||
    title.includes('agb') ||
    title.includes('widerrufsbelehrung') ||
    title.includes('rechtliche hinweise')
  ) {
    return 'text';
  }
  
  // CODE-FIX: Technische Implementierungen
  if (
    category.includes('accessibility') ||
    category.includes('barrierefreiheit') ||
    category.includes('cookie') ||
    title.includes('alt-text') ||
    title.includes('aria') ||
    title.includes('meta-tag') ||
    title.includes('cookie-banner') ||
    title.includes('consent')
  ) {
    return 'code';
  }
  
  // GUIDE: Komplexe/strategische Themen (Default)
  return 'guide';
};

interface ComplianceIssueCardProps {
  issue: ComplianceIssue;
  planType: 'free' | 'ai' | 'expert';
  websiteUrl?: string;
  scanId?: string; // ✅ PERSISTENCE: scan_id für Job-Erstellung
  onStartFix?: (issueId: string) => void;
}

export const ComplianceIssueCard: React.FC<ComplianceIssueCardProps> = ({
  issue,
  planType,
  websiteUrl,
  scanId,
  onStartFix
}) => {
  const { showToast } = useToast();
  const createFixJob = useCreateFixJob();
  const [isFixing, setIsFixing] = useState(false);
  const [generatedFix, setGeneratedFix] = useState<FixResult | null>(null);
  const [showFixModal, setShowFixModal] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);
  const [showPaywall, setShowPaywall] = useState(false);
  const [fixLimitInfo, setFixLimitInfo] = useState<{ fixes_used: number; fixes_limit: number } | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showAIPreview, setShowAIPreview] = useState(false);
  
  // 💬 Chat-State für KI-Rückfragen
  const [showChat, setShowChat] = useState(false);
  const [chatMessages, setChatMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  
  const domain = websiteUrl ? extractDomain(websiteUrl) : undefined;

  // Severity-basierte Farben
  const severityColors = {
    critical: 'border-l-red-500 bg-red-50',
    warning: 'border-l-yellow-500 bg-yellow-50',
    info: 'border-l-blue-500 bg-blue-50'
  };

  const severityIcons = {
    critical: '🚨',
    warning: '⚠️',
    info: 'ℹ️'
  };

  const severityLabels = {
    critical: 'Kritisch',
    warning: 'Warnung',
    info: 'Information'
  };

  const handleCopyCode = async (code: string) => {
    // ✅ SSR-Check
    if (typeof navigator === 'undefined') return;
    
    try {
      await navigator.clipboard.writeText(code);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
      showToast('Code kopiert!', 'success');
    } catch {
      showToast('Kopieren fehlgeschlagen', 'error');
    }
  };

  // 💬 Chat-Funktion für KI-Rückfragen
  const handleSendChatMessage = async () => {
    if (!chatInput.trim() || isChatLoading) return;
    
    const userMessage = chatInput.trim();
    setChatInput('');
    setIsChatLoading(true);
    
    // Füge User-Message zum Chat hinzu
    const newMessages = [...chatMessages, { role: 'user', content: userMessage }];
    setChatMessages(newMessages);
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('https://api.complyo.tech/api/chat/issue-solution', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          website_url: websiteUrl || 'unknown',
          issue_title: issue.title,
          issue_description: issue.description,
          ai_solution: (issue as any).ai_solution || null,
          user_question: userMessage,
          chat_history: chatMessages
        })
      });
      
      if (!response.ok) {
        throw new Error('Chat-Anfrage fehlgeschlagen');
      }
      
      const data = await response.json();
      
      // Füge AI-Response zum Chat hinzu
      setChatMessages([...newMessages, { role: 'assistant', content: data.response }]);
      showToast('Antwort erhalten!', 'success');
    } catch (error) {
      console.error('Chat-Fehler:', error);
      showToast('Fehler beim Chat. Bitte versuchen Sie es erneut.', 'error');
      // Entferne letzte User-Message bei Fehler
      setChatMessages(chatMessages);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleStartFixClick = () => {
    if (!issue.auto_fixable) {
      showToast('Dieser Issue kann nicht automatisch behoben werden', 'warning');
      return;
    }

    if (!issue.id || typeof issue.id !== 'string') {
      showToast('Fehler: Ungültige Issue-ID. Bitte laden Sie die Seite neu.', 'error');
      return;
    }

    if (!issue.category || typeof issue.category !== 'string') {
      showToast('Fehler: Ungültige Issue-Kategorie. Bitte laden Sie die Seite neu.', 'error');
      return;
    }

    setShowConfirmModal(true);
  };

  const handleConfirmFix = async () => {
    console.log('🚀 KI-Fix gestartet!', { 
      hasScanId: !!scanId, 
      scanId, 
      issueId: issue.id,
      issueTitle: issue.title 
    });
    
    setShowConfirmModal(false);
    
    // ✅ SPECIAL: Für Impressum/Datenschutz nutze eRecht24-API direkt
    const isLegalText = issue.title.toLowerCase().includes('impressum') || 
                       issue.title.toLowerCase().includes('datenschutz');
    
    if (isLegalText) {
      setIsFixing(true);
      try {
        const textType = issue.title.toLowerCase().includes('impressum') ? 'imprint' : 'privacy_policy';
        const endpoint = textType === 'imprint' 
          ? '/api/erecht24/imprint'
          : '/api/erecht24/privacy-policy';

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}?language=de`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        });

        if (!response.ok) {
          throw new Error('Generierung fehlgeschlagen');
        }

        const data = await response.json();
        
        // Auto-Download
        // ✅ SSR-Check
        if (typeof document !== 'undefined') {
          const filename = textType === 'imprint' ? 'impressum.html' : 'datenschutzerklaerung.html';
          const blob = new Blob([data.html], { type: 'text/html;charset=utf-8' });
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
        }

        showToast('✅ Rechtstext wurde generiert und heruntergeladen!', 'success', 5000);
        
        if (onStartFix) {
          onStartFix(issue.id);
        }
      } catch (err) {
        console.error('Fehler bei Rechtstext-Generierung:', err);
        showToast('Generierung fehlgeschlagen. Bitte versuchen Sie es erneut.', 'error');
      } finally {
        setIsFixing(false);
      }
      return;
    }
    
    // ✅ PERSISTENCE: Wenn scanId vorhanden, Job erstellen
    if (scanId) {
      console.log('✅ ScanId vorhanden, erstelle Fix-Job...');
      try {
        const jobData = await createFixJob.mutateAsync({
          scan_id: scanId,
          issue_id: issue.id,
          issue_data: issue
        });
        
        console.log('✅ Fix-Job erstellt:', jobData);
        
        // Scroll to top to show the active jobs panel
        // ✅ SSR-Check
        if (typeof window !== 'undefined') {
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        
        showToast(
          '🤖 KI-Fix wird im Hintergrund generiert! Sie können die Seite refreshen, der Fix läuft weiter.',
          'success',
          7000
        );
        
        if (onStartFix) {
          onStartFix(issue.id);
        }
      } catch (error: any) {
        console.error('❌ Fehler beim Erstellen des Fix-Jobs:', error);
        console.error('Error details:', {
          code: error?.code,
          status: error?.status,
          response: error?.response,
          message: error?.message
        });
        
        if (error?.code === 'FIX_LIMIT_REACHED') {
          setFixLimitInfo({
            fixes_used: error.fixes_used || 1,
            fixes_limit: error.fixes_limit || 1
          });
          setShowPaywall(true);
          return;
        }
        
        if (error?.response?.status === 402 || error?.status === 402) {
          const errorDetail = error?.response?.data?.detail || error?.detail || {};
          const limitData = typeof errorDetail === 'object' ? errorDetail : {};
          
          setFixLimitInfo({
            fixes_used: limitData.fixes_used || 1,
            fixes_limit: limitData.fixes_limit || 1
          });
          setShowPaywall(true);
          return;
        }
        
        const errorMessage = error instanceof Error ? error.message : 'Unbekannter Fehler';
        showToast(errorMessage, 'error', 7000);
      }
      return;
    }
    
    console.log('⚠️ Keine ScanId, verwende Fallback-Methode...');
    
    // ✅ FALLBACK: Alte Methode wenn keine scanId (direkt generieren)
    setIsFixing(true);
    
    try {
      const categoryMap: Record<string, string> = {
        'accessibility': 'wcag',
        'Barrierefreiheit': 'wcag',
        'gdpr': 'dsgvo',
        'DSGVO': 'dsgvo',
        'legal': 'legal_texts',
        'Rechtssichere Texte': 'legal_texts',
        'cookies': 'cookie_compliance',
        'Cookie Compliance': 'cookie_compliance'
      };

      const mappedCategory = categoryMap[issue.category] || issue.category;
      const result = await generateFix(issue.id, mappedCategory);
      
      setGeneratedFix(result);
      setShowFixModal(true);
      showToast('Fix erfolgreich generiert!', 'success');
      
      if (onStartFix) {
        onStartFix(issue.id);
      }
    } catch (error: any) {
      if (error?.code === 'FIX_LIMIT_REACHED') {
        setFixLimitInfo({
          fixes_used: error.fixes_used || 1,
          fixes_limit: error.fixes_limit || 1
        });
        setShowPaywall(true);
        return;
      }
      
      if (error?.response?.status === 402 || error?.status === 402) {
        const errorDetail = error?.response?.data?.detail || error?.detail || {};
        const limitData = typeof errorDetail === 'object' ? errorDetail : {};
        
        setFixLimitInfo({
          fixes_used: limitData.fixes_used || 1,
          fixes_limit: limitData.fixes_limit || 1
        });
        setShowPaywall(true);
        return;
      }
      
      const errorMessage = error instanceof Error ? error.message : 'Unbekannter Fehler';
      showToast(errorMessage, 'error', 7000);
    } finally {
      setIsFixing(false);
    }
  };

  return (
    <div className={`border-l-4 rounded-lg p-6 mb-4 shadow-md ${severityColors[issue.severity as keyof typeof severityColors] || 'border-l-gray-500 bg-gray-50'}`}>
      {/* Header mit Severity */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span className="text-2xl flex-shrink-0">{severityIcons[issue.severity as keyof typeof severityIcons] || '📋'}</span>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-lg font-bold text-gray-800 break-words line-clamp-2">
                {issue.title}
              </h3>
              {issue.auto_fixable && (issue.category?.toLowerCase().includes('barriere') || issue.title?.toLowerCase().includes('alt-text') || issue.title?.toLowerCase().includes('aria')) && (
                <span className="px-2 py-1 bg-gradient-to-r from-green-500 to-emerald-600 text-white text-[10px] font-bold rounded-full flex items-center gap-1 whitespace-nowrap">
                  <Sparkles className="w-3 h-3" />
                  Widget fixt
                </span>
              )}
            </div>
            <p className="text-sm text-gray-600 break-words">
              {severityLabels[issue.severity as keyof typeof severityLabels] || issue.severity} · {issue.category}
            </p>
          </div>
        </div>
        
        {/* Risiko-Badge */}
        {issue.risk_euro_max && (
          <div className="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm font-semibold">
            Bis zu {issue.risk_euro_max}€ Bußgeld
          </div>
        )}
      </div>

      {/* Beschreibung */}
      <p className="text-gray-700 mb-4 leading-relaxed">{issue.description}</p>

      {/* ✅ KI-Lösung - Individuell generiert (wenn vorhanden) */}
      {(issue as any).ai_solution && (
        <>
          <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-5 border-2 border-blue-200 mb-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">🤖</span>
              <h4 className="font-bold text-gray-800">KI-Analyse & Lösung</h4>
              <span className="ml-auto px-3 py-1 bg-blue-600 text-white text-xs font-semibold rounded-full">
                Individuell für Ihre Website
              </span>
            </div>
            
            <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap bg-white rounded-lg p-4 border border-blue-100">
              {(issue as any).ai_solution}
            </div>
          </div>
          
          {/* 💬 KI-Chat für Rückfragen */}
          <div className="bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg p-4 border-2 border-purple-200 mb-4">
            <button
              onClick={() => setShowChat(!showChat)}
              className="flex items-center gap-2 w-full text-left font-semibold text-gray-800 hover:text-purple-600 transition-colors"
            >
              <span className="text-xl">💬</span>
              <span>Fragen Sie die KI zur Umsetzung</span>
              <span className="ml-auto text-xs bg-purple-600 text-white px-2 py-1 rounded-full">
                {showChat ? 'Schließen' : 'Öffnen'}
              </span>
            </button>
            
            {showChat && (
              <div className="mt-4">
                {/* Chat-Messages */}
                {chatMessages.length > 0 && (
                  <div className="space-y-3 mb-4 max-h-96 overflow-y-auto bg-white rounded-lg p-3 border border-purple-100">
                    {chatMessages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`${
                          msg.role === 'user' 
                            ? 'bg-blue-100 ml-8 text-right' 
                            : 'bg-gray-100 mr-8 text-left'
                        } rounded-lg p-3`}
                      >
                        <div className="text-xs font-semibold mb-1 text-gray-600">
                          {msg.role === 'user' ? '👤 Sie' : '🤖 KI-Assistent'}
                        </div>
                        <div className="text-sm text-gray-800 whitespace-pre-wrap">
                          {msg.content}
                        </div>
                      </div>
                    ))}
                    
                    {isChatLoading && (
                      <div className="bg-gray-100 mr-8 rounded-lg p-3 animate-pulse">
                        <div className="text-xs font-semibold mb-1 text-gray-600">
                          🤖 KI-Assistent
                        </div>
                        <div className="text-sm text-gray-500">
                          Tippt...
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Chat-Input */}
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSendChatMessage()}
                    placeholder="z.B. 'Wie implementiere ich das in React?'"
                    className="flex-1 px-4 py-2 border border-purple-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    disabled={isChatLoading}
                  />
                  <button
                    onClick={handleSendChatMessage}
                    disabled={!chatInput.trim() || isChatLoading}
                    className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold transition-colors"
                  >
                    {isChatLoading ? '...' : 'Senden'}
                  </button>
                </div>
                
                <p className="text-xs text-gray-500 mt-2">
                  💡 Stellen Sie spezifische Fragen zur Umsetzung, Code-Beispielen oder Ihrem Tech-Stack
                </p>
              </div>
            )}
          </div>
        </>
      )}

      {/* Lösung - IMMER SICHTBAR, mit spezifischen Handlungsanweisungen */}
      {issue.solution && (
        <div className="bg-white rounded-lg p-4 border border-gray-200 mb-4">
          <h4 className="font-semibold text-gray-800 mb-3">📝 Konkrete Handlungsschritte:</h4>
          
          {/* ✅ Datenschutz/Impressum: Spezifische Anleitung */}
          {(issue.category === 'datenschutz' || issue.title?.toLowerCase().includes('datenschutz')) && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <p className="text-sm text-blue-800 font-medium mb-2">🔒 Datenschutz-Problem beheben:</p>
              <ol className="list-decimal list-inside text-sm text-blue-700 space-y-2">
                <li>Klicken Sie oben auf <strong>"Alle Probleme beheben"</strong> für eine vollständige Datenschutzerklärung</li>
                <li>Laden Sie die generierte HTML-Datei herunter</li>
                <li>Ersetzen Sie Ihre bestehende Datenschutzerklärung mit dem neuen Text</li>
                <li>Führen Sie einen neuen Scan durch, um die Behebung zu bestätigen</li>
              </ol>
              <p className="text-xs text-blue-600 mt-2">
                💡 Der generierte Text ist rechtssicher und DSGVO-konform!
              </p>
            </div>
          )}
          
          {(issue.category === 'impressum' || issue.title?.toLowerCase().includes('impressum')) && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
              <p className="text-sm text-purple-800 font-medium mb-2">📋 Impressum-Problem beheben:</p>
              <ol className="list-decimal list-inside text-sm text-purple-700 space-y-2">
                <li>Klicken Sie oben auf <strong>"Alle Probleme beheben"</strong> für ein vollständiges Impressum</li>
                <li>Laden Sie die generierte HTML-Datei herunter</li>
                <li>Ersetzen Sie Ihr bestehendes Impressum mit dem neuen Text</li>
                <li>Achten Sie darauf, alle Pflichtangaben (Name, Adresse, E-Mail) korrekt einzutragen</li>
              </ol>
              <p className="text-xs text-purple-600 mt-2">
                💡 Das generierte Impressum erfüllt alle TMG-Anforderungen!
              </p>
            </div>
          )}
          
          {/* Steps für andere Issue-Typen */}
          {issue.solution.steps && issue.solution.steps.length > 0 && 
           !issue.category?.includes('datenschutz') && 
           !issue.category?.includes('impressum') &&
           !issue.title?.toLowerCase().includes('datenschutz') &&
           !issue.title?.toLowerCase().includes('impressum') && (
            <div className="space-y-3 mb-4">
              {issue.solution.steps.map((step, index) => (
                <div key={index} className="flex items-start gap-2">
                  <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-semibold flex-shrink-0">
                    {index + 1}
                  </div>
                  <p className="text-gray-700 flex-1">{step}</p>
                </div>
              ))}
            </div>
          )}

          {/* Code Snippet mit Copy Button */}
          {issue.solution.code_snippet && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-gray-700">💻 Code zum Kopieren:</span>
                <button
                  onClick={() => handleCopyCode(issue.solution.code_snippet)}
                  className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700"
                >
                  {copiedCode ? (
                    <>
                      <Check className="w-4 h-4" />
                      Kopiert!
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" />
                      Kopieren
                    </>
                  )}
                </button>
              </div>
              <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                <code>{issue.solution.code_snippet}</code>
              </pre>
            </div>
          )}
        </div>
      )}

      {/* AI-Fix Section - Prominent und interaktiv - ALLE NUTZER (auch Free!) */}
      {issue.auto_fixable && (planType === 'free' || planType === 'ai' || planType === 'expert') && (
        <div className="mt-4 space-y-3">
          {!showAIPreview ? (
            <div className="flex items-center gap-3">
              <UnifiedFixButton
                issueTitle={issue.title}
                isGroup={false}
                onFix={() => setShowAIPreview(true)}
                disabled={false}
                isLoading={false}
              />
              <span className="text-sm text-gray-600">
                Lassen Sie die KI eine Lösung generieren
              </span>
            </div>
          ) : (
            <AIFixPreview
              issue={issue}
              onGenerateFull={handleStartFixClick}
            />
          )}
          
          {/* Mini alternative for less prominent placement */}
          {!showAIPreview && issue.severity === 'critical' && (
            <div className="p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200">
              <p className="text-sm text-gray-700 mb-2">
                💡 <strong>KI-Tipp:</strong> Dieses Problem lässt sich schnell beheben
              </p>
              <button
                onClick={() => setShowAIPreview(true)}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
              >
                Vorschau anzeigen
                <Sparkles className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Expert Service CTA */}
      {planType === 'expert' && (
        <div className="mt-4 bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">👨‍💻</span>
            <div className="flex-1">
              <div className="font-semibold text-gray-800 mb-1">
                Expertenservice verfügbar
              </div>
              <p className="text-sm text-gray-600">
                Unser Team setzt diesen Fix professionell für Sie um.
              </p>
            </div>
            <button className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg font-semibold whitespace-nowrap">
              Service buchen
            </button>
          </div>
        </div>
      )}

      {/* Modals */}
      <ConfirmFixModal
        isOpen={showConfirmModal}
        onConfirm={handleConfirmFix}
        onCancel={() => setShowConfirmModal(false)}
        issueTitle={issue.title}
        fixType={getFixTypeForIssue(issue)}
        isFirstFix={false}
      />

      <FixModal
        isOpen={showFixModal}
        onClose={() => setShowFixModal(false)}
        fix={generatedFix}
        issueTitle={issue.title}
      />

      <StripePaywallModal
        isOpen={showPaywall}
        onClose={() => setShowPaywall(false)}
        domain={domain}
        fixesUsed={fixLimitInfo?.fixes_used}
        fixesLimit={fixLimitInfo?.fixes_limit}
      />
    </div>
  );
};

export default ComplianceIssueCard;
