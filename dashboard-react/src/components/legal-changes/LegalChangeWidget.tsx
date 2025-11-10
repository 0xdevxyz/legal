/**
 * Legal Change Monitoring Widget
 * Zeigt automatisch erkannte Gesetzesänderungen und deren Status
 */

import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle2, Clock, TrendingUp, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';

interface LegalChangeSummary {
  affected_changes: number;
  critical_changes: number;
  pending_fixes: number;
  next_deadline: {
    title: string | null;
    date: string | null;
  };
}

export default function LegalChangeWidget() {
  const router = useRouter();
  const [summary, setSummary] = useState<LegalChangeSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSummary();
  }, []);

  const loadSummary = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';
      const response = await fetch(`${API_URL}/api/legal-changes/dashboard/summary`, {
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setSummary(data);
      }
    } catch (error) {
      console.error('Failed to load legal changes:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <CardContent className="pt-6">
          <div className="flex items-center justify-center h-32">
            <div className="w-8 h-8 border-4 border-orange-500/30 border-t-orange-500 rounded-full animate-spin"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!summary) return null;

  const hasChanges = summary.affected_changes > 0;
  const hasCritical = summary.critical_changes > 0;

  return (
    <Card 
      className={`border-gray-700 backdrop-blur-sm transition-all duration-200 hover:shadow-lg ${
        hasCritical
          ? 'bg-gradient-to-br from-red-500/10 to-red-600/5 border-red-500/30 hover:border-red-500/50'
          : hasChanges
          ? 'bg-gradient-to-br from-orange-500/10 to-orange-600/5 border-orange-500/30 hover:border-orange-500/50'
          : 'bg-gray-800/50 hover:border-gray-600'
      }`}
    >
      <CardHeader>
        <CardTitle className="flex items-center justify-between text-white">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-orange-400" />
            <span>Gesetzesänderungen</span>
          </div>
          {hasCritical && (
            <Badge className="bg-red-500 text-white animate-pulse">
              Dringend!
            </Badge>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Kritischer Alert */}
        {hasCritical && (
          <div className="p-3 bg-red-500/20 border border-red-500/30 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-semibold text-red-300 text-sm">
                {summary.critical_changes} kritische Änderung{summary.critical_changes > 1 ? 'en' : ''}
              </h4>
              <p className="text-xs text-red-200 mt-1">
                Erfordert sofortige Aufmerksamkeit
              </p>
            </div>
          </div>
        )}

        {/* Statistics Grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-gray-700/50 rounded-lg border border-gray-600">
            <div className="flex items-center gap-2 mb-1">
              <AlertCircle className="w-4 h-4 text-orange-400" />
              <span className="text-xs text-gray-400">Betroffene Änderungen</span>
            </div>
            <p className="text-2xl font-bold text-white">{summary.affected_changes}</p>
          </div>

          <div className="p-3 bg-gray-700/50 rounded-lg border border-gray-600">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-blue-400" />
              <span className="text-xs text-gray-400">Ausstehende Fixes</span>
            </div>
            <p className="text-2xl font-bold text-white">{summary.pending_fixes}</p>
          </div>
        </div>

        {/* Next Deadline */}
        {summary.next_deadline.title && (
          <div className="p-3 bg-gray-700/30 rounded-lg border border-gray-600">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle2 className="w-4 h-4 text-green-400" />
              <span className="text-xs font-medium text-gray-300">Nächste Deadline</span>
            </div>
            <h4 className="font-semibold text-white text-sm mb-1">
              {summary.next_deadline.title}
            </h4>
            <p className="text-xs text-gray-400">
              {new Date(summary.next_deadline.date!).toLocaleDateString('de-DE', {
                day: '2-digit',
                month: 'long',
                year: 'numeric'
              })}
            </p>
          </div>
        )}

        {/* No Changes Message */}
        {!hasChanges && (
          <div className="text-center py-4">
            <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto mb-2 opacity-50" />
            <p className="text-sm text-gray-400">
              Keine ausstehenden Gesetzesänderungen
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Sie sind auf dem aktuellen Stand! ✓
            </p>
          </div>
        )}

        {/* Action Button */}
        <Button
          onClick={() => router.push('/legal-changes')}
          className={`w-full ${
            hasCritical
              ? 'bg-red-500 hover:bg-red-600'
              : hasChanges
              ? 'bg-orange-500 hover:bg-orange-600'
              : 'bg-gray-700 hover:bg-gray-600'
          } transition-all`}
        >
          {hasChanges ? 'Änderungen ansehen' : 'Übersicht öffnen'}
          <ChevronRight className="w-4 h-4 ml-2" />
        </Button>

        {/* Info Note */}
        <p className="text-xs text-gray-500 text-center">
          KI-basierte automatische Erkennung von Gesetzesänderungen
        </p>
      </CardContent>
    </Card>
  );
}

