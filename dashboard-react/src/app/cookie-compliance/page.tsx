'use client';

export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Cookie, Settings, Eye, Code, BarChart3, CheckCircle, AlertCircle, Globe, Lock, Zap, ShieldCheck, CreditCard } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '@/contexts/AuthContext';
import apiClient from '@/lib/api';

// Import Cookie Compliance Components
import CookieBannerDesigner from '@/components/cookie-compliance/CookieBannerDesigner';
import ServiceManager from '@/components/cookie-compliance/ServiceManager';
import IntegrationGuide from '@/components/cookie-compliance/IntegrationGuide';
import ConsentStatistics from '@/components/cookie-compliance/ConsentStatistics';
import RevocationChart from '@/components/cookie-compliance/RevocationChart';
import AdvancedSettings from '@/components/cookie-compliance/AdvancedSettings';

export default function CookieCompliancePage() {
  const router = useRouter();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [siteId, setSiteId] = useState<string>('');
  const [config, setConfig] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('design');
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [checkoutError, setCheckoutError] = useState('');
  
  // ✅ NEU: 1 Website pro Account Absicherung
  const [websiteLocked, setWebsiteLocked] = useState(false);
  const [websiteUrl, setWebsiteUrl] = useState<string>('');
  
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.de';

  const handleUnlockCookie = async () => {
    setCheckoutLoading(true);
    setCheckoutError('');
    try {
      const res = await apiClient.post('/api/stripe/create-checkout', {
        plan: 'single',
        modules: ['cookie'],
        billing_period: 'monthly',
        success_url: `${window.location.origin}/cookie-compliance?activated=true`,
        cancel_url: `${window.location.origin}/cookie-compliance`,
      });
      if (res.data.checkout_url) {
        window.location.href = res.data.checkout_url;
      } else {
        setCheckoutError(res.data.detail || 'Checkout konnte nicht gestartet werden.');
      }
    } catch (err: any) {
      setCheckoutError(err.response?.data?.detail || 'Fehler beim Starten des Checkouts.');
    } finally {
      setCheckoutLoading(false);
    }
  };  useEffect(() => {
    loadConfig();
  }, []);
  
  // ✅ Helper für authentifizierte API-Calls
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
  };
  
  const loadConfig = async () => {
    try {
      setLoading(true);
      
      // ✅ ZUERST: Prüfe ob User bereits eine Website konfiguriert hat
      const myConfigResponse = await fetch(`${API_URL}/api/cookie-compliance/my-config`, {
        headers: getAuthHeaders(),
        credentials: 'include',
      });
      
      if (myConfigResponse.ok) {
        const myConfigData = await myConfigResponse.json();
        
        if (myConfigData.success && myConfigData.has_config && myConfigData.data) {
          // ✅ User hat bereits eine Website - diese ist GESPERRT
          const existingConfig = myConfigData.data;
          
          setSiteId(existingConfig.site_id);
          setConfig(existingConfig);
          setWebsiteLocked(true);
          
          // URL aus site_id rekonstruieren oder aus last_scan_url
          if (existingConfig.last_scan_url) {
            setWebsiteUrl(existingConfig.last_scan_url);
          } else {
            // z.B. "complyo-tech" -> "complyo.tech"
            setWebsiteUrl(existingConfig.site_id.replace(/-/g, '.'));
          }
          
          setLoading(false);
          return; // Fertig - keine weitere Suche nötig
        }
        
        // ✅ Wenn keine Config aber registered_site_id vorhanden
        if (myConfigData.registered_site_id) {
          setSiteId(myConfigData.registered_site_id);
          setWebsiteUrl(myConfigData.registered_site_id.replace(/-/g, '.'));
        }
      }
      
      // FALLBACK: Wenn keine Config, versuche Website aus /api/v2/websites
      const websiteResponse = await fetch(`${API_URL}/api/v2/websites`, {
        headers: getAuthHeaders(),
        credentials: 'include',
      });
      
      if (websiteResponse.ok) {
        const websiteData = await websiteResponse.json();
        if (websiteData.success && websiteData.websites?.length) {
          const primaryWebsite = websiteData.websites.find((w: any) => w.is_primary) || websiteData.websites[0];
          const determinedSiteId = generateSiteIdFromUrl(primaryWebsite.url);
          setSiteId(determinedSiteId);
          setWebsiteUrl(primaryWebsite.url);
          
          // Lade Config für diese Website
          const configResponse = await fetch(`${API_URL}/api/cookie-compliance/config/${determinedSiteId}`, {
            headers: getAuthHeaders(),
            credentials: 'include',
          });
          
          if (configResponse.ok) {
            const data = await configResponse.json();
            if (data.success) {
              setConfig(data.data);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error loading config:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const generateSiteIdFromUrl = (url: string): string => {
    try {
      const urlObj = new URL(url.startsWith('http') ? url : `https://${url}`);
      const hostname = urlObj.hostname.replace('www.', '');
      return hostname.replace(/\./g, '-').toLowerCase();
    } catch {
      return 'unknown-site';
    }
  };
  
  const saveConfig = async (newConfig: any) => {
    try {
      const response = await fetch(`${API_URL}/api/cookie-compliance/config`, {
        method: 'POST',
        headers: getAuthHeaders(),
        credentials: 'include',
        body: JSON.stringify({
          ...newConfig,
          site_id: siteId,
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setConfig(newConfig);
          // Nach erstem Speichern ist die Website gesperrt
          setWebsiteLocked(true);
          return true;
        }
      }
      
      return false;
    } catch (error) {
      console.error('Error saving config:', error);
      return false;
    }
  };
  
  if (loading) {
    return (
      <main role="main" aria-label="Cookie-Compliance wird geladen" className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Lade Cookie-Compliance-Konfiguration...</p>
        </div>
      </main>
    );
  }

  // Paywall: Cookie-Modul erforderlich
  const hasCookieModule = user?.active_modules?.includes('cookie');
  if (!hasCookieModule) {
    return (
      <main role="main" className="min-h-screen bg-gray-900 text-white flex items-center justify-center p-4">
        <div className="max-w-lg w-full text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-orange-500/20 rounded-full mb-6">
            <Lock className="w-10 h-10 text-orange-400" />
          </div>
          <h1 className="text-2xl font-bold mb-3">Cookie & DSGVO Modul</h1>
          <p className="text-gray-400 mb-8">
            Um den Cookie-Banner zu konfigurieren und auf Ihrer Website einzubinden, benötigen Sie das
            <strong className="text-white"> Cookie & DSGVO Modul</strong>.
          </p>
          <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6 mb-8 text-left space-y-3">
            <div className="flex items-center gap-3 text-sm text-gray-300">
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
              <span>DSGVO- & TTDSG-konformes Cookie-Banner</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-gray-300">
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
              <span>Automatisches Script-Blocking vor Zustimmung</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-gray-300">
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
              <span>1 Domain – inkl. Einbinde-Code & Integration</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-gray-300">
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
              <span>Consent-Statistiken & Google Consent Mode v2</span>
            </div>
            <div className="flex items-center gap-3 text-sm text-gray-300">
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
              <span>35+ Services (Google Analytics, Facebook Pixel, …)</span>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            {checkoutError && (
              <p className="text-red-400 text-sm text-center w-full">{checkoutError}</p>
            )}
            <Button
              onClick={handleUnlockCookie}
              disabled={checkoutLoading}
              className="bg-orange-500 hover:bg-orange-600 text-white font-semibold gap-2"
            >
              <CreditCard className="w-4 h-4" />
              {checkoutLoading ? 'Wird gestartet…' : 'Jetzt freischalten'}
            </Button>
            <Button
              variant="outline"
              onClick={() => router.push('/')}
              className="border-gray-600 text-gray-300 hover:bg-gray-800 gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Zurück zum Dashboard
            </Button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main role="main" aria-label="Cookie-Compliance Management" className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push('/')}
                className="gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Zurück zum Dashboard
              </Button>
              <div className="h-6 w-px bg-gray-700" />
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-500/20 rounded-lg">
                  <Cookie className="w-5 h-5 text-orange-400" />
                </div>
                <div>
                  <h1 className="text-xl font-bold">Cookie-Compliance</h1>
                  <p className="text-sm text-gray-400">DSGVO-konformes Cookie-Management</p>
                </div>
              </div>
            </div>
            
            {/* ✅ NEU: Zeige gesperrte Website */}
            <div className="flex items-center gap-3">
              {websiteLocked && websiteUrl && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/20 border border-blue-500/30 rounded-lg">
                  <Globe className="w-4 h-4 text-blue-400" />
                  <span className="text-sm text-blue-300 font-medium">{websiteUrl}</span>
                  <Lock className="w-3 h-3 text-blue-400" />
                </div>
              )}
              <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm font-medium flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                Aktiv
              </span>
            </div>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <section aria-label="Cookie-Compliance Konfiguration" className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* ✅ NEU: Hinweis 1 Website pro Account */}
        {websiteLocked && (
          <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg flex items-center gap-3">
            <Lock className="w-5 h-5 text-blue-400 flex-shrink-0" />
            <div>
              <p className="text-sm text-blue-300 font-medium">1 Website pro Account</p>
              <p className="text-xs text-gray-400">
                Ihr Cookie-Banner ist für <strong className="text-blue-300">{websiteUrl}</strong> konfiguriert. 
                Diese Einstellung kann nicht geändert werden.
              </p>
            </div>
          </div>
        )}
        
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20 hover:border-green-500/40 transition-all duration-200 hover:shadow-lg hover:shadow-green-900/20">
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-sm font-medium text-green-300 mb-1">Opt-In-Rate</div>
                  <div className="text-3xl font-bold text-green-400">--</div>
                  <div className="text-xs text-green-300/70 mt-1">Letzte 30 Tage</div>
                </div>
                <div className="p-2 bg-green-500/20 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20 hover:border-blue-500/40 transition-all duration-200 hover:shadow-lg hover:shadow-blue-900/20">
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-sm font-medium text-blue-300 mb-1">Consents</div>
                  <div className="text-3xl font-bold text-blue-400">--</div>
                  <div className="text-xs text-blue-300/70 mt-1">Gesamt</div>
                </div>
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <BarChart3 className="w-5 h-5 text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border-purple-500/20 hover:border-purple-500/40 transition-all duration-200 hover:shadow-lg hover:shadow-purple-900/20">
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-sm font-medium text-purple-300 mb-1">Services</div>
                  <div className="text-3xl font-bold text-purple-400">{config?.services?.length || 0}</div>
                  <div className="text-xs text-purple-300/70 mt-1">Aktiv</div>
                </div>
                <div className="p-2 bg-purple-500/20 rounded-lg">
                  <Eye className="w-5 h-5 text-purple-400" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-orange-500/10 to-orange-600/5 border-orange-500/20 hover:border-orange-500/40 transition-all duration-200 hover:shadow-lg hover:shadow-orange-900/20">
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-sm font-medium text-orange-300 mb-1">Banner</div>
                  <div className="text-xl font-bold text-orange-400 capitalize">
                    {config?.layout?.replace('_', ' ') || 'Banner Bottom'}
                  </div>
                  <div className="text-xs text-orange-300/70 mt-1">Layout</div>
                </div>
                <div className="p-2 bg-orange-500/20 rounded-lg">
                  <Settings className="w-5 h-5 text-orange-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* ✅ NEU: Klare Meldung wenn Scan abgeschlossen aber KEINE Cookies gefunden */}
        {config?.scan_completed && (!config?.services || config.services.length === 0) && (
          <Card className="mb-6 bg-gradient-to-r from-green-500/20 to-green-600/10 border-green-500/30 hover:border-green-500/50 transition-all shadow-lg shadow-green-900/20">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-green-500/20 rounded-lg flex-shrink-0">
                  <CheckCircle className="w-6 h-6 text-green-400" />
                </div>
                <div className="flex-1">
                  <div className="font-bold text-white mb-1 text-lg">✅ Kein Cookie-Banner erforderlich!</div>
                  <div className="text-sm text-gray-300 mb-2">
                    Unser Scan hat <strong className="text-green-400">keine Tracking-Cookies</strong> auf Ihrer Website gefunden.
                    Ihre Website verwendet nur essenzielle Cookies, die keine Einwilligung benötigen.
                  </div>
                  <div className="text-xs text-gray-400 bg-gray-800/50 p-3 rounded-lg mt-3">
                    <strong className="text-gray-300">Was bedeutet das?</strong>
                    <ul className="list-disc list-inside mt-1 space-y-1">
                      <li>Sie müssen keinen Cookie-Banner einbinden</li>
                      <li>Ihre Website ist bereits DSGVO-konform bezüglich Cookies</li>
                      <li>Falls Sie später Tracking-Tools (wie Google Analytics) hinzufügen, scannen Sie erneut</li>
                    </ul>
                  </div>
                </div>
                <Button
                  onClick={() => setActiveTab('services')}
                  variant="outline"
                  className="border-green-500/50 text-green-400 hover:bg-green-500/10"
                >
                  Services manuell hinzufügen
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
        
        {/* Setup Alert - NUR wenn Scan NICHT abgeschlossen oder KEINE Config */}
        {(!config?.scan_completed && (!config?.services || config.services.length === 0)) && (
          <Card className="mb-6 bg-gradient-to-r from-orange-500/20 to-orange-600/10 border-orange-500/30 hover:border-orange-500/50 transition-all shadow-lg shadow-orange-900/20">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-orange-500/20 rounded-lg flex-shrink-0">
                  <AlertCircle className="w-5 h-5 text-orange-400" />
                </div>
                <div className="flex-1">
                  <div className="font-bold text-white mb-1">🚀 Setup erforderlich</div>
                  <div className="text-sm text-gray-300">
                    Scannen Sie Ihre Website um Cookies zu erkennen, oder wählen Sie Services manuell aus.
                  </div>
                </div>
                <Button
                  onClick={() => setActiveTab('services')}
                  className="bg-orange-500 hover:bg-orange-600 shadow-lg shadow-orange-500/30 transition-all hover:scale-105"
                >
                  Jetzt einrichten
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
        
        {/* Main Tabs */}
        <Card className="bg-gray-800/50 border-gray-700 backdrop-blur-sm shadow-xl">
          <CardContent className="pt-6">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
              <TabsList className="grid w-full grid-cols-5 bg-gray-900/50 p-1 h-auto">
                <TabsTrigger 
                  value="design" 
                  className="gap-2 data-[state=active]:bg-orange-500 data-[state=active]:text-white transition-all py-3"
                >
                  <Settings className="w-4 h-4" />
                  <span className="hidden sm:inline">Design</span>
                </TabsTrigger>
                <TabsTrigger 
                  value="services" 
                  className="gap-2 data-[state=active]:bg-orange-500 data-[state=active]:text-white transition-all py-3"
                >
                  <Eye className="w-4 h-4" />
                  <span className="hidden sm:inline">Services</span>
                </TabsTrigger>
                <TabsTrigger 
                  value="advanced" 
                  className="relative gap-2 data-[state=active]:bg-orange-500 data-[state=active]:text-white transition-all py-3"
                >
                  <Zap className="w-4 h-4" />
                  <span className="hidden sm:inline">Erweitert</span>
                  <span className="absolute -top-1 -right-1 px-1 py-0.5 text-[10px] rounded bg-red-500 text-white">Neu</span>
                </TabsTrigger>
                <TabsTrigger 
                  value="integration" 
                  className="gap-2 data-[state=active]:bg-orange-500 data-[state=active]:text-white transition-all py-3"
                >
                  <Code className="w-4 h-4" />
                  <span className="hidden sm:inline">Integration</span>
                </TabsTrigger>
                <TabsTrigger 
                  value="statistics" 
                  className="gap-2 data-[state=active]:bg-orange-500 data-[state=active]:text-white transition-all py-3"
                >
                  <BarChart3 className="w-4 h-4" />
                  <span className="hidden sm:inline">Statistiken</span>
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="design">
                <CookieBannerDesigner
                  config={config}
                  siteId={siteId}
                  onSave={saveConfig}
                />
              </TabsContent>
              
              <TabsContent value="services">
                <ServiceManager
                  selectedServices={config?.services || []}
                  onServicesChange={(services) => {
                    saveConfig({ ...config, services });
                  }}
                  websiteUrl={websiteUrl}
                  websiteLocked={websiteLocked}
                  siteId={siteId}
                />
              </TabsContent>
              
              <TabsContent value="advanced">
                <AdvancedSettings
                  siteId={siteId}
                  config={config}
                  onSave={saveConfig}
                />
              </TabsContent>
              
              <TabsContent value="integration">
                <IntegrationGuide siteId={siteId} config={config} />
              </TabsContent>
              
              <TabsContent value="statistics">
                <ConsentStatistics siteId={siteId} />
                <div className="mt-6">
                  <RevocationChart siteId={siteId} />
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
