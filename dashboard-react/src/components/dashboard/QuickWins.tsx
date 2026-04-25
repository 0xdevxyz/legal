'use client';

import React, { useEffect, useState } from 'react';
import { Clock } from 'lucide-react';

interface QuickWin {
  id: string;
  title: string;
  category: string;
  estimated_minutes: number;
  pillarId: string;
}

interface QuickWinsProps {
  websiteId?: number;
  issues?: any[];
  onNavigateToPillar?: (pillarId: string) => void;
}

const categoryToPillar = (category: string): string => {
  const c = category.toLowerCase();
  if (c.includes('barrierefreiheit') || c.includes('accessibility') || c.includes('wcag')) return 'accessibility';
  if (c.includes('datenschutz') || c.includes('dsgvo') || c.includes('gdpr') || c.includes('privacy')) return 'gdpr';
  if (c.includes('cookie') || c.includes('consent') || c.includes('tracking')) return 'cookies';
  return 'legal';
};

const estimateEffort = (category: string): number => {
  const effortMap: Record<string, number> = {
    'impressum': 15,
    'datenschutz': 20,
    'ssl': 30,
    'cookies': 45,
    'agb': 25,
    'barrierefreiheit': 60
  };
  return effortMap[category] || 30;
};

export default function QuickWins({ issues = [], onNavigateToPillar }: QuickWinsProps) {
  const [quickWins, setQuickWins] = useState<QuickWin[]>([]);

  useEffect(() => {
    if (issues.length > 0) {
      const wins = issues
        .filter(issue => {
          const effort = estimateEffort(issue.category);
          const severity = issue.severity;
          return effort <= 30 && (severity === 'critical' || severity === 'warning');
        })
        .map(issue => ({
          id: issue.id,
          title: issue.title,
          category: issue.category,
          estimated_minutes: estimateEffort(issue.category),
          pillarId: categoryToPillar(issue.category)
        }))
        .slice(0, 5);
      setQuickWins(wins);
    }
  }, [issues]);

  if (quickWins.length === 0) return null;

  const totalMinutes = quickWins.reduce((sum, w) => sum + w.estimated_minutes, 0);

  return (
    <div className="flex items-center gap-3 px-4 py-3 bg-zinc-800/50 rounded-xl border border-zinc-700/50 mb-4">
      <Clock className="w-4 h-4 text-yellow-400 flex-shrink-0" />
      <span className="text-sm text-zinc-300">
        <span className="text-yellow-400 font-semibold">{quickWins.length} schnell behebbare Problem{quickWins.length !== 1 ? 'e' : ''}</span>
        {' — '}Geschätzter Aufwand:
        <span className="text-white font-semibold ml-1">
          {totalMinutes < 60
            ? `ca. ${totalMinutes} Minuten`
            : `ca. ${Math.round(totalMinutes / 60 * 10) / 10} Stunden`}
        </span>
      </span>
    </div>
  );
}
