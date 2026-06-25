'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { SuccessAnimation, ConfettiAnimation } from '@/components/ui/SuccessAnimation';
import { useToast } from '@/components/ui/Toast';
import { useActiveSite } from '@/contexts/ActiveSiteContext';
import {
  Rocket,
  ScanSearch,
  Wrench,
  ShieldCheck,
  Radar,
  CheckCircle2,
  Circle,
  Loader2,
  ArrowRight,
  Clock,
  Globe,
  AlertTriangle,
  Sparkles,
  Trophy,
} from 'lucide-react';

// ---------- Types ----------
interface WorkflowStep {
  id: string;
  stage: string;
  title: string;
  description: string;
  instructions: string[];
  estimated_time_minutes: number;
  requires_technical_knowledge?: boolean;
  success_criteria?: string[];
}

interface StageProgress {
  completed: number;
  total: number;
  percentage: number;
}

interface JourneyProgress {
  error?: string;
  website_url?: string;
  skill_level?: string;
  current_stage?: string;
  progress_percentage?: number;
  completed_steps?: number;
  total_steps?: number;
  stage_progress?: Record<string, StageProgress>;
  estimated_time_remaining?: number;
}

// ---------- Stage metadata ----------
const STAGES = [
  { key: 'onboarding', label: 'Onboarding', icon: Rocket },
  { key: 'website_analysis', label: 'Analyse', icon: ScanSearch },
  { key: 'guided_optimization', label: 'Optimierung', icon: Wrench },
  { key: 'compliance_verification', label: 'Verifizierung', icon: ShieldCheck },
  { key: 'maintenance', label: 'Wartung', icon: Radar },
] as const;

const SKILL_LEVELS = [
  { key: 'absolute_beginner', label: 'Anfänger', hint: 'Ausführliche Erklärungen' },
  { key: 'beginner', label: 'Grundkenntnisse', hint: 'Schritt für Schritt' },
  { key: 'intermediate', label: 'Fortgeschritten', hint: 'Kompakte Hinweise' },
  { key: 'advanced', label: 'Profi', hint: 'Nur das Wesentliche' },
] as const;

// ---------- API ----------
const fetchCurrentStep = async (): Promise<WorkflowStep | null> => {
  const { data } = await apiClient.get('/api/v2/workflow/current-step');
  return data.data;
};

const fetchProgress = async (): Promise<JourneyProgress> => {
  const { data } = await apiClient.get('/api/v2/workflow/progress');
  return data.data;
};

const completeStep = async (payload: { step_id: string; validation_data?: any }) => {
  const { data } = await apiClient.post('/api/v2/workflow/complete-step', payload);
  return data.data;
};

const startJourney = async (payload: { website_url: string; skill_level: string }) => {
  const { data } = await apiClient.post('/api/v2/workflow/start-journey', payload);
  return data.data;
};

// ---------- Subcomponents ----------
function GradientBar({ value }: { value: number }) {
  return (
    <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-zinc-200/60 dark:bg-zinc-800/80">
      <div
        className="h-full rounded-full bg-gradient-to-r from-blue-600 to-purple-600 transition-all duration-700 ease-out"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}

function StageTimeline({
  currentStage,
  stageProgress,
}: {
  currentStage?: string;
  stageProgress?: Record<string, StageProgress>;
}) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {STAGES.map((stage, idx) => {
        const sp = stageProgress?.[stage.key];
        const pct = sp?.percentage ?? 0;
        const isDone = pct >= 100;
        const isActive = stage.key === currentStage && !isDone;
        const Icon = stage.icon;

        return (
          <div
            key={stage.key}
            className={[
              'relative flex flex-col gap-2 rounded-xl border p-3 transition-all duration-300',
              isActive
                ? 'border-blue-500/60 bg-blue-500/5 shadow-lg shadow-blue-500/10 dark:bg-blue-500/10'
                : isDone
                ? 'border-emerald-500/40 bg-emerald-500/5 dark:bg-emerald-500/10'
                : 'border-zinc-200/70 bg-transparent dark:border-zinc-800/70',
            ].join(' ')}
          >
            <div className="flex items-center justify-between">
              <span
                className={[
                  'flex h-8 w-8 items-center justify-center rounded-lg',
                  isActive
                    ? 'bg-gradient-to-br from-blue-600 to-purple-600 text-white'
                    : isDone
                    ? 'bg-emerald-500/15 text-emerald-500'
                    : 'bg-zinc-200/60 text-zinc-400 dark:bg-zinc-800/80',
                ].join(' ')}
              >
                {isDone ? <CheckCircle2 className="h-5 w-5" /> : <Icon className="h-4 w-4" />}
              </span>
              <span className="text-[10px] font-medium uppercase tracking-wide text-zinc-400">
                {idx + 1}/5
              </span>
            </div>
            <div>
              <p
                className={[
                  'text-sm font-semibold leading-tight',
                  isActive
                    ? 'text-blue-600 dark:text-blue-400'
                    : isDone
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-zinc-500 dark:text-zinc-400',
                ].join(' ')}
              >
                {stage.label}
              </p>
              {sp && (
                <p className="mt-0.5 text-[11px] text-zinc-400">
                  {sp.completed}/{sp.total} Schritte
                </p>
              )}
            </div>
            <GradientBar value={pct} />
          </div>
        );
      })}
    </div>
  );
}

function JourneySkeleton() {
  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <Skeleton className="h-8 w-72" />
        <Skeleton className="h-3 w-full max-w-md" />
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-64 w-full rounded-2xl" />
    </div>
  );
}

// ---------- Page ----------
export default function JourneyPage() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const { activeSite, sites, isLoading: sitesLoading } = useActiveSite();

  const [skillLevel, setSkillLevel] = useState<string>('beginner');
  const [showStepSuccess, setShowStepSuccess] = useState(false);
  const [showConfetti, setShowConfetti] = useState(false);

  const stepQuery = useQuery({ queryKey: ['workflowStep'], queryFn: fetchCurrentStep });
  const progressQuery = useQuery({ queryKey: ['workflowProgress'], queryFn: fetchProgress });

  const currentStep = stepQuery.data;
  const progress = progressQuery.data;
  const hasJourney = !!progress && !progress.error;

  const refreshAll = () => {
    queryClient.invalidateQueries({ queryKey: ['workflowStep'] });
    queryClient.invalidateQueries({ queryKey: ['workflowProgress'] });
  };

  const completeStepMutation = useMutation({
    mutationFn: completeStep,
    onSuccess: (result: any) => {
      if (result?.journey_completed) {
        setShowConfetti(true);
        showToast(result.celebration_message || '🎉 Journey abgeschlossen!', 'success');
      } else if (result?.status === 'validation_failed') {
        showToast(result.validation_message || 'Schritt konnte nicht bestätigt werden.', 'warning');
      } else {
        setShowStepSuccess(true);
        showToast('Schritt abgeschlossen!', 'success');
      }
      refreshAll();
    },
    onError: () => showToast('Schritt konnte nicht abgeschlossen werden.', 'error'),
  });

  const startJourneyMutation = useMutation({
    mutationFn: startJourney,
    onSuccess: () => {
      showToast('Journey gestartet – los geht\'s!', 'success');
      refreshAll();
    },
    onError: () => showToast('Journey konnte nicht gestartet werden.', 'error'),
  });

  const handleCompleteStep = () => {
    if (currentStep) {
      completeStepMutation.mutate({
        step_id: currentStep.id,
        validation_data: { manual_completion: true },
      });
    }
  };

  const handleStartJourney = () => {
    const url = activeSite?.url;
    if (!url) {
      showToast('Bitte zuerst eine Website hinzufügen.', 'warning');
      return;
    }
    startJourneyMutation.mutate({ website_url: url, skill_level: skillLevel });
  };

  // ----- Loading -----
  if (stepQuery.isLoading || progressQuery.isLoading || sitesLoading) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <JourneySkeleton />
      </div>
    );
  }

  // ----- Error -----
  if (stepQuery.isError || progressQuery.isError) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <Card className="flex flex-col items-center gap-4 py-12 text-center">
          <AlertTriangle className="h-12 w-12 text-amber-500" />
          <div>
            <h2 className="text-lg font-semibold">Workflow konnte nicht geladen werden</h2>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              Bitte versuchen Sie es in einem Moment erneut.
            </p>
          </div>
          <Button onClick={refreshAll}>Erneut versuchen</Button>
        </Card>
      </div>
    );
  }

  const overallPct = Math.round(progress?.progress_percentage ?? 0);

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      <SuccessAnimation
        show={showStepSuccess}
        type="achievement"
        message="Schritt geschafft!"
        onComplete={() => setShowStepSuccess(false)}
      />
      <ConfettiAnimation show={showConfetti} onComplete={() => setShowConfetti(false)} />

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-purple-500" />
          <h1 className="text-2xl font-bold ai-gradient-text sm:text-3xl">
            Ihre Compliance-Journey
          </h1>
        </div>
        <p className="mt-2 max-w-2xl text-sm text-zinc-500 dark:text-zinc-400">
          Ein geführter Weg in fünf Phasen – von der Analyse bis zur dauerhaften
          Rechtssicherheit Ihrer Website.
        </p>
      </div>

      {!hasJourney ? (
        /* ---------- Empty / Start state ---------- */
        <Card className="flex flex-col items-center gap-6 py-12 text-center">
          <span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-purple-600 text-white shadow-lg shadow-purple-500/20">
            <Rocket className="h-8 w-8" />
          </span>
          <div className="max-w-md">
            <h2 className="text-xl font-bold">Starten Sie Ihre Compliance-Reise</h2>
            <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
              Complyo führt Sie Schritt für Schritt zur rechtskonformen Website – ganz ohne
              juristisches Fachwissen.
            </p>
          </div>

          {activeSite ? (
            <div className="flex items-center gap-2 rounded-lg border border-zinc-200/70 bg-zinc-50/60 px-3 py-2 text-sm dark:border-zinc-800/70 dark:bg-zinc-900/40">
              <Globe className="h-4 w-4 text-blue-500" />
              <span className="font-medium">
                {activeSite.url.replace(/^https?:\/\//, '').replace(/\/$/, '')}
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2 rounded-lg border border-amber-300/60 bg-amber-50/60 px-3 py-2 text-sm text-amber-700 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-400">
              <AlertTriangle className="h-4 w-4" />
              <span>
                {sites.length === 0
                  ? 'Bitte fügen Sie zuerst eine Website hinzu.'
                  : 'Bitte wählen Sie oben eine Website aus.'}
              </span>
            </div>
          )}

          {/* Skill level chooser */}
          <div className="w-full max-w-lg">
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-400">
              Wie vertraut sind Sie mit Web-Technik?
            </p>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {SKILL_LEVELS.map((lvl) => (
                <button
                  key={lvl.key}
                  type="button"
                  onClick={() => setSkillLevel(lvl.key)}
                  className={[
                    'rounded-xl border p-3 text-left transition-all duration-200',
                    skillLevel === lvl.key
                      ? 'border-blue-500/60 bg-blue-500/5 dark:bg-blue-500/10'
                      : 'border-zinc-200/70 hover:border-zinc-300 dark:border-zinc-800/70 dark:hover:border-zinc-700',
                  ].join(' ')}
                >
                  <p className="text-sm font-semibold">{lvl.label}</p>
                  <p className="mt-0.5 text-[11px] text-zinc-400">{lvl.hint}</p>
                </button>
              ))}
            </div>
          </div>

          <Button
            onClick={handleStartJourney}
            disabled={startJourneyMutation.isPending || !activeSite}
            className="ai-primary min-w-[200px]"
          >
            {startJourneyMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Rocket className="mr-2 h-4 w-4" />
            )}
            Journey starten
          </Button>
        </Card>
      ) : (
        /* ---------- Active journey ---------- */
        <div className="space-y-6">
          {/* Overall progress */}
          <Card>
            <div className="mb-3 flex items-end justify-between">
              <div>
                <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
                  Gesamtfortschritt
                </p>
                <p className="text-2xl font-bold">
                  {overallPct}
                  <span className="text-base font-medium text-zinc-400"> %</span>
                </p>
              </div>
              <div className="text-right text-sm text-zinc-500 dark:text-zinc-400">
                <p>
                  {progress?.completed_steps ?? 0} von {progress?.total_steps ?? 0} Schritten
                </p>
                {!!progress?.estimated_time_remaining && (
                  <p className="mt-0.5 flex items-center justify-end gap-1 text-xs">
                    <Clock className="h-3 w-3" />
                    noch ca. {progress.estimated_time_remaining} Min
                  </p>
                )}
              </div>
            </div>
            <GradientBar value={overallPct} />
          </Card>

          {/* Stage timeline */}
          <StageTimeline
            currentStage={progress?.current_stage}
            stageProgress={progress?.stage_progress}
          />

          {/* Current step or completion */}
          {currentStep ? (
            <Card className="overflow-hidden p-0">
              <div className="border-b border-zinc-200/70 bg-gradient-to-r from-blue-600/5 to-purple-600/5 p-6 dark:border-zinc-800/70">
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <Badge variant="info">
                    {STAGES.find((s) => s.key === currentStep.stage)?.label ?? 'Aktueller Schritt'}
                  </Badge>
                  {(() => {
                    const sp = progress?.stage_progress?.[currentStep.stage];
                    if (!sp) return null;
                    return (
                      <span className="text-xs text-zinc-400">
                        Schritt {Math.min(sp.completed + 1, sp.total)} von {sp.total}
                      </span>
                    );
                  })()}
                  {currentStep.requires_technical_knowledge && (
                    <Badge variant="warning">Technisch</Badge>
                  )}
                </div>
                <h2 className="text-xl font-bold">{currentStep.title}</h2>
                <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
                  {currentStep.description}
                </p>
              </div>

              <div className="space-y-5 p-6">
                <div>
                  <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-400">
                    Anleitung
                  </h3>
                  <ol className="space-y-3">
                    {currentStep.instructions.map((instr, index) => (
                      <li key={index} className="flex gap-3">
                        <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-blue-500/10 text-xs font-semibold text-blue-600 dark:text-blue-400">
                          {index + 1}
                        </span>
                        <span className="pt-0.5 text-sm leading-relaxed">{instr}</span>
                      </li>
                    ))}
                  </ol>
                </div>

                {!!currentStep.success_criteria?.length && (
                  <div className="rounded-xl border border-zinc-200/70 bg-zinc-50/50 p-4 dark:border-zinc-800/70 dark:bg-zinc-900/40">
                    <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-zinc-400">
                      Erfolgskriterien
                    </h3>
                    <ul className="space-y-1.5">
                      {currentStep.success_criteria.map((c, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-500" />
                          <span>{c}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex flex-col-reverse items-stretch justify-between gap-3 sm:flex-row sm:items-center">
                  <span className="flex items-center gap-1.5 text-sm text-zinc-400">
                    <Clock className="h-4 w-4" />
                    Geschätzte Zeit: {currentStep.estimated_time_minutes} Min
                  </span>
                  <Button
                    onClick={handleCompleteStep}
                    disabled={completeStepMutation.isPending}
                    className="ai-primary sm:min-w-[220px]"
                  >
                    {completeStepMutation.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <CheckCircle2 className="mr-2 h-4 w-4" />
                    )}
                    Schritt abschließen
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ) : (
            <Card className="flex flex-col items-center gap-4 py-12 text-center">
              <span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-500/20">
                <Trophy className="h-8 w-8" />
              </span>
              <div>
                <h2 className="text-xl font-bold">🎉 Journey abgeschlossen!</h2>
                <p className="mt-2 max-w-md text-sm text-zinc-500 dark:text-zinc-400">
                  Herzlichen Glückwunsch – Sie haben alle Phasen durchlaufen. Ihre Website ist
                  jetzt rundum compliant.
                </p>
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
