'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, CheckCircle2, AlertCircle, Info, Sparkles, Download, Loader2, FileText, X } from 'lucide-react';
import { ComplianceIssueCard } from './ComplianceIssueCard';
import { UnifiedFixButton } from './UnifiedFixButton';
import { useToast } from '@/components/ui/Toast';
import { LegalDocumentGenerator, type WizardDocType } from '@/components/legal/LegalDocumentGenerator';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api-client';
import { generateLegalText, type LegalDocumentType } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

interface IssueGroup {
  group_id: string;
  group_type: string;
  parent_issue?: any;
  sub_issues: any[];
  category: string;
  severity: string;
  solution_type: string;
  has_unified_solution: boolean;
  total_risk_euro: number;
  completed_count: number;
  total_count: number;
  title: string;
  description: string;
  icon: string;
}

interface ComplianceIssueGroupProps {
  group: IssueGroup;
  planType: 'free' | 'paid' | 'expert';
  websiteUrl?: string;
  scanId?: string;
  onStartFix?: (issueId: string) => void;
  isAnalysisOnly?: boolean;
}

export const ComplianceIssueGroup: React.FC<ComplianceIssueGroupProps> = ({
  group,
  planType,
  websiteUrl,
  scanId,
  onStartFix,
  isAnalysisOnly = false
}) => {
  const { showToast } = useToast();
  const { user } = useAuth();
  const [isExpanded, setIsExpanded] = useState(false);
  const [showAllIssues, setShowAllIssues] = useState(false);
  const [isFixingAll, setIsFixingAll] = useState(false);
  const [showLegalWizard, setShowLegalWizard] = useState<WizardDocType | null>(null);

  // ✅ Welcher Rechtstext gehört zu dieser Gruppe? (Titel/Kategorie-Heuristik)
  const _gt = `${group.title} ${group.category || ''}`.toLowerCase();
  const legalDocumentType: WizardDocType | null =
    _gt.includes('impressum') ? 'impressum' :
    (_gt.includes('widerruf') || _gt.includes('withdrawal')) ? 'widerruf' :
    (_gt.includes('agb') || _gt.includes('geschäftsbedingung') || _gt.includes('tos') || _gt.includes('terms')) ? 'agb' :
    _gt.includes('datenschutz') ? 'datenschutz' :
    null;

  // Cookie-Richtlinie wird über die dedizierte Cookie-Compliance-Seite gepflegt,
  // daher hier NICHT als Wizard-Gruppe behandelt.
  const isLegalTextGroup = legalDocumentType !== null;

  // Label-Map für UI-Texte
  const DOC_LABELS: Record<WizardDocType, { title: string; basis: string; cta: string }> = {
    impressum:   { title: 'Impressum erstellen',            basis: 'ein rechtssicheres Impressum nach § 5 TMG',                 cta: 'Impressum Generator starten' },
    datenschutz: { title: 'Datenschutzerklärung erstellen', basis: 'eine DSGVO-konforme Datenschutzerklärung',                  cta: 'Datenschutz Generator starten' },
    agb:         { title: 'AGB erstellen',                  basis: 'rechtssichere Allgemeine Geschäftsbedingungen',             cta: 'AGB Generator starten' },
    cookie:      { title: 'Cookie-Richtlinie erstellen',    basis: 'eine TTDSG-konforme Cookie-Richtlinie',                     cta: 'Cookie-Richtlinie Generator starten' },
    widerruf:    { title: 'Widerrufsbelehrung erstellen',   basis: 'eine Widerrufsbelehrung inkl. Muster-Widerrufsformular',    cta: 'Widerruf Generator starten' },
  };

  // Severity-basierte Farben
  const severityColors = {
    critical: {
      border: 'border-red-500/30',
      bg: 'bg-gradient-to-br from-red-500/10 to-red-600/5',
      badge: 'bg-red-500/20 text-red-300',
      icon: 'text-red-400'
    },
    warning: {
      border: 'border-yellow-500/30',
      bg: 'bg-gradient-to-br from-yellow-500/10 to-yellow-600/5',
      badge: 'bg-yellow-500/20 text-yellow-300',
      icon: 'text-yellow-400'
    },
    info: {
      border: 'border-blue-500/30',
      bg: 'bg-gradient-to-br from-blue-500/10 to-blue-600/5',
      badge: 'bg-blue-500/20 text-blue-300',
      icon: 'text-blue-400'
    }
  };

  const colors = severityColors[group.severity as keyof typeof severityColors] || severityColors.info;

  const severityIconMap: Record<string, typeof AlertCircle> = {
    critical: AlertCircle,
    warning: AlertCircle,
    info: Info
  };
  const SeverityIcon = severityIconMap[group.severity] || Info;

  // Fortschritt berechnen
  const progress = group.total_count > 0 
    ? (group.completed_count / group.total_count) * 100 
    : 0;

  // Zeige limitierte Anzahl wenn nicht expanded
  const displayIssues = showAllIssues 
    ? (group.sub_issues ?? []) 
    : (group.sub_issues ?? []).slice(0, 3);
  
  const hasMore = (group.sub_issues ?? []).length > 3;

  // ✅ NEU: "Alle beheben" Funktion - gemeinsame Lösung für alle Issues der Gruppe
  const handleFixAllIssues = async () => {
    if (!scanId || isFixingAll) return;
    
    setIsFixingAll(true);
    
    try {
      // Nutze internen Rechtstexte-Generator
      const isLegalText = group.category === 'datenschutz' || 
                          group.category === 'impressum' ||
                          group.category === 'legal' ||
                          group.title.toLowerCase().includes('datenschutz') ||
                          group.title.toLowerCase().includes('impressum');
      
      if (isLegalText) {
        const textType: LegalDocumentType = group.title.toLowerCase().includes('impressum') ? 'imprint' : 'privacy';

        if (!user?.company && !user?.full_name) {
          showToast('Bitte hinterlegen Sie zuerst Ihre Firmendaten im Profil.', 'error');
          return;
        }

        const data = await generateLegalText(textType, {
          user_data: {
            company_name: user.company || user.full_name,
            email: user.email,
          },
          language: 'de',
        });

        // Auto-Download
        if (typeof document !== 'undefined' && data.html_content) {
          const filename = textType === 'imprint' ? 'impressum.html' : 'datenschutzerklaerung.html';
          const blob = new Blob([data.html_content], { type: 'text/html;charset=utf-8' });
          const url = URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
        }

        showToast(
          `✅ ${textType === 'imprint' ? 'Impressum' : 'Datenschutzerklärung'} generiert und heruntergeladen! Ersetzen Sie den alten Text auf Ihrer Website.`, 
          'success', 
          7000
        );
      } else {
        // ✅ TECHNISCHE FIXES: Batch-Fix API nutzen
        let result: any;
        try {
          result = await apiClient.post(`/api/fixes/batch`, {
            scan_id: scanId,
            group_id: group.group_id,
            issue_ids: (group.sub_issues ?? []).map(i => i.id),
            category: group.category
          });
        } catch {
          showToast(
            `📋 Für ${group.total_count} ${group.category}-Probleme: Bitte prüfen Sie die einzelnen Issues unten für detaillierte Lösungen.`,
            'info',
            5000
          );
          setIsExpanded(true);
          return;
        }

        showToast(`✅ ${result?.fixed_count || group.total_count} Probleme werden behoben...`, 'success', 5000);
      }
      
      // Callback für Parent-Komponente
      if (onStartFix && group.parent_issue) {
        onStartFix(group.parent_issue.id);
      }
      
    } catch (error) {
      console.error('Batch-Fix Fehler:', error);
      showToast(
        '⚠️ Automatische Behebung nicht verfügbar. Bitte nutzen Sie die einzelnen Fix-Buttons unten.',
        'warning',
        5000
      );
      setIsExpanded(true); // Öffne Details damit User einzelne Issues sehen kann
    } finally {
      setIsFixingAll(false);
    }
  };

  return (
    <div className={`rounded-xl border-2 ${colors.border} ${colors.bg} overflow-hidden mb-4 transition-all duration-300`}>
      {/* Header */}
      <div className="p-6">
        <div className="flex items-start justify-between gap-4">
          {/* Left: Icon, Title, Description */}
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <div className={`text-3xl ${colors.icon}`}>
                {group.icon}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="text-xl font-bold text-white">
                    {group.title}
                  </h3>
                  
                  {/* Severity Badge */}
                  <span className={`px-2 py-1 rounded-md text-xs font-semibold ${colors.badge}`}>
                    {group.severity === 'critical' ? 'Kritisch' : group.severity === 'warning' ? 'Warnung' : 'Info'}
                  </span>
                  
                  {/* Unified Solution Badge */}
                  {group.has_unified_solution && (
                    <span className="px-2 py-1 rounded-md text-xs font-semibold bg-purple-500/20 text-purple-300 flex items-center gap-1">
                      <Sparkles className="w-3 h-3" />
                      Gemeinsame Lösung
                    </span>
                  )}
                </div>
                
                <p className="text-sm text-zinc-400 mt-1">
                  {group.description}
                </p>
              </div>
            </div>
          </div>

          {/* Right: Stats & Action */}
          <div className="flex flex-col items-end gap-2">
            {/* Risiko */}
            <div className="text-right">
              <div className="text-xs text-zinc-500 uppercase tracking-wider">Geschätztes Risiko</div>
              <div className="text-xl font-bold text-red-400">
                {new Intl.NumberFormat('de-DE', {
                  style: 'currency',
                  currency: 'EUR',
                  maximumFractionDigits: 0
                }).format(group.total_risk_euro)}
              </div>
            </div>

            {/* Issue Count */}
            <div className={`px-3 py-1 rounded-lg ${colors.badge} text-sm font-semibold`}>
              {group.total_count} {group.total_count === 1 ? 'Problem' : 'Probleme'}
            </div>

            {/* Expand Button */}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg transition-colors text-sm font-medium"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="w-4 h-4" />
                  Einklappen
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4" />
                  Details anzeigen
                </>
              )}
            </button>
          </div>
        </div>

        {/* Progress Bar (if has completed items) */}
        {group.completed_count > 0 && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-zinc-400">Fortschritt</span>
              <span className="text-sm font-semibold text-white">
                {group.completed_count} / {group.total_count} behoben
              </span>
            </div>
            <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-green-500 to-emerald-500 transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* ✅ Für Impressum/Datenschutz: Spezieller Wizard statt "Alle beheben" */}
        {!isAnalysisOnly && isLegalTextGroup ? (
          <div className="mt-4 space-y-3">
            {/* Info-Box */}
            <div className="p-4 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-lg">
              <div className="flex items-start gap-3">
                <FileText className="w-5 h-5 text-blue-400 mt-0.5" />
                <div>
                  <p className="text-sm text-white font-medium mb-1">
                    {legalDocumentType && DOC_LABELS[legalDocumentType].title}
                  </p>
                  <p className="text-xs text-zinc-400">
                    Unser Assistent führt Sie durch alle notwendigen Angaben und erstellt{' '}
                    {legalDocumentType && DOC_LABELS[legalDocumentType].basis} basierend auf Ihrer Website.
                  </p>
                </div>
              </div>
            </div>
            
            {/* Wizard-Button */}
            <Button
              onClick={() => legalDocumentType && setShowLegalWizard(legalDocumentType)}
              className="w-full gap-2 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-semibold py-3"
              size="lg"
            >
              <FileText className="w-5 h-5" />
              {legalDocumentType && DOC_LABELS[legalDocumentType].cta}
            </Button>
          </div>
        ) : (
          /* ✅ Für andere Kategorien: Standard-Fix-Button */
          !isAnalysisOnly && (group.has_unified_solution || group.total_count > 1) && (
            <div className="mt-4 space-y-3">
              <div className="p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                <p className="text-sm text-purple-200">
                  <Sparkles className="w-4 h-4 inline mr-1" />
                  <strong>Gemeinsame Lösung:</strong> Behebt alle {group.total_count} Probleme in dieser Kategorie.
                </p>
              </div>
              
              <UnifiedFixButton
                issueTitle={group.title}
                isGroup={true}
                onFix={handleFixAllIssues}
                disabled={isFixingAll}
                isLoading={isFixingAll}
              />
            </div>
          )
        )}
      </div>

      {/* Expanded Content: Issue Cards */}
      {isExpanded && (
        <div className="border-t border-zinc-800/50 bg-black/20">
          <div className="p-6 space-y-4">
            {/* Parent Issue (if exists) */}
            {group.parent_issue && (
              <div className="mb-6">
                <div className="text-xs text-zinc-500 uppercase tracking-wider mb-2">
                  Hauptproblem
                </div>
                <ComplianceIssueCard
                  issue={group.parent_issue}
                  planType={planType}
                  websiteUrl={websiteUrl}
                  scanId={scanId}
                  onStartFix={onStartFix}
                  isAnalysisOnly={isAnalysisOnly}
                />
              </div>
            )}

            {/* Sub Issues */}
            {(group.sub_issues ?? []).length > 0 && (
              <div>
                <div className="text-xs text-zinc-500 uppercase tracking-wider mb-2">
                  {group.parent_issue ? 'Detaillierte Probleme' : 'Alle Probleme'}
                </div>
                
                <div className="space-y-3">
                  {displayIssues.map((issue, idx) => (
                    <ComplianceIssueCard
                      key={`${issue.id}-${idx}`}
                      issue={issue}
                      planType={planType}
                      websiteUrl={websiteUrl}
                      scanId={scanId}
                      onStartFix={onStartFix}
                      isAnalysisOnly={isAnalysisOnly}
                    />
                  ))}
                </div>

                {/* Show More Button */}
                {hasMore && !showAllIssues && (
                  <button
                    onClick={() => setShowAllIssues(true)}
                    className="mt-4 w-full px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    Zeige {(group.sub_issues ?? []).length - 3} weitere Problem{(group.sub_issues ?? []).length - 3 > 1 ? 'e' : ''}
                  </button>
                )}
                
                {showAllIssues && hasMore && (
                  <button
                    onClick={() => setShowAllIssues(false)}
                    className="mt-4 w-full px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    Weniger anzeigen
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ✅ Legal Document Generator Modal/Overlay */}
      {showLegalWizard && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black/80 backdrop-blur-sm"
            onClick={() => setShowLegalWizard(null)}
          />
          
          {/* Modal Content */}
          <div className="relative min-h-screen flex items-start justify-center p-4 pt-10 pb-20">
            <div className="relative w-full max-w-4xl bg-zinc-950 rounded-2xl shadow-2xl border border-zinc-800">
              {/* Close Button */}
              <button
                onClick={() => setShowLegalWizard(null)}
                className="absolute top-4 right-4 p-2 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors z-10"
              >
                <X className="w-5 h-5" />
              </button>
              
              {/* Wizard Content */}
              <div className="p-6">
                <LegalDocumentGenerator
                  documentType={showLegalWizard}
                  onComplete={(data) => {
                    setShowLegalWizard(null);
                    showToast(
                      `✅ ${DOC_LABELS[showLegalWizard].title.replace(' erstellen', '')} erfolgreich erstellt!`,
                      'success',
                      5000
                    );
                  }}
                  onBack={() => setShowLegalWizard(null)}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

