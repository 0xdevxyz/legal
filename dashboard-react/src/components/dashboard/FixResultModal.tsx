'use client';

import React, { useState } from 'react';
import { X, CheckCircle, Copy, Download, Code, FileText, Sparkles, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { createPortal } from 'react-dom';
import { LegalTextWizard } from './LegalTextWizard';

interface FixResultModalProps {
  isOpen: boolean;
  onClose: () => void;
  fixResult: any;
}

export const FixResultModal: React.FC<FixResultModalProps> = ({ isOpen, onClose, fixResult }) => {
  const [copied, setCopied] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [showWizard, setShowWizard] = useState(false);

  React.useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  // Check if this is a legal text fix
  const isLegalText = fixResult?.type === 'text' && 
    (fixResult?.title?.toLowerCase().includes('impressum') || 
     fixResult?.title?.toLowerCase().includes('datenschutz') ||
     fixResult?.title?.toLowerCase().includes('agb') ||
     fixResult?.title?.toLowerCase().includes('widerruf'));

  const getLegalTextType = (): 'impressum' | 'datenschutz' | 'agb' | 'widerruf' => {
    const title = fixResult?.title?.toLowerCase() || '';
    if (title.includes('impressum')) return 'impressum';
    if (title.includes('datenschutz')) return 'datenschutz';
    if (title.includes('agb')) return 'agb';
    if (title.includes('widerruf')) return 'widerruf';
    return 'impressum';
  };

  React.useEffect(() => {
    // Auto-open wizard for legal texts
    if (isOpen && isLegalText && !fixResult?.content?.includes('[')) {
      setShowWizard(false); // Start with wizard for empty/template content
    }
  }, [isOpen, isLegalText, fixResult]);

  if (!isOpen || !fixResult || !mounted) return null;

  const handleCopy = () => {
    const content = fixResult.content || JSON.stringify(fixResult, null, 2);
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const content = fixResult.content || JSON.stringify(fixResult, null, 2);
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `complyo-fix-${fixResult.title?.toLowerCase().replace(/\s+/g, '-') || 'solution'}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getIcon = () => {
    switch (fixResult.type) {
      case 'code':
        return <Code className="w-6 h-6 text-blue-500" />;
      case 'text':
        return <FileText className="w-6 h-6 text-purple-500" />;
      case 'widget':
        return <Sparkles className="w-6 h-6 text-green-500" />;
      case 'guide':
        return <BookOpen className="w-6 h-6 text-orange-500" />;
      default:
        return <CheckCircle className="w-6 h-6 text-green-500" />;
    }
  };

  const modalContent = (
    <div 
      className="fixed inset-0 z-[999999] flex items-center justify-center p-4"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.75)' }}
      onClick={(e) => {
        if (e.target === e.currentTarget && !showWizard) onClose();
      }}
    >
      <Card className="w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-white dark:bg-gray-900 shadow-2xl">{showWizard && isLegalText ? (
          /* Legal Text Wizard */
          <>
            <CardHeader className="border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-2xl font-bold text-gray-900 dark:text-white">
                    ⚖️ {fixResult.title || 'Rechtstext erstellen'}
                  </CardTitle>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Geführte Erstellung mit Ihren Firmendaten
                  </p>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  aria-label="Schließen"
                >
                  <X className="w-6 h-6 text-gray-500 dark:text-gray-400" />
                </button>
              </div>
            </CardHeader>
            <CardContent className="p-6">
              <LegalTextWizard
                fixType={getLegalTextType()}
                generatedContent={fixResult.content}
                onComplete={(data) => {
                  console.log('Legal text completed:', data);
                  setShowWizard(false);
                  onClose();
                }}
                onBack={() => setShowWizard(false)}
              />
            </CardContent>
          </>
        ) : (
          /* Regular Fix Display */
          <>
        <CardHeader className="border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
                {getIcon()}
              </div>
              <div>
                <CardTitle className="text-2xl font-bold text-gray-900 dark:text-white">
                  ✅ Fix erfolgreich generiert!
                </CardTitle>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {fixResult.title || 'Lösung bereit zur Integration'}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
              aria-label="Schließen"
            >
              <X className="w-6 h-6 text-gray-500 dark:text-gray-400" />
            </button>
          </div>
        </CardHeader>

        <CardContent className="p-6 space-y-6">
          {/* Description */}
          {fixResult.description && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 p-4 rounded-r-lg">
              <p className="text-gray-700 dark:text-gray-300">{fixResult.description}</p>
            </div>
          )}

          {/* Main Content */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {fixResult.type === 'code' && '💻 Code-Snippet'}
                {fixResult.type === 'text' && '📄 Text-Content'}
                {fixResult.type === 'widget' && '✨ Widget-Integration'}
                {fixResult.type === 'guide' && '📖 Schritt-für-Schritt-Anleitung'}
              </h3>
              <div className="flex gap-2">
                <Button
                  onClick={handleCopy}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <Copy className="w-4 h-4" />
                  {copied ? 'Kopiert!' : 'Kopieren'}
                </Button>
                <Button
                  onClick={handleDownload}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Download
                </Button>
              </div>
            </div>

            {/* Content based on type */}
            {(fixResult.type === 'code' || fixResult.type === 'widget') && fixResult.content && (
              <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
                <pre className="text-sm font-mono whitespace-pre-wrap">
                  <code>{fixResult.content}</code>
                </pre>
              </div>
            )}

            {fixResult.type === 'text' && fixResult.content && (
              <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4 rounded-lg overflow-y-auto max-h-96">
                <div 
                  className="prose prose-sm dark:prose-invert max-w-none"
                  dangerouslySetInnerHTML={{ __html: fixResult.content }}
                />
              </div>
            )}

            {fixResult.type === 'guide' && fixResult.guide_steps && (
              <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4 rounded-lg">
                <ol className="space-y-3">
                  {fixResult.guide_steps.map((step: string, index: number) => (
                    <li key={index} className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold flex-shrink-0">
                        {index + 1}
                      </div>
                      <p className="text-gray-700 dark:text-gray-300 pt-1">{step}</p>
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {/* Fallback: Show raw content */}
            {!['code', 'text', 'widget', 'guide'].includes(fixResult.type) && fixResult.content && (
              <div className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4 rounded-lg overflow-x-auto">
                <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {typeof fixResult.content === 'string' 
                    ? fixResult.content 
                    : JSON.stringify(fixResult.content, null, 2)}
                </pre>
              </div>
            )}
          </div>

          {/* Integration Instructions */}
          {fixResult.integration_instructions && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-500 p-4 rounded-r-lg">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                📋 Integrations-Anleitung:
              </h4>
              <p className="text-sm text-gray-700 dark:text-gray-300">
                {fixResult.integration_instructions}
              </p>
            </div>
          )}

          {/* Auto-Fixable Issues List (for Widget) */}
          {fixResult.auto_fixable_issues && fixResult.auto_fixable_issues.length > 0 && (
            <div className="bg-green-50 dark:bg-green-900/20 border-l-4 border-green-500 p-4 rounded-r-lg">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-green-600" />
                Das Widget behebt automatisch:
              </h4>
              <ul className="space-y-2">
                {fixResult.auto_fixable_issues.map((issue: string, index: number) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <span className="text-green-600 font-bold">✓</span>
                    <span>{issue}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-xs text-gray-600 dark:text-gray-400">
                Diese Probleme werden sofort behoben, sobald Sie das Widget einbinden. Keine weiteren Schritte erforderlich!
              </p>
            </div>
          )}

          {/* Site ID Info */}
          {fixResult.site_id && fixResult.site_id !== "YOUR_SITE_ID" && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-4 rounded-lg">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                🔑 Ihre Site-ID
              </h4>
              <code className="block bg-white dark:bg-gray-800 px-3 py-2 rounded border border-gray-300 dark:border-gray-600 text-sm font-mono text-blue-600 dark:text-blue-400">
                {fixResult.site_id}
              </code>
              <p className="mt-2 text-xs text-gray-600 dark:text-gray-400">
                Diese ID ist bereits im Script eingefügt. Sie müssen sie nicht mehr ändern.
              </p>
            </div>
          )}

          {/* Additional Info */}
          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            {fixResult.target_url && (
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Ziel-URL:</p>
                <p className="text-sm font-medium text-gray-900 dark:text-white">{fixResult.target_url}</p>
              </div>
            )}
            {fixResult.widget_script_url && (
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Widget-URL:</p>
                <p className="text-sm font-mono text-blue-600 dark:text-blue-400">{fixResult.widget_script_url}</p>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
            <Button
              onClick={onClose}
              variant="outline"
            >
              Schließen
            </Button>
            {isLegalText ? (
              <Button
                onClick={() => setShowWizard(true)}
                className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white"
              >
                <FileText className="w-4 h-4 mr-2" />
                Mit Firmendaten personalisieren
              </Button>
            ) : (
              <Button
                onClick={() => {
                  handleCopy();
                  // Optional: Auto-close after copy
                  // setTimeout(() => onClose(), 1500);
                }}
                className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white"
              >
                <Copy className="w-4 h-4 mr-2" />
                Kopieren & Verwenden
              </Button>
            )}
          </div>
        </CardContent>
        </>
        )}
      </Card>
    </div>
  );

  return createPortal(modalContent, document.body);
};

