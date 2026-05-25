'use client';

import React, { useState } from 'react';
import { Cookie, ExternalLink, Code, Copy, CheckCircle, Shield, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export const ComplyoCookieManager: React.FC = () => {
  const [copied, setCopied] = useState(false);

  const integrationCode = `<!-- Complyo Cookie-Manager Integration -->
<script src="https://widget.complyo.tech/cookie-consent.js" data-site-id="IHRE-SITE-ID"></script>

<!-- Complyo DSGVO-konformes Cookie-Consent Widget -->
<!-- Automatische Konfiguration basierend auf Ihrer Website -->`;

  const handleCopyCode = () => {
    navigator.clipboard.writeText(integrationCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Cookie className="w-6 h-6 text-orange-400" />
          Complyo Cookie-Manager Integration
        </CardTitle>
        <p className="text-sm text-gray-400 mt-2">
          Rechtssicherer Cookie-Consent mit Complyo - DSGVO & TTDSG konform
        </p>
      </CardHeader>

      <CardContent>
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Linke Spalte: Info & Anleitung */}
          <div className="space-y-6">
            <section>
              <div className="flex items-center gap-2 mb-4">
                <Shield className="w-5 h-5 text-green-400" />
                <h3 className="text-lg font-semibold text-white">
                  Warum Complyo Cookie-Manager?
                </h3>
              </div>
              
              <div className="space-y-3">
                <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-white mb-1">100% Rechtssicher</h4>
                      <p className="text-sm text-gray-400">
                        Von Rechtsanwälten geprüft und ständig aktualisiert gemäß DSGVO & TTDSG
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-white mb-1">Einfache Integration</h4>
                      <p className="text-sm text-gray-400">
                        Ein Code-Snippet einfügen - fertig! Keine Programmierung nötig
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-white mb-1">Automatische Updates</h4>
                      <p className="text-sm text-gray-400">
                        Bei Gesetzesänderungen wird der Cookie-Banner automatisch angepasst
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-white mb-1">Compliance-Hinweis</h4>
                      <p className="text-sm text-gray-400">
                        Schützt vor teuren Abmahnungen durch fehlerhafte Cookie-Banner
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* CTA Button */}
            <Button
              className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-lg py-6"
              onClick={() => {
                // TODO: Öffne Complyo Cookie-Manager Setup
                console.log('Öffne Complyo Cookie-Manager Setup');
              }}
            >
              <ExternalLink className="w-5 h-5 mr-2" />
              Jetzt Complyo Cookie-Manager aktivieren
            </Button>
          </div>

          {/* Rechte Spalte: Integration & Code */}
          <div className="space-y-6">
            {/* Schritt-für-Schritt Anleitung */}
            <section>
              <div className="flex items-center gap-2 mb-4">
                <Code className="w-5 h-5 text-blue-400" />
                <h3 className="text-lg font-semibold text-white">
                  Integration in 3 Schritten
                </h3>
              </div>

              <div className="space-y-3">
                <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold flex-shrink-0">
                      1
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-white mb-1">Complyo Site-ID anfordern</h4>
                      <p className="text-sm text-gray-400">
                        Ihre persönliche Site-ID wird automatisch generiert
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold flex-shrink-0">
                      2
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-white mb-1">Code-Snippet kopieren</h4>
                      <p className="text-sm text-gray-400">
                        Kopieren Sie das Widget-Snippet mit Ihrer Site-ID
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold flex-shrink-0">
                      3
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-white mb-1">In Website einfügen</h4>
                      <p className="text-sm text-gray-400">
                        Fügen Sie den Code vor dem schließenden <code className="bg-gray-900 px-2 py-0.5 rounded text-blue-300">&lt;/body&gt;</code>-Tag ein
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Code-Beispiel */}
            <section>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-md font-semibold text-white">
                  Beispiel-Code zur Integration
                </h4>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={handleCopyCode}
                >
                  {copied ? (
                    <>
                      <CheckCircle className="w-4 h-4 mr-2 text-green-400" />
                      Kopiert!
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4 mr-2" />
                      Code kopieren
                    </>
                  )}
                </Button>
              </div>

              <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono overflow-x-auto">
                  {integrationCode}
                </pre>
              </div>

              <div className="mt-3 p-3 bg-yellow-900/20 rounded-lg border border-yellow-500/30">
                <div className="flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-yellow-200">
                    <p className="font-semibold mb-1">Wichtiger Hinweis:</p>
                    <p className="text-xs">
                      Ersetzen Sie <code className="bg-yellow-800/30 px-1 py-0.5 rounded">IHRE-SITE-ID</code> mit 
                      Ihrer echten Site-ID aus dem Complyo-Dashboard.
                    </p>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>

        {/* Info-Box unten */}
        <div className="mt-6 p-4 bg-blue-900/20 rounded-lg border border-blue-500/30">
          <div className="flex items-start gap-3">
            <Shield className="w-6 h-6 text-blue-400 flex-shrink-0" />
            <div className="text-sm text-blue-200">
              <p className="font-semibold mb-2">💡 Complyo Cookie-Manager</p>
              <p>
                Unser Cookie-Consent Widget ist vollständig DSGVO & TTDSG-konform und wird 
                von Rechtsanwälten geprüft. Es bietet automatische Updates bei Gesetzesänderungen 
                und schützt vor Abmahnungen durch fehlerhafte Cookie-Banner.
              </p>
              <p className="mt-2">
                <strong>Unser Versprechen:</strong> Professionelle, rechtssichere Lösung mit 
                einfacher Integration und ohne versteckte Kosten.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

