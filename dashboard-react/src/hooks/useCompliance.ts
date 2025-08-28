import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { analyzeWebsite, startAIFix, bookExpertConsultation } from '@/lib/api';
import type { ComplianceAnalysis } from '@/types/api';

export const useComplianceAnalysis = (url: string | null) => {
  return useQuery<ComplianceAnalysis>({
    queryKey: ['compliance-analysis', url],
    queryFn: async () => {
      console.log('🔍 useComplianceAnalysis queryFn called with URL:', url, typeof url);
      
      // ✅ CRITICAL FIX: Strenge URL validation
      if (!url || typeof url !== 'string' || !url.trim()) {
        console.warn('🚫 useComplianceAnalysis: Invalid URL provided:', { url, type: typeof url });
        throw new Error('Invalid URL: URL must be a non-empty string');
      }

      const trimmedUrl = url.trim();
      console.log('🔍 Starting website analysis for:', trimmedUrl);

      try {
        const result = await analyzeWebsite(trimmedUrl);
        console.log('📥 Received analysis:', result);
        return result;
      } catch (error) {
        console.error('💥 Website analysis failed:', error);
        throw error;
      }
    },
    enabled: false, // disable autoexec
    retry: 2,
    retryDelay: 1000,
    staleTime: 5 * 60 * 1000, // 5 Minuten
  });
};

// ✅ AI Fix Hook
export const useStartAIFix = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (issueId: string) => {
      if (!issueId || !issueId.trim()) {
        throw new Error('Invalid issueId: must be a non-empty string');
      }
      
      console.log('🤖 Starting AI fix for issue:', issueId);
      return await startAIFix(issueId.trim());
    },
    onSuccess: (data, issueId) => {
      console.log('✅ AI fix started successfully for:', issueId);
      // Invalidate compliance analysis to refresh data
      queryClient.invalidateQueries({ queryKey: ['compliance-analysis'] });
    },
    onError: (error, issueId) => {
      console.error('💥 AI fix failed for:', issueId, error);
    },
  });
};

// ✅ Expert Booking Hook  
export const useBookExpert = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (issueId: string) => {
      if (!issueId || !issueId.trim()) {
        throw new Error('Invalid issueId: must be a non-empty string');
      }
      
      console.log('👨‍💼 Booking expert for issue:', issueId);
      return await bookExpertConsultation(issueId.trim());
    },
    onSuccess: (data, issueId) => {
      console.log('✅ Expert booked successfully for:', issueId);
      // Invalidate compliance analysis to refresh data
      queryClient.invalidateQueries({ queryKey: ['compliance-analysis'] });
    },
    onError: (error, issueId) => {
      console.error('💥 Expert booking failed for:', issueId, error);
    },
  });
};

// ✅ Dashboard Overview Hook (falls benötigt)
export const useDashboardOverview = () => {
  return useQuery({
    queryKey: ['dashboard-overview'],
    queryFn: async () => {
      // Hier würde der API-Call für Dashboard-Daten stehen
      console.log('📊 Fetching dashboard overview...');
      // return await getDashboardOverview();
      return null; // Placeholder
    },
    staleTime: 2 * 60 * 1000, // 2 Minuten
  });
};

// ✅ Legal News Hook (falls benötigt)
export const useLegalNews = () => {
  return useQuery({
    queryKey: ['legal-news'],
    queryFn: async () => {
      // Hier würde der API-Call für Legal News stehen
      console.log('📰 Fetching legal news...');
      // return await getLegalNews();
      return null; // Placeholder
    },
    staleTime: 10 * 60 * 1000, // 10 Minuten
  });
};
