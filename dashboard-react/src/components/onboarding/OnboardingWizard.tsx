'use client';

import React, { useState, useEffect } from 'react';
import { Sparkles, Globe, CheckCircle, ArrowRight, Loader2 } from 'lucide-react';
import { analyzeWebsite } from '@/lib/api';
import { useDashboardStore } from '@/stores/dashboard';
import { useToast } from '@/components/ui/Toast';
import type { ComplianceIssue } from '@/types/api';

interface OnboardingWizardProps {
  onComplete: () => void;
}

export const OnboardingWizard: React.FC<OnboardingWizardProps> = ({ onComplete }) => {
  const [step, setStep] = useState(1);
  const [url, setUrl] = useState('');
  const [urlValid, setUrlValid] = useState(false);
  const [urlError, setUrlError] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [currentCheck, setCurrentCheck] = useState('');
  const [scanResult, setScanResult] = useState<any>(null);
  
  const { showToast } = useToast();
  const { setCurrentWebsite, setAnalysisData, updateMetrics } = useDashboardStore();

  // Validate URL in real-time with strict validation
  useEffect(() => {
    if (!url) {
      setUrlValid(false);
      setUrlError('');
      return;
    }

    try {
      let testUrl = url.trim();
      
      // Remove protocol if present for validation
      testUrl = testUrl.replace(/^https?:\/\//, '');
      
      // Remove trailing slashes and paths for validation
      testUrl = testUrl.split('/')[0];
      
      // Check basic format: must have at least one dot
      if (!testUrl.includes('.')) {
        setUrlValid(false);
        setUrlError('Bitte geben Sie eine gültige Domain ein (z.B. beispiel.de)');
        return;
      }
      
      // Split domain and TLD
      const parts = testUrl.split('.');
      
      // Must have at least 2 parts (domain.tld)
      if (parts.length < 2) {
        setUrlValid(false);
        setUrlError('Domain muss mindestens aus Name und Endung bestehen (z.B. beispiel.de)');
        return;
      }
      
      // Check each part is not empty
      if (parts.some(part => part.length === 0)) {
        setUrlValid(false);
        setUrlError('Ungültiges Domain-Format');
        return;
      }
      
      // Get TLD (last part)
      const tld = parts[parts.length - 1];
      
      // TLD must be at least 2 characters and only letters
      if (tld.length < 2 || !/^[a-zA-Z]{2,}$/.test(tld)) {
        setUrlValid(false);
        setUrlError(`Ungültige Domain-Endung: "${tld}". Bitte verwenden Sie eine gültige Endung wie .de, .com, .net`);
        return;
      }
      
      // Domain parts should only contain alphanumeric and hyphens
      const domainRegex = /^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$/;
      for (let i = 0; i < parts.length - 1; i++) {
        if (!domainRegex.test(parts[i])) {
          setUrlValid(false);
          setUrlError('Domain darf nur Buchstaben, Zahlen und Bindestriche enthalten');
          return;
        }
      }
      
      // Final check with URL constructor
      const fullUrl = 'https://' + testUrl;
      const urlObj = new URL(fullUrl);
      setUrlValid(!!urlObj.hostname);
      setUrlError('');
    } catch {
      setUrlValid(false);
      setUrlError('Ungültiges URL-Format');
    }
  }, [url]);

  const handleScan = async () => {
    if (!urlValid) return;

    setIsScanning(true);
    setStep(2);
    setScanProgress(0);

    // Simulate progress with realistic checks
    const checks = [
      { name: 'Prüfe SSL-Zertifikat...', duration: 1000 },
      { name: 'Scanne Impressum...', duration: 2000 },
      { name: 'Analysiere Cookies...', duration: 2500 },
      { name: 'Prüfe Datenschutzerklärung...', duration: 2000 },
      { name: 'Finalisiere Analyse...', duration: 1500 }
    ];

    let currentProgress = 0;
    for (const check of checks) {
      setCurrentCheck(check.name);
      await new Promise(resolve => setTimeout(resolve, check.duration));
      currentProgress += 100 / checks.length;
      setScanProgress(Math.min(currentProgress, 95));
    }

    try {
      // Normalize URL
      let normalizedUrl = url.trim();
      if (!normalizedUrl.startsWith('http://') && !normalizedUrl.startsWith('https://')) {
        normalizedUrl = 'https://' + normalizedUrl;
      }
      const urlObj = new URL(normalizedUrl);
      const domain = urlObj.hostname;

      // Use quick scan endpoint
      const result = await analyzeWebsite(domain);
      
      setScanProgress(100);
      setCurrentCheck('Analyse abgeschlossen!');
      
      // Store results
      setCurrentWebsite({
        id: Date.now().toString(),
        url: domain,
        name: domain,
        lastScan: new Date().toISOString(),
        complianceScore: result.compliance_score || 0,
        status: 'completed' as const
      });

      setAnalysisData(result);
      setScanResult(result);

      // Update metrics
      const criticalCount = Array.isArray(result.issues)
        ? result.issues.filter((issue: any) => issue.severity === 'critical').length
        : 0;

      updateMetrics({
        totalScore: result.compliance_score || 0,
        criticalIssues: criticalCount,
        websites: 1
      });

      // Move to results step
      setTimeout(() => {
        setStep(3);
      }, 800);

    } catch (error) {
      showToast('Scan fehlgeschlagen. Bitte versuchen Sie es erneut.', 'error');
      setIsScanning(false);
      setStep(1);
    }
  };

  const handleComplete = () => {
    // Mark onboarding as completed in localStorage
    localStorage.setItem('complyo_onboarding_completed', 'true');
    onComplete();
  };

  // Helper: Get compliance message based on score
  const getComplianceMessage = (score: number, criticalCount: number, warningCount: number, totalIssues: number) => {
    if (score >= 90) {
      return {
        title: "Großartig! Ihre Website ist compliant!",
        color: "text-green-700",
        bgColor: "bg-green-100",
        emoji: "🎉"
      };
    } else if (score >= 70) {
      const issueCount = criticalCount + warningCount;
      const issueText = issueCount === 1 ? 'Optimierungsmöglichkeit' : 'Optimierungsmöglichkeiten';
      return {
        title: `Größtenteils compliant! Es gibt ${issueCount} ${issueText}.`,
        color: "text-emerald-700",
        bgColor: "bg-emerald-100",
        emoji: "👍"
      };
    } else if (score >= 40) {
      const issueCount = totalIssues || (criticalCount + warningCount);
      const issueText = issueCount === 1 ? 'Problem' : 'Probleme';
      return {
        title: `Verbesserungsbedarf vorhanden. Ich habe ${issueCount} ${issueText} gefunden.`,
        color: "text-yellow-700",
        bgColor: "bg-yellow-100",
        emoji: "⚠️"
      };
    } else {
      // Score unter 40 = kritisch
      const issueCount = totalIssues || (criticalCount + warningCount);
      let title = "Erhebliche Compliance-Probleme gefunden.";
      
      if (criticalCount > 0) {
        const criticalText = criticalCount === 1 ? 'kritisches Issue muss' : 'kritische Issues müssen';
        title = `Erhebliche Compliance-Probleme gefunden. ${criticalCount} ${criticalText} sofort behoben werden.`;
      } else if (issueCount > 0) {
        const issueText = issueCount === 1 ? 'Problem muss' : 'Probleme müssen';
        title = `Erhebliche Compliance-Probleme gefunden. ${issueCount} ${issueText} behoben werden.`;
      }
      
      return {
        title,
        color: "text-red-700",
        bgColor: "bg-red-100",
        emoji: "🚨"
      };
    }
  };

  // Helper: Get top issues prioritized by severity
  const getTopIssues = (issues: ComplianceIssue[], limit: number = 5): ComplianceIssue[] => {
    if (!issues || issues.length === 0) return [];
    
    const severityOrder = { critical: 0, warning: 1, info: 2 };
    
    return [...issues]
      .sort((a, b) => {
        const severityDiff = severityOrder[a.severity] - severityOrder[b.severity];
        if (severityDiff !== 0) return severityDiff;
        return 0;
      })
      .slice(0, limit);
  };

  // Helper: Get category icon and label
  const getCategoryInfo = (category: string) => {
    const categoryMap: Record<string, { icon: string; label: string; color: string }> = {
      // Impressum
      impressum: { icon: '📋', label: 'Impressum', color: 'text-blue-700' },
      
      // Datenschutz
      datenschutz: { icon: '🔒', label: 'Datenschutz', color: 'text-purple-700' },
      privacy: { icon: '🔒', label: 'Datenschutz', color: 'text-purple-700' },
      
      // Cookies
      cookies: { icon: '🍪', label: 'Cookies', color: 'text-orange-700' },
      cookie: { icon: '🍪', label: 'Cookies', color: 'text-orange-700' },
      'cookie-compliance': { icon: '🍪', label: 'Cookies', color: 'text-orange-700' },
      
      // Sicherheit
      ssl: { icon: '🔐', label: 'Sicherheit', color: 'text-green-700' },
      security: { icon: '🔐', label: 'Sicherheit', color: 'text-green-700' },
      sicherheit: { icon: '🔐', label: 'Sicherheit', color: 'text-green-700' },
      
      // AGB
      agb: { icon: '📄', label: 'AGB', color: 'text-indigo-700' },
      terms: { icon: '📄', label: 'AGB', color: 'text-indigo-700' },
      
      // Barrierefreiheit
      barrierefreiheit: { icon: '♿', label: 'Barrierefreiheit', color: 'text-cyan-700' },
      accessibility: { icon: '♿', label: 'Barrierefreiheit', color: 'text-cyan-700' },
      
      // Kontaktdaten
      kontaktdaten: { icon: '📞', label: 'Kontaktdaten', color: 'text-teal-700' },
      contact: { icon: '📞', label: 'Kontaktdaten', color: 'text-teal-700' },
      
      // Social Media
      'social media': { icon: '📱', label: 'Social Media', color: 'text-pink-700' },
      social: { icon: '📱', label: 'Social Media', color: 'text-pink-700' },
    };
    
    return categoryMap[category.toLowerCase()] || { icon: '⚡', label: 'Sonstige', color: 'text-gray-700' };
  };

  // Helper: Group issues by category (using display name for grouping)
  const groupIssuesByCategory = (issues: ComplianceIssue[]) => {
    if (!issues || issues.length === 0) return [];
    
    const grouped = issues.reduce((acc, issue) => {
      const category = issue.category || 'sonstige';
      // Get the display name for grouping (so different backend categories with same display name get grouped together)
      const catInfo = getCategoryInfo(category);
      const displayKey = catInfo.label.toLowerCase();
      
      if (!acc[displayKey]) {
        acc[displayKey] = {
          originalCategory: category, // Keep one original category for reference
          displayInfo: catInfo,
          issues: []
        };
      }
      acc[displayKey].issues.push(issue);
      return acc;
    }, {} as Record<string, { originalCategory: string; displayInfo: any; issues: ComplianceIssue[] }>);
    
    return Object.entries(grouped).map(([displayKey, data]) => ({
      category: data.originalCategory,
      displayInfo: data.displayInfo,
      issues: data.issues,
      criticalCount: data.issues.filter(i => i.severity === 'critical').length,
      warningCount: data.issues.filter(i => i.severity === 'warning').length,
    }));
  };

  return (
    <div className="fixed inset-0 z-50 bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* Step 1: Welcome & URL Input */}
        {step === 1 && (
          <div className="bg-white rounded-2xl shadow-2xl p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-center mb-6">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
            </div>
            
            <h1 className="text-3xl font-bold text-gray-900 text-center mb-4">
              Willkommen bei Complyo! 👋
            </h1>
            
            <p className="text-lg text-gray-600 text-center mb-8">
              Ich bin Ihr KI-Compliance-Assistent. Lassen Sie mich Ihre Website auf DSGVO, Impressum und Cookie-Compliance prüfen.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Welche Website möchten Sie prüfen?
                </label>
                <div className="relative">
                  <Globe className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="beispiel-website.de"
                    className="w-full pl-12 pr-4 py-4 border-2 border-gray-300 rounded-xl focus:border-blue-600 focus:ring-4 focus:ring-blue-100 outline-none transition-all text-lg text-gray-900"
                    onKeyPress={(e) => e.key === 'Enter' && urlValid && handleScan()}
                  />
                  {urlValid && (
                    <CheckCircle className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-green-500" />
                  )}
                </div>
                {url && !urlValid && urlError && (
                  <p className="text-sm text-red-600 mt-2">
                    ✗ {urlError}
                  </p>
                )}
                {urlValid && (
                  <p className="text-sm text-green-600 mt-2">
                    ✓ Gut erkannt: {url.replace(/^https?:\/\//, '')}
                  </p>
                )}
              </div>

              <button
                onClick={handleScan}
                disabled={!urlValid}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-4 rounded-xl font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
              >
                <Sparkles className="w-5 h-5" />
                Website jetzt prüfen
                <ArrowRight className="w-5 h-5" />
              </button>

              <p className="text-center text-sm text-gray-500">
                ⚡ Erste Ergebnisse in 10-20 Sekunden
              </p>
            </div>
          </div>
        )}

        {/* Step 2: Scanning */}
        {step === 2 && (
          <div className="bg-white rounded-2xl shadow-2xl p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-center mb-6">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center animate-pulse">
                <Loader2 className="w-8 h-8 text-white animate-spin" />
              </div>
            </div>
            
            <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
              KI-Analyse läuft...
            </h2>
            
            <p className="text-gray-600 text-center mb-8">
              Ich prüfe Ihre Website auf Compliance-Probleme
            </p>

            {/* Progress Bar */}
            <div className="mb-6">
              <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-600 to-purple-600 transition-all duration-500 ease-out"
                  style={{ width: `${scanProgress}%` }}
                />
              </div>
              <p className="text-center text-sm text-gray-600 mt-2">
                {Math.round(scanProgress)}%
              </p>
            </div>

            {/* Current Check */}
            <div className="bg-blue-50 rounded-lg p-4 mb-6">
              <p className="text-blue-900 font-medium flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                {currentCheck}
              </p>
            </div>

            {/* Check list */}
            <div className="space-y-2">
              {[
                { name: 'SSL-Zertifikat', done: scanProgress > 20 },
                { name: 'Impressum', done: scanProgress > 40 },
                { name: 'Cookies', done: scanProgress > 60 },
                { name: 'Datenschutz', done: scanProgress > 80 }
              ].map((check, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  {check.done ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
                  )}
                  <span className={`text-sm ${check.done ? 'text-gray-900 font-medium' : 'text-gray-500'}`}>
                    {check.name}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Results */}
        {step === 3 && scanResult && (() => {
          const totalIssues = (scanResult.issues || []).length;
          const complianceMsg = getComplianceMessage(
            scanResult.compliance_score || 0,
            scanResult.critical_issues || 0,
            scanResult.warning_issues || 0,
            totalIssues
          );
          const topIssues = getTopIssues(scanResult.issues || [], 5);
          const categorizedIssues = groupIssuesByCategory(scanResult.issues || []);

          return (
            <div className="bg-white rounded-2xl shadow-2xl p-8 animate-in fade-in slide-in-from-bottom-4 duration-500 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-center mb-6">
                <div className={`w-20 h-20 rounded-full flex items-center justify-center text-3xl font-bold ${complianceMsg.bgColor} ${complianceMsg.color}`}>
                  {scanResult.compliance_score}
                </div>
              </div>
              
              <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
                Analyse abgeschlossen!
              </h2>
              
              <p className="text-gray-600 text-center mb-8">
                <span className="text-2xl mr-2">{complianceMsg.emoji}</span>
                {complianceMsg.title}
              </p>

              {/* Issues by Category */}
              {categorizedIssues.length > 0 && (
                <div className="mb-6">
                  <h3 className="font-semibold text-gray-900 mb-3 text-lg">Gefundene Problembereiche:</h3>
                  <div className="grid grid-cols-1 gap-2">
                    {categorizedIssues.map((cat, idx) => {
                      const catInfo = cat.displayInfo;
                      return (
                        <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                          <div className="flex items-center gap-3">
                            <span className="text-2xl">{catInfo.icon}</span>
                            <div>
                              <p className={`font-medium ${catInfo.color}`}>{catInfo.label}</p>
                              <p className="text-sm text-gray-600">
                                {cat.criticalCount > 0 && <span className="text-red-600">{cat.criticalCount} kritisch</span>}
                                {cat.criticalCount > 0 && cat.warningCount > 0 && <span className="text-gray-400"> • </span>}
                                {cat.warningCount > 0 && <span className="text-yellow-600">{cat.warningCount} Warnung</span>}
                              </p>
                            </div>
                          </div>
                          <span className="text-gray-400 font-semibold">{cat.issues.length}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Top Issues */}
              {topIssues.length > 0 && (
                <div className="mb-8 space-y-3">
                  <h3 className="font-semibold text-gray-900 mb-3 text-lg">Wichtigste Probleme:</h3>
                  {topIssues.map((issue: ComplianceIssue, idx: number) => {
                    const severityColors = {
                      critical: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', badge: 'bg-red-100 text-red-700' },
                      warning: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-700', badge: 'bg-yellow-100 text-yellow-700' },
                      info: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', badge: 'bg-blue-100 text-blue-700' }
                    };
                    const colors = severityColors[issue.severity] || severityColors.info;
                    
                    return (
                      <div key={idx} className={`flex items-start gap-3 p-4 ${colors.bg} rounded-lg border ${colors.border}`}>
                        <span className={`${colors.text} font-bold text-lg`}>{idx + 1}</span>
                        <div className="flex-1">
                          <div className="flex items-start justify-between mb-1">
                            <p className="font-medium text-gray-900">{issue.title}</p>
                            <span className={`text-xs px-2 py-1 rounded-full ${colors.badge} font-semibold uppercase ml-2`}>
                              {issue.severity === 'critical' ? 'Kritisch' : issue.severity === 'warning' ? 'Warnung' : 'Info'}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 line-clamp-2">{issue.description}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* CTA */}
              <button
                onClick={handleComplete}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-4 rounded-xl font-semibold text-lg transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
              >
                <Sparkles className="w-5 h-5" />
                Jetzt Probleme beheben
                <ArrowRight className="w-5 h-5" />
              </button>

              <p className="text-center text-sm text-gray-500 mt-4">
                💡 Tiefere Analyse läuft im Hintergrund weiter...
              </p>
            </div>
          );
        })()}
      </div>
    </div>
  );
};

