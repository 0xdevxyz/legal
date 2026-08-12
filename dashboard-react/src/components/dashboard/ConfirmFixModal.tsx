'use client';

import React, { useState, useEffect } from 'react';
import { X, AlertTriangle, CheckCircle, Info, Code, FileText, BookOpen } from 'lucide-react';
import { ClientOnlyPortal } from '../ClientOnlyPortal';

// KI-Fix Typen für bessere UX
type FixType = 'code' | 'text' | 'guide';

interface ConfirmFixModalProps {
  isOpen: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  issueTitle: string;
  fixType?: FixType;
  isFirstFix?: boolean;
}

const FIX_TYPE_INFO: Record<FixType, {
  icon: React.ElementType;
  title: string;
  description: string;
  examples: string[];
}> = {
  code: {
    icon: Code,
    title: 'Code-Lösung',
    description: 'Fertiger HTML/CSS/JavaScript Code zum direkten Einbau',
    examples: [
      'Cookie-Banner Code',
      'ARIA-Labels für Barrierefreiheit',
      'Meta-Tags für SEO',
    ]
  },
  text: {
    icon: FileText,
    title: 'Text-Vorlage',
    description: 'Rechtsichere Texte zum Kopieren und Anpassen',
    examples: [
      'Datenschutzerklärung',
      'Impressum',
      'AGB-Textbausteine',
    ]
  },
  guide: {
    icon: BookOpen,
    title: 'Schritt-für-Schritt Anleitung',
    description: 'Detaillierte Implementierungs-Anleitung',
    examples: [
      'Setup-Anleitung mit Screenshots',
      'Checkliste zur Umsetzung',
      'Best Practices',
    ]
  }
};

export const ConfirmFixModal: React.FC<ConfirmFixModalProps> = ({
  isOpen,
  onConfirm,
  onCancel,
  issueTitle,
  fixType = 'guide',
  isFirstFix = false
}) => {
  const [acknowledged, setAcknowledged] = useState(false);
  const [mounted, setMounted] = useState(false);
  
  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  // ✅ CRITICAL: EARLY RETURN für SSR - BEVOR irgendetwas anderes passiert!
  if (!mounted || typeof document === 'undefined') return null;
  if (!isOpen) return null;

  const fixInfo = FIX_TYPE_INFO[fixType];
  const FixIcon = fixInfo.icon;

  const handleConfirm = () => {
    if (isFirstFix && !acknowledged) {
      alert('Bitte bestätigen Sie, dass Sie die Warnung gelesen haben.');
      return;
    }
    onConfirm();
  };

  const modalContent = (
    <div 
      className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center p-4"
      style={{ zIndex: 999999 }}
      onClick={(e) => {
        // Close on backdrop click
        if (e.target === e.currentTarget) {
          onCancel();
        }
      }}
    >
      <div 
        className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-purple-50">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-lg">
              <FixIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{fixInfo.title}</h2>
              <p className="text-sm text-gray-600">{fixInfo.description}</p>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="text-gray-600 dark:text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
          {/* Issue Title */}
          <div className="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-1 text-sm uppercase tracking-wide">Ihr Problem:</h3>
            <p className="text-blue-900 text-lg font-medium">{issueTitle}</p>
          </div>

          {/* Was Sie bekommen - basierend auf Fix-Typ */}
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-lg p-5">
            <h3 className="font-bold text-gray-900 flex items-center gap-2 mb-4 text-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
              Was die KI für Sie erstellt:
            </h3>
            <ul className="space-y-3">
              {fixInfo.examples.map((example, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <span className="text-green-600 text-xl flex-shrink-0">✓</span>
                  <span className="text-gray-800 font-medium">{example}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Rechtlicher Disclaimer (IMMER anzeigen) */}
          <div className="bg-gray-50 border border-gray-300 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-gray-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 mb-2">📋 Rechtlicher Hinweis</h3>
                <p className="text-sm text-gray-700 mb-2">
                  <strong>Complyo generiert Patches basierend auf öffentlich zugänglichem Code.</strong> 
                  Sie übernehmen die Verantwortung für die Anwendung dieser Änderungen in Ihrem System.
                </p>
                <p className="text-xs text-gray-600">
                  Complyo wendet Code-Änderungen ausschließlich nach ausdrücklicher Bestätigung durch den Nutzer an. 
                  Wir übernehmen keine Haftung für fehlerhafte Patches. 
                  <a href="/terms-liability" target="_blank" className="text-blue-600 hover:underline ml-1">
                    Vollständige AGB lesen →
                  </a>
                </p>
              </div>
            </div>
          </div>

          {/* Warning für ersten Fix */}
          {isFirstFix && (
            <div className="bg-yellow-50 border-l-4 border-yellow-500 rounded-r-lg p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-semibold text-yellow-900 mb-2">⚠️ Wichtiger Hinweis</h3>
                  <p className="text-yellow-800 text-sm mb-3">
                    Mit dem Start der Fix-Generierung verfällt Ihr 14-tägiges Rückgaberecht.
                    Dies gilt nur für den ersten generierten Fix.
                  </p>
                  <label className="flex items-start gap-2 cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={acknowledged}
                      onChange={(e) => setAcknowledged(e.target.checked)}
                      className="mt-1 w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                    />
                    <span className="text-sm text-yellow-900 font-medium group-hover:text-yellow-950">
                      Ich habe die Warnung verstanden und möchte fortfahren
                    </span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Info: Geschätzte Zeit */}
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-purple-900 mb-1">⏱️ Geschätzte Dauer</h4>
                <p className="text-sm text-purple-800">
                  Die KI-Generierung dauert <strong>5-15 Sekunden</strong>. 
                  Bei komplexen Rechtsfragen kann es etwas länger dauern.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer/Actions */}
        <div className="flex gap-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={() => {
              onCancel();
            }}
            className="flex-1 px-6 py-3 border-2 border-gray-300 rounded-lg hover:bg-white hover:border-gray-400 font-bold text-gray-700 transition-all"
          >
            Abbrechen
          </button>
          <button
            onClick={handleConfirm}
            disabled={isFirstFix && !acknowledged}
            className="flex-1 px-6 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-bold disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
          >
            {isFirstFix ? '✅ Verstanden, Fix generieren' : '🤖 Jetzt KI-Fix starten'}
          </button>
        </div>
      </div>
    </div>
  );

  // ✅ 100% SSR-SAFE mit ClientOnlyPortal
  return <ClientOnlyPortal>{modalContent}</ClientOnlyPortal>;
};

