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

// localStorage hat nur ~5 MB. Scan-Ergebnisse mit base64-Screenshots können weit
// größer sein → setItem wirft "QuotaExceededError: The quota has been exceeded."
// Diese Helper fangen das ab (App darf nie crashen) und speichern bei Bedarf eine
// abgespeckte Variante. Die vollständigen Daten bleiben im In-Memory-State.
function safeSetItem(key: string, value: string): boolean {
  try {
    if (typeof localStorage === 'undefined') return false;
    localStorage.setItem(key, value);
    return true;
  } catch {
    return false;
  }
}

// Schwere Felder pro Issue (base64-Bilder / HTML) für die Persistenz entfernen.
function slimIssueForStorage(issue: any): any {
  if (!issue || typeof issue !== 'object') return issue;
  const { screenshot_url, element_html, fix_code, ...rest } = issue;
  return rest;
}

function persistAnalysis(data: ComplianceAnalysis | null): void {
  if (typeof localStorage === 'undefined') return;
  if (!data) {
    try { localStorage.removeItem('complyo_last_analysis'); } catch { /* ignore */ }
    return;
  }
  const issues = Array.isArray((data as any).issues) ? (data as any).issues : [];
  // Mehrere Versuche, vom vollständigen bis zum stark reduzierten Payload:
  const candidates: Array<() => string> = [
    () => JSON.stringify(data),
    () => JSON.stringify({ ...data, issues: issues.map(slimIssueForStorage) }),
    () => JSON.stringify({ ...data, issues: issues.map(slimIssueForStorage), positive_checks: [], issue_groups: [], ungrouped_issues: [] }),
  ];
  for (const build of candidates) {
    let payload: string;
    try { payload = build(); } catch { continue; }
    if (safeSetItem('complyo_last_analysis', payload)) return;
  }
  // Selbst die schlanke Variante passt nicht → alten Stand entfernen, nicht crashen.
  try { localStorage.removeItem('complyo_last_analysis'); } catch { /* ignore */ }
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
      if (website) {
        safeSetItem('complyo_current_website', JSON.stringify(website));
      }
      return set({ currentWebsite: website });
    },

    setAnalysisData: (data) => {
      // Persistenz quota-sicher (volle Daten bleiben im In-Memory-State unten).
      persistAnalysis(data);
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
