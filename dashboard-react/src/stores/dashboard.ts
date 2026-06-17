import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { DashboardState, Website } from '@/types/dashboard';
import { ComplianceAnalysis, LegalNews, ComplianceIssue } from '@/types/api';

export interface RescanContext {
  legal_update_id: number;
  legal_update_title: string;
  focus_category?: 'cookies' | 'datenschutz' | 'impressum' | 'barrierefreiheit';
  triggered_at: string;
}

// Kleiner, quota-sicherer localStorage-Schreibhelfer (nur noch für winzige
// UI-State-Werte wie den Optimierungs-Lock genutzt — NICHT für Scan-Daten).
// Scan-Ergebnisse werden bewusst NICHT mehr im localStorage gecacht: Quelle ist
// die DB (scan_history via /api/scans/latest). Das vermeidet den früheren
// QuotaExceededError und hält die Persistenz an einer Stelle (DB).
function safeSetItem(key: string, value: string): boolean {
  try {
    if (typeof localStorage === 'undefined') return false;
    localStorage.setItem(key, value);
    return true;
  } catch {
    return false;
  }
}

interface DashboardStore extends DashboardState {
  // Actions
  setCurrentWebsite: (website: Website) => void;
  setAnalysisData: (data: ComplianceAnalysis) => void;
  setLegalNews: (news: LegalNews[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  updateMetrics: (metrics: Partial<DashboardState['metrics']>) => void;

  // Optimierungsmodus - Eine gelockte Seite für Optimierung
  lockedOptimizationUrl: string | null;
  isInOptimizationMode: boolean;
  lockForOptimization: (url: string) => void;
  restoreLockFromPrimary: (primaryUrl: string) => void;
  unlockOptimization: () => void;
  setOptimizationMode: (enabled: boolean) => void;

  // Rescan-Kontext von Legal News
  pendingRescanContext: RescanContext | null;
  setPendingRescanContext: (ctx: RescanContext | null) => void;

  // Computed
  getCriticalIssues: () => number;
  getComplianceScore: () => number;
}

export const useDashboardStore = create<DashboardStore>()(
  subscribeWithSelector((set, get) => ({
    currentWebsite: null,
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
    isLoading: true,
    error: null,

    lockedOptimizationUrl: null,
    isInOptimizationMode: false,

    pendingRescanContext: null,

    // Actions
    setCurrentWebsite: (website) => {
      // Keine localStorage-Persistenz mehr — die getrackte Website kommt aus der DB
      // (/api/v2/websites). In-Memory-State genügt für die laufende Session.
      return set({ currentWebsite: website });
    },

    setAnalysisData: (data) => {
      // Bewusst KEINE localStorage-Persistenz: Scan-Ergebnisse leben in der DB
      // (scan_history, geladen via /api/scans/latest). localStorage war nur ein
      // fragiler Cache (Quota). In-Memory-State für die laufende Session genügt.
      return set({
        analysisData: data,
        metrics: {
          ...get().metrics,
          totalScore: data?.compliance_score || 0,
          criticalIssues: data?.critical_issues || 0
        }
      });
    },

    setLegalNews: (news) => set({ legalNews: news }),

    setLoading: (loading) => set({ isLoading: loading }),

    setError: (error) => set({ error }),

    updateMetrics: (metrics) => set((state) => ({
      metrics: { ...state.metrics, ...metrics }
    })),

    // ✅ NEU: Optimierungsmodus Actions
    lockForOptimization: (url: string) => {
      set({ 
        lockedOptimizationUrl: url, 
        isInOptimizationMode: true 
      });
      if (typeof localStorage !== 'undefined') {
        safeSetItem('complyo_locked_optimization_url', url);
        safeSetItem('complyo_optimization_mode', 'true');
      }
    },

    restoreLockFromPrimary: (primaryUrl: string) => {
      const stored = typeof localStorage !== 'undefined'
        ? localStorage.getItem('complyo_locked_optimization_url')
        : null;
      const url = stored || primaryUrl;
      if (url) {
        set({ lockedOptimizationUrl: url, isInOptimizationMode: true });
        if (typeof localStorage !== 'undefined') {
          safeSetItem('complyo_locked_optimization_url', url);
          safeSetItem('complyo_optimization_mode', 'true');
        }
      }
    },

    unlockOptimization: () => {
      console.warn('⛔ unlockOptimization ist deaktiviert. Die Website-Verknüpfung ist dauerhaft und kann nur über den Support geändert werden: support@complyo.tech');
    },

    setOptimizationMode: (enabled: boolean) => {
      set({ isInOptimizationMode: enabled });
      if (typeof localStorage !== 'undefined') {
        if (enabled) {
          safeSetItem('complyo_optimization_mode', 'true');
        } else {
          localStorage.removeItem('complyo_optimization_mode');
        }
      }
    },

    setPendingRescanContext: (ctx) => set({ pendingRescanContext: ctx }),

    // Computed values
    getCriticalIssues: () => {
      const { analysisData } = get();
      if (!analysisData?.issues) return 0;

      return analysisData.issues.filter(
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
