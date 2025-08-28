import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { complianceApi } from '@/lib/api';
import { ComplianceAnalysis } from '@/types/api';

export function useComplianceAnalysis(url?: string) {
  return useQuery({
    queryKey: ['compliance', 'analysis', url],
    queryFn: () => complianceApi.analyzeWebsite(url!),
    enabled: !!url,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}

export function useDashboardData() {
  return useQuery({
    queryKey: ['dashboard', 'overview'],
    queryFn: complianceApi.getDashboardData,
    refetchInterval: 30000, // Auto-refresh every 30 seconds
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

export function useLegalNews() {
  return useQuery({
    queryKey: ['legal', 'news'],
    queryFn: complianceApi.getLegalNews,
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
}

export function useStartAIFix() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: complianceApi.startAIFix,
    onSuccess: () => {
      // Invalidate dashboard data to refresh
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['compliance'] });
    },
  });
}

export function useBookExpert() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: complianceApi.bookExpertConsultation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}
