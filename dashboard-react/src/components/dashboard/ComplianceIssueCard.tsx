'use client';

import React, { useState } from 'react';
import { ComplianceIssue, FixResult } from '@/types/api';
import { generateFix } from '@/lib/api';
import { Copy, Check, FileText, Shield, ExternalLink, Sparkles, Cookie, Lock, Image as ImageIcon, Pencil, Eye, ArrowRight } from 'lucide-react';
import { StripePaywallModal } from './StripePaywallModal';
import { ConfirmFixModal } from './ConfirmFixModal';
import { FixModal } from './FixModal';
import { useToast } from '@/components/ui/Toast';
import { AIFixPreview, AIFixPreviewMini } from '@/components/ai/AIFixPreview';
import { AIFixDisplay } from '@/components/ai/AIFixDisplay';
import { useCreateFixJob } from '@/hooks/useCompliance';
import { UnifiedFixButton } from './UnifiedFixButton';
import { useRouter } from 'next/navigation';
import { useDashboardStore } from '@/stores/dashboard';
import { apiClient } from '@/lib/api-client';

// Hilfsfunktion: Ist es ein Cookie-Problem?
const isCookieIssue = (issue: ComplianceIssue): boolean => {
  const category = issue.category?.toLowerCase() || '';
  const title = issue.title?.toLowerCase() || '';
  return category.includes('cookie') || title.includes('cookie') || title.includes('consent');
};

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
  scanId?: string;
  onStartFix?: (issueId: string) => void;
  isAnalysisOnly?: boolean;
}

export const ComplianceIssueCard: React.FC<ComplianceIssueCardProps> = ({
  issue,
  planType,
  websiteUrl,
  scanId,
  onStartFix,
  isAnalysisOnly = false
}) => {
  const { showToast } = useToast();
  const router = useRouter();
  const createFixJob = useCreateFixJob();
  const { isInOptimizationMode, lockedOptimizationUrl } = useDashboardStore();
  
  // KI-Fix immer verfügbar — Lock-Status nur als Hinweis, nicht als Blockade
  const canOptimize = true;
  const isOtherSiteLocked = isInOptimizationMode && 
    lockedOptimizationUrl && websiteUrl && 
    websiteUrl !== lockedOptimizationUrl && 
    !websiteUrl.includes(lockedOptimizationUrl) &&
    !lockedOptimizationUrl.includes(websiteUrl);
  const [isFixing, setIsFixing] = useState(false);
  const [generatedFix, setGeneratedFix] = useState<FixResult | null>(null);
  const [showFixModal, setShowFixModal] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);
  const [showPaywall, setShowPaywall] = useState(false);
  const [fixLimitInfo, setFixLimitInfo] = useState<{ fixes_used: number; fixes_limit: number } | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showAIPreview, setShowAIPreview] = useState(false);
  const [altTextValue, setAltTextValue] = useState(issue.suggested_alt || '');
  const [altTextSaved, setAltTextSaved] = useState(false);
  
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
    
    // Interner Rechtstexte-Generator
    const isLegalText = issue.title.toLowerCase().includes('impressum') || 
                       issue.title.toLowerCase().includes('datenschutz');
    
    if (isLegalText) {
      setIsFixing(true);
      try {
        const textType = issue.title.toLowerCase().includes('impressum') ? 'imprint' : 'privacy_policy';
        const endpoint = textType === 'imprint' 
          ? '/api/legal-texts/imprint'
          : '/api/legal-texts/privacy';

        const data = await apiClient.get(`${endpoint}`, { language: 'de' } as any) as any;

        if (!data) {
          throw new Error('Generierung fehlgeschlagen');
        }

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
      showToast('✅ Fix erfolgreich generiert!', 'success', 5000);
      // ✅ Success-Animation für wichtige Erfolge
      if (window.dispatchEvent) {
        window.dispatchEvent(new CustomEvent('complyo:fix-success', { 
          detail: { issueId: issue.id, category: issue.category } 
        }));
      }
      
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

      {/* Alt-Text Editor — nur für Bilder ohne Alt-Text */}
      {issue.image_src && (
        <div className="mb-4 rounded-xl border border-blue-200 bg-blue-50 overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-2 bg-blue-100 border-b border-blue-200">
            <ImageIcon className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-semibold text-blue-800">Betroffenes Bild</span>
          </div>
          <div className="p-4 flex gap-4 flex-col sm:flex-row">
            {/* Bildvorschau */}
            <div className="flex-shrink-0">
              <img
                src={issue.screenshot_url || issue.image_src}
                alt="Vorschau des betroffenen Bildes"
                className="w-32 h-32 object-cover rounded-lg border border-blue-200 bg-white"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
              <p className="text-xs text-blue-600 mt-1 truncate max-w-[8rem]" title={issue.image_src}>
                {issue.image_src.split('/').pop()}
              </p>
            </div>

            {/* Alt-Text Eingabe */}
            <div className="flex-1 space-y-2">
              {issue.suggested_alt && (
                <div className="flex items-start gap-2 p-2 bg-white rounded-lg border border-blue-200">
                  <Sparkles className="w-4 h-4 text-purple-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-xs font-semibold text-purple-700 mb-0.5">KI-Vorschlag</p>
                    <p className="text-sm text-gray-700 italic">„{issue.suggested_alt}"</p>
                    <button
                      onClick={() => setAltTextValue(issue.suggested_alt!)}
                      className="text-xs text-purple-600 hover:text-purple-800 font-medium mt-1"
                    >
                      Vorschlag übernehmen
                    </button>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  <Pencil className="w-3 h-3 inline mr-1" />
                  Alt-Text eingeben oder anpassen
                </label>
                <textarea
                  value={altTextValue}
                  onChange={(e) => { setAltTextValue(e.target.value); setAltTextSaved(false); }}
                  placeholder="Beschreibung des Bildinhalts…"
                  rows={2}
                  className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
                />
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={async () => {
                    if (!altTextValue.trim()) return;
                    try {
                      await apiClient.post('/api/accessibility/alt-text', {
                        image_src: issue.image_src,
                        alt_text: altTextValue.trim(),
                        fix_code: `<img src="${issue.image_src}" alt="${altTextValue.trim()}" />`,
                      });
                      setAltTextSaved(true);
                      showToast('Alt-Text gespeichert!', 'success');
                    } catch {
                      showToast('Speichern fehlgeschlagen', 'error');
                    }
                  }}
                  disabled={!altTextValue.trim() || altTextSaved}
                  className="flex items-center gap-1.5 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white text-sm font-semibold rounded-lg transition-colors"
                >
                  {altTextSaved ? <Check className="w-4 h-4" /> : <Check className="w-4 h-4" />}
                  {altTextSaved ? 'Gespeichert' : 'Alt-Text speichern'}
                </button>
                {issue.fix_code && (
                  <button
                    onClick={() => handleCopyCode(issue.fix_code!)}
                    className="flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 hover:bg-gray-50 text-gray-700 text-sm rounded-lg transition-colors"
                  >
                    <Copy className="w-3.5 h-3.5" />
                    HTML kopieren
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ✅ KI-Lösung - Individuell generiert (wenn vorhanden) */}
      {(issue as any).ai_solution && (
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
                💡 Das generierte Impressum erfüllt alle DDG-Anforderungen!
              </p>
            </div>
          )}
          
          {/* ✅ NEU: Cookie-Compliance Anleitung mit Link zur integrierten Lösung */}
          {isCookieIssue(issue) && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-orange-500/20 rounded-lg flex-shrink-0">
                  <Cookie className="w-5 h-5 text-orange-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-orange-800 font-medium mb-2">🍪 Cookie-Compliance mit Complyo beheben:</p>
                  <p className="text-sm text-orange-700 mb-3">
                    Complyo bietet eine <strong>integrierte DSGVO-konforme Cookie-Banner-Lösung</strong> - 
                    ohne externe Tools wie Cookiebot oder Usercentrics!
                  </p>
                  <ul className="text-sm text-orange-700 space-y-1.5 mb-4">
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                      Automatische Cookie-Erkennung
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                      Anpassbares Design & Texte
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                      Consent-Statistiken & Reporting
                    </li>
                    <li className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                      WCAG 2.2 Level AA barrierefrei
                    </li>
                  </ul>
                  <button
                    onClick={() => router.push('/cookie-compliance')}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white font-semibold rounded-lg hover:from-orange-600 hover:to-red-600 transition-all shadow-lg shadow-orange-500/25"
                  >
                    <Cookie className="w-5 h-5" />
                    Cookie-Compliance einrichten
                    <ExternalLink className="w-4 h-4" />
                  </button>
                  <p className="text-xs text-orange-600 mt-2 text-center">
                    ✨ Im AI Plan enthalten - keine Zusatzkosten!
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* ✅ NEU: Barrierefreiheit / WCAG / Accessibility */}
          {!isCookieIssue(issue) &&
           (issue.category?.toLowerCase().includes('barriere') ||
            issue.category?.toLowerCase().includes('accessibility') ||
            issue.title?.toLowerCase().includes('wcag') ||
            issue.title?.toLowerCase().includes('aria') ||
            issue.title?.toLowerCase().includes('kontrast') ||
            issue.title?.toLowerCase().includes('alt-text')) && (
            <div className="bg-sky-50 border border-sky-200 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-sky-500/20 rounded-lg flex-shrink-0">
                  <Eye className="w-5 h-5 text-sky-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-sky-800 font-medium mb-2">Barrierefreiheit beheben:</p>
                  <ol className="list-decimal list-inside text-sm text-sky-700 space-y-2 mb-4">
                    <li>Öffnen Sie die Säule <strong>"Barrierefreiheit"</strong> und klicken Sie auf <strong>"KI-Fix starten"</strong></li>
                    <li>Das Complyo Widget behebt Alt-Texte, Kontrast und ARIA-Labels automatisch auf Ihrer Website</li>
                    <li>Integrieren Sie das Widget per Script-Tag (einmalige Einrichtung, ca. 2 Minuten)</li>
                    <li>Führen Sie einen neuen Scan durch, um die Verbesserung zu bestätigen</li>
                  </ol>
                  <button
                    onClick={() => {
                      if (typeof window !== 'undefined') {
                        window.dispatchEvent(new CustomEvent('complyo:scroll-to-pillar', { detail: { pillarId: 'accessibility' } }));
                      }
                    }}
                    className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-sky-500 to-blue-500 text-white font-semibold rounded-lg hover:from-sky-600 hover:to-blue-600 transition-all text-sm"
                  >
                    <Eye className="w-4 h-4" />
                    Zur Barrierefreiheit-Lösung
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ✅ NEU: DSGVO allgemein / Datenschutz (nicht Datenschutzerklärung fehlt) */}
          {!isCookieIssue(issue) &&
           !issue.category?.toLowerCase().includes('barriere') &&
           !issue.category?.toLowerCase().includes('accessibility') &&
           (issue.category?.toLowerCase().includes('dsgvo') ||
            issue.category?.toLowerCase().includes('gdpr') ||
            issue.category?.toLowerCase().includes('datenschutz') ||
            issue.title?.toLowerCase().includes('dsgvo') ||
            issue.title?.toLowerCase().includes('personenbezogen') ||
            issue.title?.toLowerCase().includes('verarbeitung')) &&
           !issue.title?.toLowerCase().includes('datenschutzerklärung') &&
           !issue.category?.toLowerCase().includes('impressum') && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-green-500/20 rounded-lg flex-shrink-0">
                  <Shield className="w-5 h-5 text-green-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-green-800 font-medium mb-2">DSGVO-Problem beheben:</p>
                  <ol className="list-decimal list-inside text-sm text-green-700 space-y-2 mb-4">
                    <li>Prüfen Sie welche personenbezogenen Daten Sie erheben (Formulare, Analytics, Tracking)</li>
                    <li>Dokumentieren Sie die Rechtsgrundlage für jede Datenverarbeitung (Art. 6 DSGVO)</li>
                    <li>Aktualisieren Sie Ihre Datenschutzerklärung entsprechend der gefundenen Datenverarbeitungen</li>
                    <li>Nutzen Sie unseren Generator für eine rechtssichere und vollständige Datenschutzerklärung</li>
                  </ol>
                  <button
                    onClick={() => {
                      if (typeof window !== 'undefined') {
                        window.dispatchEvent(new CustomEvent('complyo:open-legal-generator', { detail: { type: 'datenschutz' } }));
                      }
                    }}
                    className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold rounded-lg hover:from-green-600 hover:to-emerald-600 transition-all text-sm"
                  >
                    <Shield className="w-4 h-4" />
                    Datenschutz-Generator öffnen
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ✅ NEU: Rechtssichere Texte — AGB / Widerruf */}
          {!isCookieIssue(issue) &&
           !issue.category?.toLowerCase().includes('barriere') &&
           !issue.category?.toLowerCase().includes('accessibility') &&
           !issue.category?.toLowerCase().includes('dsgvo') &&
           !issue.category?.toLowerCase().includes('gdpr') &&
           !issue.category?.toLowerCase().includes('datenschutz') &&
           !issue.category?.toLowerCase().includes('impressum') &&
           !issue.title?.toLowerCase().includes('datenschutz') &&
           !issue.title?.toLowerCase().includes('impressum') &&
           (issue.category?.toLowerCase().includes('legal') ||
            issue.category?.toLowerCase().includes('rechtssicher') ||
            issue.title?.toLowerCase().includes('agb') ||
            issue.title?.toLowerCase().includes('widerruf') ||
            issue.title?.toLowerCase().includes('allgemeine geschäfts')) && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-purple-500/20 rounded-lg flex-shrink-0">
                  <FileText className="w-5 h-5 text-purple-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm text-purple-800 font-medium mb-2">Rechtssicherer Text fehlt:</p>
                  <ol className="list-decimal list-inside text-sm text-purple-700 space-y-2 mb-4">
                    <li>Prüfen Sie ob Sie AGB oder eine Widerrufserklärung benötigen (erforderlich bei Onlineshops & Dienstleistungen)</li>
                    <li>Nutzen Sie unseren KI-Generator für rechtssichere, anwaltlich geprüfte Texte</li>
                    <li>Passen Sie den generierten Text auf Ihr Unternehmen an und veröffentlichen Sie ihn</li>
                  </ol>
                  <button
                    onClick={() => setShowAIPreview(true)}
                    className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all text-sm"
                  >
                    <Sparkles className="w-4 h-4" />
                    KI-Fix starten
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ✅ NEU: Allgemeiner Fallback für alle anderen Issue-Typen ohne spezifische Anleitung */}
          {!isCookieIssue(issue) &&
           !issue.category?.toLowerCase().includes('barriere') &&
           !issue.category?.toLowerCase().includes('accessibility') &&
           !issue.title?.toLowerCase().includes('wcag') &&
           !issue.title?.toLowerCase().includes('aria') &&
           !issue.title?.toLowerCase().includes('kontrast') &&
           !issue.title?.toLowerCase().includes('alt-text') &&
           !issue.category?.toLowerCase().includes('dsgvo') &&
           !issue.category?.toLowerCase().includes('gdpr') &&
           !issue.category?.toLowerCase().includes('datenschutz') &&
           !issue.title?.toLowerCase().includes('dsgvo') &&
           !issue.title?.toLowerCase().includes('personenbezogen') &&
           !issue.title?.toLowerCase().includes('verarbeitung') &&
           !issue.category?.toLowerCase().includes('legal') &&
           !issue.category?.toLowerCase().includes('rechtssicher') &&
           !issue.title?.toLowerCase().includes('agb') &&
           !issue.title?.toLowerCase().includes('widerruf') &&
           !issue.title?.toLowerCase().includes('allgemeine geschäfts') &&
           !issue.category?.toLowerCase().includes('impressum') &&
           !issue.title?.toLowerCase().includes('datenschutz') &&
           !issue.title?.toLowerCase().includes('impressum') && (
            <div className="bg-zinc-50 border border-zinc-200 rounded-lg p-4 mb-4">
              <p className="text-sm text-zinc-700 font-medium mb-2">So beheben Sie dieses Problem:</p>
              <ol className="list-decimal list-inside text-sm text-zinc-600 space-y-2">
                <li>Lesen Sie die Beschreibung des Problems oben sorgfältig durch</li>
                <li>Klicken Sie auf <strong>"KI-Fix starten"</strong> für eine automatisch generierte Lösung</li>
                <li>Kopieren Sie den generierten Code oder Text und fügen Sie ihn in Ihre Website ein</li>
                <li>Starten Sie anschließend einen neuen Scan, um die Behebung zu bestätigen</li>
              </ol>
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

      {/* AI-Fix Section */}
      {issue.auto_fixable && !isAnalysisOnly && (planType === 'free' || planType === 'ai' || planType === 'expert') && (
        <div className="mt-4 space-y-3">
          {/* Plan-Hinweis für Free-Nutzer — BEVOR sie klicken */}
          {planType === 'free' && (
            <div className="flex items-center gap-2 px-3 py-2 bg-zinc-100 border border-zinc-300 rounded-lg">
              <Lock className="w-4 h-4 text-zinc-500 flex-shrink-0" />
              <span className="text-xs text-zinc-600">
                KI-Fix erfordert <strong>AI Plan</strong> — Klick zeigt Upgrade-Optionen
              </span>
            </div>
          )}

          {/* Hinweis wenn andere Seite gelockt ist — aber Fix trotzdem möglich */}
          {isOtherSiteLocked && (
            <div className="flex items-center gap-2 px-3 py-2 bg-zinc-100 border border-zinc-300 rounded-lg mb-2">
              <span className="text-xs text-zinc-600">
                Hinweis: Ihre KI-Fixes sind personalisiert für <strong>{lockedOptimizationUrl}</strong>. Der Fix gilt für die analysierte Seite.
              </span>
            </div>
          )}
          
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
        </div>
      )}

      {/* Analyse-Only Hinweis: Fixes gesperrt */}
      {isAnalysisOnly && (
        <div className="mt-4 flex items-center gap-2 px-3 py-2 bg-zinc-100 border border-zinc-300 rounded-lg">
          <Lock className="w-4 h-4 text-zinc-500 flex-shrink-0" />
          <span className="text-xs text-zinc-600">
            Fixes sind nur für Ihre registrierte Website verfügbar. Wechseln Sie zurück, um Optimierungen zu starten.
          </span>
        </div>
      )}

      {/* Expert Service CTA */}
      {planType === 'expert' && !isAnalysisOnly && (
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
