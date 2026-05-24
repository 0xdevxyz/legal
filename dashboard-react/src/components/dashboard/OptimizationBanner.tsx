'use client';

import React from 'react';
import { useDashboardMetrics } from '@/hooks/useMetrics';
import { useDashboardStore } from '@/stores/dashboard';
import { Sparkles, MessageSquare, ArrowRight } from 'lucide-react';

export default function OptimizationBanner() {
  const { metrics, isLoading } = useDashboardMetrics();
  const { analysisData } = useDashboardStore();

  if (isLoading) {
    return (
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-6 mb-6 animate-pulse">
        <div className="h-8 bg-white/20 rounded w-64"></div>
      </div>
    );
  }

  if (!analysisData) {
    return null;
  }

  const aiFixesUsed = metrics?.aiFixesUsed || 0;
  const aiFixesMax = metrics?.aiFixesMax || 1;
  const hasOptimizationsLeft = aiFixesUsed < aiFixesMax;

  const handleScrollToFirstCritical = () => {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('complyo:scroll-to-first-critical'));
    }
  };

  if (hasOptimizationsLeft) {
    return (
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-6 mb-6 shadow-lg">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <div className="bg-white/20 p-3 rounded-lg">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <div>
              <h3 className="text-white text-xl font-bold">
                Sie haben {aiFixesMax - aiFixesUsed} KI-Optimierung{aiFixesMax - aiFixesUsed !== 1 ? 'en' : ''} verfügbar!
              </h3>
              <p className="text-white/80 text-sm mt-1">
                Lassen Sie unsere KI Ihre Compliance-Probleme analysieren und Copy-Paste-ready Lösungen generieren.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="bg-white/20 px-4 py-2 rounded-lg">
              <span className="text-white font-bold text-2xl">{aiFixesMax - aiFixesUsed}</span>
              <span className="text-white/80 text-sm ml-2">/ {aiFixesMax}</span>
            </div>
            <button
              onClick={handleScrollToFirstCritical}
              className="flex items-center gap-2 bg-white text-blue-700 hover:bg-blue-50 px-5 py-2.5 rounded-lg font-semibold transition-all shadow-md whitespace-nowrap"
            >
              Jetzt optimieren
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-green-500 to-teal-600 rounded-xl p-6 mb-6 shadow-lg border-2 border-green-400">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="bg-white/20 p-3 rounded-lg">
            <MessageSquare className="w-8 h-8 text-white" />
          </div>
          <div>
            <h3 className="text-white text-xl font-bold">
              Ihre KI-Optimierung wurde genutzt
            </h3>
            <p className="text-white/80 text-sm mt-1">
              Für weitere Optimierungen und professionelle Umsetzung kontaktieren Sie unseren Expertenservice.
            </p>
          </div>
        </div>
        <button
          onClick={() => {
            const modal = document.getElementById('expert-service-modal');
            if (modal) {
              (modal as any).showModal?.();
            }
          }}
          className="bg-white text-green-600 px-6 py-3 rounded-lg font-semibold hover:bg-green-50 transition-all flex items-center gap-2"
        >
          <MessageSquare className="w-5 h-5" />
          Expertenservice kontaktieren
        </button>
      </div>
    </div>
  );
}
