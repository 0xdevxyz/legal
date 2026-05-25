'use client';

import React, { useEffect, useRef, useState } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useDashboardStore } from '@/stores/dashboard';
import { useTheme } from '@/contexts/ThemeContext';

interface GaugeTab {
  key: string;
  label: string;
  score: number;
}

interface ComplianceGaugeProps {
  userName?: string;
  scoreTrend?: number | null;
}

const GAUGE_RADIUS = 90;
const GAUGE_CIRCUMFERENCE = Math.PI * GAUGE_RADIUS;

function getGaugeColor(score: number): string {
  if (score <= 40) return '#ef4444';
  if (score <= 60) return '#eab308';
  if (score <= 75) return '#84cc16';
  return '#22c55e';
}

function getGaugeGradientId(score: number): string {
  if (score <= 40) return 'gaugeRed';
  if (score <= 60) return 'gaugeYellow';
  if (score <= 75) return 'gaugeLightGreen';
  return 'gaugeGreen';
}

function getScoreLabel(score: number): string {
  if (score <= 40) return 'Kritisch';
  if (score <= 60) return 'Verbesserungswürdig';
  if (score <= 75) return 'Gut';
  if (score <= 89) return 'Sehr gut';
  return 'Exzellent';
}

export const ComplianceGauge: React.FC<ComplianceGaugeProps> = ({ userName, scoreTrend }) => {
  const { currentWebsite, metrics, analysisData } = useDashboardStore();
  const { theme } = useTheme();
  const isLight = theme === 'light';
  const [activeTab, setActiveTab] = useState<string>('gesamt');
  const [animatedScore, setAnimatedScore] = useState(0);
  const animFrameRef = useRef<number | null>(null);

  const gesamtScore = currentWebsite?.complianceScore ?? metrics.totalScore ?? 0;

  const pillarScores: Array<{ pillar: string; score: number }> =
    (analysisData as any)?.pillar_scores ?? [];

  // Fallback: clientseitige Pillar-Score-Berechnung aus issues
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
    for (const id of ids) {
      const found = pillarScores.find((p) => p.pillar === id);
      if (found) return found.score;
    }
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

  const dsgvoScore = getPillarScore('gdpr', 'datenschutz');
  const rechtstexteScore = getPillarScore('legal', 'impressum');
  const cookieScore = getPillarScore('cookies', 'cookie');
  const barriereScore = getPillarScore('accessibility', 'barrierefreiheit');

  const tabs: GaugeTab[] = [
    { key: 'gesamt', label: 'Gesamt', score: gesamtScore },
    { key: 'dsgvo', label: 'DSGVO', score: dsgvoScore },
    { key: 'cookie', label: 'Cookie', score: cookieScore },
    { key: 'barriere', label: 'Barriere', score: barriereScore },
    { key: 'rechtstexte', label: 'Rechtstexte', score: rechtstexteScore },
  ];

  const currentTab = tabs.find((t) => t.key === activeTab) ?? tabs[0];
  const targetScore = currentTab.score;

  useEffect(() => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    const start = animatedScore;
    const end = targetScore;
    const duration = 900;
    const startTime = performance.now();
    const animate = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(start + (end - start) * eased);
      setAnimatedScore(current);
      if (progress < 1) animFrameRef.current = requestAnimationFrame(animate);
    };
    animFrameRef.current = requestAnimationFrame(animate);
    return () => { if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current); };
  }, [targetScore]);

  const dashOffset = GAUGE_CIRCUMFERENCE - (animatedScore / 100) * GAUGE_CIRCUMFERENCE;
  const color = getGaugeColor(animatedScore);
  const scoreLabel = getScoreLabel(animatedScore);

  const textPrimary = isLight ? '#111827' : '#ffffff';
  const textSecondary = isLight ? '#6b7280' : '#a1a1aa';
  const textMuted = isLight ? '#9ca3af' : '#71717a';
  const trackColor = isLight ? '#e5e7eb' : '#27272a';
  const tabBg = isLight ? '#f3f4f6' : 'rgba(24,24,27,0.6)';
  const tabBorder = isLight ? '#e5e7eb' : 'rgba(63,63,70,0.6)';
  const tabInactiveColor = isLight ? '#6b7280' : '#71717a';
  const tabInactiveHover = isLight ? '#374151' : '#d4d4d8';
  const breakdownBg = isLight ? '#f9fafb' : 'transparent';

  const trendColor =
    scoreTrend == null ? tabInactiveColor :
    scoreTrend > 0 ? '#22c55e' :
    scoreTrend < 0 ? '#ef4444' : tabInactiveColor;

  return (
    <div className="stat-card-new flex flex-col h-full">
      {/* Greeting */}
      <div className="mb-4">
        <p className="text-sm" style={{ color: textSecondary }}>
          Willkommen zurück{userName ? `, ${userName.split(' ')[0]}` : ''}
        </p>
        <h2 className="text-xl font-bold mt-0.5" style={{ color: textPrimary }}>
          Ihr Compliance-Score
        </h2>
      </div>

      {/* Tabs */}
      <div
        className="flex gap-1 mb-5 rounded-xl p-1"
        style={{ background: tabBg, border: `1px solid ${tabBorder}` }}
      >
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className="flex-1 text-xs font-medium py-1.5 px-2 rounded-lg transition-all duration-200"
            style={
              activeTab === tab.key
                ? { background: 'rgba(249,115,22,0.15)', color: '#f97316', border: '1px solid rgba(249,115,22,0.3)' }
                : { color: tabInactiveColor }
            }
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Gauge SVG */}
      <div className="flex flex-col items-center">
        <div className="relative overflow-hidden" style={{ height: '125px' }}>
          <svg
            width="220"
            height="145"
            viewBox="0 0 220 145"
            className="overflow-visible"
            aria-label={`Compliance Score: ${animatedScore}%`}
          >
            <defs>
              <linearGradient id="gaugeGreen" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#16a34a" />
                <stop offset="100%" stopColor="#22c55e" />
              </linearGradient>
              <linearGradient id="gaugeLightGreen" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#65a30d" />
                <stop offset="100%" stopColor="#84cc16" />
              </linearGradient>
              <linearGradient id="gaugeYellow" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#d97706" />
                <stop offset="100%" stopColor="#eab308" />
              </linearGradient>
              <linearGradient id="gaugeRed" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#b91c1c" />
                <stop offset="100%" stopColor="#ef4444" />
              </linearGradient>
            </defs>

            {/* Background arc track */}
            <path
              d="M 20 110 A 90 90 0 0 1 200 110"
              fill="none"
              stroke={trackColor}
              strokeWidth="14"
              strokeLinecap="round"
            />

            {/* Subtle red band hint */}
            <path
              d="M 20 110 A 90 90 0 0 1 200 110"
              fill="none"
              stroke="#ef4444"
              strokeWidth="14"
              strokeLinecap="round"
              opacity={isLight ? '0.06' : '0.12'}
            />

            {/* Animated score arc */}
            <circle
              cx="110"
              cy="110"
              r={GAUGE_RADIUS}
              fill="none"
              stroke={`url(#${getGaugeGradientId(animatedScore)})`}
              strokeWidth="14"
              strokeLinecap="round"
              strokeDasharray={GAUGE_CIRCUMFERENCE}
              strokeDashoffset={dashOffset}
              transform="rotate(-180 110 110)"
              style={{ transition: 'stroke-dashoffset 0.05s linear, stroke 0.3s ease' }}
            />

            {/* Scale labels */}
            <text x="14" y="126" fill={textMuted} fontSize="10" textAnchor="middle">0</text>
            <text x="110" y="16" fill={textMuted} fontSize="10" textAnchor="middle">50</text>
            <text x="206" y="126" fill={textMuted} fontSize="10" textAnchor="middle">100</text>

            {/* Score number */}
            <text
              x="110"
              y="105"
              fill={textPrimary}
              fontSize="40"
              fontWeight="800"
              textAnchor="middle"
              style={{ fontVariantNumeric: 'tabular-nums' }}
            >
              {animatedScore}
            </text>
          </svg>
        </div>

        {/* Trend badge */}
        {scoreTrend != null && (
          <div className="flex items-center gap-1 text-xs font-semibold mt-1" style={{ color: trendColor }}>
            {scoreTrend > 0 ? <TrendingUp className="w-3.5 h-3.5" /> :
             scoreTrend < 0 ? <TrendingDown className="w-3.5 h-3.5" /> :
             <Minus className="w-3.5 h-3.5" />}
            <span>{scoreTrend > 0 ? `+${scoreTrend}` : scoreTrend} Pkt. diese Woche</span>
          </div>
        )}

        {/* Score label */}
        <div className="mt-2 flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
          <span className="text-sm font-medium" style={{ color }}>{scoreLabel}</span>
        </div>
      </div>

      {/* Mini score-breakdown row */}
      {analysisData && (
        <div
          className="mt-5 grid grid-cols-4 gap-2 rounded-xl p-3"
          style={{ background: breakdownBg, border: `1px solid ${tabBorder}` }}
        >
          {[
            { label: 'DSGVO', score: dsgvoScore },
            { label: 'Cookie', score: cookieScore },
            { label: 'Barriere', score: barriereScore },
            { label: 'Rechtstexte', score: rechtstexteScore },
          ].map((item) => (
            <div key={item.label} className="text-center">
              <div className="text-lg font-bold" style={{ color: getGaugeColor(item.score) }}>
                {item.score}
              </div>
              <div className="text-[10px] mt-0.5" style={{ color: textMuted }}>{item.label}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
