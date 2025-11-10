'use client';

import React, { useState } from 'react';
import { Cookie, Settings, Code, Eye, Copy, CheckCircle, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { generateCookieBanner } from '@/lib/api';

interface DetectedCookie {
  name: string;
  category: 'essential' | 'analytics' | 'marketing' | 'preferences';
  purpose: string;
  provider?: string;
}

export const CookieBannerManagement: React.FC = () => {
  const [detectedCookies, setDetectedCookies] = useState<DetectedCookie[]>([
    { name: '_ga', category: 'analytics', purpose: 'Google Analytics Tracking', provider: 'Google' },
    { name: '_fbp', category: 'marketing', purpose: 'Facebook Pixel', provider: 'Meta' },
    { name: 'session_id', category: 'essential', purpose: 'Session Management', provider: 'Intern' }
  ]);
  
  const [generatedScript, setGeneratedScript] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [bannerConfig, setBannerConfig] = useState({
    position: 'bottom',
    primaryColor: '#4F46E5',
    acceptText: 'Alle akzeptieren',
    rejectText: 'Ablehnen',
    settingsText: 'Einstellungen'
  });

  const handleGenerateBanner = async () => {
    setIsGenerating(true);
    try {
      const config = await generateCookieBanner(detectedCookies);
      
      // Generate HTML/JS Code
      const script = `<!-- Complyo Cookie Banner -->
<div id="complyo-cookie-banner" style="display: none;">
  <div class="cookie-banner-content">
    <h3>🍪 Cookie-Einstellungen</h3>
    <p>${config.banner_text}</p>
    
    <div class="cookie-categories">
      ${config.categories.map(cat => `
        <label>
          <input type="checkbox" ${cat.required ? 'checked disabled' : ''} 
                 data-category="${cat.name}">
          ${cat.name} ${cat.required ? '(Erforderlich)' : ''}
          <span class="category-desc">${cat.description}</span>
        </label>
      `).join('')}
    </div>
    
    <div class="cookie-actions">
      <button onclick="acceptAllCookies()">${bannerConfig.acceptText}</button>
      <button onclick="rejectNonEssentialCookies()">${bannerConfig.rejectText}</button>
    </div>
  </div>
</div>

<script>
// Complyo Cookie Consent Manager
(function() {
  function showBanner() {
    const banner = document.getElementById('complyo-cookie-banner');
    if (banner && !localStorage.getItem('cookieConsent')) {
      banner.style.display = 'block';
    }
  }
  
  window.acceptAllCookies = function() {
    localStorage.setItem('cookieConsent', JSON.stringify({
      essential: true,
      analytics: true,
      marketing: true,
      preferences: true,
      timestamp: new Date().toISOString()
    }));
    document.getElementById('complyo-cookie-banner').style.display = 'none';
    loadScripts();
  };
  
  window.rejectNonEssentialCookies = function() {
    localStorage.setItem('cookieConsent', JSON.stringify({
      essential: true,
      analytics: false,
      marketing: false,
      preferences: false,
      timestamp: new Date().toISOString()
    }));
    document.getElementById('complyo-cookie-banner').style.display = 'none';
  };
  
  function loadScripts() {
    // Load analytics and marketing scripts here after consent

  }
  
  // Show banner on page load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', showBanner);
  } else {
    showBanner();
  }
})();
</script>

<style>
#complyo-cookie-banner {
  position: fixed;
  ${bannerConfig.position}: 0;
  left: 0;
  right: 0;
  background: #1F2937;
  padding: 20px;
  box-shadow: 0 -2px 10px rgba(0,0,0,0.2);
  z-index: 9999;
  font-family: system-ui, -apple-system, sans-serif;
}

.cookie-banner-content {
  max-width: 1200px;
  margin: 0 auto;
  color: #fff;
}

.cookie-banner-content h3 {
  margin: 0 0 10px 0;
  font-size: 20px;
}

.cookie-categories {
  margin: 15px 0;
  display: grid;
  gap: 10px;
}

.cookie-categories label {
  display: flex;
  align-items: start;
  gap: 10px;
  padding: 10px;
  background: rgba(255,255,255,0.05);
  border-radius: 8px;
  cursor: pointer;
}

.category-desc {
  font-size: 13px;
  color: #9CA3AF;
  display: block;
  margin-top: 4px;
}

.cookie-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.cookie-actions button {
  flex: 1;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.cookie-actions button:first-child {
  background: ${bannerConfig.primaryColor};
  color: white;
}

.cookie-actions button:first-child:hover {
  filter: brightness(1.1);
}

.cookie-actions button:last-child {
  background: rgba(255,255,255,0.1);
  color: white;
}
</style>`;
      
      setGeneratedScript(script);
    } catch (error) {
      console.error('Failed to generate banner:', error);
      alert('Fehler beim Generieren des Cookie-Banners. Bitte versuchen Sie es erneut.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopyScript = () => {
    if (generatedScript) {
      navigator.clipboard.writeText(generatedScript);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'essential': return 'bg-green-500/20 text-green-400 border-green-500';
      case 'analytics': return 'bg-blue-500/20 text-blue-400 border-blue-500';
      case 'marketing': return 'bg-orange-500/20 text-orange-400 border-orange-500';
      case 'preferences': return 'bg-purple-500/20 text-purple-400 border-purple-500';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500';
    }
  };

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'essential': return 'Notwendig';
      case 'analytics': return 'Analyse';
      case 'marketing': return 'Marketing';
      case 'preferences': return 'Einstellungen';
      default: return category;
    }
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Cookie className="w-6 h-6 text-orange-400" />
          Cookie-Banner Management
        </CardTitle>
        <p className="text-sm text-gray-400 mt-2">
          Verwalten Sie Ihren Cookie-Banner direkt über Complyo - DSGVO & TTDSG konform
        </p>
      </CardHeader>

      <CardContent>
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Linke Spalte: Erkannte Cookies & Konfiguration */}
          <div className="space-y-6">
            {/* Erkannte Cookies */}
            <section>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Cookie className="w-5 h-5" />
                  Erkannte Cookies ({detectedCookies.length})
                </h3>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    alert('🔄 Cookie-Scan wird gestartet...\n\n(Feature wird im nächsten Schritt implementiert)');
                  }}
                >
                  Neu scannen
                </Button>
              </div>

              <div className="space-y-3">
                {detectedCookies.map((cookie, idx) => (
                  <div
                    key={idx}
                    className="bg-gray-800/50 rounded-lg p-4 border border-gray-700"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h4 className="font-semibold text-white">{cookie.name}</h4>
                        <p className="text-sm text-gray-400">{cookie.purpose}</p>
                        {cookie.provider && (
                          <p className="text-xs text-gray-500 mt-1">
                            Anbieter: {cookie.provider}
                          </p>
                        )}
                      </div>
                      <Badge className={`${getCategoryColor(cookie.category)} border`}>
                        {getCategoryLabel(cookie.category)}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Banner-Konfiguration */}
            <section>
              <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
                <Settings className="w-5 h-5" />
                Banner konfigurieren
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="text-sm text-gray-300 mb-2 block">Position</label>
                  <select
                    value={bannerConfig.position}
                    onChange={(e) => setBannerConfig({ ...bannerConfig, position: e.target.value })}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
                  >
                    <option value="bottom">Unten</option>
                    <option value="top">Oben</option>
                  </select>
                </div>

                <div>
                  <label className="text-sm text-gray-300 mb-2 block">Primärfarbe</label>
                  <input
                    type="color"
                    value={bannerConfig.primaryColor}
                    onChange={(e) => setBannerConfig({ ...bannerConfig, primaryColor: e.target.value })}
                    className="w-full h-10 bg-gray-700 border border-gray-600 rounded-lg cursor-pointer"
                  />
                </div>

                <Button
                  className="w-full bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700"
                  onClick={handleGenerateBanner}
                  disabled={isGenerating}
                >
                  {isGenerating ? (
                    <>
                      <div className="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Generiere Banner...
                    </>
                  ) : (
                    <>
                      <Code className="w-4 h-4 mr-2" />
                      Cookie-Banner generieren
                    </>
                  )}
                </Button>
              </div>
            </section>
          </div>

          {/* Rechte Spalte: Generated Code & Preview */}
          <div className="space-y-6">
            {/* Generated Script */}
            {generatedScript && (
              <section>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                    <Code className="w-5 h-5" />
                    Cookie-Script für Ihre Website
                  </h3>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={handleCopyScript}
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

                <div className="bg-gray-900 rounded-lg p-4 border border-gray-700 max-h-96 overflow-y-auto">
                  <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono">
                    {generatedScript}
                  </pre>
                </div>

                <div className="mt-4 p-4 bg-blue-900/20 rounded-lg border border-blue-500/30">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-blue-200">
                      <p className="font-semibold mb-2">So verwenden Sie den Code:</p>
                      <ol className="list-decimal list-inside space-y-1 text-xs">
                        <li>Kopieren Sie den gesamten Code</li>
                        <li>Fügen Sie ihn vor dem schließenden <code>&lt;/body&gt;</code>-Tag ein</li>
                        <li>Testen Sie den Banner auf Ihrer Website</li>
                        <li>Passen Sie Farben und Texte nach Bedarf an</li>
                      </ol>
                    </div>
                  </div>
                </div>
              </section>
            )}

            {/* Live Preview */}
            {generatedScript && (
              <section>
                <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
                  <Eye className="w-5 h-5" />
                  Live-Vorschau
                </h3>

                <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <div className="bg-gray-900 rounded-lg overflow-hidden" style={{ height: '300px', position: 'relative' }}>
                    {/* Simulated Website Content */}
                    <div className="p-6 space-y-4">
                      <div className="h-8 bg-gray-700 rounded w-3/4"></div>
                      <div className="h-4 bg-gray-800 rounded w-full"></div>
                      <div className="h-4 bg-gray-800 rounded w-5/6"></div>
                      <div className="h-4 bg-gray-800 rounded w-4/5"></div>
                    </div>

                    {/* Simulated Cookie Banner */}
                    <div
                      className="absolute left-0 right-0 bg-gray-800 p-4 border-t border-gray-700 shadow-lg"
                      style={{ [bannerConfig.position]: 0 }}
                    >
                      <div className="max-w-2xl mx-auto">
                        <h4 className="text-white font-semibold text-sm mb-2">🍪 Cookie-Einstellungen</h4>
                        <p className="text-gray-300 text-xs mb-3">
                          Wir verwenden Cookies zur Verbesserung Ihrer Erfahrung.
                        </p>
                        <div className="flex gap-2">
                          <button
                            className="flex-1 px-3 py-2 rounded text-white text-xs font-semibold"
                            style={{ backgroundColor: bannerConfig.primaryColor }}
                          >
                            {bannerConfig.acceptText}
                          </button>
                          <button className="flex-1 px-3 py-2 rounded bg-gray-700 text-white text-xs font-semibold">
                            {bannerConfig.rejectText}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </section>
            )}

            {/* Empty State */}
            {!generatedScript && (
              <div className="h-full flex items-center justify-center bg-gray-800/30 rounded-lg border-2 border-dashed border-gray-700 p-8">
                <div className="text-center">
                  <Cookie className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400 text-sm">
                    Konfigurieren Sie den Banner und klicken Sie auf "Generieren",<br />
                    um den Code zu erhalten.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

