/**
 * Age Verification Settings (Jugendschutz)
 * Art. 8 DSGVO - Altersgrenzen für Minderjährige
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertCircle, Shield, Info, Users } from 'lucide-react';

interface AgeVerificationProps {
  siteId: string;
  config: any;
  onSave: (config: any) => Promise<boolean>;
}

// Länderspezifische Altersgrenzen nach DSGVO Art. 8
const COUNTRY_AGE_LIMITS: Record<string, { name: string; age: number }> = {
  'DE': { name: 'Deutschland', age: 16 },
  'AT': { name: 'Österreich', age: 14 },
  'BE': { name: 'Belgien', age: 13 },
  'BG': { name: 'Bulgarien', age: 14 },
  'HR': { name: 'Kroatien', age: 16 },
  'CY': { name: 'Zypern', age: 14 },
  'CZ': { name: 'Tschechien', age: 15 },
  'DK': { name: 'Dänemark', age: 13 },
  'EE': { name: 'Estland', age: 13 },
  'FI': { name: 'Finnland', age: 13 },
  'FR': { name: 'Frankreich', age: 15 },
  'GR': { name: 'Griechenland', age: 15 },
  'HU': { name: 'Ungarn', age: 16 },
  'IE': { name: 'Irland', age: 16 },
  'IT': { name: 'Italien', age: 14 },
  'LV': { name: 'Lettland', age: 13 },
  'LT': { name: 'Litauen', age: 14 },
  'LU': { name: 'Luxemburg', age: 16 },
  'MT': { name: 'Malta', age: 13 },
  'NL': { name: 'Niederlande', age: 16 },
  'PL': { name: 'Polen', age: 16 },
  'PT': { name: 'Portugal', age: 13 },
  'RO': { name: 'Rumänien', age: 16 },
  'SK': { name: 'Slowakei', age: 16 },
  'SI': { name: 'Slowenien', age: 16 },
  'ES': { name: 'Spanien', age: 14 },
  'SE': { name: 'Schweden', age: 13 },
  'GB': { name: 'Großbritannien', age: 13 },
  'CH': { name: 'Schweiz', age: 16 }
};

export default function AgeVerification({ siteId, config, onSave }: AgeVerificationProps) {
  const [enabled, setEnabled] = useState(config?.age_verification_enabled ?? false);
  const [minAge, setMinAge] = useState(config?.age_verification_min_age ?? 16);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${API_URL}/api/cookie-compliance/age-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          site_id: siteId,
          enabled: enabled,
          min_age: minAge
        })
      });
      
      if (response.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      }
    } catch (error) {
      console.error('Error saving age verification settings:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Info Banner */}
      <Card className="bg-gradient-to-r from-purple-500/10 to-purple-600/5 border-purple-500/30">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Shield className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-purple-300">Jugendschutz nach DSGVO Art. 8</h4>
              <p className="text-sm text-gray-300 mt-1">
                Minderjährige können nur mit Zustimmung eines Erziehungsberechtigten einwilligen.
                Die Altersgrenzen variieren je nach EU-Mitgliedstaat zwischen 13 und 16 Jahren.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Settings */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-purple-400" />
            Altersverifikation
          </CardTitle>
          <CardDescription>
            Stellen Sie sicher, dass Minderjährige rechtswirksam einwilligen können
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Enable/Disable */}
          <div className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg border border-gray-700">
            <div>
              <Label className="text-white font-medium">Altersabfrage aktivieren</Label>
              <p className="text-sm text-gray-400 mt-1">
                Zeigt eine Altersabfrage vor dem Cookie-Banner
              </p>
            </div>
            <Switch 
              checked={enabled} 
              onCheckedChange={setEnabled}
            />
          </div>

          {enabled && (
            <>
              {/* Age Selection */}
              <div className="space-y-3">
                <Label className="text-sm text-gray-300">Standard-Mindestalter</Label>
                <Select value={String(minAge)} onValueChange={(v) => setMinAge(Number(v))}>
                  <SelectTrigger className="bg-gray-900 border-gray-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    {[13, 14, 15, 16].map(age => (
                      <SelectItem key={age} value={String(age)} className="text-white">
                        {age} Jahre
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500">
                  Wird verwendet, wenn das Land des Besuchers nicht erkannt werden kann.
                </p>
              </div>

              {/* Country Age Limits */}
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-gray-300">Länderspezifische Altersgrenzen</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-64 overflow-y-auto p-2 bg-gray-900/30 rounded-lg border border-gray-700">
                  {Object.entries(COUNTRY_AGE_LIMITS).map(([code, { name, age }]) => (
                    <div 
                      key={code} 
                      className="flex items-center justify-between p-2 bg-gray-800/50 rounded text-sm"
                    >
                      <span className="text-gray-300">{code}</span>
                      <Badge variant="outline" className={`text-xs ${age === minAge ? 'border-purple-500 text-purple-400' : ''}`}>
                        {age} J.
                      </Badge>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-gray-500">
                  Die Altersgrenze wird automatisch basierend auf dem Land des Besuchers angepasst.
                </p>
              </div>

              {/* Preview */}
              <div className="p-4 bg-gray-900/50 rounded-lg border border-gray-700">
                <h4 className="text-sm font-medium text-gray-300 mb-3">Vorschau der Altersabfrage</h4>
                <div className="p-4 bg-white rounded-lg text-gray-800 text-center">
                  <p className="font-medium mb-2">🔒 Altersverifikation erforderlich</p>
                  <p className="text-sm text-gray-600 mb-4">
                    Um diese Website zu nutzen, müssen Sie mindestens {minAge} Jahre alt sein.
                  </p>
                  <div className="flex gap-2 justify-center">
                    <button className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm">
                      Ich bin {minAge}+ Jahre alt
                    </button>
                    <button className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg text-sm">
                      Ich bin jünger
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Save Button */}
          <div className="flex justify-end pt-4">
            <Button
              onClick={handleSave}
              disabled={saving}
              className="bg-purple-500 hover:bg-purple-600"
            >
              {saving ? 'Speichern...' : saved ? '✓ Gespeichert' : 'Einstellungen speichern'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
