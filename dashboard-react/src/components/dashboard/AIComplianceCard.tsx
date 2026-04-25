'use client';

import React, { useEffect, useState } from 'react';
import { Brain, Shield, FileText, TrendingUp, ArrowRight, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { useRouter } from 'next/navigation';
import { getAIComplianceStats } from '@/lib/ai-compliance-api';
import type { AIComplianceStats } from '@/types/ai-compliance';

interface AIComplianceCardProps {
  user?: {
    addons?: string[];
    plan_type?: string;
  };
}

export const AIComplianceCard: React.FC<AIComplianceCardProps> = ({ user }) => {
  const router = useRouter();
  const hasAddon = user?.addons?.includes('comploai_guard');
  const [aiStats, setAiStats] = useState<AIComplianceStats | null>(null);

  useEffect(() => {
    if (!hasAddon) return;
    getAIComplianceStats()
      .then(setAiStats)
      .catch(() => setAiStats(null));
  }, [hasAddon]);

  if (hasAddon) {
    return (
      <div className="glass-strong rounded-2xl p-5 sticky top-24 space-y-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-gradient-to-br from-purple-500/20 to-indigo-500/20 rounded-lg">
              <Brain className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">AI Compliance</h3>
              <p className="text-xs text-zinc-500">EU AI Act</p>
            </div>
          </div>
          <div className="px-2 py-0.5 bg-green-500/20 rounded-full text-xs font-medium text-green-400 border border-green-500/30">
            Aktiv
          </div>
        </div>

        <div className="space-y-3">
          <div className="glass-card p-3 rounded-xl">
            <div className="text-2xl font-bold text-white">
              {aiStats ? aiStats.total_systems : '—'}
            </div>
            <div className="text-xs text-zinc-400">AI-Systeme</div>
          </div>
          <div className="glass-card p-3 rounded-xl">
            <div className="text-2xl font-bold text-purple-400">
              {aiStats ? `${aiStats.average_compliance_score}%` : '—'}
            </div>
            <div className="text-xs text-zinc-400">Compliance</div>
          </div>
        </div>

        {aiStats && (aiStats.risk_distribution?.['high'] ?? 0) > 0 && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-3">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-red-400" />
              <span className="text-xs font-medium text-red-300">
                {aiStats.risk_distribution['high']} Hochrisiko-System{aiStats.risk_distribution['high'] > 1 ? 'e' : ''}
              </span>
            </div>
          </div>
        )}

        <button
          onClick={() => router.push('/ai-compliance')}
          className="w-full bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white font-semibold py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 transition-all text-sm shadow-lg"
        >
          Übersicht
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <div className="glass-strong rounded-2xl p-5 sticky top-24 hover:glass-effect transition-all">
      <div className="flex items-center gap-2 mb-4">
        <div className="p-2 bg-gradient-to-br from-purple-500/20 to-indigo-500/20 rounded-lg">
          <Brain className="w-5 h-5 text-purple-400" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white flex items-center gap-1">
            AI Compliance
            <Badge variant="info" className="text-xs">Add-on</Badge>
          </h3>
          <p className="text-xs text-zinc-500">EU AI Act</p>
        </div>
      </div>

      <div className="space-y-2.5 mb-4">
        <div className="flex items-start gap-2">
          <Shield className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
          <div>
            <div className="text-xs font-medium text-white">Risiko-Klassifizierung</div>
            <div className="text-xs text-zinc-500">High, Limited, Minimal</div>
          </div>
        </div>

        <div className="flex items-start gap-2">
          <FileText className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
          <div>
            <div className="text-xs font-medium text-white">Auto-Dokumentation</div>
            <div className="text-xs text-zinc-500">Reports & Analysen</div>
          </div>
        </div>

        <div className="flex items-start gap-2">
          <TrendingUp className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
          <div>
            <div className="text-xs font-medium text-white">Monitoring</div>
            <div className="text-xs text-zinc-500">Scans & Alerts</div>
          </div>
        </div>
      </div>

      <div className="flex items-baseline gap-1.5 mb-4">
        <div className="text-2xl font-bold text-white">99€</div>
        <div className="text-zinc-500 text-sm">/Monat</div>
      </div>

      <button
        onClick={() => router.push('/ai-compliance/upgrade')}
        className="w-full bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white font-semibold py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 shadow-lg transition-all text-sm"
      >
        <Sparkles className="w-4 h-4" />
        Add-on jetzt aktivieren
      </button>

      <div className="mt-3 text-center">
        <button
          onClick={() => router.push('/ai-compliance')}
          className="text-sm text-purple-400 hover:text-purple-300 font-medium underline"
        >
          Mehr über AI Compliance erfahren →
        </button>
      </div>
    </div>
  );
};
