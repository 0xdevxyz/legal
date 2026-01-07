'use client';

import React, { useState, useMemo } from 'react';
import {
  CheckCircle,
  Circle,
  ChevronRight,
  ChevronLeft,
  Download,
  Zap,
  Code,
  BookOpen,
  AlertTriangle,
  Shield,
  RefreshCw,
  ExternalLink,
  Copy,
  Check,
} from 'lucide-react';
import { FixStepCard } from './FixStepCard';

// =============================================================================
// Types
// =============================================================================

export type FixType = 'widget' | 'code' | 'manual';
export type Difficulty = 'easy' | 'medium' | 'hard';
export type FeatureId = 
  | 'ALT_TEXT' 
  | 'CONTRAST' 
  | 'FORM_LABELS' 
  | 'LANDMARKS' 
  | 'KEYBOARD' 
  | 'FOCUS' 
  | 'ARIA' 
  | 'HEADINGS' 
  | 'MEDIA';

export interface StructuredIssue {
  id: string;
  feature_id: FeatureId;
  title: string;
  description: string;
  severity: string;
  wcag_criteria: string[];
  legal_refs: string[];
  auto_fix_level: 'HIGH' | 'MEDIUM' | 'LOW' | 'MANUAL';
  difficulty: Difficulty;
  fix_types: FixType[];
  recommended_fix_type: FixType;
  element_html?: string;
  selector?: string;
  page_url?: string;
  suggested_fix?: string;
  fix_code?: string;
  risk_euro: number;
  metadata?: Record<string, unknown>;
}

export interface WidgetFix {
  feature_id: string;
  issues_count: number;
  fix_type: 'widget';
  difficulty: 'easy';
  integration_code: string;
  description: string;
  instructions: string;
}

export interface CodePatch {
  success: boolean;
  feature_id: string;
  file_path: string;
  unified_diff: string | null;
  fix_type: 'code';
  difficulty: Difficulty;
  ai_model_used: string;
  generation_time_ms: number;
  tokens_used?: number;
  cost_usd?: number;
  error?: string;
  wcag_criteria: string[];
  description: string;
  instructions: string;
}

export interface ManualGuide {
  feature_id: string;
  title: string;
  description: string;
  wcag_criteria: string[];
  legal_refs: string[];
  difficulty: Difficulty;
  steps: string[];
  resources: { title: string; url: string }[];
}

export interface FixPackage {
  site_url: string;
  generated_at: string;
  total_issues: number;
  fixed_issues: number;
  widget_fixes: WidgetFix[];
  code_patches: CodePatch[];
  manual_guides: ManualGuide[];
  summary: {
    total_issues: number;
    auto_fixable: number;
    widget_fixable: number;
    manual_only: number;
    by_difficulty: {
      easy: number;
      medium: number;
      hard: number;
    };
    by_feature: Record<string, number>;
    total_risk_euro: number;
    recommendation: string;
  };
}

interface FixWizardProps {
  fixPackage: FixPackage;
  siteUrl: string;
  onWidgetActivate?: () => void;
  onDownloadBundle?: () => void;
  onRescan?: () => void;
  isLoading?: boolean;
}

// =============================================================================
// Wizard Steps
// =============================================================================

type WizardStep = 'overview' | 'categorize' | 'select' | 'apply' | 'verify';

const WIZARD_STEPS: { id: WizardStep; title: string; description: string }[] = [
  { id: 'overview', title: 'Übersicht', description: 'Zusammenfassung der Probleme' },
  { id: 'categorize', title: 'Kategorien', description: 'Nach Schwierigkeit sortiert' },
  { id: 'select', title: 'Lösung wählen', description: 'Widget oder Code-Patch' },
  { id: 'apply', title: 'Anwenden', description: 'Fixes implementieren' },
  { id: 'verify', title: 'Prüfen', description: 'Ergebnis verifizieren' },
];

// =============================================================================
// Feature Labels
// =============================================================================

const FEATURE_LABELS: Record<FeatureId, { label: string; icon: React.ReactNode }> = {
  ALT_TEXT: { label: 'Alt-Texte', icon: '🖼️' },
  CONTRAST: { label: 'Kontrast', icon: '🎨' },
  FORM_LABELS: { label: 'Formular-Labels', icon: '📝' },
  LANDMARKS: { label: 'Seitenstruktur', icon: '🏗️' },
  KEYBOARD: { label: 'Tastatur', icon: '⌨️' },
  FOCUS: { label: 'Fokus', icon: '🎯' },
  ARIA: { label: 'ARIA', icon: '🔊' },
  HEADINGS: { label: 'Überschriften', icon: '📑' },
  MEDIA: { label: 'Medien', icon: '🎬' },
};

// =============================================================================
// Component
// =============================================================================

export function FixWizard({
  fixPackage,
  siteUrl,
  onWidgetActivate,
  onDownloadBundle,
  onRescan,
  isLoading = false,
}: FixWizardProps) {
  const [currentStep, setCurrentStep] = useState<WizardStep>('overview');
  const [selectedFixType, setSelectedFixType] = useState<'widget' | 'code' | null>(null);
  const [copiedCode, setCopiedCode] = useState(false);
  const [widgetActivated, setWidgetActivated] = useState(false);

  const { summary, widget_fixes, code_patches, manual_guides } = fixPackage;

  // Gruppiere nach Schwierigkeit
  const issuesByDifficulty = useMemo(() => {
    const easy = widget_fixes.length + code_patches.filter(p => p.difficulty === 'easy').length;
    const medium = code_patches.filter(p => p.difficulty === 'medium').length;
    const hard = manual_guides.length + code_patches.filter(p => p.difficulty === 'hard').length;
    return { easy, medium, hard };
  }, [widget_fixes, code_patches, manual_guides]);

  const currentStepIndex = WIZARD_STEPS.findIndex(s => s.id === currentStep);

  const goToNextStep = () => {
    const nextIndex = currentStepIndex + 1;
    if (nextIndex < WIZARD_STEPS.length) {
      setCurrentStep(WIZARD_STEPS[nextIndex].id);
    }
  };

  const goToPrevStep = () => {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      setCurrentStep(WIZARD_STEPS[prevIndex].id);
    }
  };

  const handleCopyCode = async (code: string) => {
    await navigator.clipboard.writeText(code);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  const handleWidgetActivate = () => {
    setWidgetActivated(true);
    onWidgetActivate?.();
  };

  // Render Step Content
  const renderStepContent = () => {
    switch (currentStep) {
      case 'overview':
        return renderOverviewStep();
      case 'categorize':
        return renderCategorizeStep();
      case 'select':
        return renderSelectStep();
      case 'apply':
        return renderApplyStep();
      case 'verify':
        return renderVerifyStep();
      default:
        return null;
    }
  };

  // =============================================================================
  // Step: Overview
  // =============================================================================
  const renderOverviewStep = () => (
    <div className="space-y-6">
      {/* Hero-Statistik */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold mb-2">
              {summary.total_issues} Probleme gefunden
            </h2>
            <p className="text-blue-100 text-lg">
              {summary.auto_fixable} davon automatisch lösbar
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-yellow-300">
              €{summary.total_risk_euro.toLocaleString()}
            </div>
            <p className="text-blue-200 text-sm">Potentielles Bußgeld-Risiko</p>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
          <div className="text-3xl font-bold text-green-700">{issuesByDifficulty.easy}</div>
          <div className="text-green-600 font-medium">Einfach</div>
          <div className="text-green-500 text-sm mt-1">One-Click Fix</div>
        </div>
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 text-center">
          <div className="text-3xl font-bold text-yellow-700">{issuesByDifficulty.medium}</div>
          <div className="text-yellow-600 font-medium">Mittel</div>
          <div className="text-yellow-500 text-sm mt-1">Code-Patch</div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <div className="text-3xl font-bold text-red-700">{issuesByDifficulty.hard}</div>
          <div className="text-red-600 font-medium">Komplex</div>
          <div className="text-red-500 text-sm mt-1">Anleitung</div>
        </div>
      </div>

      {/* Empfehlung */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-blue-100 rounded-lg">
            <Shield className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-blue-900 mb-1">Unsere Empfehlung</h3>
            <p className="text-blue-700">{summary.recommendation}</p>
          </div>
        </div>
      </div>

      {/* Features-Übersicht */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Betroffene Bereiche</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {Object.entries(summary.by_feature).map(([featureId, count]) => {
            const feature = FEATURE_LABELS[featureId as FeatureId];
            if (!feature || count === 0) return null;
            return (
              <div
                key={featureId}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
              >
                <span className="text-2xl">{feature.icon}</span>
                <div>
                  <div className="font-medium text-gray-900">{feature.label}</div>
                  <div className="text-sm text-gray-500">{count} Problem{count !== 1 ? 'e' : ''}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );

  // =============================================================================
  // Step: Categorize
  // =============================================================================
  const renderCategorizeStep = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Probleme nach Schwierigkeit</h2>
      
      {/* Einfache Fixes */}
      {(widget_fixes.length > 0 || code_patches.filter(p => p.difficulty === 'easy').length > 0) && (
        <div className="bg-white border border-green-200 rounded-xl overflow-hidden">
          <div className="bg-green-50 px-6 py-4 border-b border-green-200">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Zap className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <h3 className="font-semibold text-green-900">Einfach - One-Click</h3>
                <p className="text-sm text-green-600">
                  {widget_fixes.length + code_patches.filter(p => p.difficulty === 'easy').length} Probleme
                </p>
              </div>
            </div>
          </div>
          <div className="p-6 space-y-3">
            {widget_fixes.map((fix, i) => (
              <FixStepCard
                key={`widget-${i}`}
                title={FEATURE_LABELS[fix.feature_id as FeatureId]?.label || fix.feature_id}
                description={fix.description}
                difficulty="easy"
                fixType="widget"
                issuesCount={fix.issues_count}
              />
            ))}
          </div>
        </div>
      )}

      {/* Mittlere Fixes */}
      {code_patches.filter(p => p.difficulty === 'medium').length > 0 && (
        <div className="bg-white border border-yellow-200 rounded-xl overflow-hidden">
          <div className="bg-yellow-50 px-6 py-4 border-b border-yellow-200">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Code className="w-5 h-5 text-yellow-600" />
              </div>
              <div>
                <h3 className="font-semibold text-yellow-900">Mittel - Code-Patch</h3>
                <p className="text-sm text-yellow-600">
                  {code_patches.filter(p => p.difficulty === 'medium').length} Probleme
                </p>
              </div>
            </div>
          </div>
          <div className="p-6 space-y-3">
            {code_patches.filter(p => p.difficulty === 'medium').map((patch, i) => (
              <FixStepCard
                key={`code-${i}`}
                title={FEATURE_LABELS[patch.feature_id as FeatureId]?.label || patch.feature_id}
                description={patch.description}
                difficulty="medium"
                fixType="code"
                filePath={patch.file_path}
              />
            ))}
          </div>
        </div>
      )}

      {/* Komplexe Fixes */}
      {manual_guides.length > 0 && (
        <div className="bg-white border border-red-200 rounded-xl overflow-hidden">
          <div className="bg-red-50 px-6 py-4 border-b border-red-200">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <BookOpen className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <h3 className="font-semibold text-red-900">Komplex - Manuelle Anleitung</h3>
                <p className="text-sm text-red-600">{manual_guides.length} Probleme</p>
              </div>
            </div>
          </div>
          <div className="p-6 space-y-3">
            {manual_guides.map((guide, i) => (
              <FixStepCard
                key={`manual-${i}`}
                title={guide.title}
                description={guide.description}
                difficulty="hard"
                fixType="manual"
                wcagCriteria={guide.wcag_criteria}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // =============================================================================
  // Step: Select
  // =============================================================================
  const renderSelectStep = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Wählen Sie Ihre Lösung</h2>
      <p className="text-gray-600">
        Wie möchten Sie die Barrierefreiheits-Probleme beheben?
      </p>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Widget-Option */}
        <button
          onClick={() => setSelectedFixType('widget')}
          className={`p-6 rounded-2xl border-2 text-left transition-all ${
            selectedFixType === 'widget'
              ? 'border-blue-500 bg-blue-50 ring-4 ring-blue-100'
              : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
          }`}
        >
          <div className="flex items-center gap-4 mb-4">
            <div className={`p-3 rounded-xl ${
              selectedFixType === 'widget' ? 'bg-blue-100' : 'bg-gray-100'
            }`}>
              <Zap className={`w-8 h-8 ${
                selectedFixType === 'widget' ? 'text-blue-600' : 'text-gray-600'
              }`} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Complyo Widget</h3>
              <span className="inline-block px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                Empfohlen
              </span>
            </div>
          </div>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              Sofortige Wirkung
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              {summary.widget_fixable} Probleme automatisch behoben
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              Eine Zeile Code
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              Keine technischen Kenntnisse nötig
            </li>
          </ul>
        </button>

        {/* Code-Patch-Option */}
        <button
          onClick={() => setSelectedFixType('code')}
          className={`p-6 rounded-2xl border-2 text-left transition-all ${
            selectedFixType === 'code'
              ? 'border-blue-500 bg-blue-50 ring-4 ring-blue-100'
              : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
          }`}
        >
          <div className="flex items-center gap-4 mb-4">
            <div className={`p-3 rounded-xl ${
              selectedFixType === 'code' ? 'bg-blue-100' : 'bg-gray-100'
            }`}>
              <Code className={`w-8 h-8 ${
                selectedFixType === 'code' ? 'text-blue-600' : 'text-gray-600'
              }`} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Code-Patches</h3>
              <span className="inline-block px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
                Permanent
              </span>
            </div>
          </div>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              Direkt im Code
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              Besser für SEO
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              ZIP-Download mit Anleitung
            </li>
            <li className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-yellow-500" />
              Technisches Verständnis hilfreich
            </li>
          </ul>
        </button>
      </div>
    </div>
  );

  // =============================================================================
  // Step: Apply
  // =============================================================================
  const renderApplyStep = () => (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">
        {selectedFixType === 'widget' ? 'Widget aktivieren' : 'Code-Patches anwenden'}
      </h2>

      {selectedFixType === 'widget' ? (
        <div className="space-y-6">
          {/* Widget-Integration */}
          <div className="bg-gray-900 rounded-xl overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 bg-gray-800">
              <span className="text-sm text-gray-400">HTML - Vor &lt;/body&gt; einfügen</span>
              <button
                onClick={() => handleCopyCode(widget_fixes[0]?.integration_code || '')}
                className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition"
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
            <pre className="p-4 text-sm text-green-400 overflow-x-auto">
              <code>{widget_fixes[0]?.integration_code || '<!-- Kein Widget-Code verfügbar -->'}</code>
            </pre>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
            <h3 className="font-semibold text-blue-900 mb-3">So geht&apos;s:</h3>
            <ol className="space-y-3 text-blue-800">
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">1</span>
                <span>Kopieren Sie den Code oben</span>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">2</span>
                <span>Öffnen Sie Ihre Website-Dateien (index.html oder Template)</span>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">3</span>
                <span>Fügen Sie den Code vor dem &lt;/body&gt;-Tag ein</span>
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">4</span>
                <span>Speichern und Website neu laden</span>
              </li>
            </ol>
          </div>

          {!widgetActivated && (
            <button
              onClick={handleWidgetActivate}
              className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition flex items-center justify-center gap-2"
            >
              <Zap className="w-5 h-5" />
              Widget jetzt aktivieren
            </button>
          )}

          {widgetActivated && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
              <h3 className="font-semibold text-green-900">Widget aktiviert!</h3>
              <p className="text-green-700">Die Fixes werden jetzt auf Ihrer Website angewendet.</p>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          {/* Download-Button */}
          <button
            onClick={onDownloadBundle}
            className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition flex items-center justify-center gap-2"
          >
            <Download className="w-5 h-5" />
            Fix-Paket herunterladen (ZIP)
          </button>

          <div className="bg-gray-50 border border-gray-200 rounded-xl p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Das Paket enthält:</h3>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                {code_patches.filter(p => p.success).length} Code-Patches (Unified Diff)
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                README mit Anleitung
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                WordPress-Plugin (falls WordPress erkannt)
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                HTML-Snippets zum direkten Einfügen
              </li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );

  // =============================================================================
  // Step: Verify
  // =============================================================================
  const renderVerifyStep = () => (
    <div className="space-y-6 text-center">
      <div className="py-8">
        <CheckCircle className="w-20 h-20 text-green-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Fast geschafft!</h2>
        <p className="text-gray-600 max-w-md mx-auto">
          Führen Sie einen erneuten Scan durch, um zu prüfen, ob alle Probleme behoben wurden.
        </p>
      </div>

      <button
        onClick={onRescan}
        disabled={isLoading}
        className="inline-flex items-center gap-2 px-8 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold rounded-xl transition"
      >
        {isLoading ? (
          <>
            <RefreshCw className="w-5 h-5 animate-spin" />
            Scanne...
          </>
        ) : (
          <>
            <RefreshCw className="w-5 h-5" />
            Website erneut scannen
          </>
        )}
      </button>

      <div className="pt-8 border-t border-gray-200 mt-8">
        <h3 className="font-semibold text-gray-900 mb-4">Weitere Ressourcen</h3>
        <div className="grid md:grid-cols-2 gap-4 max-w-lg mx-auto">
          <a
            href="https://complyo.tech/guides/accessibility"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 p-4 bg-gray-50 hover:bg-gray-100 rounded-xl text-left transition"
          >
            <BookOpen className="w-5 h-5 text-blue-600" />
            <span className="text-gray-900">BFSG-Leitfaden</span>
            <ExternalLink className="w-4 h-4 text-gray-400 ml-auto" />
          </a>
          <a
            href="https://complyo.tech/support"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 p-4 bg-gray-50 hover:bg-gray-100 rounded-xl text-left transition"
          >
            <Shield className="w-5 h-5 text-blue-600" />
            <span className="text-gray-900">Support kontaktieren</span>
            <ExternalLink className="w-4 h-4 text-gray-400 ml-auto" />
          </a>
        </div>
      </div>
    </div>
  );

  // =============================================================================
  // Main Render
  // =============================================================================
  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      {/* Progress Header */}
      <div className="bg-gray-50 border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-bold text-gray-900">Barrierefreiheit beheben</h1>
          <span className="text-sm text-gray-500">
            Schritt {currentStepIndex + 1} von {WIZARD_STEPS.length}
          </span>
        </div>
        
        {/* Step Indicators */}
        <div className="flex items-center gap-2">
          {WIZARD_STEPS.map((step, index) => (
            <React.Fragment key={step.id}>
              <button
                onClick={() => setCurrentStep(step.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                  index === currentStepIndex
                    ? 'bg-blue-100 text-blue-700'
                    : index < currentStepIndex
                    ? 'bg-green-100 text-green-700'
                    : 'bg-gray-100 text-gray-500'
                }`}
              >
                {index < currentStepIndex ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  <Circle className="w-4 h-4" />
                )}
                <span className="hidden md:inline">{step.title}</span>
              </button>
              {index < WIZARD_STEPS.length - 1 && (
                <ChevronRight className="w-4 h-4 text-gray-300" />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="p-6 md:p-8">
        {renderStepContent()}
      </div>

      {/* Navigation Footer */}
      <div className="bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-between">
        <button
          onClick={goToPrevStep}
          disabled={currentStepIndex === 0}
          className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          <ChevronLeft className="w-4 h-4" />
          Zurück
        </button>
        
        {currentStep !== 'verify' && (
          <button
            onClick={goToNextStep}
            disabled={currentStep === 'select' && !selectedFixType}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium rounded-lg transition"
          >
            Weiter
            <ChevronRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}

export default FixWizard;

