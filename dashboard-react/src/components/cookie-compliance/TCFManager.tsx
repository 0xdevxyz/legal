/**
 * TCF 2.2 Manager
 * Transparency and Consent Framework - IAB Europe Standard
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { AlertCircle, Shield, ExternalLink, Lock, CheckCircle } from 'lucide-react';

interface TCFManagerProps {
  siteId: string;
  config: any;
  onSave: (config: any) => Promise<boolean>;
}

const TCF_PURPOSES = [
  { id: 1, name: 'Speicherung/Zugriff auf Informationen', required: true },
  { id: 2, name: 'Einfache Anzeigen auswählen', required: false },
  { id: 3, name: 'Personalisiertes Anzeigenprofil erstellen', required: false },
  { id: 4, name: 'Personalisierte Anzeigen auswählen', required: false },
  { id: 5, name: 'Personalisiertes Inhaltsprofil erstellen', required: false },
  { id: 6, name: 'Personalisierte Inhalte auswählen', required: false },
  { id: 7, name: 'Anzeigen-Performance messen', required: false },
  { id: 8, name: 'Inhalte-Performance messen', required: false },
  { id: 9, name: 'Marktforschung durchführen', required: false },
  { id: 10, name: 'Produkte entwickeln und verbessern', required: false },
];

export default function TCFManager({ siteId, config, onSave }: TCFManagerProps) {
  const [enabled, setEnabled] = useState(config?.tcf_enabled ?? false);
  const [vendors, setVendors] = useState<any[]>([]);
  const [selectedVendors, setSelectedVendors] = useState<number[]>(config?.tcf_vendors || []);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

  useEffect(() => {
    loadVendors();
  }, []);

  const loadVendors = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/cookie-compliance/tcf/vendors`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setVendors(data.vendors || []);
        }
      }
    } catch (error) {
      console.error('Error loading TCF vendors:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${API_URL}/api/cookie-compliance/tcf/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          site_id: siteId,
          tcf_enabled: enabled,
          tcf_vendors: selectedVendors
        })
      });
      
      if (response.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      }
    } catch (error) {
      console.error('Error saving TCF settings:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Warning Banner */}
      <Card className="bg-gradient-to-r from-yellow-500/10 to-yellow-600/5 border-yellow-500/30">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-yellow-300">TCF 2.2 - Registrierung erforderlich</h4>
              <p className="text-sm text-gray-300 mt-1">
                Um TCF zu nutzen, müssen Sie sich bei IAB Europe als Consent Management Platform (CMP) registrieren.
                Diese Funktion ist derzeit als Vorschau verfügbar.
              </p>
              <a 
                href="https://iabeurope.eu/tcf-2-0/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-yellow-400 hover:text-yellow-300 mt-2"
              >
                Mehr über TCF erfahren <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Settings */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Shield className="w-5 h-5 text-yellow-400" />
            TCF 2.2 Konfiguration
            <Badge className="ml-2 bg-yellow-500/20 text-yellow-400">Beta</Badge>
          </CardTitle>
          <CardDescription>
            Transparency and Consent Framework für standardisierte Einwilligungen
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Enable/Disable */}
          <div className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg border border-gray-700">
            <div>
              <Label className="text-white font-medium flex items-center gap-2">
                TCF 2.2 aktivieren
                <Lock className="w-4 h-4 text-gray-500" />
              </Label>
              <p className="text-sm text-gray-400 mt-1">
                Standardisierte Einwilligungen nach IAB Europe
              </p>
            </div>
            <Switch 
              checked={enabled} 
              onCheckedChange={setEnabled}
              disabled={true} // Deaktiviert bis Registrierung
            />
          </div>

          {/* TCF Purposes */}
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-300">TCF 2.2 Zwecke</h4>
            <div className="grid gap-2">
              {TCF_PURPOSES.map(purpose => (
                <div 
                  key={purpose.id}
                  className="flex items-center justify-between p-3 bg-gray-900/30 rounded-lg border border-gray-700"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 flex items-center justify-center bg-gray-800 rounded text-xs text-gray-400">
                      {purpose.id}
                    </span>
                    <span className="text-sm text-gray-300">{purpose.name}</span>
                  </div>
                  {purpose.required && (
                    <Badge variant="outline" className="text-xs text-green-400 border-green-500/50">
                      Basis
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Vendor Info */}
          <div className="p-4 bg-gray-900/50 rounded-lg border border-gray-700">
            <h4 className="text-sm font-medium text-gray-300 mb-3">Vendor-Verwaltung</h4>
            <p className="text-sm text-gray-400">
              Nach der Registrierung bei IAB Europe können Sie hier Ihre TCF-Vendors verwalten.
              {vendors.length > 0 && ` (${vendors.length} Vendors verfügbar)`}
            </p>
          </div>

          {/* Google Certified CMP */}
          <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-blue-300">Google Zertifizierte CMP</h4>
                <p className="text-xs text-gray-300 mt-1">
                  Nach TCF-Aktivierung wird Complyo als Google-zertifizierte CMP konfiguriert,
                  kompatibel mit AdSense und Google Ad Manager.
                </p>
              </div>
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end pt-4">
            <Button
              onClick={handleSave}
              disabled={saving || !enabled}
              className="bg-yellow-500 hover:bg-yellow-600 text-black"
            >
              {saving ? 'Speichern...' : saved ? '✓ Gespeichert' : 'Einstellungen speichern'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
