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
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [currentCheck, setCurrentCheck] = useState('');
  const [scanResult, setScanResult] = useState<any>(null);
  
  const { showToast } = useToast();
  const { setCurrentWebsite, setAnalysisData, updateMetrics } = useDashboardStore();

  // Validate URL in real-time
  useEffect(() => {
    if (!url) {
      setUrlValid(false);
      return;
    }

    try {
      let testUrl = url.trim();
      if (!testUrl.startsWith('http://') && !testUrl.startsWith('https://')) {
        testUrl = 'https://' + testUrl;
      }
      const urlObj = new URL(testUrl);
      setUrlValid(!!urlObj.hostname);
    } catch {
      setUrlValid(false);
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
                {url && !urlValid && (
                  <p className="text-sm text-red-600 mt-2">
                    Bitte geben Sie eine gültige URL ein
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
        {step === 3 && scanResult && (
          <div className="bg-white rounded-2xl shadow-2xl p-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-center mb-6">
              <div className={`w-20 h-20 rounded-full flex items-center justify-center text-3xl font-bold ${
                scanResult.compliance_score >= 80 ? 'bg-green-100 text-green-700' :
                scanResult.compliance_score >= 60 ? 'bg-yellow-100 text-yellow-700' :
                'bg-red-100 text-red-700'
              }`}>
                {scanResult.compliance_score}
              </div>
            </div>
            
            <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
              Analyse abgeschlossen!
            </h2>
            
            <p className="text-gray-600 text-center mb-8">
              {scanResult.critical_issues > 0 ? (
                <>Ich habe <span className="font-bold text-red-600">{scanResult.critical_issues} kritische Probleme</span> gefunden, die Sie sofort beheben sollten.</>
              ) : scanResult.warning_issues > 0 ? (
                <>Ihre Website ist größtenteils compliant. Es gibt <span className="font-bold text-yellow-600">{scanResult.warning_issues} Verbesserungsvorschläge</span>.</>
              ) : (
                <>🎉 Großartig! Ihre Website ist compliant!</>
              )}
            </p>

            {/* Top Issues */}
            {scanResult.issues && scanResult.issues.length > 0 && (
              <div className="mb-8 space-y-3">
                <h3 className="font-semibold text-gray-900 mb-3">Top Probleme:</h3>
                {scanResult.issues
                  .filter((issue: ComplianceIssue) => issue.severity === 'critical')
                  .slice(0, 3)
                  .map((issue: ComplianceIssue, idx: number) => (
                    <div key={idx} className="flex items-start gap-3 p-3 bg-red-50 rounded-lg border border-red-200">
                      <span className="text-red-600 font-bold text-lg">{idx + 1}</span>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{issue.title}</p>
                        <p className="text-sm text-gray-600">{issue.description}</p>
                      </div>
                    </div>
                  ))}
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
        )}
      </div>
    </div>
  );
};

