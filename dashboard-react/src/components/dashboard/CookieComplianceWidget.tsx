'use client';

import React, { useState, useEffect } from 'react';
import { Cookie, ExternalLink, Code, Copy, CheckCircle, Shield, Settings, BarChart3, Zap } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useRouter } from 'next/navigation';

export const CookieComplianceWidget: React.FC = () => {
  const router = useRouter();
  const [copied, setCopied] = useState(false);
  const [stats, setStats] = useState<any>(null);

  const integrationCode = `<!-- Complyo Cookie-Compliance Widget -->
<script 
  src="https://api.complyo.tech/api/widgets/cookie-compliance.js" 
  data-site-id="my-site"
  async
></script>`;

  useEffect(() => {
    // Load quick stats
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';
      const response = await fetch(`${API_URL}/api/cookie-compliance/stats/my-site?days=7`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setStats(data);
        }
      } else if (response.status === 404) {
        // ✅ Cookie-Compliance noch nicht konfiguriert - graceful ignorieren
        console.log('Cookie-Compliance noch nicht konfiguriert');
      }
    } catch (error) {
      // ✅ Netzwerkfehler - graceful ignorieren
      console.log('Cookie-Compliance stats nicht verfügbar');
    }
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(integrationCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOpenSettings = () => {
    router.push('/cookie-compliance');
  };

  return (
    <Card className="mb-8">
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-3">
          <CardTitle className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-orange-500/20 to-red-500/20 rounded-xl">
              <Cookie className="w-6 h-6 text-orange-400" />
            </div>
            <div>
              <span className="flex items-center gap-2">
                Cookie-Compliance Management
                <Badge variant="success" className="text-xs">
                  Neu
                </Badge>
              </span>
              <p className="text-sm text-zinc-400 mt-1 font-normal">
                DSGVO-konformes Cookie-Banner mit Consent-Management
              </p>
            </div>
          </CardTitle>
          <Button
            onClick={handleOpenSettings}
            variant="secondary"
            size="sm"
            className="gap-2"
          >
            <Settings className="w-4 h-4" />
            Einrichten
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Quick Stats */}
          <div className="lg:col-span-1 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-4">
              <BarChart3 className="w-4 h-4" />
              Letzte 7 Tage
            </h3>
            
            <div className="space-y-3">
              <div className="glass-card p-4 rounded-xl">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs text-zinc-400 font-medium">Opt-In-Rate</span>
                  <span className="text-lg font-bold text-green-400">
                    {stats?.summary?.acceptance_rate?.toFixed(1) || '--'}%
                  </span>
                </div>
                <div className="w-full bg-zinc-800 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${stats?.summary?.acceptance_rate || 0}%` }}
                  />
                </div>
              </div>

              <div className="glass-card p-4 rounded-xl">
                <div className="text-xs text-zinc-400 font-medium mb-1">Consents</div>
                <div className="text-2xl font-bold text-white">
                  {stats?.summary?.total_impressions?.toLocaleString() || '0'}
                </div>
              </div>

              <div className="glass-card p-4 rounded-xl">
                <div className="text-xs text-zinc-400 font-medium mb-1">Services</div>
                <div className="text-2xl font-bold text-white">
                  20
                </div>
                <div className="text-xs text-zinc-500 mt-1">verfügbar</div>
              </div>
            </div>
          </div>

          {/* Features */}
          <div className="lg:col-span-1 space-y-4">
            <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
              <Shield className="w-4 h-4" />
              Features
            </h3>
            
            <div className="space-y-2.5">
              <div className="flex items-start gap-3 text-sm">
                <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium">DSGVO & TTDSG konform</div>
                  <div className="text-xs text-gray-400">Rechtssichere Einwilligungen</div>
                </div>
              </div>

              <div className="flex items-start gap-3 text-sm">
                <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium">Content Blocker</div>
                  <div className="text-xs text-gray-400">YouTube, Google Maps, Analytics</div>
                </div>
              </div>

              <div className="flex items-start gap-3 text-sm">
                <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium">20+ Service-Vorlagen</div>
                  <div className="text-xs text-gray-400">Google, Facebook, TikTok, etc.</div>
                </div>
              </div>

              <div className="flex items-start gap-3 text-sm">
                <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium">Vollständig anpassbar</div>
                  <div className="text-xs text-gray-400">Farben, Texte, Layout</div>
                </div>
              </div>

              <div className="flex items-start gap-3 text-sm">
                <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium">Consent-Statistiken</div>
                  <div className="text-xs text-gray-400">Opt-In-Rate Analytics</div>
                </div>
              </div>

              <div className="flex items-start gap-3 text-sm">
                <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="text-white font-medium">WCAG 2.2 Level AA</div>
                  <div className="text-xs text-gray-400">Barrierefrei</div>
                </div>
              </div>
            </div>
          </div>

          {/* Integration Code */}
          <div className="lg:col-span-1 space-y-4">
            <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
              <Code className="w-4 h-4" />
              Integration
            </h3>

            <div className="space-y-3">
              <div className="relative">
                <pre className="bg-gray-950 text-green-400 p-4 rounded-lg text-xs overflow-x-auto border border-gray-800">
                  <code>{integrationCode}</code>
                </pre>
                <Button
                  onClick={handleCopyCode}
                  size="sm"
                  variant="ghost"
                  className="absolute top-2 right-2 h-8 w-8 p-0"
                >
                  {copied ? (
                    <CheckCircle className="w-4 h-4 text-green-400" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </Button>
              </div>

              <div className="flex flex-col gap-2">
                <Button
                  onClick={handleOpenSettings}
                  className="w-full gap-2 bg-orange-500 hover:bg-orange-600"
                >
                  <Settings className="w-4 h-4" />
                  Banner konfigurieren
                </Button>

                <Button
                  variant="outline"
                  className="w-full gap-2"
                  onClick={() => window.open('https://docs.complyo.tech/cookie-compliance', '_blank')}
                >
                  <ExternalLink className="w-4 h-4" />
                  Dokumentation
                </Button>
              </div>

              <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <div className="flex items-start gap-2">
                  <Zap className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <div className="text-xs text-blue-300">
                    <strong>Tipp:</strong> Das Cookie-Banner wird automatisch auf Ihrer Website angezeigt. 
                    Alle Einstellungen können im Dashboard angepasst werden.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-6 pt-6 border-t border-gray-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/20 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-400" />
              </div>
              <div>
                <div className="text-sm font-semibold text-white">
                  Cookie-Compliance ist im AI Plan enthalten
                </div>
                <div className="text-xs text-gray-400">
                  Keine zusätzlichen Kosten - Vollständig integriert in Complyo
                </div>
              </div>
            </div>
            <Button
              onClick={handleOpenSettings}
              variant="outline"
              className="gap-2"
            >
              Jetzt einrichten
              <ExternalLink className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

