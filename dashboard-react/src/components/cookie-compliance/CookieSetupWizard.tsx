'use client';

import React, { useState } from 'react';
import {
  Globe, Settings, Code, CheckCircle, ChevronRight, ChevronLeft,
  X, Lock, Sparkles, Loader2, Copy, AlertCircle, Download,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { apiClient } from '@/lib/api-client';
import { API_BASE, Grundsystem, istGrundsystem, pluginDownloadUrl, pluginSchritte } from '@/lib/grundsystem';

interface CookieSetupWizardProps {
  websiteUrl?: string;
  websiteLocked?: boolean;
  siteId?: string;
  onComplete: () => void;
  onSkip: () => void;
  /** Erkanntes Grundsystem nach dem Scan, damit die Seite es an den Integrations-Tab weiterreicht. */
  onGrundsystem?: (g: Grundsystem | null) => void;
}

const STEPS = [
  { id: 1, title: 'Website scannen', icon: Globe },
  { id: 2, title: 'Services prüfen', icon: Settings },
  { id: 3, title: 'Code einbinden', icon: Code },
];

const CookieSetupWizard: React.FC<CookieSetupWizardProps> = ({
  websiteUrl: initialUrl = '',
  websiteLocked = false,
  siteId = '',
  onComplete,
  onSkip,
  onGrundsystem,
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);
  const [copied, setCopied] = useState(false);
  const [url, setUrl] = useState(initialUrl);

  const runScan = async () => {
    if (!url) return;
    setScanning(true);
    setScanResult(null);
    try {
      const data = await apiClient.post('/api/cookie-compliance/scan', {
        url,
        site_id: siteId,
      }) as any;
      setScanResult(data);
      if (data.success) {
        onGrundsystem?.(istGrundsystem(data) ? data : null);
        setTimeout(() => setCurrentStep(2), 600);
      }
    } catch {
      setScanResult({ success: false, error: 'Scan fehlgeschlagen. Bitte versuchen Sie es erneut.' });
    } finally {
      setScanning(false);
    }
  };

  // Dieselbe Fassung wie IntegrationGuide.tsx. Vorher stand hier
  // cdn.complyo.de/cookie-banner.js - ein Host ohne DNS-Eintrag. Wer das
  // Snippet einbaute, bekam kein Banner und keine Einwilligungsprotokolle,
  // hielt sich aber fuer abgedeckt. Der Blocker muss VOR dem Banner laden,
  // sonst laufen fremde Skripte vor der Einwilligung an.
  const integrationCode = `<!-- Complyo Cookie Compliance & Auto-Blocking -->
<!-- Schritt 1: Cookie-Blocker (laedt ZUERST, blockiert Skripte) -->
<script
  src="${API_BASE}/public/cookie-blocker.js"
  data-site-id="${siteId}"
></script>

<!-- Schritt 2: Cookie-Banner -->
<script
  src="${API_BASE}/api/widgets/cookie-compliance.js"
  data-site-id="${siteId}"
  data-complyo-site-id="${siteId}"
  async
></script>`;

  const handleCopy = () => {
    navigator.clipboard.writeText(integrationCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const canAdvance = currentStep === 1 ? !!scanResult?.success : true;

  // Grundsystem aus dem Scan: WordPress und Joomla bekommen das fertige
  // Plugin, alle anderen den Schnipsel mit dem Hinweis fuer ihr System.
  const grundsystem: Grundsystem | null = istGrundsystem(scanResult) ? scanResult : null;
  const pluginUrl = pluginDownloadUrl(grundsystem);
  const cmsName = grundsystem?.detected_cms || null;
  const cmsKey = grundsystem?.cms_key || 'html';

  const codeBlock = (
    <div className="bg-gray-950 rounded-lg p-4 border border-gray-200 dark:border-gray-700 relative group">
      <pre className="text-xs text-gray-700 dark:text-gray-300 font-mono whitespace-pre-wrap pr-8">{integrationCode}</pre>
      <button
        onClick={handleCopy}
        className="absolute top-3 right-3 p-1.5 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
        title="Code kopieren"
      >
        {copied ? <CheckCircle className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
      </button>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-2xl w-full max-w-2xl shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-200 dark:border-gray-800 flex-shrink-0">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">Ersteinrichtung</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
              Schritt {currentStep} von {STEPS.length} · {STEPS[currentStep - 1].title}
            </p>
          </div>
          <button
            onClick={onSkip}
            className="p-2 text-gray-500 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            aria-label="Schließen"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="px-6 pt-5 flex-shrink-0">
          <div className="flex items-center gap-2">
            {STEPS.map((step, idx) => {
              const isDone = currentStep > step.id;
              const isActive = currentStep === step.id;
              return (
                <React.Fragment key={step.id}>
                  <div className="flex items-center gap-2 min-w-0">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 flex-shrink-0 transition-all ${
                      isDone
                        ? 'bg-green-500/20 border-green-500 text-green-400'
                        : isActive
                          ? 'bg-orange-500/20 border-orange-500 text-orange-400'
                          : 'bg-gray-800 border-gray-700 text-gray-600'
                    }`}>
                      {isDone ? <CheckCircle className="w-4 h-4" /> : step.id}
                    </div>
                    <span className={`text-xs hidden sm:block truncate ${isActive ? 'text-white' : isDone ? 'text-green-400' : 'text-gray-600'}`}>
                      {step.title}
                    </span>
                  </div>
                  {idx < STEPS.length - 1 && (
                    <div className={`flex-1 h-0.5 transition-all ${currentStep > step.id ? 'bg-green-500' : currentStep > step.id - 1 ? 'bg-orange-500' : 'bg-gray-700'}`} />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 flex-1 overflow-y-auto">
          {/* Step 1: Scan */}
          {currentStep === 1 && (
            <div className="space-y-5">
              <div className="text-center">
                <div className="w-16 h-16 bg-orange-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Globe className="w-8 h-8 text-orange-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Website automatisch scannen</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 max-w-md mx-auto">
                  Wir erkennen automatisch alle Tracking-Services und Cookies auf Ihrer Website — in unter 10 Sekunden.
                </p>
              </div>

              {websiteLocked && url ? (
                <div className="flex items-center gap-3 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <Lock className="w-4 h-4 text-blue-400 flex-shrink-0" />
                  <span className="text-sm text-gray-900 dark:text-white font-medium flex-1 truncate">{url}</span>
                  <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/30 text-xs flex-shrink-0">Gesperrt</Badge>
                </div>
              ) : (
                <div className="flex gap-2">
                  <Input
                    placeholder="https://ihre-website.de"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && !scanning && url && runScan()}
                    className="flex-1 bg-gray-100 dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white placeholder:text-gray-500"
                  />
                </div>
              )}

              {scanning && (
                <div className="space-y-2">
                  <div className="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-orange-500 to-orange-400 rounded-full animate-pulse" style={{ width: '100%' }} />
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400 text-center">Analysiere {url}…</p>
                </div>
              )}

              {scanResult && !scanning && (
                <div className={`p-4 rounded-lg border ${scanResult.success ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'}`}>
                  <div className="flex items-start gap-3">
                    {scanResult.success
                      ? <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                      : <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                    }
                    <div>
                      {scanResult.success ? (
                        <>
                          <p className="text-sm font-semibold text-green-400">
                            {scanResult.total_found > 0
                              ? `✅ ${scanResult.total_found} Service${scanResult.total_found !== 1 ? 's' : ''} erkannt`
                              : '✅ Keine Tracking-Services gefunden'}
                          </p>
                          {scanResult.detected_services?.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {scanResult.detected_services.map((s: any) => (
                                <Badge key={s.service_key} className="bg-green-500/20 text-green-300 border-green-500/30 text-xs">
                                  {s.name}
                                </Badge>
                              ))}
                            </div>
                          )}
                          {cmsName && (
                            <p className="text-xs text-gray-700 dark:text-gray-300 mt-2">
                              Grundsystem: <strong>{cmsName}</strong>
                              {pluginUrl ? ' · fertiges Plugin verfügbar' : ''}
                            </p>
                          )}
                          <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">Weiter zum nächsten Schritt →</p>
                        </>
                      ) : (
                        <p className="text-sm text-red-400">{scanResult.error}</p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <Button
                onClick={runScan}
                disabled={scanning || !url}
                className="w-full bg-orange-500 hover:bg-orange-600 text-white"
              >
                {scanning
                  ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Scannt…</>
                  : <><Sparkles className="w-4 h-4 mr-2" />Website jetzt scannen</>
                }
              </Button>
            </div>
          )}

          {/* Step 2: Review Services */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <div className="text-center">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Erkannte Services überprüfen</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Diese Services wurden automatisch aktiviert. Sie können sie jederzeit im Tab „Services" anpassen.
                </p>
              </div>

              {scanResult?.detected_services?.length > 0 ? (
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {scanResult.detected_services.map((s: any) => (
                    <div key={s.service_key} className="flex items-center gap-3 p-3 bg-gray-100/50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
                      <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">{s.name}</p>
                        <p className="text-xs text-gray-600 dark:text-gray-400 capitalize">{s.category}</p>
                      </div>
                      <Badge variant="secondary" className="text-xs bg-gray-700 text-gray-700 dark:text-gray-300 flex-shrink-0">
                        {s.category}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-6 bg-green-500/10 border border-green-500/30 rounded-lg text-center">
                  <CheckCircle className="w-10 h-10 text-green-400 mx-auto mb-2" />
                  <p className="text-sm font-semibold text-green-400">Kein Cookie-Banner erforderlich</p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    Im Scan wurden nur essenzielle Cookies gefunden, die keine Einwilligung benötigen.
                  </p>
                </div>
              )}

              {scanResult?.farben_quelle === 'website' && scanResult?.farben && (
                <div className="p-3 bg-gray-100/50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs font-medium text-gray-900 dark:text-white">
                      {scanResult.farben_gespeichert
                        ? 'Bannerfarben aus Ihrer Website übernommen'
                        : 'Farbvorschlag aus Ihrer Website (bestehende Farben bleiben)'}
                    </p>
                    <div className="flex gap-1" aria-label="Farbvorschau">
                      {(['primary_color', 'accent_color', 'text_color', 'bg_color'] as const).map((k) => (
                        <span
                          key={k}
                          title={`${k}: ${scanResult.farben[k]}`}
                          className="w-5 h-5 rounded border border-gray-300 dark:border-gray-600"
                          style={{ backgroundColor: scanResult.farben[k] }}
                        />
                      ))}
                    </div>
                  </div>
                  {Array.isArray(scanResult.farben_angepasst) && scanResult.farben_angepasst.length > 0 && (
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                      Für lesbare Knöpfe abgedunkelt: {scanResult.farben_angepasst.map((a: any) => `${a.von} → ${a.zu}`).join(', ')} (Kontrast mindestens 4,5:1).
                    </p>
                  )}
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    {scanResult.farben_gespeichert
                      ? 'Anpassen jederzeit im Tab „Design".'
                      : 'Übernehmen im Tab „Design" über „Farben von Website übernehmen".'}
                  </p>
                </div>
              )}

              <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <p className="text-xs text-blue-300">
                  Im Tab <strong className="text-blue-200">„Services"</strong> können Sie weitere Services manuell hinzufügen oder entfernen. Das Banner-Design lässt sich im Tab <strong className="text-blue-200">„Design"</strong> anpassen.
                </p>
              </div>
            </div>
          )}

          {/* Step 3: Integration, je nach erkanntem Grundsystem */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <div className="text-center">
                <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                  <CheckCircle className="w-8 h-8 text-green-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {cmsName ? `Erkannt: ${cmsName}` : 'Alles bereit! Code einbinden.'}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {pluginUrl
                    ? 'Für Ihr System gibt es ein fertiges Plugin: hochladen, aktivieren, fertig.'
                    : <>Fügen Sie diesen Schnipsel in den <code className="text-orange-400 bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded">&lt;head&gt;</code> jeder Seite ein.</>}
                </p>
              </div>

              {pluginUrl ? (
                <>
                  <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg space-y-3">
                    <a
                      href={pluginUrl}
                      download
                      className="inline-flex items-center justify-center w-full gap-2 rounded-md bg-green-500 hover:bg-green-600 text-white text-sm font-medium px-4 py-2 transition-colors"
                    >
                      <Download className="w-4 h-4" />
                      Plugin für {cmsName} herunterladen
                    </a>
                    <ol className="space-y-2">
                      {pluginSchritte(grundsystem, siteId).map((s, i) => (
                        <li key={i} className="flex items-start gap-2 text-xs text-gray-700 dark:text-gray-300">
                          <span className="w-5 h-5 rounded-full bg-green-500/20 text-green-400 flex items-center justify-center flex-shrink-0 font-semibold">{i + 1}</span>
                          <span>{s}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                  <details>
                    <summary className="cursor-pointer text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
                      Alternativ ohne Plugin: Schnipsel von Hand in den &lt;head&gt; einbauen
                    </summary>
                    <div className="mt-2">{codeBlock}</div>
                  </details>
                </>
              ) : (
                <>
                  {codeBlock}

                  {grundsystem?.anleitung && (
                    <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                      <p className="text-xs text-blue-300">
                        <strong className="text-blue-200">{cmsName || 'HTML'}:</strong> {grundsystem.anleitung}
                      </p>
                    </div>
                  )}

                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { key: 'wordpress', name: 'WordPress', hint: 'Im Theme-Editor in header.php einfügen' },
                      { key: 'webflow', name: 'Webflow', hint: 'Unter Site Settings → Custom Code → Head' },
                      { key: 'html', name: 'HTML', hint: 'Direkt vor dem </head>-Tag einfügen' },
                    ].map((p) => (
                      <div
                        key={p.key}
                        className={`p-3 rounded-lg border text-center ${p.key === cmsKey
                          ? 'bg-orange-500/10 border-orange-500/50'
                          : 'bg-gray-100/50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700'}`}
                      >
                        <p className="text-xs font-medium text-gray-900 dark:text-white mb-1">
                          {p.name}{p.key === cmsKey && cmsName ? ' · erkannt' : ''}
                        </p>
                        <p className="text-xs text-gray-500 leading-tight">{p.hint}</p>
                      </div>
                    ))}
                  </div>
                </>
              )}

              <div className="p-3 bg-orange-500/10 border border-orange-500/30 rounded-lg">
                <p className="text-xs text-orange-300">
                  Der vollständige Einbinde-Code mit allen Optionen ist im Tab <strong className="text-orange-200">„Integration"</strong> verfügbar.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 dark:border-gray-800 flex-shrink-0">
          <Button
            variant="ghost"
            onClick={currentStep === 1 ? onSkip : () => setCurrentStep((s) => s - 1)}
            className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
          >
            {currentStep === 1 ? (
              'Überspringen'
            ) : (
              <><ChevronLeft className="w-4 h-4 mr-1" />Zurück</>
            )}
          </Button>

          <Button
            onClick={currentStep === STEPS.length ? onComplete : () => setCurrentStep((s) => s + 1)}
            disabled={!canAdvance}
            className={currentStep === STEPS.length
              ? 'bg-green-500 hover:bg-green-600 text-white'
              : 'bg-orange-500 hover:bg-orange-600 text-white'
            }
          >
            {currentStep === STEPS.length
              ? <><CheckCircle className="w-4 h-4 mr-2" />Fertig</>
              : <>Weiter <ChevronRight className="w-4 h-4 ml-1" /></>
            }
          </Button>
        </div>
      </div>
    </div>
  );
};

export default CookieSetupWizard;
