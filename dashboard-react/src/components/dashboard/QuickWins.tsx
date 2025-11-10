'use client';

import React, { useEffect, useState } from 'react';
import { Zap, Clock, TrendingUp, ChevronRight } from 'lucide-react';

interface QuickWin {
  id: string;
  title: string;
  category: string;
  estimated_minutes: number;
  impact_score: number;
  score_improvement: number;
}

interface QuickWinsProps {
  websiteId?: number;
  issues?: any[];
}

/**
 * QuickWins - Zeigt schnell umsetzbare Issues mit hohem Impact
 * "Low-hanging fruits" für User
 */
export default function QuickWins({ websiteId, issues = [] }: QuickWinsProps) {
  const [quickWins, setQuickWins] = useState<QuickWin[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  useEffect(() => {
    if (issues.length > 0) {
      calculateQuickWins(issues);
    }
  }, [issues]);
  
  const calculateQuickWins = (allIssues: any[]) => {
    // Filter für Quick Wins: < 30 Min Aufwand, mittlerer/hoher Impact
    const wins = allIssues
      .filter(issue => {
        const effort = estimateEffort(issue.category);
        const impact = estimateImpact(issue.severity);
        return effort <= 30 && impact >= 50;
      })
      .map(issue => ({
        id: issue.id,
        title: issue.title,
        category: issue.category,
        estimated_minutes: estimateEffort(issue.category),
        impact_score: estimateImpact(issue.severity),
        score_improvement: estimateScoreImprovement(issue.severity)
      }))
      .sort((a, b) => b.score_improvement - a.score_improvement)
      .slice(0, 3);  // Top 3
    
    setQuickWins(wins);
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
  
  const estimateImpact = (severity: string): number => {
    const impactMap: Record<string, number> = {
      'critical': 85,
      'warning': 60,
      'info': 30
    };
    return impactMap[severity] || 50;
  };
  
  const estimateScoreImprovement = (severity: string): number => {
    const improvementMap: Record<string, number> = {
      'critical': 15,
      'warning': 10,
      'info': 5
    };
    return improvementMap[severity] || 5;
  };
  
  if (quickWins.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 text-center">
        <Zap className="w-12 h-12 text-gray-600 mx-auto mb-3" />
        <p className="text-gray-400">
          Keine Quick Wins verfügbar. Super - Sie sind auf einem guten Weg!
        </p>
      </div>
    );
  }
  
  return (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-yellow-500/20">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="bg-yellow-500/20 p-2 rounded-lg">
          <Zap className="w-6 h-6 text-yellow-500" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-white">
            🎯 Quick Wins
          </h3>
          <p className="text-gray-400 text-sm">
            Schnell umgesetzt - maximaler Nutzen
          </p>
        </div>
      </div>
      
      {/* Quick Win Cards */}
      <div className="space-y-3">
        {quickWins.map((win, index) => (
          <div
            key={win.id}
            className="bg-gray-700/50 rounded-lg p-4 hover:bg-gray-700 transition cursor-pointer group"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-yellow-500 font-bold text-lg">
                    #{index + 1}
                  </span>
                  <h4 className="text-white font-semibold">
                    {win.title}
                  </h4>
                </div>
                
                <div className="flex items-center gap-4 text-sm">
                  {/* Zeit */}
                  <div className="flex items-center gap-1 text-gray-400">
                    <Clock className="w-4 h-4" />
                    <span>{win.estimated_minutes} Min</span>
                  </div>
                  
                  {/* Score-Verbesserung */}
                  <div className="flex items-center gap-1 text-green-400">
                    <TrendingUp className="w-4 h-4" />
                    <span>+{win.score_improvement}% Score</span>
                  </div>
                  
                  {/* Kategorie */}
                  <div className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">
                    {win.category}
                  </div>
                </div>
              </div>
              
              {/* Arrow */}
              <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-white transition" />
            </div>
          </div>
        ))}
      </div>
      
      {/* Summary */}
      <div className="mt-6 pt-4 border-t border-gray-700">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">
            Gesamt-Zeitaufwand:
          </span>
          <span className="text-white font-semibold">
            ca. {quickWins.reduce((sum, w) => sum + w.estimated_minutes, 0)} Minuten
          </span>
        </div>
        <div className="flex items-center justify-between text-sm mt-2">
          <span className="text-gray-400">
            Potenzielle Score-Verbesserung:
          </span>
          <span className="text-green-400 font-bold">
            +{quickWins.reduce((sum, w) => sum + w.score_improvement, 0)}% Compliance
          </span>
        </div>
      </div>
    </div>
  );
}

