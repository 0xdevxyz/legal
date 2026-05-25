import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { useAuth } from '@/contexts/AuthContext';

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
  const { user, accessToken } = useAuth();

  const { data, isLoading, error, refetch } = useQuery<DashboardMetrics>({
    queryKey: ['dashboard-metrics'],
    queryFn: async () => {
      const data = await apiClient.get<DashboardMetrics>('/api/v2/dashboard/metrics');
      return data;
    },
    enabled: !!user && !!accessToken,
    staleTime: Infinity,
    gcTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchInterval: false,
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

