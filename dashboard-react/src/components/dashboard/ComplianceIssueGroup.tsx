'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, CheckCircle2, AlertCircle, Info, Sparkles } from 'lucide-react';
import { ComplianceIssueCard } from './ComplianceIssueCard';

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
  const [isExpanded, setIsExpanded] = useState(false);
  const [showAllIssues, setShowAllIssues] = useState(false);

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

        {/* Unified Solution Button */}
        {group.has_unified_solution && (
          <div className="mt-4">
            <button
              onClick={() => {
                // TODO: Trigger unified fix for all issues
                if (onStartFix && group.parent_issue) {
                  onStartFix(group.parent_issue.id);
                }
              }}
              className="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white rounded-lg font-semibold shadow-lg transition-all duration-200 flex items-center justify-center gap-2"
            >
              <Sparkles className="w-5 h-5" />
              Alle Probleme gemeinsam beheben
            </button>
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

