/**
 * Google Consent Mode v2 Settings
 * Pflicht seit März 2024 für Google Services
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { AlertCircle, CheckCircle, Info, ExternalLink } from 'lucide-react';

interface ConsentModeSettingsProps {
  siteId: string;
  config: any;
  onSave: (config: any) => Promise<boolean>;
}

export default function ConsentModeSettings({ siteId, config, onSave }: ConsentModeSettingsProps) {
  const [enabled, setEnabled] = useState(config?.consent_mode_enabled ?? true);
  const [gtmEnabled, setGtmEnabled] = useState(config?.gtm_enabled ?? false);
  const [gtmContainerId, setGtmContainerId] = useState(config?.gtm_container_id || '');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${API_URL}/api/cookie-compliance/consent-mode-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          site_id: siteId,
          consent_mode_enabled: enabled,
          gtm_enabled: gtmEnabled,
          gtm_container_id: gtmContainerId || null
        })
      });
      
      if (response.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      }
    } catch (error) {
      console.error('Error saving consent mode settings:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Info Banner */}
      <Card className="bg-gradient-to-r from-blue-500/10 to-blue-600/5 border-blue-500/30">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-blue-300">Google Consent Mode v2</h4>
              <p className="text-sm text-gray-300 mt-1">
                Seit März 2024 ist der Google Consent Mode v2 Pflicht für alle Websites, 
                die Google Services wie Analytics, Ads oder Tag Manager verwenden.
              </p>
              <a 
                href="https://support.google.com/analytics/answer/9976101" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-blue-400 hover:text-blue-300 mt-2"
              >
                Mehr erfahren <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Settings */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <img src="https://www.gstatic.com/images/branding/product/1x/googleg_48dp.png" alt="Google" className="w-5 h-5" />
            Consent Mode Einstellungen
          </CardTitle>
          <CardDescription>
            Konfigurieren Sie die Google Consent Mode v2 Integration
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Enable/Disable */}
          <div className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg border border-gray-700">
            <div>
              <Label className="text-white font-medium">Consent Mode aktivieren</Label>
              <p className="text-sm text-gray-400 mt-1">
                Sendet Einwilligungssignale an Google Services
              </p>
            </div>
            <Switch 
              checked={enabled} 
              onCheckedChange={setEnabled}
            />
          </div>

          {/* Consent Types */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-300">Consent-Typen (automatisch konfiguriert)</h4>
            <div className="grid grid-cols-2 gap-3">
              {[
                { key: 'ad_storage', label: 'Werbe-Cookies', category: 'Marketing' },
                { key: 'analytics_storage', label: 'Analytics-Cookies', category: 'Statistik' },
                { key: 'ad_user_data', label: 'Daten an Google Ads', category: 'Marketing' },
                { key: 'ad_personalization', label: 'Personalisierte Werbung', category: 'Marketing' }
              ].map(type => (
                <div key={type.key} className="p-3 bg-gray-900/30 rounded-lg border border-gray-700">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white">{type.label}</span>
                    <Badge variant="outline" className="text-xs">
                      {type.category}
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{type.key}</p>
                </div>
              ))}
            </div>
          </div>

          {/* GTM Integration */}
          <div className="space-y-4 p-4 bg-gray-900/50 rounded-lg border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-white font-medium">Google Tag Manager Integration</Label>
                <p className="text-sm text-gray-400 mt-1">
                  Sende Consent-Events an den Google Tag Manager
                </p>
              </div>
              <Switch 
                checked={gtmEnabled} 
                onCheckedChange={setGtmEnabled}
              />
            </div>
            
            {gtmEnabled && (
              <div className="space-y-2">
                <Label className="text-sm text-gray-300">GTM Container ID</Label>
                <Input
                  placeholder="GTM-XXXXXXX"
                  value={gtmContainerId}
                  onChange={(e) => setGtmContainerId(e.target.value)}
                  className="bg-gray-800 border-gray-600 text-white"
                />
                <p className="text-xs text-gray-500">
                  Optional: Wenn Sie GTM bereits eingebunden haben, lassen Sie dieses Feld leer.
                </p>
              </div>
            )}
          </div>

          {/* DataLayer Events Info */}
          <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
            <h4 className="text-sm font-medium text-green-300 flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              Automatische DataLayer Events
            </h4>
            <p className="text-xs text-gray-300 mt-2">
              Folgende Events werden automatisch an den dataLayer gesendet:
            </p>
            <div className="flex flex-wrap gap-2 mt-2">
              <code className="text-xs bg-gray-800 px-2 py-1 rounded">complyo_consent_update</code>
              <code className="text-xs bg-gray-800 px-2 py-1 rounded">complyo_analytics_granted</code>
              <code className="text-xs bg-gray-800 px-2 py-1 rounded">complyo_marketing_granted</code>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end pt-4">
            <Button
              onClick={handleSave}
              disabled={saving}
              className="bg-orange-500 hover:bg-orange-600"
            >
              {saving ? 'Speichern...' : saved ? '✓ Gespeichert' : 'Einstellungen speichern'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
