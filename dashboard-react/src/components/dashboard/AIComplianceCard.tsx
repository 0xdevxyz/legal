'use client';

import React from 'react';
import { Brain, Shield, FileText, TrendingUp, ArrowRight, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface AIComplianceCardProps {
  user?: {
    addons?: string[];
    plan_type?: string;
  };
}

interface AIStats {
  total_systems?: number;
  avg_score?: number;
  high_risk_count?: number;
  last_scan?: string;
}

export const AIComplianceCard: React.FC<AIComplianceCardProps> = ({ user }) => {
  const hasAddon = user?.addons?.includes('comploai_guard');
  
  // Mock stats for demo - would come from API in production
  const aiStats: AIStats = {
    total_systems: 3,
    avg_score: 78,
    high_risk_count: 1,
    last_scan: '2 Tage'
  };

  const handleActivate = () => {
    // Navigate to AI Compliance activation
    window.location.href = '/ai-compliance/upgrade';
  };

  const handleViewDashboard = () => {
    window.location.href = '/ai-compliance';
  };

  if (hasAddon) {
    // User has AI Compliance Add-on - show compact stats sidebar
    return (
      <div className="glass-strong rounded-2xl p-5 sticky top-24 space-y-4">
        {/* Header */}
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

        {/* Compact Stats */}
        <div className="space-y-3">
          <div className="glass-card p-3 rounded-xl">
            <div className="text-2xl font-bold text-white">{aiStats.total_systems}</div>
            <div className="text-xs text-zinc-400">AI-Systeme</div>
          </div>
          <div className="glass-card p-3 rounded-xl">
            <div className="text-2xl font-bold text-purple-400">{aiStats.avg_score}%</div>
            <div className="text-xs text-zinc-400">Compliance</div>
          </div>
        </div>

        {/* High Risk Alert - Compact */}
        {aiStats.high_risk_count && aiStats.high_risk_count > 0 && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-3">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-red-400" />
              <span className="text-xs font-medium text-red-300">
                {aiStats.high_risk_count} Hochrisiko-System{aiStats.high_risk_count > 1 ? 'e' : ''}
              </span>
            </div>
          </div>
        )}

        {/* Compact Action Button */}
        <button
          onClick={handleViewDashboard}
          className="w-full bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white font-semibold py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 transition-all text-sm shadow-lg"
        >
          Übersicht
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    );
  }

  // User doesn't have AI Compliance - show compact upgrade prompt
  return (
    <div className="glass-strong rounded-2xl p-5 sticky top-24 hover:glass-effect transition-all">
      {/* Compact Header */}
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

      {/* Compact Features */}
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

      {/* Compact Pricing */}
      <div className="flex items-baseline gap-1.5 mb-4">
        <div className="text-2xl font-bold text-white">99€</div>
        <div className="text-zinc-500 text-sm">/Monat</div>
      </div>

      {/* Compact CTA Button */}
      <button
        onClick={handleActivate}
        className="w-full bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white font-semibold py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 shadow-lg transition-all text-sm"
      >
        <Sparkles className="w-4 h-4" />
        Add-on jetzt aktivieren
      </button>

      {/* Info Link */}
      <div className="mt-3 text-center">
        <a
          href="/ai-compliance"
          className="text-sm text-purple-600 hover:text-purple-700 font-medium underline"
        >
          Mehr über AI Compliance erfahren →
        </a>
      </div>
    </div>
  );
};

