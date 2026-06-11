'use client';

import React, { useEffect, useRef } from 'react';
import { TrendingUp, Globe, AlertTriangle, Sparkles, ArrowRight } from 'lucide-react';
import { useDashboardStore } from '@/stores/dashboard';
import { useDashboardMetrics } from '@/hooks/useMetrics';
import { useRouter } from 'next/navigation';
import { useTheme } from '@/contexts/ThemeContext';

function useAnimatedNumber(target: number, duration = 800): number {
  const [current, setCurrent] = React.useState(0);
  const raf = useRef<number | null>(null);
  const startRef = useRef(0);

  useEffect(() => {
    startRef.current = current;
    const end = target;
    const startTime = performance.now();

    const animate = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setCurrent(Math.round(startRef.current + (end - startRef.current) * eased));
      if (progress < 1) raf.current = requestAnimationFrame(animate);
    };

    raf.current = requestAnimationFrame(animate);
    return () => { if (raf.current) cancelAnimationFrame(raf.current); };
  }, [target, duration]);

  return current;
}

export const MetricsCards: React.FC = () => {
  const { updateMetrics } = useDashboardStore();
  const { metrics: apiMetrics, isLoading } = useDashboardMetrics();
  const router = useRouter();
  const { theme } = useTheme();
  const isLight = theme === 'light';
  const textPrimary = isLight ? '#111827' : '#ffffff';
  const textMuted = isLight ? '#6b7280' : '#71717a';

  useEffect(() => {
    if (apiMetrics) {
      updateMetrics({
        totalScore: apiMetrics.totalScore,
        websites: apiMetrics.websites,
        criticalIssues: apiMetrics.criticalIssues,
        scansAvailable: apiMetrics.scansAvailable,
        scansUsed: apiMetrics.scansUsed
      });
    }
  }, [apiMetrics, updateMetrics]);

  const { metrics } = useDashboardStore();

  const aiFixesUsed = apiMetrics?.aiFixesUsed ?? 0;
  const aiFixesMax = apiMetrics?.aiFixesMax ?? 1;
  const aiFixesUnlimited = aiFixesMax < 0; // -1 = unbegrenzt (bezahlte Pläne)
  const websitesMax = apiMetrics?.websitesMax ?? 1;

  const getScoreTrend = () => {
    const trend = apiMetrics?.scoreTrend;
    if (trend == null) return { text: 'Keine Vergleichsdaten', type: 'neutral' as const };
    if (trend > 0) return { text: `+${trend}% diese Woche`, type: 'positive' as const };
    if (trend < 0) return { text: `${trend}% diese Woche`, type: 'negative' as const };
    return { text: 'Unverändert', type: 'neutral' as const };
  };

  const getCriticalTrend = () => {
    const trend = apiMetrics?.criticalTrend;
    if (trend == null) return { text: 'Sofortige Beachtung', type: 'negative' as const };
    if (trend > 0) return { text: `+${trend} seit letzter Woche`, type: 'negative' as const };
    if (trend < 0) return { text: `${trend} seit letzter Woche`, type: 'positive' as const };
    return { text: 'Unverändert', type: 'neutral' as const };
  };

  const scoreTrend = getScoreTrend();
  const criticalTrend = getCriticalTrend();
  const aiLimitReached = !aiFixesUnlimited && aiFixesUsed >= aiFixesMax;
  const websiteLimitReached = metrics.websites >= websitesMax;

  const animScore = useAnimatedNumber(metrics.totalScore);
  const animCritical = useAnimatedNumber(metrics.criticalIssues);

  const cards = [
    {
      title: 'Gesamt-Score',
      value: animScore,
      suffix: '',
      sublabel: scoreTrend.text,
      sublabelType: scoreTrend.type,
      icon: TrendingUp,
      accent: '#22c55e',
      accentBg: 'rgba(34,197,94,0.12)',
    },
    {
      title: 'Websites',
      value: metrics.websites,
      suffix: `/${websitesMax}`,
      sublabel: websiteLimitReached ? 'Limit erreicht' : `${websitesMax - metrics.websites} verfügbar`,
      sublabelType: websiteLimitReached ? 'negative' as const : 'neutral' as const,
      icon: Globe,
      accent: '#38bdf8',
      accentBg: 'rgba(56,189,248,0.12)',
    },
    {
      title: 'KI-Optimierungen',
      value: aiFixesUnlimited ? '∞' : aiFixesUsed,
      suffix: aiFixesUnlimited ? '' : `/${aiFixesMax}`,
      sublabel: aiFixesUnlimited ? 'Unbegrenzt' : (aiLimitReached ? 'Upgrade für mehr' : `${aiFixesMax - aiFixesUsed} verfügbar`),
      sublabelType: aiFixesUnlimited ? 'positive' as const : (aiLimitReached ? 'negative' as const : 'positive' as const),
      icon: Sparkles,
      accent: '#a855f7',
      accentBg: 'rgba(168,85,247,0.12)',
      onSublabelClick: aiLimitReached ? () => router.push('/subscription') : undefined,
    },
    {
      title: 'Kritische Issues',
      value: animCritical,
      suffix: '',
      sublabel: criticalTrend.text,
      sublabelType: criticalTrend.type,
      icon: AlertTriangle,
      accent: '#ef4444',
      accentBg: 'rgba(239,68,68,0.12)',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 h-full content-start">
      {cards.map((card, i) => {
        const Icon = card.icon;
        const sublabelColor =
          card.sublabelType === 'positive' ? '#22c55e' :
          card.sublabelType === 'negative' ? '#ef4444' : '#71717a';

        return (
          <div key={i} className="stat-card-new flex items-center gap-4">
            <div
              className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: card.accentBg }}
            >
              <Icon className="w-5 h-5" style={{ color: card.accent }} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium mb-0.5" style={{ color: textMuted }}>{card.title}</p>
              <p className="text-2xl font-black leading-none" style={{ fontVariantNumeric: 'tabular-nums', color: textPrimary }}>
                {isLoading ? '—' : card.value}
                {!isLoading && card.suffix && (
                  <span className="text-base font-semibold" style={{ color: textMuted }}>{card.suffix}</span>
                )}
              </p>
              {card.onSublabelClick ? (
                <button
                  onClick={card.onSublabelClick}
                  className="flex items-center gap-1 text-xs font-medium mt-1 transition-opacity hover:opacity-80"
                  style={{ color: sublabelColor }}
                >
                  {card.sublabel}
                  <ArrowRight className="w-3 h-3" />
                </button>
              ) : (
                <p className="text-xs mt-1" style={{ color: sublabelColor }}>
                  {card.sublabel}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
