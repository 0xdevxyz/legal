'use client';

import React, { useState, useMemo } from 'react';
import { Check, X, ChevronRight, ChevronLeft, Loader2, AlertCircle } from 'lucide-react';
import { sanitizeHtml } from '@/lib/sanitize';

interface Fix {
  fix_id: string;
  type: 'code' | 'text' | 'widget' | 'guide';
  title: string;
  description: string;
  estimated_time?: string;
  priority?: string;
  [key: string]: any;
}

interface ImplementationWizardProps {
  scanId: string;
  fixes: Fix[];
  onComplete?: () => void;
  onSkip?: (fixId: string) => void;
}

export const ImplementationWizard: React.FC<ImplementationWizardProps> = ({
  scanId,
  fixes,
  onComplete,
  onSkip
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [skippedSteps, setSkippedSteps] = useState<Set<number>>(new Set());

  // Sort fixes by priority
  const sortedFixes = useMemo(() => {
    const priorityOrder = { high: 3, medium: 2, low: 1 };
    return [...fixes].sort((a, b) => {
      const aPrio = priorityOrder[a.priority as keyof typeof priorityOrder] || 2;
      const bPrio = priorityOrder[b.priority as keyof typeof priorityOrder] || 2;
      return bPrio - aPrio;
    });
  }, [fixes]);

  const currentFix = sortedFixes[currentStep];
  const totalSteps = sortedFixes.length;
  const completedCount = completedSteps.size;
  const skippedCount = skippedSteps.size;
  const remainingCount = totalSteps - completedCount - skippedCount;

  const handleComplete = () => {
    const newCompleted = new Set(completedSteps);
    newCompleted.add(currentStep);
    setCompletedSteps(newCompleted);

    if (currentStep < totalSteps - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      // Wizard finished
      if (onComplete) {
        onComplete();
      }
    }
  };

  const handleSkip = () => {
    const newSkipped = new Set(skippedSteps);
    newSkipped.add(currentStep);
    setSkippedSteps(newSkipped);

    if (onSkip && currentFix) {
      onSkip(currentFix.fix_id);
    }

    if (currentStep < totalSteps - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      // Wizard finished
      if (onComplete) {
        onComplete();
      }
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  if (!currentFix) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">Keine Fixes verfügbar</p>
      </div>
    );
  }

  // Calculate progress
  const progress = ((completedCount) / totalSteps) * 100;

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Progress Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold">Complyo Fix-Assistent</h2>
            <p className="text-blue-100">
              Schritt {currentStep + 1} von {totalSteps}
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold">{Math.round(progress)}%</div>
            <div className="text-sm text-blue-100">Fortschritt</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-blue-800 rounded-full h-3 overflow-hidden">
          <div
            className="bg-white h-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Stats */}
        <div className="flex gap-4 mt-4 text-sm">
          <div className="flex items-center gap-1">
            <Check className="w-4 h-4" />
            <span>{completedCount} erledigt</span>
          </div>
          <div className="flex items-center gap-1">
            <X className="w-4 h-4" />
            <span>{skippedCount} übersprungen</span>
          </div>
          <div className="flex items-center gap-1">
            <Loader2 className="w-4 h-4" />
            <span>{remainingCount} offen</span>
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="p-6">
        {/* Current Fix Display */}
        <div className="mb-6">
          <div className="flex items-start gap-3 mb-4">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
              currentFix.priority === 'high' ? 'bg-red-100 text-red-600' :
              currentFix.priority === 'medium' ? 'bg-yellow-100 text-yellow-600' :
              'bg-blue-100 text-blue-600'
            }`}>
              {currentStep + 1}
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-900 mb-1">
                {currentFix.title}
              </h3>
              <p className="text-gray-600 mb-2">{currentFix.description}</p>
              {currentFix.estimated_time && (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Geschätzte Zeit: {currentFix.estimated_time}</span>
                </div>
              )}
            </div>
          </div>

          {/* Fix Content - Dynamic based on type */}
          <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
            {currentFix.type === 'code' && <CodeFixDisplay fix={currentFix} />}
            {currentFix.type === 'text' && <TextFixDisplay fix={currentFix} />}
            {currentFix.type === 'widget' && <WidgetFixDisplay fix={currentFix} />}
            {currentFix.type === 'guide' && <GuideFixDisplay fix={currentFix} />}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleBack}
            disabled={currentStep === 0}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-gray-700 font-medium"
          >
            <ChevronLeft className="w-4 h-4" />
            Zurück
          </button>

          <button
            onClick={handleSkip}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 font-medium"
          >
            Später
          </button>

          <button
            onClick={handleComplete}
            className="flex-1 px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-bold flex items-center justify-center gap-2"
          >
            <Check className="w-5 h-5" />
            Erledigt, weiter
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

// Sub-components for different fix types

const CodeFixDisplay: React.FC<{ fix: Fix }> = ({ fix }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (fix.code?.content) {
      navigator.clipboard.writeText(fix.code.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div>
      <div className="mb-4">
        <h4 className="font-semibold text-gray-900 mb-2">📝 Code zum Einbauen:</h4>
        <div className="relative">
          <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
            <code>{fix.code?.content || fix.content}</code>
          </pre>
          <button
            onClick={handleCopy}
            className="absolute top-2 right-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded flex items-center gap-1"
          >
            {copied ? <Check className="w-3 h-3" /> : <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>}
            {copied ? 'Kopiert!' : 'Kopieren'}
          </button>
        </div>
      </div>
      
      {fix.integration?.instructions && (
        <div className="mt-4">
          <h4 className="font-semibold text-gray-900 mb-2">🎯 So fügen Sie es ein:</h4>
          <div className="bg-blue-50 border border-blue-200 rounded p-4">
            <p className="text-gray-800 whitespace-pre-wrap">{fix.integration.instructions}</p>
          </div>
        </div>
      )}
    </div>
  );
};

const TextFixDisplay: React.FC<{ fix: Fix }> = ({ fix }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (fix.text?.content) {
      navigator.clipboard.writeText(fix.text.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div>
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-semibold text-gray-900">📄 Ihr rechtssicherer Text:</h4>
          <button
            onClick={handleCopy}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded flex items-center gap-2"
          >
            {copied ? <Check className="w-4 h-4" /> : <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>}
            {copied ? 'Kopiert!' : 'Text kopieren'}
          </button>
        </div>
        <div className="bg-white border border-gray-300 rounded p-4 max-h-96 overflow-y-auto">
          <div dangerouslySetInnerHTML={{ __html: sanitizeHtml(fix.text?.content || fix.content || '') }} />
        </div>
        <div className="mt-2 text-xs text-gray-500">
          {fix.branding || 'Erstellt von Complyo'}
        </div>
      </div>
      
      {fix.integration?.instructions && (
        <div className="mt-4">
          <h4 className="font-semibold text-gray-900 mb-2">🎯 So binden Sie es ein:</h4>
          <div className="bg-blue-50 border border-blue-200 rounded p-4">
            <p className="text-gray-800 whitespace-pre-wrap">{fix.integration.instructions}</p>
          </div>
        </div>
      )}
    </div>
  );
};

const WidgetFixDisplay: React.FC<{ fix: Fix }> = ({ fix }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (fix.integration?.code) {
      navigator.clipboard.writeText(fix.integration.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div>
      <div className="mb-4">
        <h4 className="font-semibold text-gray-900 mb-2">🚀 Complyo Widget - One-Line Integration</h4>
        <p className="text-gray-600 mb-4">Kopieren Sie diesen Code und fügen Sie ihn vor dem <code className="bg-gray-200 px-1 rounded">&lt;/body&gt;</code>-Tag ein:</p>
        
        <div className="relative">
          <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
            <code>{fix.integration?.code}</code>
          </pre>
          <button
            onClick={handleCopy}
            className="absolute top-2 right-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded flex items-center gap-1"
          >
            {copied ? <Check className="w-3 h-3" /> : <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>}
            {copied ? 'Kopiert!' : 'Kopieren'}
          </button>
        </div>
      </div>
      
      {fix.integration?.instructions && (
        <div className="mt-4">
          <h4 className="font-semibold text-gray-900 mb-2">📋 Anleitung:</h4>
          <div className="bg-blue-50 border border-blue-200 rounded p-4">
            <p className="text-gray-800 whitespace-pre-wrap">{fix.integration.instructions}</p>
          </div>
        </div>
      )}

      {fix.preview && (
        <div className="mt-4">
          <a
            href={fix.preview}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-700 underline text-sm"
          >
            👁️ Widget-Vorschau ansehen
          </a>
        </div>
      )}
    </div>
  );
};

const GuideFixDisplay: React.FC<{ fix: Fix }> = ({ fix }) => {
  const [completedSubSteps, setCompletedSubSteps] = useState<Set<number>>(new Set());

  const steps = fix.steps || [];

  const toggleSubStep = (index: number) => {
    const newCompleted = new Set(completedSubSteps);
    if (newCompleted.has(index)) {
      newCompleted.delete(index);
    } else {
      newCompleted.add(index);
    }
    setCompletedSubSteps(newCompleted);
  };

  return (
    <div>
      <h4 className="font-semibold text-gray-900 mb-4">📖 Schritt-für-Schritt Anleitung:</h4>
      
      <div className="space-y-3">
        {steps.map((step: any, index: number) => (
          <div
            key={index}
            className={`border rounded-lg p-4 cursor-pointer transition-colors ${
              completedSubSteps.has(index)
                ? 'bg-green-50 border-green-300'
                : 'bg-white border-gray-300 hover:border-blue-300'
            }`}
            onClick={() => toggleSubStep(index)}
          >
            <div className="flex items-start gap-3">
              <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                completedSubSteps.has(index)
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-200 text-gray-600'
              }`}>
                {completedSubSteps.has(index) ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <span className="text-sm">{index + 1}</span>
                )}
              </div>
              <div className="flex-1">
                <h5 className="font-medium text-gray-900 mb-1">{step.title}</h5>
                <p className="text-gray-600 text-sm">{step.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {completedSubSteps.size === steps.length && steps.length > 0 && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-800 font-medium flex items-center gap-2">
            <Check className="w-5 h-5" />
            Alle Schritte abgeschlossen!
          </p>
        </div>
      )}
    </div>
  );
};

