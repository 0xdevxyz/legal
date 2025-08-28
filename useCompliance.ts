import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { complianceApi } from '@/lib/api';
import { ComplianceAnalysis } from '@/types/api';

// ✅ URL NORMALIZATION - FIXED: Moved from component to hook level
function normalizeUrl(input: string): string {
  if (!input) return '';
  let url = input.trim();
  const lowerUrl = url.toLowerCase();
  
  // 1. Already complete URLs - keep as is
  if (lowerUrl.startsWith('https://') || lowerUrl.startsWith('http://')) {
    return url;
  }
  
  // 2. Localhost/IP addresses - use http
  if (lowerUrl.includes('localhost') || lowerUrl.match(/^\d+\.\d+\.\d+\.\d+/)) {
    return `http://${url}`;
  }
  
  // 3. www without protocol - add https
  if (lowerUrl.startsWith('www.')) {
    return `https://${url}`;
  }
  
  // 4. Plain domains - add https (FIXES 422 ERROR!)
  return `https://${url}`;
}

export function useComplianceAnalysis(url?: string) {
  return useQuery({
    queryKey: ['compliance', 'analysis', url],
    queryFn: () => complianceApi.analyzeWebsite(normalizeUrl(url!)), // ✅ FIXED!
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
      queryClient.invalidateQueries({ queryKey: ['compliance'] });
    },
  });
}

export function useBookExpert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: complianceApi.bookExpertConsultation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compliance'] });
    },
  });
}
