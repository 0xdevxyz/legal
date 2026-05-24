'use client';

import React, { useEffect, useState } from 'react';
import { AlertTriangle, Info, ChevronRight, RefreshCw, Bell, BellOff } from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface EarlyWarning {
  id: number;
  title: string;
  summary: string;
  severity: 'info' | 'low' | 'medium' | 'high' | 'critical';
  law_category: string;
  source: string | null;
  url: string | null;
  published_at: string | null;
  detected_at: string | null;
  action_required: boolean;
  recommendation: string;
}

interface EarlyWarningFeedProps {
  maxItems?: number;
  showFilter?: boolean;
  compact?: boolean;
}

const SEVERITY_CONFIG: Record<string, { label: string; badge: string; icon: React.ReactNode }> = {
  info:     { label: 'Info',     badge: 'bg-gray-700 text-gray-200',     icon: <Info className="w-4 h-4 text-gray-400" /> },
  low:      { label: 'Niedrig',  badge: 'bg-blue-900/50 text-blue-300',   icon: <Info className="w-4 h-4 text-blue-400" /> },
  medium:   { label: 'Mittel',   badge: 'bg-yellow-900/50 text-yellow-300', icon: <AlertTriangle className="w-4 h-4 text-yellow-400" /> },
  high:     { label: 'Hoch',     badge: 'bg-orange-900/50 text-orange-300', icon: <AlertTriangle className="w-4 h-4 text-orange-400" /> },
  critical: { label: 'Kritisch', badge: 'bg-red-900/50 text-red-300',    icon: <AlertTriangle className="w-4 h-4 text-red-400" /> },
};

const LAW_LABELS: Record<string, string> = {
  dsgvo: 'DSGVO',
  ttdsg: 'TTDSG',
  uwg: 'UWG',
  bfsg: 'BFSG',
  agb: 'AGB',
  other: 'Allgemein',
};

const SEVERITY_ORDER = ['info', 'low', 'medium', 'high', 'critical'];

export const EarlyWarningFeed: React.FC<EarlyWarningFeedProps> = ({
  maxItems = 10,
  showFilter = true,
  compact = false,
}) => {
  const [warnings, setWarnings] = useState<EarlyWarning[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<string>('low');
  const [read, setRead] = useState<Set<number>>(new Set());

  useEffect(() => {
    loadWarnings();
  }, [severityFilter]);

  const loadWarnings = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ severity_min: severityFilter, limit: String(maxItems) });
      const res = await fetch(`/api/risk-radar/early-warnings?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setWarnings(data.warnings ?? []);
      }
    } catch (e) {
      console.error('EarlyWarningFeed load error:', e);
    } finally {
      setLoading(false);
    }
  };

  const markRead = (id: number) => setRead(prev => new Set([...prev, id]));

  const formatDate = (ds: string | null) => {
    if (!ds) return '';
    try {
      return new Date(ds).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
    } catch { return ''; }
  };

  const unreadCount = warnings.filter(w => !read.has(w.id)).length;
  const criticalCount = warnings.filter(w => w.severity === 'critical' || w.severity === 'high').length;

  return (
    <Card className="bg-gray-900 border border-gray-700 shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Bell className="w-5 h-5 text-yellow-400" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center font-bold">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">Abmahnfallen-Frühwarner</h3>
              <p className="text-xs text-gray-400">Automatisch aus Update-Pipeline — keine Rechtsberatung</p>
            </div>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={loadWarnings}
            disabled={loading}
            className="text-gray-400 hover:text-white"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        {criticalCount > 0 && (
          <div className="mt-3 bg-red-900/20 border border-red-700/40 rounded-lg px-3 py-2 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
            <span className="text-xs text-red-300">
              {criticalCount} dringende Warnung{criticalCount > 1 ? 'en' : ''} — Handlungsbedarf prüfen
            </span>
          </div>
        )}

        {showFilter && (
          <div className="flex gap-1 mt-3 flex-wrap">
            {SEVERITY_ORDER.map(s => (
              <button
                key={s}
                onClick={() => setSeverityFilter(s)}
                className={`text-xs px-2 py-1 rounded-full border transition-colors ${
                  severityFilter === s
                    ? 'bg-blue-600 border-blue-500 text-white'
                    : 'border-gray-600 text-gray-400 hover:text-white hover:border-gray-400'
                }`}
              >
                {SEVERITY_CONFIG[s]?.label}
              </button>
            ))}
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-2 pt-0">
        {loading ? (
          <div className="flex items-center justify-center py-8 text-gray-500">
            <RefreshCw className="w-5 h-5 animate-spin mr-2" />
            <span className="text-sm">Frühwarnungen werden geladen...</span>
          </div>
        ) : warnings.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-gray-500 gap-2">
            <BellOff className="w-8 h-8" />
            <span className="text-sm">Keine aktuellen Warnungen</span>
          </div>
        ) : (
          warnings.map(w => {
            const sc = SEVERITY_CONFIG[w.severity] ?? SEVERITY_CONFIG['info'];
            const isRead = read.has(w.id);
            return (
              <div
                key={w.id}
                className={`rounded-lg p-3 border transition-colors ${
                  isRead
                    ? 'bg-gray-800/40 border-gray-700/50 opacity-60'
                    : w.action_required
                    ? 'bg-red-900/10 border-red-700/40'
                    : 'bg-gray-800/60 border-gray-700'
                }`}
              >
                <div className="flex items-start gap-2">
                  <div className="mt-0.5 flex-shrink-0">{sc.icon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${sc.badge}`}>
                        {sc.label}
                      </span>
                      {w.law_category && w.law_category !== 'other' && (
                        <span className="text-xs text-gray-400 bg-gray-800 px-1.5 py-0.5 rounded">
                          {LAW_LABELS[w.law_category] ?? w.law_category.toUpperCase()}
                        </span>
                      )}
                      {w.action_required && (
                        <span className="text-xs text-red-300 font-semibold">Handlungsbedarf</span>
                      )}
                    </div>
                    <p className={`text-sm font-medium ${isRead ? 'text-gray-500' : 'text-white'} truncate`}>
                      {w.title}
                    </p>
                    {!compact && w.summary && (
                      <p className="text-xs text-gray-400 mt-1 line-clamp-2">{w.summary}</p>
                    )}
                    {!compact && w.recommendation && (
                      <p className="text-xs text-blue-300 mt-1">{w.recommendation}</p>
                    )}
                    <div className="flex items-center gap-3 mt-2">
                      {w.published_at && (
                        <span className="text-xs text-gray-500">{formatDate(w.published_at)}</span>
                      )}
                      {w.url && (
                        <a
                          href={w.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                          onClick={() => markRead(w.id)}
                        >
                          Quelle <ChevronRight className="w-3 h-3" />
                        </a>
                      )}
                      {!isRead && (
                        <button
                          onClick={() => markRead(w.id)}
                          className="text-xs text-gray-500 hover:text-gray-300 ml-auto"
                        >
                          Als gelesen markieren
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}

        <div className="pt-2 border-t border-gray-800">
          <p className="text-xs text-gray-500 flex items-start gap-1">
            <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />
            Frühwarnsystem — automatisch aus Gesetzgebungs-Pipeline. Kein Ersatz für Rechtsberatung.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default EarlyWarningFeed;
