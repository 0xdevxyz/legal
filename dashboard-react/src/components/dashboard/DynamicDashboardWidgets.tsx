'use client';

import React from 'react';
import { useDashboardStore } from '@/stores/dashboard';
import ScoreChart from './ScoreChart';
import QuickWins from './QuickWins';

/**
 * DynamicDashboardWidgets - Rendert ScoreChart & QuickWins dynamisch
 * basierend auf aktueller Website und Analysis-Daten
 * 
 * ✅ Angepasst für Single-Domain-View (ohne SelectedWebsiteContext)
 */
export default function DynamicDashboardWidgets() {
  const { currentWebsite, analysisData } = useDashboardStore();
  
  // Extrahiere Issues aus analysisData
  const currentIssues = analysisData?.issues || [];
  
  // Zeige nur wenn Website analysiert wurde
  if (!currentWebsite) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        <div className="bg-gray-800 rounded-xl p-8 text-center border border-dashed border-gray-700">
          <p className="text-gray-500">
            📊 Analysieren Sie eine Website, um den Score-Verlauf zu sehen
          </p>
        </div>
        <div className="bg-gray-800 rounded-xl p-8 text-center border border-dashed border-gray-700">
          <p className="text-gray-500">
            ⚡ Quick Wins werden angezeigt, sobald eine Analyse verfügbar ist
          </p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
      <div>
        <ScoreChart websiteId={parseInt(currentWebsite.id)} />
      </div>
      <div>
        <QuickWins websiteId={parseInt(currentWebsite.id)} issues={currentIssues} />
      </div>
    </div>
  );
}

