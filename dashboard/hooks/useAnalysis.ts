import { useState, useEffect, useCallback } from 'react';
import { analysisService } from '../services/analysis';
import { ComplyoAccessibility } from '../services/accessibility-framework';

export function useAnalysis() {
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [a11y, setA11y] = useState<ComplyoAccessibility | null>(null);

  // Initialize accessibility framework
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const accessibility = ComplyoAccessibility.init({
        autoFix: true,
        announceChanges: true
      });
      setA11y(accessibility);
      
      // Store globally for testing
      window.ComplyoA11y = accessibility;
    }
  }, []);

  useEffect(() => {
    const lastAnalysis = analysisService.getLastAnalysis();
    if (lastAnalysis) {
      setCurrentAnalysis(lastAnalysis);
    }
    
    const trendData = analysisService.getTrendData();
    setAnalysisHistory(trendData);
  }, []);

  const analyzeWebsite = useCallback(async (url: string) => {
    setLoading(true);
    setError(null);
    
    // Announce analysis start to screen readers
    if (a11y) {
      a11y.announce('Website-Analyse wird gestartet', 'polite');
    }
    
    try {
      const result = await analysisService.analyzeWebsite(url);
      setCurrentAnalysis(result);
      
      const trendData = analysisService.getTrendData();
      setAnalysisHistory(trendData);
      
      // Announce completion with results
      if (a11y && result.compliance_score) {
        const scoreMessage = `Analyse abgeschlossen. Compliance-Score: ${result.compliance_score} von 100 Punkten`;
        a11y.announce(scoreMessage, 'polite');
      }
      
      return result;
    } catch (err: any) {
      const errorMessage = `Fehler bei der Website-Analyse: ${err.message || 'Unbekannter Fehler'}`;
      setError(errorMessage);
      if (a11y) {
        a11y.announceAlert(errorMessage);
      }
      throw err;
    } finally {
      setLoading(false);
    }
  }, [a11y]);

  return {
    currentAnalysis,
    analysisHistory,
    loading,
    error,
    analyzeWebsite,
    accessibility: a11y,
  };
}
