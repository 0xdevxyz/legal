'use client';

import React, { useState, useEffect } from 'react';
import { 
  ChevronRight, 
  ChevronLeft, 
  CheckCircle2, 
  Circle, 
  X, 
  AlertTriangle,
  Info,
  Sparkles,
  ArrowRight,
  SkipForward
} from 'lucide-react';
import { ComplianceIssueCard } from './ComplianceIssueCard';

interface ComplianceWizardProps {
  issues: any[];
  groups?: any[];
  planType: 'free' | 'ai' | 'expert';
  websiteUrl?: string;
  scanId?: string;
  onComplete?: () => void;
  onClose?: () => void;
}

interface WizardStep {
  id: string;
  issue: any;
  completed: boolean;
  skipped: boolean;
}

export const ComplianceWizard: React.FC<ComplianceWizardProps> = ({
  issues,
  groups = [],
  planType,
  websiteUrl,
  scanId,
  onComplete,
  onClose
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [steps, setSteps] = useState<WizardStep[]>([]);
  const [showSkipWarning, setShowSkipWarning] = useState(false);

  // Initialisiere Steps aus Issues und Groups
  useEffect(() => {
    const allSteps: WizardStep[] = [];
    
    // Füge gruppierte Issues als Steps hinzu (Gruppen-Parent als Step)
    groups.forEach((group) => {
      if (group.parent_issue) {
        allSteps.push({
          id: `group-${group.group_id}`,
          issue: {
            ...group.parent_issue,
            _isGroup: true,
            _group: group
          },
          completed: false,
          skipped: false
        });
      } else {
        // Gruppe ohne Parent → Alle Sub-Issues als einzelne Steps
        group.sub_issues.forEach((subIssue: any) => {
          allSteps.push({
            id: subIssue.id,
            issue: subIssue,
            completed: false,
            skipped: false
          });
        });
      }
    });
    
    // Füge ungrupedIssues hinzu
    const groupedIssueIds = groups.flatMap((g: any) => [
      ...(g.sub_issues || []).map((si: any) => si.id),
      g.parent_issue?.id
    ]).filter(Boolean);
    
    issues
      .filter(issue => !groupedIssueIds.includes(issue.id))
      .forEach(issue => {
        allSteps.push({
          id: issue.id,
          issue,
          completed: false,
          skipped: false
        });
      });
    
    // Sortiere nach Severity (critical zuerst)
    allSteps.sort((a, b) => {
      const severityOrder = { critical: 0, warning: 1, info: 2 };
      const aSev = severityOrder[a.issue.severity as keyof typeof severityOrder] ?? 3;
      const bSev = severityOrder[b.issue.severity as keyof typeof severityOrder] ?? 3;
      return aSev - bSev;
    });
    
    setSteps(allSteps);
  }, [issues, groups]);

  const currentStep = steps[currentStepIndex];
  const progress = steps.length > 0 ? ((currentStepIndex + 1) / steps.length) * 100 : 0;
  const completedCount = steps.filter(s => s.completed).length;
  const skippedCount = steps.filter(s => s.skipped).length;

  const handleNext = () => {
    if (currentStepIndex < steps.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
      setShowSkipWarning(false);
    } else {
      // Wizard abgeschlossen
      onComplete?.();
    }
  };

  const handlePrevious = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
      setShowSkipWarning(false);
    }
  };

  const handleMarkComplete = () => {
    const newSteps = [...steps];
    newSteps[currentStepIndex].completed = true;
    newSteps[currentStepIndex].skipped = false;
    setSteps(newSteps);
    
    // Auto-advance nach kurzer Verzögerung
    setTimeout(() => {
      handleNext();
    }, 500);
  };

  const handleSkip = () => {
    if (!showSkipWarning && currentStep?.issue?.severity === 'critical') {
      setShowSkipWarning(true);
      return;
    }
    
    const newSteps = [...steps];
    newSteps[currentStepIndex].skipped = true;
    newSteps[currentStepIndex].completed = false;
    setSteps(newSteps);
    setShowSkipWarning(false);
    
    handleNext();
  };

  const handleGoToStep = (index: number) => {
    setCurrentStepIndex(index);
    setShowSkipWarning(false);
  };

  if (!currentStep) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-zinc-900 rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        
        {/* Header */}
        <div className="p-6 border-b border-zinc-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <Sparkles className="w-6 h-6 text-purple-400" />
                Compliance-Wizard
              </h2>
              <p className="text-sm text-zinc-400 mt-1">
                Schritt-für-Schritt durch alle Compliance-Probleme
              </p>
            </div>
            
            <button
              onClick={onClose}
              className="p-2 hover:bg-zinc-800 rounded-lg transition-colors"
            >
              <X className="w-6 h-6 text-zinc-400" />
            </button>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-zinc-400">
                Schritt {currentStepIndex + 1} von {steps.length}
              </span>
              <span className="text-white font-semibold">
                {completedCount} behoben, {skippedCount} übersprungen
              </span>
            </div>
            
            <div className="h-3 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-purple-600 to-pink-600 transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Step Indicators */}
          <div className="flex gap-2 mt-4 overflow-x-auto pb-2">
            {steps.map((step, idx) => (
              <button
                key={step.id}
                onClick={() => handleGoToStep(idx)}
                className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center text-sm font-semibold transition-all ${
                  step.completed
                    ? 'bg-green-500/20 text-green-400 border-2 border-green-500/50'
                    : step.skipped
                    ? 'bg-zinc-700 text-zinc-500 border-2 border-zinc-600'
                    : idx === currentStepIndex
                    ? 'bg-purple-500/20 text-purple-300 border-2 border-purple-500/50 ring-2 ring-purple-500/30'
                    : 'bg-zinc-800 text-zinc-400 border-2 border-zinc-700 hover:border-zinc-600'
                }`}
                title={step.issue.title}
              >
                {step.completed ? (
                  <CheckCircle2 className="w-5 h-5" />
                ) : (
                  idx + 1
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Current Issue */}
          <div className="mb-6">
            {currentStep.issue._isGroup ? (
              // Gruppiertes Issue
              <div className="space-y-4">
                <div className="flex items-start gap-4 p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                  <div className="text-3xl">{currentStep.issue._group.icon}</div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-white mb-2">
                      {currentStep.issue._group.title}
                    </h3>
                    <p className="text-sm text-zinc-300 mb-3">
                      {currentStep.issue._group.description}
                    </p>
                    <div className="flex gap-2 flex-wrap">
                      <span className="px-2 py-1 bg-purple-500/20 text-purple-300 rounded text-xs font-semibold">
                        {currentStep.issue._group.total_count} Probleme
                      </span>
                      {currentStep.issue._group.has_unified_solution && (
                        <span className="px-2 py-1 bg-pink-500/20 text-pink-300 rounded text-xs font-semibold">
                          Gemeinsame Lösung
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                <ComplianceIssueCard
                  issue={currentStep.issue}
                  planType={planType}
                  websiteUrl={websiteUrl}
                  scanId={scanId}
                  onStartFix={() => handleMarkComplete()}
                />
              </div>
            ) : (
              // Einzelnes Issue
              <ComplianceIssueCard
                issue={currentStep.issue}
                planType={planType}
                websiteUrl={websiteUrl}
                scanId={scanId}
                onStartFix={() => handleMarkComplete()}
              />
            )}
          </div>

          {/* Contextual Help */}
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mb-6">
            <div className="flex gap-3">
              <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-blue-300 mb-1">
                  Hilfe
                </h4>
                <p className="text-sm text-blue-200/80">
                  {currentStep.issue.severity === 'critical' 
                    ? 'Dieses Problem sollte prioritär behoben werden, um rechtliche Risiken zu minimieren.'
                    : currentStep.issue.severity === 'warning'
                    ? 'Dieses Problem sollte zeitnah behoben werden.'
                    : 'Dieses Problem kann nach den kritischen Issues behoben werden.'
                  }
                </p>
              </div>
            </div>
          </div>

          {/* Skip Warning */}
          {showSkipWarning && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6 animate-pulse">
              <div className="flex gap-3">
                <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-red-300 mb-1">
                    Warnung: Kritisches Problem
                  </h4>
                  <p className="text-sm text-red-200/80 mb-3">
                    Dieses Problem ist als kritisch eingestuft. Das Überspringen kann zu rechtlichen Konsequenzen führen.
                    Geschätztes Risiko: <strong>{new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(currentStep.issue.risk_euro || 0)}</strong>
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setShowSkipWarning(false)}
                      className="px-3 py-1.5 bg-zinc-700 hover:bg-zinc-600 text-white rounded text-sm font-medium transition-colors"
                    >
                      Abbrechen
                    </button>
                    <button
                      onClick={handleSkip}
                      className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded text-sm font-medium transition-colors"
                    >
                      Trotzdem überspringen
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-zinc-800 bg-zinc-900/50">
          <div className="flex items-center justify-between gap-4">
            <button
              onClick={handlePrevious}
              disabled={currentStepIndex === 0}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              <ChevronLeft className="w-5 h-5" />
              Zurück
            </button>

            <div className="flex gap-2">
              <button
                onClick={handleSkip}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                <SkipForward className="w-5 h-5" />
                Überspringen
              </button>
              
              <button
                onClick={handleMarkComplete}
                className="px-6 py-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white rounded-lg font-semibold transition-all shadow-lg flex items-center gap-2"
              >
                <CheckCircle2 className="w-5 h-5" />
                Als behoben markieren
              </button>
              
              <button
                onClick={handleNext}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
              >
                {currentStepIndex === steps.length - 1 ? 'Abschließen' : 'Weiter'}
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

