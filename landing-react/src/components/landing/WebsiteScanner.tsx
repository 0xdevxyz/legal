'use client';

import React, { useState, useEffect } from 'react';
import { Shield, Cookie, FileText, Eye, AlertTriangle, CheckCircle, Search, TrendingUp, Euro } from 'lucide-react';
import { complianceApi } from '@/lib/api';

/**
 * WebsiteScanner - Hauptfeature auf der Landing Page
 * Ermöglicht Besuchern, ihre Website sofort zu scannen
 */
export default function WebsiteScanner() {
  const [url, setUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Ergebnis beim Mount aus localStorage wiederherstellen
  useEffect(() => {
    try {
      const stored = localStorage.getItem('last_scan_data');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed?.results) {
          setScanResult(parsed.results);
          setUrl(parsed.url || '');
        }
      }
    } catch {
      // ignorieren – kein gültiger gespeicherter Scan
    }
  }, []);

  const pillars = [
    {
      id: 'accessibility',
      name: 'Barrierefreiheit',
      icon: Eye,
      color: 'blue',
      description: 'WCAG 2.1 AA Konformität'
    },
    {
      id: 'gdpr',
      name: 'DSGVO',
      icon: Shield,
      color: 'green',
      description: 'Datenschutz-Compliance'
    },
    {
      id: 'legal',
      name: 'Rechtssichere Texte',
      icon: FileText,
      color: 'purple',
      description: 'Impressum, AGB, Widerrufsrecht'
    },
    {
      id: 'cookies',
      name: 'Cookie Compliance',
      icon: Cookie,
      color: 'orange',
      description: 'Cookie-Banner & Consent'
    }
  ];

  /**
   * Berechnet Scores aus Issues mit verschärfter Formel:
   * Score = max(0, 100 - (critical * 60 + warning * 15))
   * CRITICAL Issues = schwere Verstöße, maximal Score 40
   */
  const calculateScoresFromIssues = (issues: any[]) => {
    // Säulen-Mapping gemäß Backend-Logik
    const categoryMapping = {
      accessibility: ['barrierefreiheit', 'kontraste', 'tastaturbedienung'],
      gdpr: ['datenschutz', 'tracking', 'datenverarbeitung'],
      legal: ['impressum', 'agb', 'widerrufsbelehrung', 'contact'],
      cookies: ['cookies']
    };

    // Kategorisiere Issues nach Säulen
    const issuesBySäule: any = {};
    for (const [pillar, categories] of Object.entries(categoryMapping)) {
      issuesBySäule[pillar] = issues.filter(issue => 
        categories.includes(issue.category?.toLowerCase() || '')
      );
    }

    // ✅ VERBESSERT: Säulen-Scores mit drastischen Abzügen für CRITICAL Issues
    const pillarScores: any = {};
    for (const [pillar, pillarIssues] of Object.entries(issuesBySäule)) {
      const issuesArray = pillarIssues as any[];
      const critical = issuesArray.filter((i: any) => i.severity === 'critical').length;
      const warning = issuesArray.filter((i: any) => i.severity === 'warning').length;
      
      // NEUE FORMEL: CRITICAL-Issues ziehen viel mehr ab!
      // - Jedes CRITICAL: -60 Punkte (statt -20)
      // - Jedes WARNING: -15 Punkte (statt -5)
      // → 1 CRITICAL = Score 40 (statt 80)
      // → 2 CRITICAL = Score 0 (komplett non-compliant)
      let score = 100 - (critical * 60 + warning * 15);
      
      // ZUSATZ: Wenn Säule CRITICAL Issues hat, maximal Score 40
      if (critical > 0) {
        score = Math.min(score, 40);
      }
      
      pillarScores[pillar] = {
        score: Math.max(0, score),
        issues: issuesArray.length,
        critical: critical
      };
    }

    // Gewichteter Gesamt-Score
    const weights = { 
      gdpr: 0.35,        // 35% - höchste Strafen
      accessibility: 0.30, // 30% - BFSG 
      cookies: 0.20,      // 20% - TTDSG
      legal: 0.15         // 15% - TMG
    };
    
    const overallScore = Math.round(
      pillarScores.gdpr.score * weights.gdpr +
      pillarScores.accessibility.score * weights.accessibility +
      pillarScores.cookies.score * weights.cookies +
      pillarScores.legal.score * weights.legal
    );

    // Berechne Abmahnrisiko
    const fineRisk = 
      pillarScores.gdpr.issues * 5000 +
      pillarScores.accessibility.issues * 3000 +
      pillarScores.cookies.issues * 2000 +
      pillarScores.legal.issues * 1500;

    return { pillarScores, overallScore, fineRisk };
  };


  // Robuste URL-Normalisierung - akzeptiert alle Formate
  const normalizeUrl = (input: string): string => {
    if (!input || typeof input !== 'string') {
      throw new Error('Ungültige URL');
    }

    let cleaned = input.trim().toLowerCase(); // FIXED: toLowerCase für Konsistenz
    
    // Entferne führende/trailing Leerzeichen
    if (!cleaned) {
      throw new Error('URL darf nicht leer sein');
    }

    // Protokoll hinzufügen wenn nötig
    if (!cleaned.startsWith('http://') && !cleaned.startsWith('https://')) {
      if (cleaned.startsWith('www.')) {
        cleaned = 'https://' + cleaned;
      } else {
        cleaned = 'https://' + cleaned;
      }
    }

    // URL-Objekt für saubere Normalisierung
    try {
      const urlObj = new URL(cleaned);
      // WICHTIG: protocol + hostname (OHNE urlObj.href!)
      // href fügt automatisch / hinzu
      // hostname ist bereits lowercase durch URL-Parser
      
      // FIXED: Entferne www. Präfix für konsistente Hashes
      let hostname = urlObj.hostname;
      if (hostname.startsWith('www.')) {
        hostname = hostname.substring(4);
      }
      
      let normalized = `${urlObj.protocol}//${hostname}`;
      
      // Optional: Port hinzufügen wenn vorhanden und nicht Standard
      if (urlObj.port && urlObj.port !== '80' && urlObj.port !== '443') {
        normalized += `:${urlObj.port}`;
      }
      
      // Optional: Pathname hinzufügen (ohne trailing slash)
      // WICHTIG: Immer den pathname entfernen für konsistente Hashes
      // URLs wie "complyo.tech" und "complyo.tech/" sollen gleich behandelt werden
      if (urlObj.pathname && urlObj.pathname !== '/' && urlObj.pathname !== '') {
        normalized += urlObj.pathname.replace(/\/+$/, '');
      }
      
      return normalized;
    } catch (e) {
      throw new Error('Ungültiges URL-Format');
    }
  };

  const handleScan = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url) {
      setError('Bitte geben Sie eine Website-URL ein');
      return;
    }

    setIsScanning(true);
    setError(null);
    
    try {
      // Normalisiere URL
      const normalizedUrl = normalizeUrl(url);
      console.log('🔗 Original URL:', url);
      console.log('✅ Normalisierte URL:', normalizedUrl);

      // API-Analyse durchführen
      const result = await complianceApi.analyzeWebsite(normalizedUrl);
      const apiData: any = result;
      
      console.log('📡 API Response:', apiData);
      
      // API liefert risk_categories[] — validieren
      const categories: any[] = Array.isArray(apiData.risk_categories) ? apiData.risk_categories : [];
      const hasData = apiData.success === true || categories.length > 0 || apiData.score != null;

      if (!hasData) {
        setError('Keine Analysedaten verfügbar. Die Website konnte nicht gescannt werden. Bitte versuchen Sie es später erneut oder kontaktieren Sie den Support.');
        setIsScanning(false);
        return;
      }

      // Mappe alle API-Kategorien auf interne Pillar-Keys
      const categoryToSäule: Record<string, string> = {
        barrierefreiheit: 'accessibility',
        dsgvo:            'gdpr',
        cookies:          'cookies',
        rechtstexte:      'legal',
        sicherheit:       'security',
        wettbewerb:       'competition',
        shop:             'shop',
        preise:           'prices',
      };

      const pillarScores: any = {};

      categories.forEach((cat: any) => {
        const key = categoryToSäule[cat.id] ?? cat.id;
        if (!cat.detected) return; // nicht relevant für diese Website → nicht anzeigen
        const cnt = cat.issues_count ?? 0;
        const crit = cat.severity === 'critical' ? cnt : 0;
        const score = Math.max(0, 100 - (crit * 60 + (cnt - crit) * 15));
        pillarScores[key] = { score, issues: cnt, critical: crit, detected: true, label: cat.label, id: cat.id };
      });

      // Abmahnrisiko: nur Kategorien mit tatsächlichen Issues, skaliert nach Schwere
      // Nicht einfach risk_max summieren – das wäre immer maximal
      const fineRisk = categories.reduce((sum: number, cat: any) => {
        const cnt = cat.issues_count ?? 0;
        if (cnt === 0) return sum;
        const riskMin = cat.risk_min ?? 0;
        const riskMax = cat.risk_max ?? riskMin;
        const isCritical = cat.severity === 'critical';
        // Kritische Issues → risk_max, normale Issues → risk_min + 20% Aufschlag
        const risk = isCritical ? riskMax : Math.round(riskMin + (riskMax - riskMin) * 0.2);
        return sum + risk;
      }, 0);

      const backendScore = apiData.score ?? apiData.compliance_score ?? Math.round(
        (pillarScores.gdpr.score * 0.45) +
        (pillarScores.accessibility.score * 0.20) +
        (pillarScores.cookies.score * 0.20) +
        (pillarScores.legal.score * 0.15)
      );

      const transformedResult = {
        url: normalizedUrl,
        overallScore: backendScore,
        fineRisk,
        pillars: pillarScores,
      };

      const scanData = {
        scan_id: apiData.scan_id || `scan_${Date.now()}`,
        url: normalizedUrl,
        timestamp: new Date().toISOString(),
        results: transformedResult,
        issues: categories,
      };
      localStorage.setItem('last_scan_data', JSON.stringify(scanData));
      console.log('✅ Scan-Daten gespeichert für Dashboard-Sync:', scanData.scan_id);
      
      setScanResult(transformedResult);
    } catch (err: any) {
      console.error('❌ API scan failed:', err.message);
      
      // Unterscheide zwischen verschiedenen Fehlerarten
      let errorMessage = 'Es ist ein Fehler aufgetreten. ';
      
      // URL-Normalisierungsfehler
      try {
        normalizeUrl(url);
      } catch (e) {
        setError('Die eingegebene URL ist ungültig. Bitte verwenden Sie das Format: beispiel.de oder www.beispiel.de');
        setIsScanning(false);
        return;
      }
      
      // API-Fehler
      if (err.message?.includes('404') || err.message?.includes('not found')) {
        errorMessage = 'Die Website wurde nicht gefunden oder ist nicht erreichbar. Bitte überprüfen Sie die URL.';
      } else if (err.message?.includes('timeout') || err.message?.includes('network')) {
        errorMessage = 'Die Website antwortet nicht oder ist nicht erreichbar. Bitte versuchen Sie es später erneut.';
      } else if (err.message?.includes('403') || err.message?.includes('forbidden')) {
        errorMessage = 'Der Zugriff auf die Website wurde verweigert. Die Website blockiert möglicherweise automatische Scans.';
      } else if (err.message?.includes('500')) {
        errorMessage = 'Die Website hat einen internen Serverfehler. Bitte versuchen Sie es später erneut.';
      } else {
        errorMessage = 'Die Website konnte nicht analysiert werden. Bitte versuchen Sie es später erneut oder kontaktieren Sie den Support.';
      }
      
      setError(errorMessage);
    } finally {
      setIsScanning(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score == null) return 'text-gray-400 bg-gray-100';
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getRiskLevel = (score: number) => {
    if (score >= 80) return { label: 'Gering', color: 'green' };
    if (score >= 60) return { label: 'Mittel', color: 'yellow' };
    return { label: 'HOCH', color: 'red' };
  };

  return (
    <section id="scanner" className="py-20 bg-[#111827]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-full text-sm font-semibold mb-4">
            <Search className="w-4 h-4" />
            Kostenloser Website-Check
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Wie rechtskonform ist Ihre Website?
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Prüfen Sie Ihre Website <span className="font-semibold text-blue-400">kostenlos</span> auf die 4 wichtigsten Compliance-Säulen
          </p>
        </div>

        {/* Scanner Input */}
        <div className="max-w-3xl mx-auto mb-12">
          <form onSubmit={handleScan} className="relative">
            <div className="flex flex-col sm:flex-row gap-3">
              <label htmlFor="website-scanner-input" className="sr-only">Website-URL für Compliance-Check</label>
              <input
                type="text"
                id="website-scanner-input"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="ihre-website.de"
                aria-label="Website-URL für kostenlosen Compliance-Check eingeben"
                className="flex-1 px-6 py-4 rounded-xl border-2 border-gray-600 bg-gray-800 text-white focus:border-blue-500 focus:ring-4 focus:ring-blue-900 outline-none text-lg placeholder-gray-400"
                required
              />
              <button
                type="submit"
                disabled={isScanning}
                className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 whitespace-nowrap"
              >
                {isScanning ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Wird gescannt...
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5" />
                    Jetzt scannen
                  </>
                )}
              </button>
            </div>
            <p className="text-sm text-gray-400 mt-2 text-center sm:text-left">
              ✓ Mit oder ohne https:// · ✓ Mit oder ohne www. · ✓ Einfach complyo.tech eingeben
            </p>
          </form>

          {/* Error Message */}
          {error && (
            <div className="bg-red-900/20 border-2 border-red-500 rounded-xl p-6 mb-8">
              <div className="flex items-start gap-4">
                <AlertTriangle className="w-6 h-6 text-red-400 flex-shrink-0 mt-1" />
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-red-400 mb-2">
                    Scan fehlgeschlagen
                  </h3>
                  <p className="text-red-200 text-sm leading-relaxed mb-4">
                    {error}
                  </p>
                  <button
                    onClick={() => {
                      setError(null);
                      setUrl('');
                    }}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition-all"
                  >
                    Erneut versuchen
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 4 Säulen Preview */}
        {!scanResult && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            {pillars.map((pillar) => {
              const Icon = pillar.icon;
              return (
                <div
                  key={pillar.id}
                  className="bg-gray-800 rounded-xl p-6 border-2 border-gray-700 hover:border-blue-500 hover:shadow-lg transition-all"
                >
                  <div className={`w-12 h-12 bg-${pillar.color}-900 bg-opacity-50 rounded-lg flex items-center justify-center mb-4`}>
                    <Icon className={`w-6 h-6 text-${pillar.color}-400`} />
                  </div>
                  <h3 className="text-lg font-bold text-white mb-2">
                    {pillar.name}
                  </h3>
                  <p className="text-sm text-gray-300">
                    {pillar.description}
                  </p>
                </div>
              );
            })}
          </div>
        )}

        {/* Scan Results */}
        {scanResult && (
          <div className="space-y-6 animate-fadeIn">
            {/* Overall Score Card */}
            <div className="bg-white rounded-2xl p-8 border-2 border-gray-200 shadow-xl">
              <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                {/* Score */}
                <div className="text-center md:text-left">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">
                    Ergebnis für {scanResult.url}
                  </h3>
                  <div className="flex items-center gap-4">
                    <div className={`text-6xl font-bold ${getScoreColor(scanResult.overallScore)}`}>
                      {scanResult.overallScore}
                      <span className="text-3xl">/100</span>
                    </div>
                    <div>
                      <div className="text-lg font-semibold text-gray-700">Compliance-Score</div>
                      <div className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-semibold ${
                        getRiskLevel(scanResult.overallScore).color === 'red' 
                          ? 'bg-red-100 text-red-700' 
                          : getRiskLevel(scanResult.overallScore).color === 'yellow'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-green-100 text-green-700'
                      }`}>
                        {getRiskLevel(scanResult.overallScore).label === 'HOCH' && (
                          <AlertTriangle className="w-4 h-4" />
                        )}
                        {getRiskLevel(scanResult.overallScore).label} Risiko
                      </div>
                    </div>
                  </div>
                </div>

                {/* Fine Risk */}
                {(() => {
                  const risk = scanResult.fineRisk;
                  const score = scanResult.overallScore;
                  const isGreen = risk === 0;
                  const isRed = score < 60;
                  const bgClass = isGreen ? 'bg-green-50 border-green-200' : isRed ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200';
                  const textClass = isGreen ? 'text-green-900' : isRed ? 'text-red-900' : 'text-yellow-900';
                  const numClass = isGreen ? 'text-green-600' : isRed ? 'text-red-600' : 'text-yellow-600';
                  const subClass = isGreen ? 'text-green-700' : isRed ? 'text-red-700' : 'text-yellow-700';
                  const label = isGreen ? 'Keine Gefahr' : isRed ? 'Abmahngefahr' : 'Handlungsbedarf';
                  const sub = isGreen ? 'Vollständig geschützt' : 'Geschätztes Risikopotenzial';
                  return (
                    <div className={`rounded-xl p-6 border-2 ${bgClass}`}>
                      <div className="flex items-center gap-3 mb-2">
                        {isGreen
                          ? <CheckCircle className="w-6 h-6 text-green-600" />
                          : <AlertTriangle className={`w-6 h-6 ${isRed ? 'text-red-600' : 'text-yellow-600'}`} />
                        }
                        <h4 className={`text-lg font-bold ${textClass}`}>{label}</h4>
                      </div>
                      <div className={`text-3xl font-bold flex items-center gap-1 ${numClass}`}>
                        {isGreen ? <span>0€</span> : <><Euro className="w-6 h-6" />{risk.toLocaleString('de-DE')}</>}
                      </div>
                      <p className={`text-sm mt-1 ${subClass}`}>{sub}</p>
                    </div>
                  );
                })()}
              </div>
            </div>

            {/* Pillar Details – nur tatsächlich geprüfte Kategorien */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Object.entries(scanResult.pillars).map(([key, pillarData]: [string, any]) => {
                const meta: Record<string, { icon: any; color: string; description: string }> = {
                  accessibility: { icon: Eye,       color: 'blue',   description: 'WCAG 2.1 AA Konformität' },
                  gdpr:          { icon: Shield,     color: 'green',  description: 'Datenschutz-Compliance' },
                  legal:         { icon: FileText,   color: 'purple', description: 'Impressum, AGB, Widerrufsrecht' },
                  cookies:       { icon: Cookie,     color: 'orange', description: 'Cookie-Banner & Consent' },
                  security:      { icon: Shield,     color: 'red',    description: 'HTTPS, Sicherheitsheader' },
                  competition:   { icon: FileText,   color: 'yellow', description: 'Wettbewerbsrechtliche Anforderungen' },
                  shop:          { icon: FileText,   color: 'indigo', description: 'Shop-Compliance' },
                  prices:        { icon: Euro,       color: 'teal',   description: 'Preisangabenverordnung' },
                };
                const m = meta[key] ?? { icon: Shield, color: 'gray', description: '' };
                const Icon = m.icon;
                return (
                  <div key={key} className="bg-white rounded-xl p-6 border-2 border-gray-200">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 bg-${m.color}-100 rounded-lg flex items-center justify-center`}>
                          <Icon className={`w-5 h-5 text-${m.color}-600`} />
                        </div>
                        <div>
                          <h4 className="font-bold text-gray-900">{pillarData.label ?? key}</h4>
                          <p className="text-sm text-gray-600">{m.description}</p>
                        </div>
                      </div>
                      <div className={`text-2xl font-bold ${getScoreColor(pillarData.score)}`}>
                        {pillarData.score}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Gefundene Issues:</span>
                        <span className="font-semibold text-gray-900">{pillarData.issues}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Kritische Issues:</span>
                        <span className="font-semibold text-red-600">{pillarData.critical}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* CTA */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-center text-white">
              <h3 className="text-2xl font-bold mb-4">
                Bereit, die gefundenen Probleme zu lösen?
              </h3>
              <p className="text-lg mb-6 opacity-90">
                Complyo zeigt dir konkrete Lösungsvorschläge für alle gefundenen Issues – verständlich erklärt, direkt umsetzbar.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <a
                  href="#waitlist"
                  className="px-8 py-4 bg-white text-blue-600 font-semibold rounded-xl hover:shadow-2xl transition-all transform hover:scale-105 inline-flex items-center justify-center gap-2"
                >
                  <TrendingUp className="w-5 h-5" />
                  Auf Warteliste setzen
                </a>
                <button
                  onClick={() => { setScanResult(null); setUrl(''); localStorage.removeItem('last_scan_data'); }}
                  className="px-8 py-4 bg-white/20 hover:bg-white/30 text-white font-semibold rounded-xl transition-all"
                >
                  Neue Website scannen
                </button>
              </div>
              <p className="text-sm mt-4 opacity-75">
                ✓ Kostenloser Fix · ✓ Keine Kreditkarte erforderlich
              </p>
            </div>
          </div>
        )}

      </div>
    </section>
  );
}

