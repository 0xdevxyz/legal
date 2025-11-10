import { useQuery, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api';

export interface DashboardMetrics {
  totalScore: number;
  websites: number;
  criticalIssues: number;
  scansAvailable: number;
  scansUsed: number;
  avgScore: number;
  totalRiskEuro: number;
  // Neue Felder für AI-Fix-Limits
  aiFixesUsed?: number;
  aiFixesMax?: number;
  websitesMax?: number;
  // Trend-Daten
  scoreTrend?: number | null;  // Prozentuale Änderung zum Vormonat
  criticalTrend?: number | null;  // Absolute Änderung kritischer Issues
}

export const useDashboardMetrics = () => {
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery<DashboardMetrics>({
    queryKey: ['dashboard-metrics'],
    queryFn: async () => {

      const response = await apiClient.get('/api/v2/dashboard/metrics');

      return response.data;
    },
    staleTime: Infinity, // Cache bleibt gültig bis manuell invalidiert
    gcTime: 10 * 60 * 1000, // 10 Minuten im Cache halten
    refetchOnWindowFocus: false, // Nicht bei jedem Focus neu laden
    refetchOnMount: false, // Nicht bei jedem Mount neu laden
    refetchOnReconnect: false, // Nicht bei Reconnect neu laden
    refetchInterval: false, // Kein automatisches Polling
    retry: 1,
  });

  const refreshMetrics = () => {

    queryClient.invalidateQueries({ queryKey: ['dashboard-metrics'] });
  };

  return {
    metrics: data,
    isLoading,
    error,
    refetch,
    refreshMetrics,
  };
};

