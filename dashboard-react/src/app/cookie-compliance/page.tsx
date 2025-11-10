'use client';

export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Cookie, Settings, Eye, Code, BarChart3, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

// Import Cookie Compliance Components
import CookieBannerDesigner from '@/components/cookie-compliance/CookieBannerDesigner';
import ServiceManager from '@/components/cookie-compliance/ServiceManager';
import IntegrationGuide from '@/components/cookie-compliance/IntegrationGuide';
import ConsentStatistics from '@/components/cookie-compliance/ConsentStatistics';

export default function CookieCompliancePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [siteId, setSiteId] = useState<string>('my-site');
  const [config, setConfig] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('design');
  
  useEffect(() => {
    loadConfig();
  }, []);
  
  const loadConfig = async () => {
    try {
      setLoading(true);
      
      const response = await fetch(`/api/cookie-compliance/config/${siteId}`, {
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setConfig(data.data);
          setSiteId(data.data.site_id || 'my-site');
        }
      }
    } catch (error) {
      console.error('Error loading config:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const saveConfig = async (newConfig: any) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';
      const response = await fetch(`${API_URL}/api/cookie-compliance/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
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
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Lade Cookie-Compliance-Konfiguration...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm sticky top-0 z-10">
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
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm font-medium flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                Aktiv
              </span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
        
        {/* Setup Alert */}
        {(!config?.services || config.services.length === 0) && (
          <Card className="mb-6 bg-gradient-to-r from-orange-500/20 to-orange-600/10 border-orange-500/30 hover:border-orange-500/50 transition-all shadow-lg shadow-orange-900/20">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-orange-500/20 rounded-lg flex-shrink-0">
                  <AlertCircle className="w-5 h-5 text-orange-400" />
                </div>
                <div className="flex-1">
                  <div className="font-bold text-white mb-1">🚀 Setup erforderlich</div>
                  <div className="text-sm text-gray-300">
                    Konfigurieren Sie Ihr Cookie-Banner und wählen Sie die Services aus, die Sie verwenden.
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
              <TabsList className="grid w-full grid-cols-4 bg-gray-900/50 p-1 h-auto">
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
                />
              </TabsContent>
              
              <TabsContent value="integration">
                <IntegrationGuide siteId={siteId} config={config} />
              </TabsContent>
              
              <TabsContent value="statistics">
                <ConsentStatistics siteId={siteId} />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

