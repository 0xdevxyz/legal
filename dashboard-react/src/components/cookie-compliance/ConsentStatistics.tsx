/**
 * Consent Statistics Component
 * Displays opt-in rates and consent analytics
 */

import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Users,
  MousePointerClick,
  PieChart as PieChartIcon,
  Info,
  Loader2,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface ConsentStatisticsProps {
  siteId: string;
}

const ConsentStatistics: React.FC<ConsentStatisticsProps> = ({ siteId }) => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<any>(null);
  const [period, setPeriod] = useState('30');
  
  useEffect(() => {
    loadStatistics();
  }, [siteId, period]);
  
  const loadStatistics = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `/api/cookie-compliance/stats/${siteId}?days=${period}`,
        { credentials: 'include' }
      );
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setStats(data);
        }
      }
    } catch (error) {
      console.error('Error loading statistics:', error);
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <Loader2 className="w-12 h-12 text-orange-500 animate-spin" />
        <p className="text-gray-400">Lade Statistiken...</p>
      </div>
    );
  }
  
  if (!stats || stats.summary?.total_impressions === 0) {
    return (
      <Card className="border-blue-500/30 bg-blue-500/10">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="font-semibold text-white mb-1">Keine Daten vorhanden</h4>
              <p className="text-sm text-gray-300">
                Sobald Besucher Ihre Website besuchen, werden hier Statistiken angezeigt.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  // Prepare chart data
  const dailyData = stats.daily_stats?.map((day: any) => ({
    date: new Date(day.date).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' }),
    accepted: day.accepted_all,
    partial: day.accepted_partial,
    rejected: day.rejected_all,
  })) || [];
  
  const categoryData = [
    { name: 'Statistik', value: stats.categories?.analytics?.total || 0, color: '#3B82F6' },
    { name: 'Marketing', value: stats.categories?.marketing?.total || 0, color: '#8B5CF6' },
    { name: 'Funktional', value: stats.categories?.functional?.total || 0, color: '#10B981' },
  ].filter(cat => cat.value > 0);
  
  const { summary } = stats;
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Consent-Statistiken</h3>
          <p className="text-sm text-gray-400 mt-1">Analyse Ihrer Cookie-Banner-Performance</p>
        </div>
        <Select value={period} onValueChange={setPeriod}>
          <SelectTrigger className="w-[180px] bg-gray-800 border-gray-700 text-white">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-gray-800 border-gray-700">
            <SelectItem value="7" className="text-white hover:bg-gray-700">Letzte 7 Tage</SelectItem>
            <SelectItem value="30" className="text-white hover:bg-gray-700">Letzte 30 Tage</SelectItem>
            <SelectItem value="90" className="text-white hover:bg-gray-700">Letzte 90 Tage</SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Impressions */}
        <Card className="border-gray-700 bg-gradient-to-br from-gray-800/80 to-gray-800/50 backdrop-blur-sm hover:shadow-lg hover:shadow-gray-900/50 transition-all">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-400">Gesamt-Impressions</p>
                <p className="text-3xl font-bold text-white">
                  {summary.total_impressions.toLocaleString('de-DE')}
                </p>
                <p className="text-xs text-gray-500">Banner angezeigt</p>
              </div>
              <div className="p-3 bg-gray-700/50 rounded-lg">
                <Users className="w-6 h-6 text-gray-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Acceptance Rate */}
        <Card className="border-green-500/30 bg-gradient-to-br from-green-500/20 to-green-600/5 backdrop-blur-sm hover:shadow-lg hover:shadow-green-900/30 transition-all">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-green-300">Akzeptiert</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-3xl font-bold text-green-400">
                    {summary.acceptance_rate.toFixed(1)}%
                  </p>
                  <TrendingUp className="w-4 h-4 text-green-400" />
                </div>
                <p className="text-xs text-green-300/70">
                  {summary.accepted_all.toLocaleString('de-DE')} Besucher
                </p>
              </div>
              <div className="p-3 bg-green-500/20 rounded-lg">
                <MousePointerClick className="w-6 h-6 text-green-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Partial Rate */}
        <Card className="border-blue-500/30 bg-gradient-to-br from-blue-500/20 to-blue-600/5 backdrop-blur-sm hover:shadow-lg hover:shadow-blue-900/30 transition-all">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-blue-300">Teilweise</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-3xl font-bold text-blue-400">
                    {summary.partial_rate.toFixed(1)}%
                  </p>
                </div>
                <p className="text-xs text-blue-300/70">
                  {summary.accepted_partial.toLocaleString('de-DE')} Besucher
                </p>
              </div>
              <div className="p-3 bg-blue-500/20 rounded-lg">
                <PieChartIcon className="w-6 h-6 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Rejection Rate */}
        <Card className="border-red-500/30 bg-gradient-to-br from-red-500/20 to-red-600/5 backdrop-blur-sm hover:shadow-lg hover:shadow-red-900/30 transition-all">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-red-300">Abgelehnt</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-3xl font-bold text-red-400">
                    {summary.rejection_rate.toFixed(1)}%
                  </p>
                  <TrendingDown className="w-4 h-4 text-red-400" />
                </div>
                <p className="text-xs text-red-300/70">
                  {summary.rejected_all.toLocaleString('de-DE')} Besucher
                </p>
              </div>
              <div className="p-3 bg-red-500/20 rounded-lg">
                <MousePointerClick className="w-6 h-6 text-red-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Daily Trend Chart */}
      <Card className="border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-white">Täglicher Verlauf</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={dailyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="date" 
                  fontSize={12} 
                  stroke="#9CA3AF"
                  tick={{ fill: '#9CA3AF' }}
                />
                <YAxis 
                  fontSize={12} 
                  stroke="#9CA3AF"
                  tick={{ fill: '#9CA3AF' }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F3F4F6'
                  }}
                />
                <Legend 
                  wrapperStyle={{ color: '#9CA3AF' }}
                />
                <Line
                  type="monotone"
                  dataKey="accepted"
                  stroke="#10B981"
                  strokeWidth={3}
                  name="Akzeptiert"
                  dot={{ fill: '#10B981', r: 4 }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="partial"
                  stroke="#3B82F6"
                  strokeWidth={3}
                  name="Teilweise"
                  dot={{ fill: '#3B82F6', r: 4 }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="rejected"
                  stroke="#EF4444"
                  strokeWidth={3}
                  name="Abgelehnt"
                  dot={{ fill: '#EF4444', r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
      
      {/* Category Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Rates */}
        <Card className="border-gray-700 bg-gray-800/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-white">Kategorien</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Analytics */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-200">Statistik</span>
                  <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/30">
                    {stats.categories?.analytics?.rate || 0}%
                  </Badge>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full transition-all duration-500"
                    style={{ width: `${stats.categories?.analytics?.rate || 0}%` }}
                  />
                </div>
              </div>
              
              {/* Marketing */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-200">Marketing</span>
                  <Badge className="bg-purple-500/20 text-purple-300 border-purple-500/30">
                    {stats.categories?.marketing?.rate || 0}%
                  </Badge>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-purple-500 rounded-full transition-all duration-500"
                    style={{ width: `${stats.categories?.marketing?.rate || 0}%` }}
                  />
                </div>
              </div>
              
              {/* Functional */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-200">Funktional</span>
                  <Badge className="bg-green-500/20 text-green-300 border-green-500/30">
                    {stats.categories?.functional?.rate || 0}%
                  </Badge>
                </div>
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 rounded-full transition-all duration-500"
                    style={{ width: `${stats.categories?.functional?.rate || 0}%` }}
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Pie Chart */}
        {categoryData.length > 0 && (
          <Card className="border-gray-700 bg-gray-800/50 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-white">Verteilung</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[240px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={categoryData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      labelLine={{ stroke: '#9CA3AF' }}
                    >
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1F2937', 
                        border: '1px solid #374151',
                        borderRadius: '8px',
                        color: '#F3F4F6'
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
      
      {/* Tips */}
      <Card className="border-orange-500/30 bg-gradient-to-r from-orange-500/10 to-orange-600/5">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-orange-400 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="font-semibold text-white mb-1">💡 Tipp zur Optimierung</h4>
              <p className="text-sm text-gray-300">
                Eine Opt-In-Rate über 70% gilt als sehr gut. Wenn Ihre Rate niedriger ist,
                versuchen Sie die Texte zu optimieren oder das Design anzupassen.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ConsentStatistics;
