interface AnalysisResult {
  id: string;
  url: string;
  compliance_score: number;
  risk_level: 'high' | 'medium' | 'low';
  estimated_risk_euro: string;
  findings: {
    impressum: string;
    datenschutzerklaerung: string;
    cookies: string;
    accessibility: string;
  };
  recommendations: string[];
  created_at: string;
  source: string;
}

interface TrendData {
  date: string;
  score: number;
  risk_euro: number;
}

class AnalysisService {
  private baseURL = '/api';
  
  async analyzeWebsite(url: string): Promise<AnalysisResult> {
    const response = await fetch(`${this.baseURL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ url }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Analyse fehlgeschlagen');
    }

    const result = await response.json();
    
    if (typeof window !== 'undefined') {
      localStorage.setItem('lastAnalysis', JSON.stringify(result));
      this.updateAnalysisHistory(result);
    }
    
    return result;
  }

  getLastAnalysis(): AnalysisResult | null {
    if (typeof window === 'undefined') return null;
    
    try {
      const analysisStr = localStorage.getItem('lastAnalysis');
      return analysisStr ? JSON.parse(analysisStr) : null;
    } catch {
      return null;
    }
  }

  private updateAnalysisHistory(analysis: AnalysisResult): void {
    if (typeof window === 'undefined') return;
    
    try {
      const historyStr = localStorage.getItem('analysisHistory');
      let history: AnalysisResult[] = historyStr ? JSON.parse(historyStr) : [];
      
      history.unshift(analysis);
      history = history.slice(0, 10);
      
      localStorage.setItem('analysisHistory', JSON.stringify(history));
    } catch (error) {
      console.error('Error updating analysis history:', error);
    }
  }

  getTrendData(): TrendData[] {
    if (typeof window === 'undefined') return [];
    
    try {
      const historyStr = localStorage.getItem('analysisHistory');
      const history: AnalysisResult[] = historyStr ? JSON.parse(historyStr) : [];
      
      return history.map(analysis => ({
        date: new Date(analysis.created_at).toLocaleDateString('de-DE'),
        score: analysis.compliance_score,
        risk_euro: this.parseRiskEuro(analysis.estimated_risk_euro)
      })).reverse();
    } catch {
      return [];
    }
  }

  private parseRiskEuro(riskStr: string): number {
    const match = riskStr.match(/(\d+)-(\d+)/);
    if (match) {
      const min = parseInt(match[1]);
      const max = parseInt(match[2]);
      return (min + max) / 2;
    }
    return 0;
  }
}

export const analysisService = new AnalysisService();
