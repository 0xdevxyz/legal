'use client';

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle2, 
  Zap,
  Brain,
  Target,
  Award,
  ArrowRight
} from 'lucide-react';

interface ComplianceInsightsProps {
  analysisData: any;
  previousScans?: any[];
}

interface Insight {
  type: 'risk' | 'opportunity' | 'trend' | 'achievement';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  action?: string;
  icon: any;
  color: string;
}

export const ComplianceInsights: React.FC<ComplianceInsightsProps> = ({
  analysisData,
  previousScans = []
}) => {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [aiSummary, setAiSummary] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (analysisData) {
      generateInsights();
    }
  }, [analysisData, previousScans]);

  const generateInsights = () => {
    const generatedInsights: Insight[] = [];
    
    // Analyse 1: Haupt-Risiko identifizieren
    const criticalIssues = analysisData.issues?.filter((i: any) => i.severity === 'critical') || [];
    if (criticalIssues.length > 0) {
      const topRisk = criticalIssues.reduce((max: any, issue: any) => 
        (issue.risk_euro || 0) > (max.risk_euro || 0) ? issue : max
      , criticalIssues[0]);
      
      generatedInsights.push({
        type: 'risk',
        priority: 'high',
        title: 'Höchstes Risiko identifiziert',
        description: `${topRisk.title} - Potenzielles Risiko: ${new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(topRisk.risk_euro || 0)}`,
        action: 'Jetzt beheben',
        icon: AlertTriangle,
        color: 'red'
      });
    }
    
    // Analyse 2: Quick Wins identifizieren
    const autoFixableIssues = analysisData.issues?.filter((i: any) => i.auto_fixable) || [];
    if (autoFixableIssues.length > 0) {
      generatedInsights.push({
        type: 'opportunity',
        priority: 'medium',
        title: 'Quick Wins verfügbar',
        description: `${autoFixableIssues.length} Probleme können automatisch behoben werden`,
        action: 'Automatisch beheben',
        icon: Zap,
        color: 'yellow'
      });
    }
    
    // Analyse 3: Trend-Analyse (wenn Previous Scans vorhanden)
    if (previousScans.length > 0) {
      const previousScore = previousScans[0]?.compliance_score || 0;
      const currentScore = analysisData.compliance_score || 0;
      const scoreDiff = currentScore - previousScore;
      
      if (scoreDiff > 0) {
        generatedInsights.push({
          type: 'trend',
          priority: 'low',
          title: 'Verbesserung erkannt',
          description: `Ihr Score ist um ${scoreDiff.toFixed(0)} Punkte gestiegen`,
          icon: TrendingUp,
          color: 'green'
        });
      } else if (scoreDiff < -5) {
        generatedInsights.push({
          type: 'trend',
          priority: 'high',
          title: 'Score-Verschlechterung',
          description: `Ihr Score ist um ${Math.abs(scoreDiff).toFixed(0)} Punkte gefallen`,
          action: 'Probleme prüfen',
          icon: TrendingDown,
          color: 'red'
        });
      }
    }
    
    // Analyse 4: Achievements
    if (analysisData.compliance_score >= 85) {
      generatedInsights.push({
        type: 'achievement',
        priority: 'low',
        title: 'Exzellente Compliance',
        description: 'Ihre Website erfüllt hohe Compliance-Standards',
        icon: Award,
        color: 'purple'
      });
    }
    
    // Analyse 5: Kategorien-spezifische Insights
    const issuesByCategory = (analysisData.issues || []).reduce((acc: any, issue: any) => {
      acc[issue.category] = (acc[issue.category] || 0) + 1;
      return acc;
    }, {});
    
    const mostProblematicCategory = Object.entries(issuesByCategory)
      .sort((a: any, b: any) => b[1] - a[1])[0];
    
    if (mostProblematicCategory) {
      const categoryNames: Record<string, string> = {
        'accessibility': 'Barrierefreiheit',
        'datenschutz': 'Datenschutz',
        'impressum': 'Impressum',
        'cookies': 'Cookie-Compliance'
      };
      
      generatedInsights.push({
        type: 'risk',
        priority: 'medium',
        title: 'Schwerpunkt identifiziert',
        description: `${categoryNames[mostProblematicCategory[0]] || mostProblematicCategory[0]}: ${mostProblematicCategory[1]} Probleme`,
        action: 'Kategorie prüfen',
        icon: Target,
        color: 'blue'
      });
    }
    
    // AI-Zusammenfassung generieren
    generateAISummary(generatedInsights);
    
    setInsights(generatedInsights);
    setLoading(false);
  };

  const generateAISummary = (insights: Insight[]) => {
    const score = analysisData.compliance_score || 0;
    const criticalCount = analysisData.critical_issues || 0;
    const totalRisk = analysisData.total_risk_euro || 0;
    
    let summary = '';
    
    if (score >= 85) {
      summary = `Ihre Website zeigt eine starke Compliance-Performance mit einem Score von ${score}/100. `;
      if (criticalCount > 0) {
        summary += `Es verbleiben jedoch ${criticalCount} kritische Punkte, die zeitnah behoben werden sollten.`;
      } else {
        summary += `Exzellente Arbeit! Halten Sie diesen Standard aufrecht.`;
      }
    } else if (score >= 60) {
      summary = `Ihre Website hat einen akzeptablen Compliance-Score von ${score}/100, aber es gibt Verbesserungspotenzial. `;
      summary += `${criticalCount} kritische Probleme sollten priorisiert werden. Das geschätzte Gesamtrisiko beträgt ${new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(totalRisk)}.`;
    } else {
      summary = `Ihre Website benötigt dringend Compliance-Verbesserungen (Score: ${score}/100). `;
      summary += `Mit ${criticalCount} kritischen Problemen und einem Risiko von ${new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(totalRisk)} sollten Sie schnell handeln.`;
    }
    
    setAiSummary(summary);
  };

  if (loading) {
    return (
      <div className="glass-card rounded-xl p-6 border border-zinc-800/50">
        <div className="flex items-center gap-3 mb-4">
          <Brain className="w-6 h-6 text-purple-400 animate-pulse" />
          <h3 className="text-lg font-bold text-white">Compliance-Insights werden generiert...</h3>
        </div>
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-zinc-800 rounded w-3/4"></div>
          <div className="h-4 bg-zinc-800 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* AI-Zusammenfassung */}
      <div className="glass-card rounded-xl p-6 border border-purple-500/30 bg-gradient-to-br from-purple-500/10 to-pink-500/5">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-purple-500/20 rounded-xl">
            <Brain className="w-6 h-6 text-purple-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-white mb-2">
              KI-Zusammenfassung
            </h3>
            <p className="text-zinc-300 leading-relaxed">
              {aiSummary}
            </p>
          </div>
        </div>
      </div>

      {/* Insights Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.map((insight, index) => {
          const colorClasses = {
            red: {
              border: 'border-red-500/30',
              bg: 'from-red-500/10 to-red-600/5',
              icon: 'bg-red-500/20 text-red-400',
              badge: 'bg-red-500/20 text-red-300'
            },
            yellow: {
              border: 'border-yellow-500/30',
              bg: 'from-yellow-500/10 to-yellow-600/5',
              icon: 'bg-yellow-500/20 text-yellow-400',
              badge: 'bg-yellow-500/20 text-yellow-300'
            },
            green: {
              border: 'border-green-500/30',
              bg: 'from-green-500/10 to-green-600/5',
              icon: 'bg-green-500/20 text-green-400',
              badge: 'bg-green-500/20 text-green-300'
            },
            blue: {
              border: 'border-blue-500/30',
              bg: 'from-blue-500/10 to-blue-600/5',
              icon: 'bg-blue-500/20 text-blue-400',
              badge: 'bg-blue-500/20 text-blue-300'
            },
            purple: {
              border: 'border-purple-500/30',
              bg: 'from-purple-500/10 to-purple-600/5',
              icon: 'bg-purple-500/20 text-purple-400',
              badge: 'bg-purple-500/20 text-purple-300'
            }
          };

          const colors = colorClasses[insight.color as keyof typeof colorClasses];
          const Icon = insight.icon;

          return (
            <div
              key={index}
              className={`glass-card rounded-xl p-5 border ${colors.border} bg-gradient-to-br ${colors.bg} transition-all hover:scale-[1.02]`}
            >
              <div className="flex items-start gap-4">
                <div className={`p-2.5 rounded-lg ${colors.icon}`}>
                  <Icon className="w-5 h-5" />
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-semibold text-white">
                      {insight.title}
                    </h4>
                    {insight.priority === 'high' && (
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${colors.badge}`}>
                        Wichtig
                      </span>
                    )}
                  </div>
                  
                  <p className="text-sm text-zinc-400 mb-3">
                    {insight.description}
                  </p>
                  
                  {insight.action && (
                    <button className="flex items-center gap-1 text-sm font-medium text-zinc-300 hover:text-white transition-colors group">
                      {insight.action}
                      <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legende */}
      <div className="flex gap-3 flex-wrap text-xs text-zinc-500">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 bg-red-500/30 rounded"></div>
          <span>Risiko</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 bg-yellow-500/30 rounded"></div>
          <span>Chance</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 bg-green-500/30 rounded"></div>
          <span>Verbesserung</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 bg-purple-500/30 rounded"></div>
          <span>Erfolg</span>
        </div>
      </div>
    </div>
  );
};

