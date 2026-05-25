'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { ChevronRight, CheckCircle2, AlertCircle, Zap, ClipboardCheck, Target, Loader2, RotateCcw, Wrench, TrendingUp, PlayCircle, ShieldCheck } from 'lucide-react';
import { useDashboardStore } from '@/stores/dashboard';
import { useToast } from '@/components/ui/Toast';
import type { ComplianceIssue } from '@/types/api';
import { safeStorage } from '@/lib/storage';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.de';

interface Step {
  id: number;
  title: string;
  description: string;
  icon: React.ElementType;
  actionLabel: string;
  actionIcon: React.ElementType;
  status: 'pending' | 'active' | 'completed';
}

export const OptimizationProcessWidget: React.FC = () => {
  const [expandedStep, setExpandedStep] = useState<number | null>(1);
  const [loadingStep, setLoadingStep] = useState<number | null>(null);
  const { analysisData, currentWebsite } = useDashboardStore();
  const { showToast } = useToast();

  const criticalIssues = useMemo(() => {
    return analysisData?.issues?.filter((i: ComplianceIssue) => i.severity === 'critical') ?? [];
  }, [analysisData]);

  const warningIssues = useMemo(() => {
    return analysisData?.issues?.filter((i: ComplianceIssue) => i.severity === 'warning') ?? [];
  }, [analysisData]);

  const steps: Step[] = [
    {
      id: 1,
      title: 'Seite scannen',
      description: 'Automatische Analyse Ihrer Website auf Compliance-Probleme',
      icon: Target,
      actionLabel: 'Re-scan starten',
      actionIcon: RotateCcw,
      status: analysisData?.issues ? 'completed' : 'active',
    },
    {
      id: 2,
      title: `Kritische Probleme (${criticalIssues.length})`,
      description: `${criticalIssues.length} Abmahnungs-relevante Probleme gefunden`,
      icon: AlertCircle,
      actionLabel: 'Alle kritischen Fixes anzeigen',
      actionIcon: Wrench,
      status: criticalIssues.length > 0 ? 'active' : 'completed',
    },
    {
      id: 3,
      title: `Warnungen optimieren (${warningIssues.length})`,
      description: `${warningIssues.length} Verbesserungen empfohlen`,
      icon: Zap,
      actionLabel: 'Optimierungen anzeigen',
      actionIcon: TrendingUp,
      status: 'pending',
    },
    {
      id: 4,
      title: 'Änderungen testen',
      description: 'Validieren Sie Ihre Fixes mit unserem Tester',
      icon: ClipboardCheck,
      actionLabel: 'Tester öffnen',
      actionIcon: PlayCircle,
      status: 'pending',
    },
    {
      id: 5,
      title: 'Validierung abschließen',
      description: 'Endgültige Sicherheitsprüfung durchführen',
      icon: CheckCircle2,
      actionLabel: 'Jetzt validieren',
      actionIcon: ShieldCheck,
      status: 'pending',
    },
  ];

  const handleAction = useCallback(async (stepId: number) => {
    setLoadingStep(stepId);
    const token = safeStorage.get('access_token');
    const websiteId = currentWebsite?.id ?? analysisData?.site_id;

    try {
      switch (stepId) {
        case 1: {
          if (!websiteId) {
            showToast('Bitte analysieren Sie zuerst eine Website.', 'warning', 4000);
            break;
          }
          showToast('Re-scan gestartet...', 'info', 3000);
          const res = await fetch(`${API_BASE}/api/scan/start`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token ?? ''}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ website_id: websiteId }),
          });
          if (res.ok) {
            showToast('Re-scan erfolgreich gestartet. Ergebnisse in wenigen Sekunden.', 'success', 5000);
          } else {
            showToast('Scan fehlgeschlagen. Bitte versuchen Sie es erneut.', 'error', 4000);
          }
          break;
        }

        case 2: {
          if (criticalIssues.length === 0) {
            showToast('Keine kritischen Probleme gefunden. Gut gemacht!', 'success', 4000);
            break;
          }
          setExpandedStep(2);
          showToast(`${criticalIssues.length} kritische Probleme → Scrollen Sie nach unten zur Website-Analyse.`, 'info', 5000);
          document.querySelector('[aria-label="Analyse & KI"]')?.scrollIntoView({ behavior: 'smooth' });
          break;
        }

        case 3: {
          if (warningIssues.length === 0) {
            showToast('Keine Warnungen gefunden.', 'success', 4000);
            break;
          }
          setExpandedStep(3);
          showToast(`${warningIssues.length} Optimierungen verfügbar → Scrollen Sie zur Website-Analyse.`, 'info', 5000);
          document.querySelector('[aria-label="Analyse & KI"]')?.scrollIntoView({ behavior: 'smooth' });
          break;
        }

        case 4: {
          if (!websiteId) {
            showToast('Bitte analysieren Sie zuerst eine Website.', 'warning', 4000);
            break;
          }
          const url = analysisData?.url ?? currentWebsite?.url;
          if (url) {
            window.open(`https://validator.w3.org/nu/?doc=${encodeURIComponent(url)}`, '_blank');
            showToast('W3C Validator geöffnet.', 'info', 3000);
          } else {
            showToast('Keine Website-URL verfügbar.', 'warning', 3000);
          }
          break;
        }

        case 5: {
          if (!websiteId) {
            showToast('Bitte analysieren Sie zuerst eine Website.', 'warning', 4000);
            break;
          }
          showToast('Validierung wird gestartet...', 'info', 2000);
          const res = await fetch(`${API_BASE}/api/scan/validate`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token ?? ''}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ website_id: websiteId }),
          });
          if (res.ok) {
            const data = await res.json();
            showToast(`Validierung abgeschlossen. Score: ${data.score ?? '–'}%`, 'success', 6000);
          } else {
            showToast('Validierung fehlgeschlagen. Bitte versuchen Sie es erneut.', 'error', 4000);
          }
          break;
        }
      }
    } catch {
      showToast('Verbindungsfehler. Bitte prüfen Sie Ihre Internetverbindung.', 'error', 4000);
    } finally {
      setLoadingStep(null);
    }
  }, [criticalIssues.length, warningIssues.length, analysisData, currentWebsite, showToast]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-500';
      case 'active':    return 'text-blue-500';
      default:          return 'text-gray-500';
    }
  };

  const getStepBgColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500/10 border-green-500/30';
      case 'active':    return 'bg-blue-500/10 border-blue-500/30';
      default:          return 'bg-gray-500/10 border-gray-500/20';
    }
  };

  const completedCount = steps.filter(s => s.status === 'completed').length;

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 rounded-xl border border-slate-700 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Target className="w-6 h-6 text-white" />
            <div>
              <h2 className="text-lg font-bold text-white">Optimierungsprozess</h2>
              <p className="text-sm text-white/70">Schritt-für-Schritt zur vollständigen Compliance</p>
            </div>
          </div>
          <div className="text-right hidden sm:block">
            <p className="text-xs text-white/60 uppercase tracking-wider">Fortschritt</p>
            <p className="text-lg font-bold text-white">{completedCount}/{steps.length}</p>
          </div>
        </div>
      </div>

      {/* KI-Anweisungen Banner */}
      <div className="px-6 pt-4 pb-0">
        <div className="flex items-start gap-2.5 p-3 bg-blue-500/10 border border-blue-500/25 rounded-lg">
          <Zap className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
          <p className="text-xs text-blue-200 leading-relaxed">
            <strong className="text-blue-300">KI-gestützter Optimierungsassistent:</strong> Folgen Sie den 5 Schritten für eine vollständige Compliance-Prüfung. Die KI analysiert Ihre Website, identifiziert Probleme und schlägt konkrete Fixes vor.
          </p>
        </div>
      </div>

      {/* Steps */}
      <div className="p-6 space-y-3">
        {steps.map(step => {
          const IconComponent = step.icon;
          const ActionIcon = step.actionIcon;
          const isExpanded = expandedStep === step.id;
          const isLoading = loadingStep === step.id;

          return (
            <div
              key={step.id}
              className={`rounded-lg border transition-all ${getStepBgColor(step.status)}`}
            >
              {/* Step Header */}
              <div
                className="p-4 flex items-start gap-4 cursor-pointer"
                onClick={() => setExpandedStep(isExpanded ? null : step.id)}
              >
                <div className="flex-shrink-0">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    step.status === 'completed' ? 'bg-green-500/20' :
                    step.status === 'active' ? 'bg-blue-500/20' : 'bg-gray-500/20'
                  }`}>
                    <IconComponent className={`w-5 h-5 ${getStatusColor(step.status)}`} />
                  </div>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-gray-600">0{step.id}</span>
                    <h3 className="font-semibold text-white text-sm">{step.title}</h3>
                    {step.status === 'completed' && (
                      <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                    )}
                  </div>
                  <p className="text-xs text-gray-400">{step.description}</p>
                </div>

                <ChevronRight className={`w-5 h-5 text-gray-400 flex-shrink-0 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
              </div>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-white/5">
                  <div className="mt-3 space-y-3">
                    {/* Step-specific content */}
                    {step.id === 1 && (
                      <div className="space-y-2">
                        <p className="text-sm text-gray-300">Die KI überprüft Ihre Website auf alle kritischen Compliance-Anforderungen:</p>
                        <ul className="text-xs space-y-1.5 text-gray-400 pl-1">
                          {['DSGVO & Datenschutzerklärung', 'Cookie-Compliance (TTDSG)', 'Impressum nach § 5 TMG', 'Barrierefreiheit (BFSG/WCAG 2.1)', 'AGB & Widerrufsbelehrung'].map(item => (
                            <li key={item} className="flex items-center gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {step.id === 2 && criticalIssues.length > 0 && (
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {criticalIssues.slice(0, 5).map((issue: ComplianceIssue, idx: number) => (
                          <div key={idx} className="bg-red-500/10 border border-red-500/20 rounded p-2">
                            <p className="text-xs font-medium text-red-400">{issue.title}</p>
                            {issue.description && (
                              <p className="text-xs text-red-300/60 mt-0.5 line-clamp-1">{issue.description}</p>
                            )}
                          </div>
                        ))}
                        {criticalIssues.length > 5 && (
                          <p className="text-xs text-gray-500 text-center">+{criticalIssues.length - 5} weitere kritische Probleme</p>
                        )}
                      </div>
                    )}

                    {step.id === 3 && warningIssues.length > 0 && (
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {warningIssues.slice(0, 5).map((issue: ComplianceIssue, idx: number) => (
                          <div key={idx} className="bg-yellow-500/10 border border-yellow-500/20 rounded p-2">
                            <p className="text-xs font-medium text-yellow-400">{issue.title}</p>
                          </div>
                        ))}
                        {warningIssues.length > 5 && (
                          <p className="text-xs text-gray-500 text-center">+{warningIssues.length - 5} weitere Warnungen</p>
                        )}
                      </div>
                    )}

                    {step.id === 4 && (
                      <p className="text-sm text-gray-300">
                        Öffnet den W3C Validator für Ihre Website, um alle implementierten Änderungen zu validieren.
                      </p>
                    )}

                    {step.id === 5 && (
                      <p className="text-sm text-gray-300">
                        Führt einen abschließenden Compliance-Check durch und erstellt einen Abschlussbericht.
                      </p>
                    )}

                    {/* Action Button */}
                    <button
                      onClick={e => { e.stopPropagation(); handleAction(step.id); }}
                      disabled={isLoading}
                      className={`mt-2 w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-60 disabled:cursor-not-allowed ${
                        step.status === 'completed'
                          ? 'bg-green-600 hover:bg-green-700 text-white'
                          : step.status === 'active'
                          ? 'bg-blue-600 hover:bg-blue-700 text-white'
                          : 'bg-gray-700 hover:bg-gray-600 text-white'
                      }`}
                    >
                      {isLoading
                        ? <><Loader2 className="w-4 h-4 animate-spin" /> Wird geladen...</>
                        : <><ActionIcon className="w-4 h-4" /> {step.actionLabel}</>
                      }
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Progress Bar */}
      <div className="px-6 pb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-400 uppercase tracking-wider">Gesamtfortschritt</span>
          <span className="text-sm font-semibold text-white">{completedCount}/{steps.length} Schritte</span>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-2">
          <div
            className="bg-gradient-to-r from-blue-600 to-purple-600 h-2 rounded-full transition-all duration-500"
            style={{ width: `${(completedCount / steps.length) * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
};
