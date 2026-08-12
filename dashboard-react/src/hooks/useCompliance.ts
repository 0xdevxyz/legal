import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { analyzeWebsite, startAIFix, bookExpertConsultation, getLegalNews, apiClient } from '@/lib/api';
import type { ComplianceAnalysis } from '@/types/api';

/**
 * @param scanTokenRef Fortschritts-Token des laufenden Scans. Der Scanner meldet
 *   darunter, welche Pruefung gerade laeuft (`/api/v2/analyze-progress/{token}`).
 *   Ohne Token gibt es keinen Fortschritt — genau deshalb zeigte der Rescan im
 *   Backoffice nur einen Spinner, waehrend der Scan auf der Startseite eine
 *   Live-Liste hatte. Als Ref, damit der Query-Key stabil bleibt und die
 *   bestehenden invalidateQueries-Aufrufe weiter greifen.
 */
export const useComplianceAnalysis = (
  url: string | null,
  scanTokenRef?: { current: string | null },
) => {
  return useQuery<ComplianceAnalysis>({
    queryKey: ['compliance-analysis', url],
    queryFn: async () => {

      // ✅ CRITICAL FIX: Strenge URL validation
      if (!url || typeof url !== 'string' || !url.trim()) {

        throw new Error('Invalid URL: URL must be a non-empty string');
      }

      const trimmedUrl = url.trim();

      try {
        const result = await analyzeWebsite(trimmedUrl, undefined, scanTokenRef?.current ?? undefined);

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
    mutationFn: async (payload: { scanId: string; categories?: string[] }) => {
      if (!payload.scanId) {
        throw new Error('Invalid payload: scanId is required');
      }

      return await startAIFix(payload.scanId, payload.categories);
    },
    onSuccess: (data, payload) => {

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

      return await bookExpertConsultation(issueId.trim());
    },
    onSuccess: (data, issueId) => {

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

      return await getLegalNews();
    },
    staleTime: 10 * 60 * 1000, // 10 Minuten
    retry: 2,
  });
};

// ✅ Letzte Scan-Ergebnisse laden (beim Mount)
export const useLatestScan = () => {
  return useQuery<ComplianceAnalysis | null>({
    queryKey: ['latest-scan'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/api/scans/latest');
        return response.data?.data || null;
      } catch (error: any) {
        // ✅ Graceful error handling
        if (error?.response?.status === 404) {
          // Noch keine Scans vorhanden
          return null;
        }
        return null;
      }
    },
    staleTime: 1 * 60 * 1000, // 1 Minute
    retry: false, // ✅ Kein Retry
  });
};

// ✅ Scan-Historie laden
export const useScanHistory = (limit: number = 10) => {
  return useQuery<any[]>({
    queryKey: ['scan-history', limit],
    queryFn: async () => {
      try {
        const response = await apiClient.get(`/api/scans/history?limit=${limit}`);
        return response.data?.data || [];
      } catch (error: any) {
        // ✅ Graceful error handling
        if (error?.response?.status === 404) {
          return [];
        }
        return [];
      }
    },
    staleTime: 2 * 60 * 1000, // 2 Minuten
    retry: false, // ✅ Kein Retry
  });
};

// ✅ Fix-Job erstellen
export const useCreateFixJob = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (payload: { 
      scan_id: string; 
      issue_id: string; 
      issue_data: any;
    }) => {
      
      try {
        const response = await apiClient.post('/api/fix-jobs', payload);
        return response.data?.data;
      } catch (error: any) {
        console.error('❌ Fix job creation failed:', {
          error,
          status: error?.response?.status,
          data: error?.response?.data,
          message: error?.message
        });
        throw error;
      }
    },
    onSuccess: () => {
      // Invalidate active jobs to refresh UI
      queryClient.invalidateQueries({ queryKey: ['active-fix-jobs'] });
    },
    onError: (error) => {
      console.error('❌ useCreateFixJob onError:', error);
    },
  });
};

// ✅ Fix-Job Status abfragen
export const useFixJobStatus = (jobId: string | null) => {
  return useQuery({
    queryKey: ['fix-job-status', jobId],
    queryFn: async () => {
      if (!jobId) return null;
      
      const response = await apiClient.get(`/api/fix-jobs/${jobId}/status`);
      return response.data?.data;
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
      // Poll alle 3 Sekunden wenn Job läuft, sonst nicht
      const data = query.state.data;
      if (!data) return false;
      return data.status === 'pending' || data.status === 'processing' ? 3000 : false;
    },
    staleTime: 0, // Immer frisch holen
  });
};

// ✅ Aktive Fix-Jobs laden
export const useActiveFixJobs = () => {
  return useQuery({
    queryKey: ['active-fix-jobs'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/api/fix-jobs/active');
        return response.data?.data || [];
      } catch (error: any) {
        // ✅ Graceful error handling - keine Spam-Logs
        if (error?.response?.status === 404) {
          // Endpoint existiert nicht - return leeres Array
          return [];
        }
        return [];
      }
    },
    // ✅ Nur pollen wenn Jobs existieren
    refetchInterval: (query) => {
      const jobs = query.state.data || [];
      const hasActiveJobs = jobs.length > 0 && jobs.some((j: any) => 
        ['pending', 'processing'].includes(j.status)
      );
      return hasActiveJobs ? 5000 : false;
    },
    staleTime: 0,
    retry: false, // ✅ Kein Retry bei Fehlern
  });
};
