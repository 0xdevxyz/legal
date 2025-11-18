'use client';

import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { 
  Copy, 
  Check, 
  Download, 
  ExternalLink, 
  Code, 
  FileText, 
  Book, 
  Sparkles,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle2,
  Clock,
  Star
} from 'lucide-react';
import { useToast } from '@/components/ui/Toast';

// ============================================================================
// Types
// ============================================================================

interface FixData {
  fix_id: string;
  fix_type: 'code' | 'text' | 'widget' | 'guide';
  title: string;
  description?: string;
  
  // Code Fix
  code?: string;
  language?: string;
  before_code?: string;
  after_code?: string;
  
  // Text Fix
  text_content?: string;
  text_type?: string;
  placeholders?: string[];
  
  // Widget Fix
  widget_type?: string;
  integration_code?: string;
  configuration?: any;
  preview_url?: string;
  features?: string[];
  
  // Guide Fix
  steps?: Array<{
    step_number: number;
    title: string;
    description: string;
    code_example?: string;
    validation?: string;
    completed?: boolean;
  }>;
  difficulty?: string;
  
  // Common
  integration?: {
    instructions?: string;
    where?: string;
    file?: string;
  };
  estimated_time?: string;
  priority?: string;
  validation?: any;
  branding?: any;
  metadata?: any;
}

interface AIFixDisplayProps {
  fixData: FixData;
  onFeedback?: (rating: number, feedback?: string) => void;
  onApply?: () => void;
  className?: string;
}

// ============================================================================
// Main Component
// ============================================================================

export const AIFixDisplay: React.FC<AIFixDisplayProps> = ({
  fixData,
  onFeedback,
  onApply,
  className = ''
}) => {
  const { showToast } = useToast();
  const [copied, setCopied] = useState(false);
  const [showValidation, setShowValidation] = useState(false);
  const [rating, setRating] = useState<number>(0);
  const [feedbackText, setFeedbackText] = useState('');

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      showToast('In Zwischenablage kopiert!', 'success');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      showToast('Kopieren fehlgeschlagen', 'error');
    }
  };

  const handleDownload = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    showToast('Download gestartet', 'success');
  };

  const handleSubmitFeedback = () => {
    if (rating > 0 && onFeedback) {
      onFeedback(rating, feedbackText);
      showToast('Vielen Dank für Ihr Feedback!', 'success');
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{fixData.title}</h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    fixData.fix_type === 'code' ? 'bg-blue-100 text-blue-700' :
                    fixData.fix_type === 'text' ? 'bg-green-100 text-green-700' :
                    fixData.fix_type === 'widget' ? 'bg-purple-100 text-purple-700' :
                    'bg-orange-100 text-orange-700'
                  }`}>
                    {fixData.fix_type.toUpperCase()}
                  </span>
                  {fixData.estimated_time && (
                    <span className="flex items-center gap-1 text-sm text-gray-600">
                      <Clock className="w-4 h-4" />
                      {fixData.estimated_time}
                    </span>
                  )}
                  {fixData.priority && (
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      fixData.priority === 'high' || fixData.priority === 'critical' 
                        ? 'bg-red-100 text-red-700' 
                        : fixData.priority === 'medium' 
                        ? 'bg-yellow-100 text-yellow-700' 
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      Priorität: {fixData.priority}
                    </span>
                  )}
                </div>
              </div>
            </div>
            {fixData.description && (
              <p className="text-gray-600 mt-3">{fixData.description}</p>
            )}
          </div>
          
          {/* Validation Status */}
          {fixData.validation && (
            <button
              onClick={() => setShowValidation(!showValidation)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              {fixData.validation.is_valid ? (
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              ) : (
                <AlertCircle className="w-5 h-5 text-yellow-500" />
              )}
              <span className="text-sm font-medium">
                {fixData.validation.is_valid ? 'Validiert' : 'Teilweise validiert'}
              </span>
              {showValidation ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          )}
        </div>

        {/* Validation Details */}
        {showValidation && fixData.validation && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            {fixData.validation.errors && fixData.validation.errors.length > 0 && (
              <div className="mb-3">
                <h4 className="font-semibold text-red-700 mb-2">Fehler:</h4>
                <ul className="list-disc list-inside space-y-1">
                  {fixData.validation.errors.map((error: string, i: number) => (
                    <li key={i} className="text-sm text-red-600">{error}</li>
                  ))}
                </ul>
              </div>
            )}
            {fixData.validation.warnings && fixData.validation.warnings.length > 0 && (
              <div>
                <h4 className="font-semibold text-yellow-700 mb-2">Warnungen:</h4>
                <ul className="list-disc list-inside space-y-1">
                  {fixData.validation.warnings.map((warning: string, i: number) => (
                    <li key={i} className="text-sm text-yellow-600">{warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Content based on fix type */}
      <div className="p-6">
        {fixData.fix_type === 'code' && (
          <CodeFixDisplay 
            fixData={fixData} 
            onCopy={handleCopy} 
            onDownload={handleDownload}
            copied={copied}
          />
        )}
        
        {fixData.fix_type === 'text' && (
          <TextFixDisplay 
            fixData={fixData} 
            onCopy={handleCopy} 
            onDownload={handleDownload}
            copied={copied}
          />
        )}
        
        {fixData.fix_type === 'widget' && (
          <WidgetFixDisplay 
            fixData={fixData} 
            onCopy={handleCopy}
            copied={copied}
          />
        )}
        
        {fixData.fix_type === 'guide' && (
          <GuideFixDisplay fixData={fixData} />
        )}

        {/* Integration Instructions */}
        {fixData.integration && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
              <Book className="w-5 h-5" />
              Integration
            </h3>
            {fixData.integration.where && (
              <p className="text-sm text-blue-800 mb-2">
                <strong>Wo:</strong> {fixData.integration.where}
              </p>
            )}
            {fixData.integration.instructions && (
              <div className="text-sm text-blue-800 whitespace-pre-line">
                {fixData.integration.instructions}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="p-6 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">War dieser Fix hilfreich?</span>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  onClick={() => setRating(star)}
                  className="transition-transform hover:scale-110"
                >
                  <Star
                    className={`w-5 h-5 ${
                      star <= rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'
                    }`}
                  />
                </button>
              ))}
            </div>
          </div>
          
          {onApply && (
            <button
              onClick={onApply}
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-semibold transition-all shadow-md hover:shadow-lg"
            >
              Fix anwenden
            </button>
          )}
        </div>

        {rating > 0 && (
          <div className="mt-3">
            <textarea
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
              placeholder="Optional: Ihr Feedback hilft uns, besser zu werden..."
              className="w-full p-3 border border-gray-300 rounded-lg text-sm resize-none"
              rows={2}
            />
            <button
              onClick={handleSubmitFeedback}
              className="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Feedback senden
            </button>
          </div>
        )}

        {/* Branding */}
        {fixData.branding && (
          <div className="mt-4 text-xs text-gray-500 text-center">
            {fixData.branding.powered_by && (
              <span>Powered by {fixData.branding.powered_by}</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// Sub-Components
// ============================================================================

const CodeFixDisplay: React.FC<{
  fixData: FixData;
  onCopy: (text: string) => void;
  onDownload: (content: string, filename: string) => void;
  copied: boolean;
}> = ({ fixData, onCopy, onDownload, copied }) => {
  const [showDiff, setShowDiff] = useState(false);

  return (
    <div>
      {/* Code Actions */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Code className="w-5 h-5 text-gray-600" />
          <span className="font-semibold text-gray-900">
            {fixData.language?.toUpperCase()} Code
          </span>
        </div>
        <div className="flex gap-2">
          {fixData.before_code && fixData.after_code && (
            <button
              onClick={() => setShowDiff(!showDiff)}
              className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              {showDiff ? 'Code anzeigen' : 'Diff anzeigen'}
            </button>
          )}
          <button
            onClick={() => onCopy(fixData.code || '')}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg transition-colors"
          >
            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Kopiert!' : 'Kopieren'}
          </button>
          <button
            onClick={() => onDownload(fixData.code || '', `fix.${fixData.language || 'txt'}`)}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-green-100 hover:bg-green-200 text-green-700 rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            Download
          </button>
        </div>
      </div>

      {/* Code Display */}
      {!showDiff ? (
        <div className="rounded-lg overflow-hidden border border-gray-200">
          <SyntaxHighlighter
            language={fixData.language || 'text'}
            style={vscDarkPlus}
            customStyle={{
              margin: 0,
              padding: '1.5rem',
              fontSize: '0.875rem',
              lineHeight: '1.5'
            }}
            showLineNumbers
          >
            {fixData.code || ''}
          </SyntaxHighlighter>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-semibold text-red-700 mb-2">Vorher:</h4>
            <div className="rounded-lg overflow-hidden border border-red-200">
              <SyntaxHighlighter
                language={fixData.language || 'text'}
                style={vscDarkPlus}
                customStyle={{ margin: 0, padding: '1rem', fontSize: '0.75rem' }}
              >
                {fixData.before_code || ''}
              </SyntaxHighlighter>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-green-700 mb-2">Nachher:</h4>
            <div className="rounded-lg overflow-hidden border border-green-200">
              <SyntaxHighlighter
                language={fixData.language || 'text'}
                style={vscDarkPlus}
                customStyle={{ margin: 0, padding: '1rem', fontSize: '0.75rem' }}
              >
                {fixData.after_code || ''}
              </SyntaxHighlighter>
            </div>
          </div>
        </div>
      )}

      {/* Explanation */}
      {fixData.metadata?.explanation && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold text-gray-900 mb-2">Erklärung:</h4>
          <p className="text-sm text-gray-700">{fixData.metadata.explanation}</p>
        </div>
      )}
    </div>
  );
};

const TextFixDisplay: React.FC<{
  fixData: FixData;
  onCopy: (text: string) => void;
  onDownload: (content: string, filename: string) => void;
  copied: boolean;
}> = ({ fixData, onCopy, onDownload, copied }) => {
  const [showPreview, setShowPreview] = useState(true);

  return (
    <div>
      {/* Text Actions */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-gray-600" />
          <span className="font-semibold text-gray-900">
            {fixData.text_type?.charAt(0).toUpperCase() + fixData.text_type?.slice(1)}
          </span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            {showPreview ? 'HTML anzeigen' : 'Vorschau anzeigen'}
          </button>
          <button
            onClick={() => onCopy(fixData.text_content || '')}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg transition-colors"
          >
            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Kopiert!' : 'Kopieren'}
          </button>
          <button
            onClick={() => onDownload(fixData.text_content || '', `${fixData.text_type || 'text'}.html`)}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-green-100 hover:bg-green-200 text-green-700 rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            Download HTML
          </button>
        </div>
      </div>

      {/* Text Display */}
      {showPreview ? (
        <div className="border border-gray-200 rounded-lg p-6 bg-white">
          <div 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: fixData.text_content || '' }}
          />
        </div>
      ) : (
        <div className="rounded-lg overflow-hidden border border-gray-200">
          <SyntaxHighlighter
            language="html"
            style={vscDarkPlus}
            customStyle={{
              margin: 0,
              padding: '1.5rem',
              fontSize: '0.875rem'
            }}
            showLineNumbers
          >
            {fixData.text_content || ''}
          </SyntaxHighlighter>
        </div>
      )}

      {/* Placeholders Warning */}
      {fixData.placeholders && fixData.placeholders.length > 0 && (
        <div className="mt-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
          <h4 className="font-semibold text-yellow-900 mb-2 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Platzhalter ersetzen
          </h4>
          <p className="text-sm text-yellow-800 mb-2">
            Bitte ersetzen Sie folgende Platzhalter durch echte Daten:
          </p>
          <ul className="list-disc list-inside space-y-1">
            {fixData.placeholders.map((placeholder, i) => (
              <li key={i} className="text-sm text-yellow-700 font-mono">
                {placeholder}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

const WidgetFixDisplay: React.FC<{
  fixData: FixData;
  onCopy: (text: string) => void;
  copied: boolean;
}> = ({ fixData, onCopy, copied }) => {
  return (
    <div>
      {/* Widget Info */}
      <div className="mb-6">
        <h3 className="font-semibold text-gray-900 mb-3">Widget-Features:</h3>
        <div className="grid grid-cols-2 gap-2">
          {fixData.features?.map((feature, i) => (
            <div key={i} className="flex items-center gap-2 text-sm text-gray-700">
              <CheckCircle2 className="w-4 h-4 text-green-500" />
              {feature}
            </div>
          ))}
        </div>
      </div>

      {/* Integration Code */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold text-gray-900">Integration-Code:</h3>
          <button
            onClick={() => onCopy(fixData.integration_code || '')}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg transition-colors"
          >
            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            {copied ? 'Kopiert!' : 'Kopieren'}
          </button>
        </div>
        <div className="rounded-lg overflow-hidden border border-gray-200">
          <SyntaxHighlighter
            language="html"
            style={vscDarkPlus}
            customStyle={{
              margin: 0,
              padding: '1.5rem',
              fontSize: '0.875rem'
            }}
          >
            {fixData.integration_code || ''}
          </SyntaxHighlighter>
        </div>
      </div>

      {/* Preview Link */}
      {fixData.preview_url && (
        <a
          href={fixData.preview_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 bg-purple-100 hover:bg-purple-200 text-purple-700 rounded-lg transition-colors font-medium"
        >
          <ExternalLink className="w-4 h-4" />
          Live-Vorschau öffnen
        </a>
      )}
    </div>
  );
};

const GuideFixDisplay: React.FC<{ fixData: FixData }> = ({ fixData }) => {
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());

  const toggleStep = (stepNumber: number) => {
    const newCompleted = new Set(completedSteps);
    if (newCompleted.has(stepNumber)) {
      newCompleted.delete(stepNumber);
    } else {
      newCompleted.add(stepNumber);
    }
    setCompletedSteps(newCompleted);
  };

  const progress = fixData.steps ? (completedSteps.size / fixData.steps.length) * 100 : 0;

  return (
    <div>
      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Fortschritt</span>
          <span className="text-sm font-medium text-gray-700">
            {completedSteps.size} / {fixData.steps?.length || 0} Schritte
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className="bg-gradient-to-r from-blue-600 to-purple-600 h-2.5 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-4">
        {fixData.steps?.map((step) => (
          <div
            key={step.step_number}
            className={`border-2 rounded-lg p-4 transition-all ${
              completedSteps.has(step.step_number)
                ? 'border-green-500 bg-green-50'
                : 'border-gray-200 bg-white'
            }`}
          >
            <div className="flex items-start gap-4">
              <button
                onClick={() => toggleStep(step.step_number)}
                className={`flex-shrink-0 w-8 h-8 rounded-full border-2 flex items-center justify-center transition-all ${
                  completedSteps.has(step.step_number)
                    ? 'border-green-500 bg-green-500'
                    : 'border-gray-300 hover:border-blue-500'
                }`}
              >
                {completedSteps.has(step.step_number) ? (
                  <Check className="w-5 h-5 text-white" />
                ) : (
                  <span className="text-sm font-medium text-gray-600">
                    {step.step_number}
                  </span>
                )}
              </button>

              <div className="flex-1">
                <h4 className="font-semibold text-gray-900 mb-2">{step.title}</h4>
                <p className="text-sm text-gray-700 whitespace-pre-line mb-3">
                  {step.description}
                </p>

                {step.code_example && (
                  <div className="mb-3 rounded overflow-hidden border border-gray-200">
                    <SyntaxHighlighter
                      language="javascript"
                      style={vscDarkPlus}
                      customStyle={{
                        margin: 0,
                        padding: '1rem',
                        fontSize: '0.75rem'
                      }}
                    >
                      {step.code_example}
                    </SyntaxHighlighter>
                  </div>
                )}

                {step.validation && (
                  <div className="text-sm text-blue-700 bg-blue-50 p-3 rounded">
                    <strong>✓ Validierung:</strong> {step.validation}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AIFixDisplay;

