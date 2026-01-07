'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, CheckCircle2, AlertCircle, Info, Sparkles, Download, Loader2 } from 'lucide-react';
import { ComplianceIssueCard } from './ComplianceIssueCard';
import { UnifiedFixButton } from './UnifiedFixButton';
import { useToast } from '@/components/ui/Toast';

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
  planType: 'free' | 'ai' | 'expert';
  websiteUrl?: string;
  scanId?: string;
  onStartFix?: (issueId: string) => void;
}

export const ComplianceIssueGroup: React.FC<ComplianceIssueGroupProps> = ({
  group,
  planType,
  websiteUrl,
  scanId,
  onStartFix
}) => {
  const { showToast } = useToast();
  const [isExpanded, setIsExpanded] = useState(false);
  const [showAllIssues, setShowAllIssues] = useState(false);
  const [isFixingAll, setIsFixingAll] = useState(false);

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

  // Severity-Icons
  const SeverityIcon = {
    critical: AlertCircle,
    warning: AlertCircle,
    info: Info
  }[group.severity as keyof typeof SeverityIcon] || Info;

  // Fortschritt berechnen
  const progress = group.total_count > 0 
    ? (group.completed_count / group.total_count) * 100 
    : 0;

  // Zeige limitierte Anzahl wenn nicht expanded
  const displayIssues = showAllIssues 
    ? group.sub_issues 
    : group.sub_issues.slice(0, 3);
  
  const hasMore = group.sub_issues.length > 3;

  // ✅ NEU: "Alle beheben" Funktion - gemeinsame Lösung für alle Issues der Gruppe
  const handleFixAllIssues = async () => {
    if (!scanId || isFixingAll) return;
    
    setIsFixingAll(true);
    
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';
      
      // Prüfe ob es sich um Datenschutz/Impressum handelt - dann eRecht24 nutzen
      const isLegalText = group.category === 'datenschutz' || 
                          group.category === 'impressum' ||
                          group.category === 'legal' ||
                          group.title.toLowerCase().includes('datenschutz') ||
                          group.title.toLowerCase().includes('impressum');
      
      if (isLegalText) {
        // ✅ RECHTSTEXT: eRecht24 API nutzen
        const textType = group.title.toLowerCase().includes('impressum') ? 'imprint' : 'privacy_policy';
        const endpoint = textType === 'imprint' 
          ? '/api/erecht24/imprint'
          : '/api/erecht24/privacy-policy';

        const response = await fetch(`${API_URL}${endpoint}?language=de`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        });

        if (!response.ok) throw new Error('Generierung fehlgeschlagen');

        const data = await response.json();
        
        // Auto-Download
        if (typeof document !== 'undefined' && data.html) {
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

        showToast(
          `✅ ${textType === 'imprint' ? 'Impressum' : 'Datenschutzerklärung'} generiert und heruntergeladen! Ersetzen Sie den alten Text auf Ihrer Website.`, 
          'success', 
          7000
        );
      } else {
        // ✅ TECHNISCHE FIXES: Batch-Fix API nutzen
        const response = await fetch(`${API_URL}/api/fixes/batch`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            scan_id: scanId,
            group_id: group.group_id,
            issue_ids: group.sub_issues.map(i => i.id),
            category: group.category
          })
        });

        if (!response.ok) {
          // Fallback: Zeige Anleitungen
          showToast(
            `📋 Für ${group.total_count} ${group.category}-Probleme: Bitte prüfen Sie die einzelnen Issues unten für detaillierte Lösungen.`,
            'info',
            5000
          );
          setIsExpanded(true);
          return;
        }

        const result = await response.json();
        showToast(`✅ ${result.fixed_count || group.total_count} Probleme werden behoben...`, 'success', 5000);
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

        {/* ✅ Unified Solution Button - JETZT FUNKTIONAL */}
        {(group.has_unified_solution || group.total_count > 1) && (
          <div className="mt-4 space-y-3">
            {/* Zusammenfassung was behoben wird */}
            <div className="p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
              <p className="text-sm text-purple-200">
                <Sparkles className="w-4 h-4 inline mr-1" />
                <strong>Gemeinsame Lösung:</strong> Behebt alle {group.total_count} Probleme in dieser Kategorie mit einem Klick.
                {group.category === 'datenschutz' && (
                  <span className="block mt-1 text-xs text-purple-300">
                    → Generiert eine vollständige Datenschutzerklärung nach aktuellen Anforderungen
                  </span>
                )}
                {group.category === 'impressum' && (
                  <span className="block mt-1 text-xs text-purple-300">
                    → Generiert ein rechtssicheres Impressum mit allen Pflichtangaben
                  </span>
                )}
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
                />
              </div>
            )}

            {/* Sub Issues */}
            {group.sub_issues.length > 0 && (
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
                    />
                  ))}
                </div>

                {/* Show More Button */}
                {hasMore && !showAllIssues && (
                  <button
                    onClick={() => setShowAllIssues(true)}
                    className="mt-4 w-full px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-sm font-medium transition-colors"
                  >
                    Zeige {group.sub_issues.length - 3} weitere Problem{group.sub_issues.length - 3 > 1 ? 'e' : ''}
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
    </div>
  );
};

