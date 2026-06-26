/**
 * Service Manager Component
 * Select and manage cookie services
 */

import React, { useState, useEffect } from 'react';
import {
  Search,
  Check,
  ExternalLink,
  Radio,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Loader2,
  Sparkles,
  Zap,
  Lock,
  Plus,
  Pencil,
  Trash2,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { apiClient } from '@/lib/api-client';

interface Service {
  id: number;
  service_key: string;
  name: string;
  category: string;
  provider: string;
  description?: string;
  cookies?: any[];
  privacy_url?: string;
  provider_privacy_url?: string;
  template: {
    description_de?: string;
    cookies?: Array<string | { name: string; duration?: string; purpose?: string; type?: string }>;
    data_processing_countries?: string[];
    privacy_policy_url?: string;
    [key: string]: any;
  } | null;
  plan_required: string;
  // Art. 49 DSGVO — vom Backend (_enrich_third_country) angereichert
  requires_third_country_consent?: boolean;
  unsafe_third_country_names?: string[];
  data_processing_countries?: Array<{ code: string; name: string; safe: boolean }>;
}

interface ServiceManagerProps {
  selectedServices: string[];
  onServicesChange: (services: string[]) => void;
  websiteUrl?: string;      // ✅ NEU: Vorkonfigurierte Website-URL
  websiteLocked?: boolean;  // ✅ NEU: URL ist gesperrt (nicht änderbar)
  siteId?: string;          // ✅ NEU: Site-ID für den Scan
}

const ServiceManager: React.FC<ServiceManagerProps> = ({
  selectedServices,
  onServicesChange,
  websiteUrl: initialWebsiteUrl,
  websiteLocked = false,
  siteId,
}) => {
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  // ✅ NEU: Verwende vorkonfigurierte URL wenn vorhanden
  const [userWebsiteUrl, setUserWebsiteUrl] = useState(initialWebsiteUrl || '');
  const [scanResults, setScanResults] = useState<any>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  // Custom services (Borlabs-style)
  const emptyCustomForm = { name: '', category: 'functional', provider: '', domains: '', cookies: '', description: '', privacy_url: '' };
  const [customServices, setCustomServices] = useState<any[]>([]);
  const [showCustomForm, setShowCustomForm] = useState(false);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [customForm, setCustomForm] = useState({ ...emptyCustomForm });
  const [savingCustom, setSavingCustom] = useState(false);
  const [customError, setCustomError] = useState('');

  // ✅ NEU: URL aktualisieren wenn sie sich ändert (z.B. beim ersten Laden)
  useEffect(() => {
    if (initialWebsiteUrl && !userWebsiteUrl) {
      setUserWebsiteUrl(initialWebsiteUrl);
    }
  }, [initialWebsiteUrl]);
  
  useEffect(() => {
    loadServicesAndWebsite();
  }, []);
  
  const loadServicesAndWebsite = async () => {
    try {
      setLoading(true);

      // Lade verfügbare Services (inkl. eigener Dienste, wenn site_id vorhanden)
      const url = siteId
        ? `/api/cookie-compliance/services?site_id=${encodeURIComponent(siteId)}`
        : '/api/cookie-compliance/services';
      const data = await apiClient.get(url) as any;
      if (data.success) {
        setServices(data.services || []);
      }
    } catch (error) {
      console.error('Error loading services:', error);
    } finally {
      setLoading(false);
    }
    loadCustomServices();
  };

  const loadCustomServices = async () => {
    if (!siteId) return;
    try {
      const data = await apiClient.get(`/api/cookie-compliance/custom-services/${siteId}`) as any;
      if (data.success) setCustomServices(data.data || []);
    } catch (error) {
      console.error('Error loading custom services:', error);
    }
  };

  const resetCustomForm = () => {
    setCustomForm({ ...emptyCustomForm });
    setEditingKey(null);
    setShowCustomForm(false);
    setCustomError('');
  };

  const startEditCustom = (svc: any) => {
    setCustomForm({
      name: svc.name || '',
      category: svc.category || 'functional',
      provider: svc.provider || '',
      domains: (svc.domains || []).join(', '),
      cookies: (svc.cookies || []).join(', '),
      description: svc.description || '',
      privacy_url: svc.privacy_url || '',
    });
    setEditingKey(svc.service_key);
    setShowCustomForm(true);
    setCustomError('');
  };

  const saveCustomService = async () => {
    if (!siteId) return;
    if (!customForm.name.trim()) { setCustomError('Bitte einen Namen angeben.'); return; }
    setSavingCustom(true);
    setCustomError('');
    const payload = {
      name: customForm.name.trim(),
      category: customForm.category,
      provider: customForm.provider.trim() || null,
      description: customForm.description.trim() || null,
      domains: customForm.domains.split(',').map((d) => d.trim()).filter(Boolean),
      cookies: customForm.cookies.split(',').map((c) => c.trim()).filter(Boolean),
      privacy_url: customForm.privacy_url.trim() || null,
    };
    try {
      let newKey = editingKey;
      if (editingKey) {
        await apiClient.put(`/api/cookie-compliance/custom-services/${siteId}/${editingKey}`, payload);
      } else {
        const res = await apiClient.post(`/api/cookie-compliance/custom-services/${siteId}`, payload) as any;
        newKey = res?.service_key || null;
      }
      await loadServicesAndWebsite();
      // Neuen Dienst automatisch aktivieren
      if (newKey && !editingKey && !selectedServices.includes(newKey)) {
        onServicesChange([...selectedServices, newKey]);
      }
      resetCustomForm();
    } catch (error: any) {
      setCustomError(error?.response?.data?.detail || 'Speichern fehlgeschlagen.');
    } finally {
      setSavingCustom(false);
    }
  };

  const deleteCustomService = async (serviceKey: string) => {
    if (!siteId) return;
    if (!confirm('Diesen eigenen Dienst wirklich löschen?')) return;
    try {
      await apiClient.delete(`/api/cookie-compliance/custom-services/${siteId}/${serviceKey}`);
      if (selectedServices.includes(serviceKey)) {
        onServicesChange(selectedServices.filter((s) => s !== serviceKey));
      }
      await loadServicesAndWebsite();
    } catch (error) {
      console.error('Error deleting custom service:', error);
    }
  };
  
  const scanWebsiteAutomatically = async (url: string) => {
    if (!url) return;
    
    try {
      setScanning(true);
      setScanResults(null);
      const data = await apiClient.post('/api/cookie-compliance/scan', { url, site_id: siteId }) as any;
      
      if (data.success) {
        setScanResults(data);
        
        // Auto-select detected services
        if (data.detected_services && data.detected_services.length > 0) {
          const detectedKeys = data.detected_services.map((s: any) => s.service_key);
          const newSelected = [...new Set([...selectedServices, ...detectedKeys])];
          onServicesChange(newSelected);
        }
      }
    } catch (error) {
      console.error('Scan error:', error);
      setScanResults({ success: false, error: 'Scan fehlgeschlagen' });
    } finally {
      setScanning(false);
    }
  };
  
  const toggleService = (serviceKey: string) => {
    const newSelected = selectedServices.includes(serviceKey)
      ? selectedServices.filter((s) => s !== serviceKey)
      : [...selectedServices, serviceKey];
    
    onServicesChange(newSelected);
  };
  
  const filteredServices = services.filter((service) => {
    const matchesSearch = service.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         service.provider?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || service.category === categoryFilter;
    
    return matchesSearch && matchesCategory;
  });
  
  const categories = [
    { value: 'all', label: 'Alle', count: services.length, color: 'bg-gray-600' },
    { value: 'analytics', label: 'Statistik', count: services.filter(s => s.category === 'analytics').length, color: 'bg-blue-600' },
    { value: 'marketing', label: 'Marketing', count: services.filter(s => s.category === 'marketing').length, color: 'bg-purple-600' },
    { value: 'functional', label: 'Funktional', count: services.filter(s => s.category === 'functional').length, color: 'bg-green-600' },
    { value: 'necessary', label: 'Notwendig', count: services.filter(s => s.category === 'necessary').length, color: 'bg-gray-600' },
  ];
  
  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      analytics: 'blue',
      marketing: 'purple',
      functional: 'green',
      necessary: 'gray',
    };
    return colors[category] || 'gray';
  };
  
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <Loader2 className="w-12 h-12 text-orange-500 animate-spin" />
        <p className="text-gray-400">Lade Services...</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-2">Service-Auswahl</h3>
        <p className="text-sm text-gray-400">
          Wählen Sie die Services aus, die Sie auf Ihrer Website verwenden.{' '}
          <Badge variant="secondary" className="bg-orange-500/20 text-orange-300 border-orange-500/30">
            {selectedServices.length} ausgewählt
          </Badge>
        </p>
      </div>
      
      {/* Website Scanner */}
      <Card className="border-orange-500/30 bg-gradient-to-br from-orange-500/10 to-orange-600/5 backdrop-blur-sm">
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <Radio className="w-5 h-5 text-orange-400" />
              <h4 className="font-semibold text-white">Website-Scanner</h4>
              <Badge variant="secondary" className="bg-orange-500 text-white text-xs">
                <Sparkles className="w-3 h-3 mr-1" />
                AI
              </Badge>
            </div>
            
            {/* ✅ NEU: Gesperrte URL-Anzeige wenn bereits konfiguriert */}
            {websiteLocked && userWebsiteUrl ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <Lock className="w-4 h-4 text-blue-400 flex-shrink-0" />
                  <div className="flex-1">
                    <p className="text-xs text-blue-300 font-medium">Ihre konfigurierte Website</p>
                    <p className="text-sm text-white font-semibold">{userWebsiteUrl}</p>
                  </div>
                  <Button
                    onClick={() => scanWebsiteAutomatically(userWebsiteUrl)}
                    disabled={scanning}
                    className="bg-orange-500 hover:bg-orange-600 text-white"
                  >
                    {scanning ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Scannt...
                      </>
                    ) : (
                      <>
                        <Zap className="w-4 h-4 mr-2" />
                        Erneut scannen
                      </>
                    )}
                  </Button>
                </div>
                <p className="text-xs text-gray-400">
                  Diese Website ist fest mit Ihrem Account verknüpft und kann nicht geändert werden.
                </p>
              </div>
            ) : (
              <>
                {/* URL Eingabe - nur wenn noch keine URL konfiguriert */}
                <div className="flex gap-2">
                  <Input
                    placeholder="https://ihre-website.de"
                    value={userWebsiteUrl}
                    onChange={(e) => setUserWebsiteUrl(e.target.value)}
                    className="flex-1 bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
                  />
                  <Button
                    onClick={() => userWebsiteUrl && scanWebsiteAutomatically(userWebsiteUrl)}
                    disabled={scanning || !userWebsiteUrl}
                    className="bg-orange-500 hover:bg-orange-600 text-white"
                  >
                    {scanning ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Scannt...
                      </>
                    ) : (
                      <>
                        <Zap className="w-4 h-4 mr-2" />
                        Scannen
                      </>
                    )}
                  </Button>
                </div>
                
                <p className="text-xs text-gray-400">
                  Geben Sie Ihre Website-URL ein, um automatisch alle verwendeten Cookies und Services zu erkennen.
                </p>
              </>
            )}
            
            {scanning && (
              <div className="space-y-2">
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-orange-500 via-orange-400 to-orange-500 animate-[shimmer_1.5s_infinite] rounded-full" style={{width: '100%'}}></div>
                </div>
                <p className="text-xs text-gray-400">Analysiere {userWebsiteUrl}...</p>
              </div>
            )}
            
            {scanResults && !scanning && (
              <div className={`p-4 rounded-lg border ${
                scanResults.total_found > 0
                  ? 'bg-green-500/10 border-green-500/30'
                  : 'bg-green-500/10 border-green-500/30'
              }`}>
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${
                    scanResults.total_found > 0 ? 'bg-green-500/20' : 'bg-green-500/20'
                  }`}>
                    <Check className="w-5 h-5 text-green-400" />
                  </div>
                  <div className="flex-1">
                    {scanResults.detected_services?.length > 0 ? (
                      <>
                        <p className="font-semibold text-sm mb-1 text-green-400">
                          ✅ {scanResults.total_found} Services erkannt
                        </p>
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {scanResults.detected_services.map((s: any, idx: number) => (
                            <Badge key={idx} className="bg-green-500/20 text-green-300 border-green-500/30 text-xs">
                              {s.name}
                            </Badge>
                          ))}
                        </div>
                      </>
                    ) : (
                      <>
                        <p className="font-bold text-lg mb-2 text-green-400">
                          ✅ Kein Cookie-Banner erforderlich!
                        </p>
                        <div className="text-sm text-gray-300 space-y-2">
                          <p>
                            Unser Scan hat <strong className="text-green-400">keine Tracking-Cookies</strong> auf Ihrer Website gefunden.
                          </p>
                          <div className="bg-gray-800/60 p-3 rounded-lg text-xs space-y-1 text-gray-400">
                            <p className="font-semibold text-gray-300">Was bedeutet das?</p>
                            <ul className="list-disc list-inside">
                              <li>Ihre Website verwendet nur essenzielle Cookies</li>
                              <li>Sie müssen keinen Cookie-Banner einbinden</li>
                              <li>Falls Sie später Tracking-Tools hinzufügen, scannen Sie erneut</li>
                            </ul>
                          </div>
                        </div>
                        <p className="text-xs text-gray-500 mt-3">
                          Optional: Wählen Sie Services manuell unten aus, falls Sie doch welche verwenden möchten.
                        </p>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Eigene Dienste (Custom Services) */}
      {siteId && (
        <Card className="border-gray-700 bg-gray-800/40 backdrop-blur-sm">
          <CardContent className="pt-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-semibold text-white">Eigene Dienste</h4>
                <p className="text-xs text-gray-400 mt-1">
                  Definieren Sie Tools, die nicht im Katalog sind. Domains werden automatisch vor Einwilligung blockiert.
                </p>
              </div>
              {!showCustomForm && (
                <Button
                  onClick={() => { setCustomForm({ ...emptyCustomForm }); setEditingKey(null); setShowCustomForm(true); }}
                  className="bg-orange-500 hover:bg-orange-600 text-white"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Eigenen Dienst hinzufügen
                </Button>
              )}
            </div>

            {/* Liste vorhandener eigener Dienste */}
            {customServices.length > 0 && (
              <div className="space-y-2">
                {customServices.map((svc) => (
                  <div key={svc.service_key} className="flex items-center justify-between p-3 bg-gray-900/60 border border-gray-700 rounded-lg">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-white truncate">{svc.name}</span>
                        <Badge variant="secondary" className="bg-gray-700 text-gray-200 text-[10px] capitalize">{svc.category}</Badge>
                      </div>
                      <p className="text-xs text-gray-500 truncate">
                        {(svc.domains || []).join(', ') || 'Keine Domains'}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <button onClick={() => startEditCustom(svc)} title="Bearbeiten" className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded">
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button onClick={() => deleteCustomService(svc.service_key)} title="Löschen" className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Formular */}
            {showCustomForm && (
              <div className="p-4 bg-gray-900/60 border border-gray-700 rounded-lg space-y-3">
                <div className="flex items-center justify-between">
                  <h5 className="text-sm font-semibold text-white">{editingKey ? 'Dienst bearbeiten' : 'Neuer Dienst'}</h5>
                  <button onClick={resetCustomForm} className="p-1 text-gray-400 hover:text-white"><X className="w-4 h-4" /></button>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-gray-400">Name *</label>
                    <Input value={customForm.name} onChange={(e) => setCustomForm({ ...customForm, name: e.target.value })}
                      placeholder="z. B. Mein Analyse-Tool" className="bg-gray-800 border-gray-700 text-white" />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Kategorie</label>
                    <select value={customForm.category} onChange={(e) => setCustomForm({ ...customForm, category: e.target.value })}
                      className="w-full h-10 px-3 rounded-md bg-gray-800 border border-gray-700 text-white text-sm">
                      <option value="necessary">Notwendig</option>
                      <option value="functional">Funktional</option>
                      <option value="analytics">Statistik</option>
                      <option value="marketing">Marketing</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Anbieter</label>
                    <Input value={customForm.provider} onChange={(e) => setCustomForm({ ...customForm, provider: e.target.value })}
                      placeholder="z. B. Beispiel GmbH" className="bg-gray-800 border-gray-700 text-white" />
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Datenschutz-URL</label>
                    <Input value={customForm.privacy_url} onChange={(e) => setCustomForm({ ...customForm, privacy_url: e.target.value })}
                      placeholder="https://…/datenschutz" className="bg-gray-800 border-gray-700 text-white" />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="text-xs text-gray-400">Domains (kommagetrennt) — werden vor Einwilligung blockiert</label>
                    <Input value={customForm.domains} onChange={(e) => setCustomForm({ ...customForm, domains: e.target.value })}
                      placeholder="example.com, cdn.example.com" className="bg-gray-800 border-gray-700 text-white" />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="text-xs text-gray-400">Cookie-Namen (kommagetrennt)</label>
                    <Input value={customForm.cookies} onChange={(e) => setCustomForm({ ...customForm, cookies: e.target.value })}
                      placeholder="_myid, _mysession" className="bg-gray-800 border-gray-700 text-white" />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="text-xs text-gray-400">Beschreibung</label>
                    <Input value={customForm.description} onChange={(e) => setCustomForm({ ...customForm, description: e.target.value })}
                      placeholder="Wofür wird der Dienst genutzt?" className="bg-gray-800 border-gray-700 text-white" />
                  </div>
                </div>
                {customError && <p className="text-sm text-red-400">{customError}</p>}
                <div className="flex items-center gap-2">
                  <Button onClick={saveCustomService} disabled={savingCustom} className="bg-orange-500 hover:bg-orange-600 text-white">
                    {savingCustom ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Speichern…</> : (editingKey ? 'Änderungen speichern' : 'Dienst anlegen')}
                  </Button>
                  <Button variant="outline" onClick={resetCustomForm} className="border-gray-700 text-gray-300 hover:bg-gray-700">
                    Abbrechen
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Search & Filter */}
      <div className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Services durchsuchen..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
          />
        </div>
        
        {/* Category Tabs */}
        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <button
              key={cat.value}
              onClick={() => setCategoryFilter(cat.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                categoryFilter === cat.value
                  ? 'bg-orange-500 text-white shadow-lg shadow-orange-500/30'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
              }`}
            >
              {cat.label} ({cat.count})
            </button>
          ))}
        </div>
      </div>
      
      {/* Services Grid */}
      {filteredServices.length === 0 ? (
        <Card className="border-gray-700 bg-gray-800/30 border-dashed">
          <CardContent className="py-12">
            <div className="text-center space-y-3">
              <AlertCircle className="w-12 h-12 text-gray-600 mx-auto" />
              <h3 className="text-lg font-semibold text-gray-400">Keine Services gefunden</h3>
              <p className="text-sm text-gray-500">
                {searchTerm || categoryFilter !== 'all' 
                  ? 'Versuchen Sie andere Suchbegriffe oder Filter.'
                  : 'Nutzen Sie den Scanner oben, um Services automatisch zu erkennen.'}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredServices.map((service) => (
            <ServiceCard
              key={service.id}
              service={service}
              isSelected={selectedServices.includes(service.service_key)}
              onToggle={() => toggleService(service.service_key)}
              categoryColor={getCategoryColor(service.category)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Service Card Component
interface ServiceCardProps {
  service: Service;
  isSelected: boolean;
  onToggle: () => void;
  categoryColor: string;
}

const ServiceCard: React.FC<ServiceCardProps> = ({
  service,
  isSelected,
  onToggle,
  categoryColor,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const categoryColors: Record<string, { border: string; bg: string; badge: string; check: string }> = {
    blue: {
      border: 'border-blue-500/50',
      bg: 'bg-blue-500/10',
      badge: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
      check: 'bg-blue-500',
    },
    purple: {
      border: 'border-purple-500/50',
      bg: 'bg-purple-500/10',
      badge: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
      check: 'bg-purple-500',
    },
    green: {
      border: 'border-green-500/50',
      bg: 'bg-green-500/10',
      badge: 'bg-green-500/20 text-green-300 border-green-500/30',
      check: 'bg-green-500',
    },
    gray: {
      border: 'border-gray-500/50',
      bg: 'bg-gray-500/10',
      badge: 'bg-gray-500/20 text-gray-300 border-gray-500/30',
      check: 'bg-gray-500',
    },
  };
  
  const colors = categoryColors[categoryColor] || categoryColors.gray;
  
  return (
    <Card
      className={`border-2 transition-all duration-200 cursor-pointer ${
        isSelected
          ? `${colors.border} ${colors.bg} shadow-lg`
          : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
      }`}
    >
      <CardContent className="pt-6">
        <div className="space-y-3">
          {/* Header */}
          <div className="flex items-start justify-between gap-3" onClick={onToggle}>
            <div className="flex items-start gap-3 flex-1 min-w-0">
              {/* Checkbox */}
              <div className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                isSelected
                  ? `${colors.check} border-transparent`
                  : 'border-gray-600 bg-gray-700/50'
              }`}>
                {isSelected && <Check className="w-3 h-3 text-white" />}
              </div>
              
              {/* Service Info */}
              <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-white truncate">{service.name}</h4>
                {service.provider && (
                  <p className="text-xs text-gray-400 mt-0.5">{service.provider}</p>
                )}
              </div>
            </div>
            
            {/* Badges: Kategorie + ggf. Art.49-Drittland */}
            <div className="flex flex-col items-end gap-1 flex-shrink-0">
              <Badge variant="secondary" className={`${colors.badge} text-xs`}>
                {service.category}
              </Badge>
              {service.requires_third_country_consent && (
                <span title={`Datenverarbeitung in unsicheren Drittländern (Art. 49 DSGVO): ${(service.unsafe_third_country_names || []).join(', ')}`}>
                  <Badge
                    variant="secondary"
                    className="bg-amber-500/20 text-amber-300 border-amber-500/30 text-[10px]"
                  >
                    🌍 Drittland (Art. 49)
                  </Badge>
                </span>
              )}
            </div>
          </div>
          
          {/* Description */}
          {(service.template?.description_de || service.description) && (
            <p className="text-sm text-gray-400 line-clamp-2">
              {service.template?.description_de || service.description}
            </p>
          )}
          
          {/* Details Toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full text-gray-400 hover:text-white hover:bg-gray-700/50"
          >
            {isExpanded ? (
              <>
                Weniger anzeigen <ChevronUp className="w-4 h-4 ml-1" />
              </>
            ) : (
              <>
                Mehr Details <ChevronDown className="w-4 h-4 ml-1" />
              </>
            )}
          </Button>
          
          {/* Expandable Details */}
          {isExpanded && (
            <div className="space-y-3 pt-3 border-t border-gray-700">
              {/* Cookies */}
              {((service.template?.cookies?.length ?? 0) > 0 || (service.cookies?.length ?? 0) > 0) && (
                <div>
                  <p className="text-xs font-semibold text-gray-300 mb-1.5">Cookies:</p>
                  <div className="flex flex-wrap gap-1">
                    {(service.template?.cookies || service.cookies || []).map((c: any, i: number) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 text-xs bg-gray-700/70 text-gray-300 rounded border border-gray-600"
                      >
                        {typeof c === 'string' ? c : c.name}
                        {typeof c !== 'string' && c.duration && (
                          <span className="text-gray-500 ml-1">· {c.duration}</span>
                        )}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Data Processing Countries — Backend-angereichert (mit Sicher/Unsicher),
                  Fallback auf alte template-Liste (reine String-Namen) */}
              {(service.data_processing_countries?.length ?? 0) > 0 ? (
                <div>
                  <p className="text-xs font-semibold text-gray-300 mb-1">Datenverarbeitung in:</p>
                  <p className="text-xs text-gray-400">
                    {service.data_processing_countries!.map(c => c.name).join(', ')}
                  </p>
                  {(service.unsafe_third_country_names?.length ?? 0) > 0 && (
                    <p className="text-xs text-amber-400 mt-1">
                      ⚠ Unsichere Drittländer (Art. 49 DSGVO): {service.unsafe_third_country_names!.join(', ')}
                    </p>
                  )}
                </div>
              ) : (service.template?.data_processing_countries?.length ?? 0) > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-300 mb-1">Datenverarbeitung in:</p>
                  <p className="text-xs text-gray-400">
                    {service.template!.data_processing_countries!.join(', ')}
                  </p>
                </div>
              )}

              {/* Privacy Policy */}
              {(service.template?.privacy_policy_url || service.privacy_url || service.provider_privacy_url) && (
                <a
                  href={service.template?.privacy_policy_url || service.privacy_url || service.provider_privacy_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-orange-400 hover:text-orange-300 transition-colors"
                >
                  Datenschutzerklärung <ExternalLink className="w-3 h-3" />
                </a>
              )}

              {/* Fallback when nothing available */}
              {!(service.template?.cookies?.length) &&
               !(service.cookies?.length) &&
               !(service.data_processing_countries?.length) &&
               !(service.template?.data_processing_countries?.length) &&
               !service.template?.privacy_policy_url &&
               !service.privacy_url &&
               !service.provider_privacy_url && (
                <p className="text-xs text-gray-500 italic">Keine weiteren Details verfügbar.</p>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default ServiceManager;
