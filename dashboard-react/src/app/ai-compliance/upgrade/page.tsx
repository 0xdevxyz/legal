'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Check, Sparkles, Shield, Zap, ArrowRight } from 'lucide-react';
import { getAddonsCatalog, subscribeToAddon, getMyAddons } from '@/lib/ai-compliance-api';
import type { AddonCatalog } from '@/types/ai-compliance';

export default function UpgradePage() {
  const router = useRouter();
  const [catalog, setCatalog] = useState<AddonCatalog | null>(null);
  const [myAddons, setMyAddons] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [subscribing, setSubscribing] = useState(false);
  
  useEffect(() => {
    loadData();
  }, []);
  
  const loadData = async () => {
    try {
      const [catalogData, addonsData] = await Promise.all([
        getAddonsCatalog(),
        getMyAddons()
      ]);
      
      setCatalog(catalogData);
      setMyAddons(addonsData.addons);
    } catch (err) {
      console.error('Error loading addons:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSubscribe = async (addonKey: string) => {
    try {
      setSubscribing(true);
      const { checkout_url } = await subscribeToAddon(addonKey, 'professional');
      
      // Redirect to Stripe Checkout
      window.location.href = checkout_url;
    } catch (err: any) {
      console.error('Error subscribing:', err);
      alert('Fehler: ' + (err.response?.data?.detail || err.message));
      setSubscribing(false);
    }
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-8 flex items-center justify-center">
        <div className="animate-pulse text-gray-400">Lade Add-ons...</div>
      </div>
    );
  }
  
  const hasComploAI = myAddons.some(a => a.addon_key === 'comploai_guard' && a.status === 'active');
  const hasPrioritySupport = myAddons.some(a => a.addon_key === 'priority_support' && a.status === 'active');
  
  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <div className="max-w-6xl mx-auto">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500/20 rounded-full mb-4">
            <Sparkles className="w-5 h-5 text-purple-400" />
            <span className="text-sm font-medium text-purple-300">ComploAI Guard</span>
          </div>
          
          <h1 className="text-5xl font-bold mb-4">
            EU AI Act Compliance
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
              Automatisiert & KI-gestützt
            </span>
          </h1>
          
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            Prüfen Sie Ihre KI-Systeme auf Compliance mit der EU KI-Verordnung.
            Automatische Risiko-Klassifizierung, Dokumentation und Reports.
          </p>
        </div>
        
        {/* Main Add-ons */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
          {/* ComploAI Guard */}
          {catalog?.monthly_addons?.comploai_guard && (
            <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-2 border-purple-500/50 rounded-2xl p-8 relative overflow-hidden">
              {catalog.monthly_addons.comploai_guard.badge && (
                <div className="absolute top-4 right-4 px-3 py-1 bg-purple-500 rounded-full text-xs font-bold">
                  {catalog.monthly_addons.comploai_guard.badge}
                </div>
              )}
              
              <div className="mb-6">
                <div className="w-16 h-16 bg-purple-500/20 rounded-xl flex items-center justify-center mb-4">
                  <Shield className="w-8 h-8 text-purple-400" />
                </div>
                
                <h3 className="text-2xl font-bold mb-2">
                  {catalog.monthly_addons.comploai_guard.name}
                </h3>
                <p className="text-gray-400 mb-4">
                  {catalog.monthly_addons.comploai_guard.tagline}
                </p>
                
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold">
                    {catalog.monthly_addons.comploai_guard.price_monthly}€
                  </span>
                  <span className="text-gray-400">/Monat</span>
                </div>
                
                {catalog.monthly_addons.comploai_guard.discount_text && (
                  <div className="mt-3 text-sm text-green-400 font-medium">
                    ✓ {catalog.monthly_addons.comploai_guard.discount_text}
                  </div>
                )}
              </div>
              
              <div className="space-y-3 mb-8">
                {catalog.monthly_addons.comploai_guard.features.map((feature, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                    <span className="text-sm">{feature}</span>
                  </div>
                ))}
              </div>
              
              <button
                onClick={() => handleSubscribe('comploai_guard')}
                disabled={hasComploAI || subscribing}
                className="w-full px-6 py-4 bg-purple-600 hover:bg-purple-700 rounded-xl font-bold text-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {hasComploAI ? (
                  'Bereits aktiviert'
                ) : subscribing ? (
                  'Wird geladen...'
                ) : (
                  <>
                    Jetzt aktivieren
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </div>
          )}
          
          {/* Priority Support */}
          {catalog?.monthly_addons?.priority_support && (
            <div className="bg-gray-800 border-2 border-gray-700 rounded-2xl p-8 relative">
              {catalog.monthly_addons.priority_support.badge && (
                <div className="absolute top-4 right-4 px-3 py-1 bg-yellow-500 text-gray-900 rounded-full text-xs font-bold">
                  {catalog.monthly_addons.priority_support.badge}
                </div>
              )}
              
              <div className="mb-6">
                <div className="w-16 h-16 bg-yellow-500/20 rounded-xl flex items-center justify-center mb-4">
                  <Zap className="w-8 h-8 text-yellow-400" />
                </div>
                
                <h3 className="text-2xl font-bold mb-2">
                  {catalog.monthly_addons.priority_support.name}
                </h3>
                <p className="text-gray-400 mb-4">
                  {catalog.monthly_addons.priority_support.tagline}
                </p>
                
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold">
                    {catalog.monthly_addons.priority_support.price_monthly}€
                  </span>
                  <span className="text-gray-400">/Monat</span>
                </div>
              </div>
              
              <div className="space-y-3 mb-8">
                {catalog.monthly_addons.priority_support.features.map((feature, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                    <span className="text-sm">{feature}</span>
                  </div>
                ))}
              </div>
              
              <button
                onClick={() => handleSubscribe('priority_support')}
                disabled={hasPrioritySupport || subscribing}
                className="w-full px-6 py-4 bg-gray-700 hover:bg-gray-600 rounded-xl font-bold text-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {hasPrioritySupport ? 'Bereits aktiviert' : 'Hinzufügen'}
              </button>
            </div>
          )}
        </div>
        
        {/* One-time Services */}
        {catalog?.onetime_addons && Object.keys(catalog.onetime_addons).length > 0 && (
          <div>
            <h2 className="text-2xl font-bold mb-6">Einmalige Services</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {Object.entries(catalog.onetime_addons).map(([key, addon]) => (
                <div key={key} className="bg-gray-800 border border-gray-700 rounded-xl p-6">
                  <h3 className="text-xl font-bold mb-2">{addon.name}</h3>
                  <p className="text-sm text-gray-400 mb-4">{addon.description}</p>
                  
                  <div className="text-2xl font-bold mb-4">
                    {addon.price.toLocaleString('de-DE')}€
                  </div>
                  
                  <div className="space-y-2 mb-6">
                    {addon.includes.slice(0, 3).map((item, idx) => (
                      <div key={idx} className="text-sm text-gray-400 flex items-start gap-2">
                        <Check className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </div>
                    ))}
                  </div>
                  
                  <button className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors">
                    Anfragen
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* FAQ */}
        <div className="mt-16 bg-gray-800 border border-gray-700 rounded-xl p-8">
          <h2 className="text-2xl font-bold mb-6">Häufig gestellte Fragen</h2>
          
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold mb-2">Was ist der EU AI Act?</h3>
              <p className="text-gray-400 text-sm">
                Die EU KI-Verordnung ist seit August 2024 in Kraft und reguliert den Einsatz von KI-Systemen 
                in der EU. Unternehmen müssen ihre KI-Systeme klassifizieren und je nach Risiko umfangreiche 
                Compliance-Anforderungen erfüllen.
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold mb-2">Wer braucht ComploAI Guard?</h3>
              <p className="text-gray-400 text-sm">
                Jedes Unternehmen, das KI-Systeme entwickelt oder einsetzt (z.B. Chatbots, HR-Tools, 
                Empfehlungssysteme, Automatisierung) muss die AI Act Anforderungen erfüllen.
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold mb-2">Kann ich jederzeit kündigen?</h3>
              <p className="text-gray-400 text-sm">
                Ja, alle monatlichen Add-ons können jederzeit gekündigt werden. Die Kündigung wird 
                zum Ende des aktuellen Abrechnungszeitraums wirksam.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

