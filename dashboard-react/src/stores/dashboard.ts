import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { DashboardState, Website } from '@/types/dashboard';
import { ComplianceAnalysis, LegalNews, ComplianceIssue } from '@/types/api';

interface DashboardStore extends DashboardState {
  // Actions
  setCurrentWebsite: (website: Website) => void;
  setAnalysisData: (data: ComplianceAnalysis) => void;
  setLegalNews: (news: LegalNews[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  updateMetrics: (metrics: Partial<DashboardState['metrics']>) => void;

  // Computed
  getCriticalIssues: () => number;
  getComplianceScore: () => number;
}

export const useDashboardStore = create<DashboardStore>()(
  subscribeWithSelector((set, get) => ({
    // ✅ Initial state ohne hardcodierte Daten
    currentWebsite: null, // Wird durch API geladen
    metrics: {
      totalScore: 0,
      websites: 0,
      criticalIssues: 0,
      scansAvailable: 100,
      scansUsed: 0
    },
    analysisData: null,
    legalNews: [],
    complianceTrends: [],
    isLoading: true, // Initial loading state
    error: null,

    // Actions
    setCurrentWebsite: (website) => set({ currentWebsite: website }),

    setAnalysisData: (data) => set({
      analysisData: data,
      metrics: {
        ...get().metrics,
        totalScore: data.compliance_score,
        criticalIssues: data.critical_issues
      }
    }),

    setLegalNews: (news) => set({ legalNews: news }),

    setLoading: (loading) => set({ isLoading: loading }),

    setError: (error) => set({ error }),

    updateMetrics: (metrics) => set((state) => ({
      metrics: { ...state.metrics, ...metrics }
    })),

    // Computed values
    getCriticalIssues: () => {
      const { analysisData } = get();
      if (!analysisData) return 0;

      return analysisData?.issues.filter(
        issue => issue.severity === 'critical'
      ).length || 0;
    },

    getComplianceScore: () => {
      const { analysisData, metrics } = get();
      return analysisData?.compliance_score || metrics.totalScore;
    }
  }))
);

// Selectors for better performance
export const selectCurrentWebsite = (state: DashboardStore) => state.currentWebsite;
export const selectMetrics = (state: DashboardStore) => state.metrics;
export const selectAnalysisData = (state: DashboardStore) => state.analysisData;
export const selectLegalNews = (state: DashboardStore) => state.legalNews;
export const selectIsLoading = (state: DashboardStore) => state.isLoading;
