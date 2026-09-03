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
  // Hochzaehlen, sobald sich die Form von scanData aendert - sonst zeigt ein
  // alter Eintrag aus dem localStorage stillschweigend falsche Werte an.
  const SCAN_SCHEMA = 3;

  const [scanResult, setScanResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Ergebnis beim Mount aus localStorage wiederherstellen
  useEffect(() => {
    try {
      const stored = localStorage.getItem('last_scan_data');
      if (stored) {
        const parsed = JSON.parse(stored);
        // Nur Ergebnisse im aktuellen Format wiederherstellen.
        //
        // Aeltere Eintraege tragen das Feld fineRisk statt kostenRisikoMax.
        // Ohne diese Pruefung waere kostenRisikoMax undefined -> 0 -> die
        // Anzeige meldete einem wiederkehrenden Besucher "Keine Gefahr",
        // obwohl sein Scan Befunde hatte.
        if (parsed?.results && parsed.schema === SCAN_SCHEMA) {
          setScanResult(parsed.results);
          setUrl(parsed.url || '');
        } else {
          localStorage.removeItem('last_scan_data');
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
      name: 'Pflichttexte',
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

  // Die fruehere Hilfsrechnung calculateScoresFromIssues() stand hier ohne
  // einen einzigen Aufrufer. Sie multiplizierte Befunde mit Pauschalen
  // (issues * 5000 fuer DSGVO usw.) — genau die Rechenart, die fuer eine
  // leere Platzhalterseite 91.800 EUR ergab. Geloescht am 03.09.2026;
  // Scores und Risiko kommen aus dem Backend.


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
      // URLs wie "complyo.de" und "complyo.de/" sollen gleich behandelt werden
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

      // API-Analyse durchführen
      const result = await complianceApi.analyzeWebsite(normalizedUrl);
      const apiData: any = result;
      
      
      // API liefert risk_categories[] — validieren
      const categories: any[] = Array.isArray(apiData.risk_categories) ? apiData.risk_categories : [];
      const hasData = apiData.success === true || categories.length > 0 || apiData.score != null;

      if (!hasData) {
        // Das Backend sagt bei success:false konkret, woran der Scan scheiterte
        // (z. B. "Website nicht erreichbar"). Diese Auskunft zu verwerfen und
        // "Keine Analysedaten verfügbar" zu zeigen, half niemandem weiter.
        setError(apiData.message || 'Die Website konnte nicht gescannt werden. Bitte prüfen Sie die URL oder versuchen Sie es später erneut.');
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

      // Risiko rechnet das Backend, nicht die Landing.
      //
      // Hier stand bis 03.09.2026 eine zweite, eigene Summenbildung ueber alle
      // Kategorien. Zwei Rechenwege fuer dieselbe Zahl heisst: irgendwann
      // stimmen sie nicht mehr ueberein, und keiner merkt es. Das Backend
      // liefert die Werte jetzt fertig (gesamtrisiko_aus_kategorien) und
      // trennt dabei zwei Dinge, die vorher vermengt waren:
      //   kostenRisiko - was eine Abmahnung den Betrieb realistisch kostet
      //   rahmenMax    - was das Gesetz im Hoechstfall zulaesst (Tatsache)
      const kostenRisikoMin: number = apiData.total_risk_min ?? 0;
      const kostenRisikoMax: number = apiData.total_risk_max ?? 0;
      const kostenRisikoText: string | null = apiData.total_risk_range ?? null;
      const rahmenMax: number = apiData.rahmen_max ?? apiData.risk_rahmen_max ?? 0;
      const bereicheBetroffen: number = apiData.risk_bereiche_betroffen ?? 0;

      const backendScore = apiData.score ?? apiData.compliance_score ?? Math.round(
        (pillarScores.gdpr.score * 0.45) +
        (pillarScores.accessibility.score * 0.20) +
        (pillarScores.cookies.score * 0.20) +
        (pillarScores.legal.score * 0.15)
      );

      const transformedResult = {
        url: normalizedUrl,
        overallScore: backendScore,
        kostenRisikoMin,
        kostenRisikoMax,
        kostenRisikoText,
        rahmenMax,
        bereicheBetroffen,
        pillars: pillarScores,
        // Phase 7.1 Regulierungs-Radar (Lead-Magnet)
        bfsg: apiData.bfsg_report ?? null,
        aiAct: apiData.ai_act_report ?? null,
      };

      const scanData = {
        schema: SCAN_SCHEMA,
        scan_id: apiData.scan_id || `scan_${Date.now()}`,
        url: normalizedUrl,
        timestamp: new Date().toISOString(),
        results: transformedResult,
        issues: categories,
      };
      localStorage.setItem('last_scan_data', JSON.stringify(scanData));
      
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
      
      // API-Fehler.
      //
      // Der Status kommt aus err.response, NICHT aus err.message: axios schreibt
      // dort "Request failed with status code 429" — die alte Textsuche traf das
      // nie und schob jeden Serverfehler dem Besucher als "Ihre Website ist nicht
      // erreichbar" unter. Wer wissen will, ob seine Seite sauber ist, liest dann
      // eine Falschaussage über die eigene Seite. Also: unsere Fehler als unsere
      // benennen, fremde als fremde.
      const status = err.response?.status;

      if (status === 429) {
        errorMessage = 'Zu viele Scans in kurzer Zeit. Bitte warten Sie eine Minute und versuchen Sie es erneut.';
      } else if (status === 404) {
        errorMessage = 'Die Website wurde nicht gefunden. Bitte überprüfen Sie die URL.';
      } else if (status === 403) {
        errorMessage = 'Der Zugriff auf die Website wurde verweigert. Die Website blockiert möglicherweise automatische Scans.';
      } else if (status >= 500) {
        errorMessage = 'Der Scan-Dienst hat gerade ein Problem. Bitte versuchen Sie es in ein paar Minuten erneut.';
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        // Unser Timeout, nicht die Seite des Besuchers — das muss so dastehen.
        errorMessage = 'Der Scan hat zu lange gedauert und wurde abgebrochen. Bitte versuchen Sie es erneut.';
      } else if (err.message?.includes('Network Error')) {
        errorMessage = 'Der Scan-Dienst ist gerade nicht erreichbar. Bitte versuchen Sie es später erneut.';
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
                className="px-8 py-4 bg-blue-700 hover:bg-blue-800 text-white font-semibold rounded-xl transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 whitespace-nowrap"
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
              ✓ Mit oder ohne https:// · ✓ Mit oder ohne www. · ✓ Einfach complyo.de eingeben
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
            {/* Regulierungs-Radar: BFSG + AI Act (Phase 7.1 Lead-Magnet) */}
            {(scanResult.bfsg || scanResult.aiAct) && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {scanResult.bfsg && (
                  <div className={`rounded-2xl p-6 border-2 shadow-xl ${scanResult.bfsg.critical_issues > 0 ? 'bg-red-50 border-red-300' : 'bg-white border-gray-200'}`}>
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-2xl">♿</span>
                      <h3 className="text-lg font-bold text-gray-900">BFSG-Check</h3>
                      <span className="ml-auto text-xs font-semibold px-2 py-1 rounded-full bg-amber-100 text-amber-800">
                        gilt seit 28.06.2025
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mb-3">{scanResult.bfsg.scope_note}</p>
                    <div className="flex items-center gap-4 text-sm">
                      <span className={`font-bold ${scanResult.bfsg.critical_issues > 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {scanResult.bfsg.critical_issues} kritische Probleme
                      </span>
                      <span className="text-gray-600">{scanResult.bfsg.warning_issues} Warnungen</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-3">{scanResult.bfsg.enforcement_note}</p>
                  </div>
                )}
                {scanResult.aiAct && scanResult.aiAct.ai_systems_detected > 0 && (
                  <div className={`rounded-2xl p-6 border-2 shadow-xl ${scanResult.aiAct.action_needed ? 'bg-red-50 border-red-300' : 'bg-white border-gray-200'}`}>
                    <div className="flex items-center gap-2 mb-3">
                      <span className="text-2xl">🤖</span>
                      <h3 className="text-lg font-bold text-gray-900">AI-Act-Transparenz</h3>
                      <span className="ml-auto text-xs font-semibold px-2 py-1 rounded-full bg-amber-100 text-amber-800">
                        Art. 50 KI-VO
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mb-3">
                      {scanResult.aiAct.ai_systems_detected} KI-/Chat-System(e) erkannt
                      {scanResult.aiAct.providers?.length > 0 && (
                        <>: {scanResult.aiAct.providers.map((p: any) => p.provider).join(', ')}</>
                      )}
                    </p>
                    <p className={`text-sm font-semibold ${scanResult.aiAct.action_needed ? 'text-red-600' : 'text-green-600'}`}>
                      {scanResult.aiAct.action_needed
                        ? 'Transparenzhinweis fehlt offenbar — Handlungsbedarf'
                        : 'Kein unmittelbarer Handlungsbedarf erkannt'}
                    </p>
                    <p className="text-xs text-gray-500 mt-3">{scanResult.aiAct.fines_note}</p>
                  </div>
                )}
              </div>
            )}

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

                {/* Kostenrisiko und gesetzlicher Rahmen — bewusst zwei Zahlen.
                    Hier stand eine einzige, aufsummierte Zahl ("Geschätztes
                    Risikopotenzial"), die für eine leere Platzhalterseite auf
                    91.800 € kam. Was ein Betrieb tatsächlich zahlt, ist die
                    Abmahnung; der Bußgeldrahmen ist etwas anderes und wird
                    jetzt als das gezeigt, was er ist: eine Obergrenze im
                    Gesetz, keine Prognose. */}
                {(() => {
                  const min = scanResult.kostenRisikoMin ?? 0;
                  const max = scanResult.kostenRisikoMax ?? 0;
                  const rahmen = scanResult.rahmenMax ?? 0;
                  const score = scanResult.overallScore;
                  const isGreen = max === 0;
                  const isRed = score < 60;
                  const bgClass = isGreen ? 'bg-green-50 border-green-200' : isRed ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200';
                  const textClass = isGreen ? 'text-green-900' : isRed ? 'text-red-900' : 'text-yellow-900';
                  const numClass = isGreen ? 'text-green-600' : isRed ? 'text-red-600' : 'text-yellow-600';
                  const subClass = isGreen ? 'text-green-700' : isRed ? 'text-red-700' : 'text-yellow-700';
                  const label = isGreen ? 'Keine Gefahr' : isRed ? 'Abmahngefahr' : 'Handlungsbedarf';
                  const euro = (n: number) => n.toLocaleString('de-DE');
                  return (
                    <div className={`rounded-xl p-6 border-2 ${bgClass}`}>
                      <div className="flex items-center gap-3 mb-2">
                        {isGreen
                          ? <CheckCircle className="w-6 h-6 text-green-600" />
                          : <AlertTriangle className={`w-6 h-6 ${isRed ? 'text-red-600' : 'text-yellow-600'}`} />
                        }
                        <h4 className={`text-lg font-bold ${textClass}`}>{label}</h4>
                      </div>
                      {isGreen ? (
                        <>
                          <div className={`text-3xl font-bold ${numClass}`}>0€</div>
                          <p className={`text-sm mt-1 ${subClass}`}>Kein Handlungsbedarf gefunden</p>
                        </>
                      ) : (
                        <>
                          <div className={`text-3xl font-bold flex items-center gap-1 ${numClass}`}>
                            <Euro className="w-6 h-6" />{euro(min)} – {euro(max)}
                          </div>
                          <p className={`text-sm mt-1 ${subClass}`}>
                            Typische Abmahnkosten (Streitwert + Anwaltskosten)
                          </p>
                          {rahmen > 0 && (
                            <p className="text-xs text-gray-600 mt-3 pt-3 border-t border-black/10">
                              Gesetzlicher Bußgeldrahmen daneben: bis {euro(rahmen)} €.
                              Das ist die Obergrenze im Gesetz, keine Prognose für
                              Ihren Betrieb.
                            </p>
                          )}
                        </>
                      )}
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
                  href={`${process.env.NEXT_PUBLIC_APP_URL || 'https://app.complyo.de'}/register?plan=free`}
                  className="px-8 py-4 bg-white text-blue-600 font-semibold rounded-xl hover:shadow-2xl transition-all transform hover:scale-105 inline-flex items-center justify-center gap-2"
                >
                  <TrendingUp className="w-5 h-5" />
                  Kostenlos registrieren und Fix starten
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

