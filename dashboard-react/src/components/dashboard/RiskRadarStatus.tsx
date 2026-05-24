'use client';

import React, { useEffect, useState } from 'react';
import { Shield, AlertTriangle, TrendingDown, TrendingUp, Info, CheckCircle, RefreshCw } from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface RiskCategory {
  score: number;
  label: string;
  issues: string[];
}

interface TopRisk {
  category: string;
  label: string;
  score: number;
  top_issue: string | null;
  recommendation: string;
}

interface RiskRadarData {
  overall_risk_score: number;
  risk_level: string;
  categories: Record<string, RiskCategory>;
  top_risks: TopRisk[];
  last_updated: string | null;
  disclaimer: string;
}

interface RiskRadarStatusProps {
  score: number;
  domain?: string;
  lastScanDate?: string;
}

const RISK_LEVEL_CONFIG: Record<string, { label: string; color: string; bgColor: string; borderColor: string; icon: React.ReactNode }> = {
  minimal: {
    label: 'Minimales Risiko',
    color: 'text-green-400',
    bgColor: 'bg-green-900/30',
    borderColor: 'border-green-500',
    icon: <CheckCircle className="w-8 h-8 text-green-400" />,
  },
  niedrig: {
    label: 'Niedriges Risiko',
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-900/30',
    borderColor: 'border-emerald-500',
    icon: <TrendingDown className="w-8 h-8 text-emerald-400" />,
  },
  mittel: {
    label: 'Mittleres Risiko',
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-900/30',
    borderColor: 'border-yellow-500',
    icon: <AlertTriangle className="w-8 h-8 text-yellow-400" />,
  },
  hoch: {
    label: 'Hohes Risiko',
    color: 'text-orange-400',
    bgColor: 'bg-orange-900/30',
    borderColor: 'border-orange-500',
    icon: <AlertTriangle className="w-8 h-8 text-orange-400" />,
  },
  kritisch: {
    label: 'Kritisches Risiko',
    color: 'text-red-400',
    bgColor: 'bg-red-900/30',
    borderColor: 'border-red-500',
    icon: <Shield className="w-8 h-8 text-red-400" />,
  },
};

const CATEGORY_COLORS: Record<string, string> = {
  dsgvo: 'bg-blue-500',
  ttdsg: 'bg-purple-500',
  uwg: 'bg-orange-500',
  bfsg: 'bg-teal-500',
  agb: 'bg-pink-500',
};

export const RiskRadarStatus: React.FC<RiskRadarStatusProps> = ({
  score,
  domain,
  lastScanDate,
}) => {
  const [radarData, setRadarData] = useState<RiskRadarData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (domain) {
      loadRiskRadar();
    }
  }, [domain]);

  const loadRiskRadar = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (domain) params.set('domain', domain);
      const res = await fetch(`/api/risk-radar/score?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setRadarData(data);
      }
    } catch (e) {
      console.error('RiskRadar load error:', e);
    } finally {
      setLoading(false);
    }
  };

  const riskLevel = radarData?.risk_level ?? (score <= 20 ? 'niedrig' : score <= 50 ? 'mittel' : score <= 75 ? 'hoch' : 'kritisch');
  const config = RISK_LEVEL_CONFIG[riskLevel] ?? RISK_LEVEL_CONFIG['mittel'];

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return 'Noch nicht gescannt';
    try {
      const date = new Date(dateString);
      const diffH = Math.floor((Date.now() - date.getTime()) / 3_600_000);
      if (diffH < 24) return `Vor ${diffH}h`;
      const diffD = Math.floor(diffH / 24);
      if (diffD < 7) return `Vor ${diffD} Tag${diffD > 1 ? 'en' : ''}`;
      return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
    } catch {
      return 'Unbekannt';
    }
  };

  return (
    <Card className={`${config.bgColor} border-2 ${config.borderColor} shadow-lg mb-6`}>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-xl border ${config.borderColor} bg-black/20`}>
            {config.icon}
          </div>
          <div className="flex-1">
            <h3 className={`text-xl font-bold text-white flex items-center gap-2`}>
              Risiko-Radar
              <Badge variant="outline" className={`${config.color} border-current text-xs`}>
                {config.label}
              </Badge>
            </h3>
            <p className="text-gray-300 text-sm mt-1">
              Frühwarnsystem für Compliance-Risiken — kein Abmahnschutz-Versprechen
            </p>
          </div>
          {loading && <RefreshCw className="w-5 h-5 text-gray-400 animate-spin" />}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-gray-400 mb-1">Compliance-Score</div>
            <div className="text-3xl font-bold text-white">
              {score}<span className="text-lg text-gray-400">/100</span>
            </div>
          </div>
          <div className="text-right text-sm text-gray-400">
            <div>Letzter Scan</div>
            <div className="text-white">{formatDate(radarData?.last_updated ?? lastScanDate)}</div>
          </div>
        </div>

        <div className="w-full bg-gray-700 rounded-full h-3 overflow-hidden">
          <div
            className={`h-full transition-all duration-500 rounded-full ${score >= 80 ? 'bg-green-500' : score >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
            style={{ width: `${Math.min(score, 100)}%` }}
          />
        </div>

        {radarData?.categories && (
          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wide mb-3">Risiko-Kategorien</div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {Object.entries(radarData.categories).map(([key, cat]) => (
                <div key={key} className="bg-black/20 rounded-lg p-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <div className={`w-2 h-2 rounded-full ${CATEGORY_COLORS[key] ?? 'bg-gray-500'}`} />
                    <span className="text-xs text-gray-300 font-medium">{cat.label}</span>
                  </div>
                  <div className={`text-sm font-bold ${cat.score === 0 ? 'text-green-400' : cat.score < 30 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {cat.score === 0 ? 'OK' : `${cat.score} Risiko`}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {radarData?.top_risks && radarData.top_risks.length > 0 && (
          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wide mb-3">Top-Risiken</div>
            <ul className="space-y-2">
              {radarData.top_risks.map((risk, i) => (
                <li key={i} className="bg-black/20 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="text-xs font-semibold text-white">{risk.label}</span>
                      {risk.top_issue && (
                        <p className="text-xs text-gray-400 mt-0.5">{risk.top_issue}</p>
                      )}
                      <p className="text-xs text-blue-300 mt-1">{risk.recommendation}</p>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="bg-amber-900/20 border border-amber-700/40 rounded-lg p-3 flex gap-2">
          <Info className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-amber-200">
            {radarData?.disclaimer ?? 'Hinweis: KI-gestütztes Frühwarnsystem — kein Ersatz für individuelle Rechtsberatung.'}
          </p>
        </div>

        {score < 100 && (
          <Button
            size="sm"
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          >
            <TrendingUp className="w-4 h-4 mr-2" />
            Risiken mit KI reduzieren
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

export default RiskRadarStatus;
