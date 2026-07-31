'use client';

import React, { useState } from 'react';
import { ClipboardCheck, ChevronDown, Info } from 'lucide-react';

/**
 * "Manuell prüfen" — Anleitungen für Kriterien, die keine automatische
 * Prüfung zuverlässig bewerten kann (Tastatur-Bedienung, AVV-Verträge, …).
 * Teil des Ehrlichkeits-Versprechens: erkennen ODER anleiten — nichts
 * bleibt stillschweigend offen.
 */

interface ManualCheck {
  pillar: string;
  id: string;
  title: string;
  anleitung: string;
}

const PILLAR_LABELS: Record<string, { label: string; badge: string }> = {
  accessibility: { label: 'Barrierefreiheit', badge: 'bg-blue-500/15 text-blue-300 border-blue-500/30' },
  gdpr: { label: 'Datenschutz', badge: 'bg-green-500/15 text-green-300 border-green-500/30' },
  legal: { label: 'Rechtstexte', badge: 'bg-purple-500/15 text-purple-300 border-purple-500/30' },
  cookies: { label: 'Cookies', badge: 'bg-amber-500/15 text-amber-300 border-amber-500/30' },
};

interface Props {
  checks: ManualCheck[];
  accessibilityNote?: string;
}

export const ManualChecksSection: React.FC<Props> = ({ checks, accessibilityNote }) => {
  const [open, setOpen] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!checks || checks.length === 0) return null;

  return (
    <div className="mt-6 rounded-xl border border-zinc-800/70 bg-zinc-900/40 overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 hover:bg-zinc-800/30 transition-colors"
      >
        <div className="flex items-center gap-3 text-left">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
            <ClipboardCheck className="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <p className="text-zinc-100 font-medium">Manuell prüfen ({checks.length})</p>
            <p className="text-zinc-400 text-sm">
              Diese Punkte kann keine automatische Prüfung zuverlässig bewerten —
              mit den Anleitungen prüfen Sie sie selbst in wenigen Minuten.
            </p>
          </div>
        </div>
        <ChevronDown
          className={`w-5 h-5 text-zinc-400 transition-transform ${open ? 'rotate-180' : ''}`}
        />
      </button>

      {open && (
        <div className="border-t border-zinc-800/50 p-4 space-y-3 bg-black/20">
          {accessibilityNote && (
            <div className="flex gap-2 p-3 rounded-lg bg-blue-500/5 border border-blue-500/20 text-sm text-zinc-300">
              <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
              <span>{accessibilityNote}</span>
            </div>
          )}

          {checks.map((check) => {
            const pillarInfo = PILLAR_LABELS[check.pillar] ?? {
              label: check.pillar,
              badge: 'bg-zinc-500/15 text-zinc-300 border-zinc-500/30',
            };
            const isExpanded = expandedId === check.id;
            return (
              <div
                key={check.id}
                className="rounded-lg border border-zinc-800/60 bg-zinc-900/40 overflow-hidden"
              >
                <button
                  type="button"
                  onClick={() => setExpandedId(isExpanded ? null : check.id)}
                  className="w-full flex items-center justify-between gap-3 p-3 hover:bg-zinc-800/30 transition-colors text-left"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span
                      className={`px-2 py-0.5 rounded text-xs border flex-shrink-0 ${pillarInfo.badge}`}
                    >
                      {pillarInfo.label}
                    </span>
                    <span className="text-sm text-zinc-200 truncate">{check.title}</span>
                  </div>
                  <ChevronDown
                    className={`w-4 h-4 text-zinc-500 flex-shrink-0 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                  />
                </button>
                {isExpanded && (
                  <div className="px-3 pb-3 text-sm text-zinc-400 whitespace-pre-line border-t border-zinc-800/40 pt-3">
                    {check.anleitung}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ManualChecksSection;
