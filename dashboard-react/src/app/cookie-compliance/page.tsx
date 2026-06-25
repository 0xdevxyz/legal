'use client';

export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Cookie, Settings, Eye, Code, BarChart3, CheckCircle, AlertCircle, Globe, Lock, Zap, CreditCard, TrendingUp, Radio } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAuth } from '@/contexts/AuthContext';
import apiClient from '@/lib/api';
import { apiClient as httpApiClient } from '@/lib/api-client';

// Import Cookie Compliance Components
import CookieBannerDesigner from '@/components/cookie-compliance/CookieBannerDesigner';
import ServiceManager from '@/components/cookie-compliance/ServiceManager';
import IntegrationGuide from '@/components/cookie-compliance/IntegrationGuide';
import ConsentStatistics from '@/components/cookie-compliance/ConsentStatistics';
import RevocationChart from '@/components/cookie-compliance/RevocationChart';
import AdvancedSettings from '@/components/cookie-compliance/AdvancedSettings';
import CookieSetupWizard from '@/components/cookie-compliance/CookieSetupWizard';
import ScanMonitor from '@/components/cookie-compliance/ScanMonitor';

export default function CookieCompliancePage() {
  const router = useRouter();
  const { user } = useAuth();
  // Agentur/Expert verwalten mehrere Seiten → kein „1 Website pro Account"-Lock.
  const isAgency = user?.plan_type === 'agency' || user?.plan_type === 'expert';
  const [loading, setLoading] = useState(true);
  const [siteId, setSiteId] = useState<string>('');
  const [config, setConfig] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('design');
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [checkoutError, setCheckoutError] = useState('');
  const [quickStats, setQuickStats] = useState<any>(null);
  const [showSetupWizard, setShowSetupWizard] = useState(false);

  const [websiteLocked, setWebsiteLocked] = useState(false);
  const [websiteUrl, setWebsiteUrl] = useState<string>('');
  // Agentur/Expert: alle verwaltbaren Websites zur Auswahl
  const [availableSites, setAvailableSites] = useState<Array<{ site_id: string; url: string; is_primary: boolean }>>([]);

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
  };

  useEffect(() => {
    // Auf geladenen User warten, damit der Plan (Agentur?) bekannt ist.
    if (!user) return;
    if (isAgency) {
      loadAgencySites();
    } else {
      loadConfig();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.plan_type]);

  useEffect(() => {
    if (siteId) loadQuickStats(siteId);
  }, [siteId]);

  const loadQuickStats = async (id: string) => {
    try {
      const data = await httpApiClient.get(`/api/cookie-compliance/stats/${id}?days=30`) as any;
      if (data?.success) setQuickStats(data);
    } catch {
      setQuickStats(null);
    }
  };
  
  const loadConfig = async () => {
    try {
      setLoading(true);
      
      // ✅ ZUERST: Prüfe ob User bereits eine Website konfiguriert hat
      let myConfigData: any = null;
      try {
        myConfigData = await httpApiClient.get('/api/cookie-compliance/my-config');
      } catch {
        myConfigData = null;
      }
      
      if (myConfigData) {
        
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
      let websiteData: any = null;
      try {
        websiteData = await httpApiClient.get('/api/v2/websites');
      } catch {
        websiteData = null;
      }
      
      if (websiteData && websiteData.success && websiteData.websites?.length) {
        const primaryWebsite = websiteData.websites.find((w: any) => w.is_primary) || websiteData.websites[0];
        const determinedSiteId = generateSiteIdFromUrl(primaryWebsite.url);
        setSiteId(determinedSiteId);
        setWebsiteUrl(primaryWebsite.url);
        
        // Lade Config für diese Website
        try {
          const configData = await httpApiClient.get(`/api/cookie-compliance/config/${determinedSiteId}`) as any;
          if (configData.success) {
            setConfig(configData.data);
          }
        } catch {
        }
      }
    } catch (error) {
      console.error('Error loading config:', error);
    } finally {
      setLoading(false);
    }
  };

  // Wizard nach Laden einblenden wenn noch kein Scan durchgeführt wurde
  useEffect(() => {
    if (!loading && !config?.scan_completed && (!config?.services || (config.services as string[]).length === 0)) {
      setShowSetupWizard(true);
    }
  }, [loading, config]);
  
  const generateSiteIdFromUrl = (url: string): string => {
    try {
      const urlObj = new URL(url.startsWith('http') ? url : `https://${url}`);
      const hostname = urlObj.hostname.replace('www.', '');
      return hostname.replace(/\./g, '-').toLowerCase();
    } catch {
      return 'unknown-site';
    }
  };

  // Agentur/Expert: alle Websites laden und die ausgewählte konfigurieren.
  const loadAgencySites = async () => {
    try {
      setLoading(true);
      let websiteData: any = null;
      try {
        websiteData = await httpApiClient.get('/api/v2/websites');
      } catch {
        websiteData = null;
      }

      const list: Array<{ site_id: string; url: string; is_primary: boolean }> = [];
      const seen = new Set<string>();
      for (const w of (websiteData?.websites || [])) {
        const sid = generateSiteIdFromUrl(w.url);
        if (sid === 'unknown-site' || seen.has(sid)) continue;
        seen.add(sid);
        list.push({ site_id: sid, url: w.url, is_primary: !!w.is_primary });
      }
      setAvailableSites(list);

      if (list.length === 0) {
        // Keine Websites → klassischer Single-Flow als Fallback
        await loadConfig();
        return;
      }

      const initial = list.find((s) => s.is_primary) || list[0];
      await loadSiteConfig(initial.site_id, initial.url);
    } catch (error) {
      console.error('Error loading agency sites:', error);
    } finally {
      setLoading(false);
    }
  };

  // Config für eine konkrete site_id laden (Agentur-Wechsel).
  const loadSiteConfig = async (sid: string, url?: string) => {
    setSiteId(sid);
    if (url) setWebsiteUrl(url);
    try {
      const configData = await httpApiClient.get(`/api/cookie-compliance/config/${sid}`) as any;
      if (configData?.success) {
        setConfig({ ...configData.data, site_id: sid });
      }
    } catch (error) {
      console.error('Error loading site config:', error);
    }
  };


  const saveConfig = async (newConfig: any) => {
    try {
      const data = await httpApiClient.post('/api/cookie-compliance/config', {
        ...newConfig,
        site_id: siteId,
      }) as any;
      
      if (data.success) {
        setConfig(newConfig);
        // Nach erstem Speichern ist die Website gesperrt
        setWebsiteLocked(true);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Error saving config:', error);
      return false;
    }
  };
  
  if (loading) {
    return (
      <main role="main" aria-label="Cookie-Compliance wird geladen" className="px-4 sm:px-6 py-6 min-h-[60vh] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[color:var(--lime)] mx-auto mb-4"></div>
          <p className="dark:text-gray-400 text-gray-600">Lade Cookie-Compliance-Konfiguration...</p>
        </div>
      </main>
    );
  }

  // Paywall: Cookie-Modul erforderlich (Backend setzt es bei pro/agency/expert/update automatisch)
  const hasCookieModule = user?.active_modules?.includes('cookie') || ['pro', 'agency', 'expert', 'update'].includes(user?.plan_type ?? '');
  if (!hasCookieModule) {
    return (
      <main role="main" className="px-4 sm:px-6 py-6 min-h-[60vh] flex items-center justify-center p-4">
        <div className="max-w-lg w-full text-center">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-[color:var(--lime)]/20 rounded-full mb-6">
            <Lock className="w-10 h-10 text-[color:var(--lime)]" />
          </div>
          <h1 className="text-2xl font-bold mb-3">Cookie & DSGVO Modul</h1>
          <p className="dark:text-gray-400 text-gray-600 mb-8">
            Um den Cookie-Banner zu konfigurieren und auf Ihrer Website einzubinden, benötigen Sie das
            <strong className="dark:text-white text-gray-900"> Cookie & DSGVO Modul</strong>.
          </p>
          <div className="dark:bg-zinc-800/50 bg-gray-100 border dark:border-zinc-700 border-gray-200 rounded-xl p-6 mb-8 text-left space-y-3">
            <div className="flex items-center gap-3 text-sm dark:text-gray-300 text-gray-700">
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
              <span>DSGVO- & TTDSG-konformes Cookie-Banner</span>
            </div>
            <div className="flex items-center gap-3 text-sm dark:text-gray-300 text-gray-700">
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
              <span>Automatisches Script-Blocking vor Zustimmung</span>
            </div>
            <div className="flex items-center gap-3 text-sm dark:text-gray-300 text-gray-700">
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
              <span>1 Domain – inkl. Einbinde-Code & Integration</span>
            </div>
            <div className="flex items-center gap-3 text-sm dark:text-gray-300 text-gray-700">
              <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
              <span>Consent-Statistiken & Google Consent Mode v2</span>
            </div>
            <div className="flex items-center gap-3 text-sm dark:text-gray-300 text-gray-700">
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
              className="bg-[var(--lime)] hover:bg-[var(--lime-bright)] dark:text-white text-gray-900 font-semibold gap-2"
            >
              <CreditCard className="w-4 h-4" />
              {checkoutLoading ? 'Wird gestartet…' : 'Jetzt freischalten'}
            </Button>
            <Button
              variant="outline"
              onClick={() => router.push('/')}
              className="dark:border-zinc-700 border-gray-200 dark:text-gray-300 text-gray-700 dark:hover:bg-zinc-800 hover:bg-gray-100 gap-2"
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
    <main role="main" aria-label="Cookie-Compliance Management" className="px-4 sm:px-6 py-6">
      {/* Ersteinrichtungs-Wizard */}
      {showSetupWizard && (
        <CookieSetupWizard
          websiteUrl={websiteUrl}
          websiteLocked={websiteLocked && !isAgency}
          siteId={siteId}
          onComplete={() => { setShowSetupWizard(false); loadConfig(); }}
          onSkip={() => setShowSetupWizard(false)}
        />
      )}
      {/* Header */}
      <header className="border-b dark:border-zinc-800 border-gray-200 dark:bg-zinc-900/50 bg-white/70 backdrop-blur-sm sticky top-0 z-10">
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
              <div className="h-6 w-px dark:bg-zinc-800 bg-gray-100" />
              <div className="flex items-center gap-3">
                <div className="p-2 bg-[color:var(--lime)]/20 rounded-lg">
                  <Cookie className="w-5 h-5 text-[color:var(--lime)]" />
                </div>
                <div>
                  <h1 className="text-xl font-bold">Cookie-Compliance</h1>
                  <p className="text-sm dark:text-gray-400 text-gray-600">DSGVO-konformes Cookie-Management</p>
                </div>
              </div>
            </div>
            
            {/* ✅ NEU: Zeige gesperrte Website */}
            <div className="flex items-center gap-3">
              {/* Agentur/Expert: Website-Auswahl statt Lock */}
              {isAgency && availableSites.length > 0 && (
                <div className="flex items-center gap-2">
                  <Globe className="w-4 h-4 text-blue-400" />
                  <Select value={siteId} onValueChange={(v) => loadSiteConfig(v, availableSites.find((s) => s.site_id === v)?.url)}>
                    <SelectTrigger className="w-[240px] h-9 text-sm">
                      <SelectValue placeholder="Website wählen" />
                    </SelectTrigger>
                    <SelectContent>
                      {availableSites.map((s) => (
                        <SelectItem key={s.site_id} value={s.site_id}>
                          {s.url.replace(/^https?:\/\//, '')}{s.is_primary ? ' ★' : ''}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              {websiteLocked && websiteUrl && !isAgency && (
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
        
        {/* ✅ NEU: Hinweis 1 Website pro Account — nur für Einzel-Pläne, nicht Agentur */}
        {websiteLocked && !isAgency && (
          <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg flex items-center gap-3">
            <Lock className="w-5 h-5 text-blue-400 flex-shrink-0" />
            <div>
              <p className="text-sm text-blue-300 font-medium">1 Website pro Account</p>
              <p className="text-xs dark:text-gray-400 text-gray-600">
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
                  {quickStats ? (
                    <>
                      <div className="text-3xl font-bold text-green-400">{quickStats.summary.acceptance_rate.toFixed(1)}%</div>
                      <div className="text-xs text-green-300/70 mt-1">{quickStats.summary.accepted_all.toLocaleString('de-DE')} Consents</div>
                    </>
                  ) : (
                    <>
                      <div className="text-xl font-semibold text-green-300/50 mt-1">Noch keine Daten</div>
                      <button onClick={() => setActiveTab('integration')} className="text-xs text-green-400 underline mt-1 hover:text-green-300">Banner einbinden →</button>
                    </>
                  )}
                </div>
                <div className="p-2 bg-green-500/20 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-green-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20 hover:border-blue-500/40 transition-all duration-200 hover:shadow-lg hover:shadow-blue-900/20">
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-sm font-medium text-blue-300 mb-1">Consents</div>
                  {quickStats ? (
                    <>
                      <div className="text-3xl font-bold text-blue-400">{quickStats.summary.total_impressions.toLocaleString('de-DE')}</div>
                      <div className="text-xs text-blue-300/70 mt-1">Letzte 30 Tage</div>
                    </>
                  ) : (
                    <>
                      <div className="text-xl font-semibold text-blue-300/50 mt-1">Noch keine Daten</div>
                      <div className="text-xs text-blue-300/50 mt-1">Letzte 30 Tage</div>
                    </>
                  )}
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
                  <div className="text-3xl font-bold text-purple-400">{Array.isArray(config?.services) ? config.services.length : 0}</div>
                  <div className="text-xs text-purple-300/70 mt-1">Konfiguriert</div>
                </div>
                <div className="p-2 bg-purple-500/20 rounded-lg">
                  <Eye className="w-5 h-5 text-purple-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-teal-500/10 to-teal-600/5 border-teal-500/20 hover:border-[color:var(--lime)]/40 transition-all duration-200 hover:shadow-lg hover:shadow-teal-900/20">
            <CardContent className="pt-6">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-sm font-medium text-[color:var(--lime-bright)] mb-1">Banner</div>
                  <div className="text-xl font-bold text-[color:var(--lime)] capitalize">
                    {config?.layout?.replace(/_/g, ' ') || 'Banner Bottom'}
                  </div>
                  <div className="text-xs text-teal-300/70 mt-1">Layout</div>
                </div>
                <div className="p-2 bg-[color:var(--lime)]/20 rounded-lg">
                  <Settings className="w-5 h-5 text-[color:var(--lime)]" />
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
                  <div className="font-bold dark:text-white text-gray-900 mb-1 text-lg">✅ Kein Cookie-Banner erforderlich!</div>
                  <div className="text-sm dark:text-gray-300 text-gray-700 mb-2">
                    Unser Scan hat <strong className="text-green-400">keine Tracking-Cookies</strong> auf Ihrer Website gefunden.
                    Ihre Website verwendet nur essenzielle Cookies, die keine Einwilligung benötigen.
                  </div>
                  <div className="text-xs dark:text-gray-400 text-gray-600 dark:bg-zinc-800/50 bg-gray-100 p-3 rounded-lg mt-3">
                    <strong className="dark:text-gray-300 text-gray-700">Was bedeutet das?</strong>
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
          <Card className="mb-6 bg-gradient-to-r from-teal-500/20 to-teal-600/10 border-teal-500/30 hover:border-teal-500/50 transition-all shadow-lg shadow-teal-900/20">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3 mb-4">
                <div className="p-2 bg-[color:var(--lime)]/20 rounded-lg flex-shrink-0">
                  <AlertCircle className="w-5 h-5 text-[color:var(--lime)]" />
                </div>
                <div className="flex-1">
                  <div className="font-bold dark:text-white text-gray-900 mb-1">Setup erforderlich</div>
                  <div className="text-sm dark:text-gray-300 text-gray-700">Folgen Sie diesen 3 Schritten, um Ihren DSGVO-konformen Cookie-Banner einzurichten.</div>
                </div>
                <Button
                  onClick={() => setActiveTab('services')}
                  className="bg-[var(--lime)] hover:bg-[var(--lime-bright)] shadow-lg shadow-teal-500/30 transition-all hover:scale-105 flex-shrink-0"
                >
                  Jetzt einrichten
                </Button>
              </div>
              <div className="grid grid-cols-3 gap-3 mt-2">
                {[
                  { step: 1, label: 'Website scannen', desc: 'Cookies automatisch erkennen', tab: 'services', icon: Eye },
                  { step: 2, label: 'Services bestätigen', desc: 'Tracking-Dienste konfigurieren', tab: 'services', icon: Settings },
                  { step: 3, label: 'Code einbinden', desc: 'Banner auf Ihrer Website', tab: 'integration', icon: Code },
                ].map(({ step, label, desc, tab, icon: Icon }) => (
                  <button
                    key={step}
                    onClick={() => setActiveTab(tab)}
                    className="flex items-center gap-3 p-3 dark:bg-zinc-800/60 bg-gray-100 rounded-lg border dark:border-zinc-700 border-gray-200 hover:border-[color:var(--lime)]/40 transition-all text-left group"
                  >
                    <div className="w-7 h-7 rounded-full bg-[color:var(--lime)]/20 border border-teal-500/40 flex items-center justify-center text-[color:var(--lime)] font-bold text-sm flex-shrink-0 group-hover:bg-teal-500/30">
                      {step}
                    </div>
                    <div className="min-w-0">
                      <div className="text-sm font-medium dark:text-white text-gray-900 truncate">{label}</div>
                      <div className="text-xs dark:text-gray-400 text-gray-600 truncate">{desc}</div>
                    </div>
                  </button>
                ))}
              </div>
              <button
                onClick={() => setShowSetupWizard(true)}
                className="mt-3 w-full text-center text-xs text-[color:var(--lime)] hover:text-[color:var(--lime-bright)] underline transition-colors"
              >
                Ersteinrichtungs-Guide öffnen →
              </button>
            </CardContent>
          </Card>
        )}
        
        {/* Main Tabs */}
        <Card className="dark:bg-zinc-800/50 bg-gray-100 dark:border-zinc-700 border-gray-200 backdrop-blur-sm shadow-xl">
          <CardContent className="pt-6">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
              {/* Mobile: Select dropdown */}
              <div className="sm:hidden">
                <Select value={activeTab} onValueChange={setActiveTab}>
                  <SelectTrigger className="w-full dark:bg-zinc-900/50 bg-white/70 dark:border-zinc-700 border-gray-200 dark:text-white text-gray-900">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-900 dark:border-zinc-700 border-gray-200">
                    <SelectItem value="design" className="dark:text-white text-gray-900">Design</SelectItem>
                    <SelectItem value="services" className="dark:text-white text-gray-900">Services</SelectItem>
                    <SelectItem value="advanced" className="dark:text-white text-gray-900">Erweitert</SelectItem>
                    <SelectItem value="integration" className="dark:text-white text-gray-900">Integration</SelectItem>
                    <SelectItem value="statistics" className="dark:text-white text-gray-900">Statistiken</SelectItem>
                    <SelectItem value="monitoring" className="dark:text-white text-gray-900">Überwachung</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {/* Desktop: Tab bar */}
              <TabsList className="hidden sm:grid w-full grid-cols-6 dark:bg-zinc-900/50 bg-white/70 p-1 h-auto">
                <TabsTrigger
                  value="design"
                  className="gap-2 data-[state=active]:bg-teal-500 data-[state=active]:text-white transition-all py-3"
                >
                  <Settings className="w-4 h-4 flex-shrink-0" />
                  <span>Design</span>
                </TabsTrigger>
                <TabsTrigger
                  value="services"
                  className="gap-2 data-[state=active]:bg-teal-500 data-[state=active]:text-white transition-all py-3"
                >
                  <Eye className="w-4 h-4 flex-shrink-0" />
                  <span>Services</span>
                </TabsTrigger>
                <TabsTrigger
                  value="advanced"
                  className="relative gap-2 data-[state=active]:bg-teal-500 data-[state=active]:text-white transition-all py-3"
                >
                  <Zap className="w-4 h-4 flex-shrink-0" />
                  <span>Erweitert</span>
                  <span className="absolute -top-1 -right-1 px-1 py-0.5 text-[10px] rounded bg-red-500 dark:text-white text-gray-900">Neu</span>
                </TabsTrigger>
                <TabsTrigger
                  value="integration"
                  className="gap-2 data-[state=active]:bg-teal-500 data-[state=active]:text-white transition-all py-3"
                >
                  <Code className="w-4 h-4 flex-shrink-0" />
                  <span>Integration</span>
                </TabsTrigger>
                <TabsTrigger
                  value="statistics"
                  className="gap-2 data-[state=active]:bg-teal-500 data-[state=active]:text-white transition-all py-3"
                >
                  <BarChart3 className="w-4 h-4 flex-shrink-0" />
                  <span>Statistiken</span>
                </TabsTrigger>
                <TabsTrigger
                  value="monitoring"
                  className="relative gap-2 data-[state=active]:bg-teal-500 data-[state=active]:text-white transition-all py-3"
                >
                  <Radio className="w-4 h-4 flex-shrink-0" />
                  <span>Überwachung</span>
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
                  websiteLocked={websiteLocked && !isAgency}
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

              <TabsContent value="monitoring">
                <ScanMonitor
                  siteId={siteId}
                  websiteUrl={websiteUrl}
                  lastScanDate={config?.scan_completed_at}
                  storedServices={Array.isArray(config?.services) ? config.services : []}
                />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
