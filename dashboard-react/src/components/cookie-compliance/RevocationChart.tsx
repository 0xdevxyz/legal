'use client';

import React, { useState, useEffect } from 'react';
import { TrendingDown, TrendingUp, RotateCcw, Loader2, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { apiClient } from '@/lib/api-client';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface RevocationChartProps {
  siteId: string;
}

interface RevocationStats {
  total_consents: number;
  total_revocations: number;
  revocation_rate: number;
  daily_stats: Array<{
    date: string;
    consents: number;
    revocations: number;
    revocation_rate: number;
  }>;
}

const RevocationChart: React.FC<RevocationChartProps> = ({ siteId }) => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<RevocationStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState('30');

  useEffect(() => {
    loadStats();
  }, [siteId, period]);

  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.get(`/api/cookie-compliance/revocation-stats/${siteId}`, { days: period });
      setStats(data as RevocationStats);
    } catch (err) {
      setError('Daten konnten nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return `${d.getDate()}.${d.getMonth() + 1}.`;
  };

  const chartData = stats?.daily_stats?.map((d) => ({
    ...d,
    date: formatDate(d.date),
    revocation_rate_pct: Math.round(d.revocation_rate * 100),
  })) ?? [];

  const revocationRatePct = stats ? Math.round(stats.revocation_rate * 100) : 0;
  const isHighRate = revocationRatePct > 20;

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-48">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-48 gap-2 text-red-500">
          <AlertCircle className="w-5 h-5" />
          <span className="text-sm">{error}</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="flex items-center gap-2 text-base font-semibold">
          <RotateCcw className="w-5 h-5 text-orange-500" />
          Consent-Widerrufe
        </CardTitle>
        <div className="flex items-center gap-3">
          <Badge variant={isHighRate ? 'critical' : 'secondary'} className="text-xs">
            {isHighRate ? (
              <TrendingUp className="w-3 h-3 mr-1" />
            ) : (
              <TrendingDown className="w-3 h-3 mr-1" />
            )}
            {revocationRatePct}% Widerrufsrate
          </Badge>
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-28 h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">7 Tage</SelectItem>
              <SelectItem value="30">30 Tage</SelectItem>
              <SelectItem value="90">90 Tage</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* KPI Row */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="bg-gray-50 dark:bg-zinc-800/50 rounded-xl p-3">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats?.total_consents?.toLocaleString('de-DE') ?? 0}
            </div>
            <div className="text-xs text-gray-500 dark:text-zinc-400 mt-1">Einwilligungen</div>
          </div>
          <div className="bg-gray-50 dark:bg-zinc-800/50 rounded-xl p-3">
            <div className="text-2xl font-bold text-orange-500">
              {stats?.total_revocations?.toLocaleString('de-DE') ?? 0}
            </div>
            <div className="text-xs text-gray-500 dark:text-zinc-400 mt-1">Widerrufe</div>
          </div>
          <div className={`rounded-xl p-3 ${isHighRate ? 'bg-red-50 dark:bg-red-900/20' : 'bg-green-50 dark:bg-green-900/20'}`}>
            <div className={`text-2xl font-bold ${isHighRate ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}`}>
              {revocationRatePct}%
            </div>
            <div className="text-xs text-gray-500 dark:text-zinc-400 mt-1">Widerrufsrate</div>
          </div>
        </div>

        {/* Acceptance vs Revocation Bar Chart */}
        {chartData.length > 0 && (
          <div>
            <p className="text-xs font-medium text-gray-500 dark:text-zinc-400 mb-3">
              Einwilligungen vs. Widerrufe pro Tag
            </p>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} barGap={2}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(150,150,150,0.1)" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} />
                <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ fontSize: 12, borderRadius: 8 }}
                  formatter={(value: number, name: string) => [
                    value,
                    name === 'consents' ? 'Einwilligungen' : 'Widerrufe',
                  ]}
                />
                <Legend
                  formatter={(value) => (value === 'consents' ? 'Einwilligungen' : 'Widerrufe')}
                  wrapperStyle={{ fontSize: 12 }}
                />
                <Bar dataKey="consents" fill="#22c55e" radius={[4, 4, 0, 0]} />
                <Bar dataKey="revocations" fill="#f97316" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Revocation Rate Line Chart */}
        {chartData.length > 0 && (
          <div>
            <p className="text-xs font-medium text-gray-500 dark:text-zinc-400 mb-3">
              Widerrufsrate über Zeit (%)
            </p>
            <ResponsiveContainer width="100%" height={140}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(150,150,150,0.1)" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} />
                <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} unit="%" />
                <Tooltip
                  contentStyle={{ fontSize: 12, borderRadius: 8 }}
                  formatter={(value: number) => [`${value}%`, 'Widerrufsrate']}
                />
                <Line
                  type="monotone"
                  dataKey="revocation_rate_pct"
                  stroke="#f97316"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {chartData.length === 0 && (
          <div className="text-center py-8 text-sm text-gray-400 dark:text-zinc-500">
            Noch keine Widerrufs-Daten für diesen Zeitraum.
          </div>
        )}

        {isHighRate && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 text-xs">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>
              Hohe Widerrufsrate erkannt. Prüfen Sie, ob der Cookie-Banner klar verständlich ist
              und ob die Widerrufsmöglichkeit gut sichtbar platziert ist (DSGVO Art. 7 Abs. 3).
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default RevocationChart;
