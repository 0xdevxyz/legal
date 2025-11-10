'use client';

import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import apiClient from '@/lib/api';

interface ScoreHistoryEntry {
  date: string;
  score: number;
  critical_count: number;
  scan_type: string;
}

interface ScoreChartProps {
  websiteId: number;
  days?: number;
}

/**
 * ScoreChart - Zeigt Score-Verlauf über Zeit
 * Nutzt recharts Library für professionelle Visualisierung
 */
export default function ScoreChart({ websiteId, days = 30 }: ScoreChartProps) {
  const [history, setHistory] = useState<ScoreHistoryEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [trend, setTrend] = useState<'up' | 'down' | 'stable'>('stable');
  
  useEffect(() => {
    fetchScoreHistory();
  }, [websiteId, days]);
  
  const fetchScoreHistory = async () => {
    try {
      const response = await apiClient.get(
        `/api/v2/websites/${websiteId}/score-history?days=${days}`
      );
      
      if (response.data) {
        setHistory(response.data);
        calculateTrend(response.data);
      }
    } catch (error) {
      console.error('Fehler beim Laden des Score-Verlaufs:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const calculateTrend = (data: ScoreHistoryEntry[]) => {
    if (data.length < 2) {
      setTrend('stable');
      return;
    }
    
    const firstScore = data[0].score;
    const lastScore = data[data.length - 1].score;
    const diff = lastScore - firstScore;
    
    if (diff > 5) setTrend('up');
    else if (diff < -5) setTrend('down');
    else setTrend('stable');
  };
  
  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-xl p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-48 mb-4"></div>
          <div className="h-64 bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }
  
  if (history.length === 0) {
    return (
      <div className="bg-gray-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-bold text-white">Score-Verlauf</h3>
            <p className="text-gray-400 text-sm mt-1">
              Letzte {days} Tage
            </p>
          </div>
        </div>
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h4 className="text-lg font-semibold text-white mb-2">
            Noch keine Score-Historie vorhanden
          </h4>
          <p className="text-gray-400 mb-4 max-w-md mx-auto">
            Der Score-Verlauf wird aufgebaut, sobald Sie mehrere Scans durchführen. 
            Führen Sie regelmäßig Re-Scans durch, um die Entwicklung Ihrer Compliance zu verfolgen.
          </p>
          <div className="inline-flex items-center gap-2 text-sm text-blue-400">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>Tipp: Nach jedem Scan wird automatisch ein Eintrag erstellt</span>
          </div>
        </div>
      </div>
    );
  }
  
  // Formatiere Daten für Chart
  const chartData = history.map(entry => ({
    date: new Date(entry.date).toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit'
    }),
    Score: entry.score,
    'Kritische Fehler': entry.critical_count
  }));
  
  // Trend-Badge
  const trendBadge = {
    up: { icon: <TrendingUp className="w-5 h-5" />, color: 'text-green-500', text: 'Verbesserung' },
    down: { icon: <TrendingDown className="w-5 h-5" />, color: 'text-red-500', text: 'Verschlechterung' },
    stable: { icon: <Minus className="w-5 h-5" />, color: 'text-gray-400', text: 'Stabil' }
  }[trend];
  
  return (
    <div className="bg-gray-800 rounded-xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-white">Score-Verlauf</h3>
          <p className="text-gray-400 text-sm mt-1">
            Letzte {days} Tage
          </p>
        </div>
        <div className={`flex items-center gap-2 px-4 py-2 bg-gray-700 rounded-lg ${trendBadge.color}`}>
          {trendBadge.icon}
          <span className="font-semibold">{trendBadge.text}</span>
        </div>
      </div>
      
      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis 
            dataKey="date" 
            stroke="#9CA3AF"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#9CA3AF"
            style={{ fontSize: '12px' }}
            domain={[0, 100]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#fff'
            }}
          />
          <Legend 
            wrapperStyle={{ color: '#9CA3AF' }}
          />
          <Line
            type="monotone"
            dataKey="Score"
            stroke="#3B82F6"
            strokeWidth={3}
            dot={{ fill: '#3B82F6', r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="Kritische Fehler"
            stroke="#EF4444"
            strokeWidth={2}
            dot={{ fill: '#EF4444', r: 3 }}
            strokeDasharray="5 5"
          />
        </LineChart>
      </ResponsiveContainer>
      
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-700">
        <div>
          <p className="text-gray-400 text-sm">Aktueller Score</p>
          <p className="text-white text-2xl font-bold">
            {history[history.length - 1]?.score || 0}%
          </p>
        </div>
        <div>
          <p className="text-gray-400 text-sm">Bester Score</p>
          <p className="text-green-500 text-2xl font-bold">
            {Math.max(...history.map(h => h.score))}%
          </p>
        </div>
        <div>
          <p className="text-gray-400 text-sm">Verbesserung</p>
          <p className="text-blue-500 text-2xl font-bold">
            +{Math.max(0, history[history.length - 1]?.score - history[0]?.score || 0)}%
          </p>
        </div>
      </div>
    </div>
  );
}

