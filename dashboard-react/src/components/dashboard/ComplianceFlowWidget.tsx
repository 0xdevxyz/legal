'use client';

import React from 'react';
import { Shield, Cookie, Eye, FileText, ChevronRight } from 'lucide-react';
import { useDashboardStore } from '@/stores/dashboard';
import { useRouter } from 'next/navigation';
import { useTheme } from '@/contexts/ThemeContext';

interface FlowArea {
  key: string;
  label: string;
  icon: React.ElementType;
  score: number;
  status: 'active' | 'warning' | 'critical' | 'idle';
  href: string;
  detail: string;
}

function getStatus(score: number): FlowArea['status'] {
  if (score === 0) return 'idle';
  if (score >= 75) return 'active';
  if (score >= 50) return 'warning';
  return 'critical';
}

function getStatusColor(status: FlowArea['status']): string {
  switch (status) {
    case 'active': return '#22c55e';
    case 'warning': return '#eab308';
    case 'critical': return '#ef4444';
    default: return '#71717a';
  }
}

function getFlowStroke(status: FlowArea['status'], isLight: boolean): string {
  if (status === 'idle') return isLight ? '#d1d5db' : '#3f3f46';
  return '#f97316';
}

export const ComplianceFlowWidget: React.FC = () => {
  const { currentWebsite, metrics, analysisData } = useDashboardStore();
  const router = useRouter();
  const { theme } = useTheme();
  const isLight = theme === 'light';

  const overallScore = currentWebsite?.complianceScore ?? metrics.totalScore ?? 0;

  const pillarScores: Array<{ pillar: string; score: number }> =
    (analysisData as any)?.pillar_scores ?? [];

  // Fallback: Berechne Pillar-Scores clientseitig aus issues, wenn pillar_scores fehlen
  const issues: Array<{ category?: string; severity?: string }> =
    (analysisData as any)?.issues ?? [];

  const SEVERITY_WEIGHTS: Record<string, number> = {
    critical: 25,
    warning: 10,
    info: 0,
  };

  const computePillarFromIssues = (matchers: string[]): number => {
    const matched = issues.filter((i) => {
      const cat = (i.category || '').toLowerCase();
      return matchers.some((m) => cat.includes(m));
    });
    if (matched.length === 0) return 100;
    let score = 100;
    for (const issue of matched) {
      score -= SEVERITY_WEIGHTS[(issue.severity || 'info').toLowerCase()] ?? 0;
    }
    return Math.max(0, Math.min(100, Math.round(score)));
  };

  const getPillarScore = (...ids: string[]) => {
    // 1. Versuch: aus pillar_scores Array (Backend)
    for (const id of ids) {
      const found = pillarScores.find((p) => p.pillar === id);
      if (found) return found.score;
    }
    // 2. Fallback: aus issues clientseitig berechnen
    if (issues.length > 0 || analysisData) {
      if (ids.includes('datenschutz') || ids.includes('gdpr')) {
        return computePillarFromIssues(['datenschutz', 'dsgvo', 'ttdsg', 'legality']);
      }
      if (ids.includes('impressum') || ids.includes('legal')) {
        return computePillarFromIssues(['impressum', 'agb']);
      }
      if (ids.includes('cookies') || ids.includes('cookie')) {
        return computePillarFromIssues(['cookie', 'tcf', 'tracking']);
      }
      if (ids.includes('accessibility') || ids.includes('barrierefreiheit')) {
        return computePillarFromIssues(['accessibility', 'aria', 'alt_text', 'contrast', 'barrierefreiheit']);
      }
    }
    return 0;
  };

  const dsgvoScore = analysisData ? getPillarScore('gdpr', 'datenschutz') : 0;
  const cookieScore = getPillarScore('cookies', 'cookie');
  const barriereScore = getPillarScore('accessibility', 'barrierefreiheit');
  const rechtstexteScore = analysisData ? getPillarScore('legal', 'impressum') : 0;

  const areas: FlowArea[] = [
    { key: 'dsgvo', label: 'DSGVO', icon: Shield, score: dsgvoScore, status: getStatus(dsgvoScore), href: '/', detail: dsgvoScore > 0 ? `Score: ${dsgvoScore}` : 'Noch nicht analysiert' },
    { key: 'cookie', label: 'Cookie-Compliance', icon: Cookie, score: cookieScore, status: getStatus(cookieScore), href: '/cookie-compliance', detail: cookieScore > 0 ? `Score: ${cookieScore}` : 'Noch nicht analysiert' },
    { key: 'barriere', label: 'Barrierefreiheit', icon: Eye, score: barriereScore, status: getStatus(barriereScore), href: '/accessibility/statement', detail: barriereScore > 0 ? `Score: ${barriereScore}` : 'Noch nicht analysiert' },
    { key: 'rechtstexte', label: 'Rechtstexte', icon: FileText, score: rechtstexteScore, status: getStatus(rechtstexteScore), href: '/documents', detail: rechtstexteScore > 0 ? `Score: ${rechtstexteScore}` : 'Noch nicht analysiert' },
  ];

  const activeCount = areas.filter((a) => a.status === 'active').length;
  const warningCount = areas.filter((a) => a.status === 'warning').length;
  const criticalCount = areas.filter((a) => a.status === 'critical').length;

  const textPrimary = isLight ? '#111827' : '#ffffff';
  const textMuted = isLight ? '#6b7280' : '#71717a';
  const cardBg = isLight ? '#f9fafb' : 'rgba(24,24,27,0.6)';
  const cardBorder = isLight ? 'rgba(0,0,0,0.07)' : 'rgba(63,63,70,0.5)';
  const cardLabelColor = isLight ? '#374151' : '#ffffff';
  const cardDetailColor = isLight ? '#9ca3af' : '#71717a';
  const chevronColor = isLight ? '#9ca3af' : '#52525b';
  const dividerColor = isLight ? '#f3f4f6' : 'rgba(63,63,70,0.6)';
  const outputBg = isLight ? 'rgba(249,115,22,0.08)' : 'rgba(249,115,22,0.15)';
  const outputBorder = isLight ? 'rgba(249,115,22,0.2)' : 'rgba(249,115,22,0.3)';
  const outputScoreColor = isLight ? '#111827' : '#ffffff';

  return (
    <div className="stat-card-new">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold" style={{ color: textPrimary }}>Compliance Flow</h3>
          <p className="text-xs mt-0.5" style={{ color: textMuted }}>Alle Bereiche im Überblick</p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          {activeCount > 0 && <span className="flex items-center gap-1.5 text-green-500"><span className="status-led green" />{activeCount} OK</span>}
          {warningCount > 0 && <span className="flex items-center gap-1.5 text-yellow-500"><span className="status-led yellow" />{warningCount} Warnung</span>}
          {criticalCount > 0 && <span className="flex items-center gap-1.5 text-red-500"><span className="status-led red" />{criticalCount} Kritisch</span>}
        </div>
      </div>

      <div className="flex items-center">
        {/* Left: OUTPUT block */}
        <div className="flex-shrink-0 flex flex-col items-center justify-center w-28">
          <div className="rounded-xl px-4 py-3 text-center" style={{ background: outputBg, border: `1px solid ${outputBorder}` }}>
            <div className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: 'var(--lime)' }}>OUTPUT</div>
            <div className="text-2xl font-black" style={{ color: outputScoreColor }}>{overallScore}</div>
            <div className="text-[10px] mt-0.5" style={{ color: textMuted }}>Gesamt</div>
          </div>
        </div>

        {/* Center: SVG Flow lines */}
        <div className="flex-1 relative" style={{ height: '160px' }}>
          <svg viewBox="0 0 200 160" className="w-full h-full" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
            {areas.map((area, i) => {
              const yPositions = [20, 53, 87, 120];
              const y = yPositions[i];
              const strokeColor = getFlowStroke(area.status, isLight);
              const isActive = area.status !== 'idle';
              return (
                <g key={area.key}>
                  <path
                    d={`M 10 80 C 70 80 70 ${y + 8} 190 ${y + 8}`}
                    fill="none"
                    stroke={strokeColor}
                    strokeWidth={isActive ? '2.5' : '1.5'}
                    strokeLinecap="round"
                    className={isActive ? 'flow-line-active' : 'flow-line-inactive'}
                    style={isActive ? { animationDelay: `${i * 0.3}s`, strokeDasharray: '8 4' } : {}}
                  />
                </g>
              );
            })}
          </svg>
        </div>

        {/* Right: Detail cards */}
        <div className="flex-shrink-0 flex flex-col gap-2 w-48">
          {areas.map((area) => {
            const Icon = area.icon;
            const color = getStatusColor(area.status);
            return (
              <button
                key={area.key}
                onClick={() => router.push(area.href)}
                className="flex items-center gap-2.5 px-3 py-2 rounded-lg transition-all duration-200 text-left group w-full"
                style={{ background: cardBg, border: `1px solid ${cardBorder}` }}
              >
                <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ backgroundColor: `${color}18` }}>
                  <Icon className="w-3.5 h-3.5" style={{ color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium truncate leading-tight" style={{ color: cardLabelColor }}>{area.label}</div>
                  <div className="text-[10px] mt-0.5" style={{ color: cardDetailColor }}>{area.detail}</div>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <span className="status-led" style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}60` }} />
                  <ChevronRight className="w-3 h-3 transition-colors group-hover:text-[#25bac8]" style={{ color: chevronColor }} />
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Bottom stats bar */}
      <div className="mt-5 pt-4 grid grid-cols-4 gap-4" style={{ borderTop: `1px solid ${dividerColor}` }}>
        {areas.map((area) => {
          const color = getStatusColor(area.status);
          return (
            <div key={area.key} className="text-center">
              <div className="text-base font-bold" style={{ color: area.score > 0 ? color : (isLight ? '#d1d5db' : '#52525b') }}>
                {area.score > 0 ? area.score : '—'}
              </div>
              <div className="text-[10px] mt-0.5 truncate" style={{ color: textMuted }}>{area.label.split(' ')[0]}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
