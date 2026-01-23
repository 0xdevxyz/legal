/**
 * Geo-Restriction Settings
 * Banner nur in bestimmten Ländern anzeigen
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Globe, MapPin, Info, CheckCircle } from 'lucide-react';

interface GeoRestrictionProps {
  siteId: string;
  config: any;
  onSave: (config: any) => Promise<boolean>;
}

// EU/EEA Länder die Cookie-Consent erfordern
const EU_COUNTRIES = [
  { code: 'AT', name: 'Österreich' },
  { code: 'BE', name: 'Belgien' },
  { code: 'BG', name: 'Bulgarien' },
  { code: 'HR', name: 'Kroatien' },
  { code: 'CY', name: 'Zypern' },
  { code: 'CZ', name: 'Tschechien' },
  { code: 'DK', name: 'Dänemark' },
  { code: 'EE', name: 'Estland' },
  { code: 'FI', name: 'Finnland' },
  { code: 'FR', name: 'Frankreich' },
  { code: 'DE', name: 'Deutschland' },
  { code: 'GR', name: 'Griechenland' },
  { code: 'HU', name: 'Ungarn' },
  { code: 'IE', name: 'Irland' },
  { code: 'IT', name: 'Italien' },
  { code: 'LV', name: 'Lettland' },
  { code: 'LT', name: 'Litauen' },
  { code: 'LU', name: 'Luxemburg' },
  { code: 'MT', name: 'Malta' },
  { code: 'NL', name: 'Niederlande' },
  { code: 'PL', name: 'Polen' },
  { code: 'PT', name: 'Portugal' },
  { code: 'RO', name: 'Rumänien' },
  { code: 'SK', name: 'Slowakei' },
  { code: 'SI', name: 'Slowenien' },
  { code: 'ES', name: 'Spanien' },
  { code: 'SE', name: 'Schweden' },
];

const OTHER_COUNTRIES = [
  { code: 'GB', name: 'Großbritannien' },
  { code: 'CH', name: 'Schweiz' },
  { code: 'NO', name: 'Norwegen' },
  { code: 'IS', name: 'Island' },
  { code: 'LI', name: 'Liechtenstein' },
  { code: 'US', name: 'USA' },
  { code: 'CA', name: 'Kanada' },
  { code: 'AU', name: 'Australien' },
  { code: 'JP', name: 'Japan' },
  { code: 'BR', name: 'Brasilien' },
];

export default function GeoRestriction({ siteId, config, onSave }: GeoRestrictionProps) {
  const [enabled, setEnabled] = useState(config?.geo_restriction_enabled ?? false);
  const [selectedCountries, setSelectedCountries] = useState<string[]>(config?.geo_countries || []);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

  const toggleCountry = (code: string) => {
    setSelectedCountries(prev => 
      prev.includes(code) 
        ? prev.filter(c => c !== code)
        : [...prev, code]
    );
  };

  const selectAllEU = () => {
    const euCodes = EU_COUNTRIES.map(c => c.code);
    setSelectedCountries(prev => {
      const nonEu = prev.filter(c => !euCodes.includes(c));
      return [...nonEu, ...euCodes];
    });
  };

  const clearAll = () => {
    setSelectedCountries([]);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${API_URL}/api/cookie-compliance/geo-restriction`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          site_id: siteId,
          enabled: enabled,
          countries: selectedCountries
        })
      });
      
      if (response.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      }
    } catch (error) {
      console.error('Error saving geo restriction settings:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Info Banner */}
      <Card className="bg-gradient-to-r from-green-500/10 to-green-600/5 border-green-500/30">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Globe className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-green-300">Geo-Restriction</h4>
              <p className="text-sm text-gray-300 mt-1">
                Zeigen Sie das Cookie-Banner nur in Ländern an, in denen es rechtlich erforderlich ist.
                Dies verbessert die Conversion-Rate für Besucher aus Nicht-EU-Ländern.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Settings */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <MapPin className="w-5 h-5 text-green-400" />
            Ländereinschränkung
          </CardTitle>
          <CardDescription>
            Wählen Sie die Länder, in denen das Cookie-Banner angezeigt werden soll
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Enable/Disable */}
          <div className="flex items-center justify-between p-4 bg-gray-900/50 rounded-lg border border-gray-700">
            <div>
              <Label className="text-white font-medium">Geo-Restriction aktivieren</Label>
              <p className="text-sm text-gray-400 mt-1">
                Banner wird nur in ausgewählten Ländern angezeigt
              </p>
            </div>
            <Switch 
              checked={enabled} 
              onCheckedChange={setEnabled}
            />
          </div>

          {enabled && (
            <>
              {/* Quick Actions */}
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={selectAllEU} className="text-green-400 border-green-500/50 hover:bg-green-500/10">
                  Alle EU-Länder
                </Button>
                <Button variant="outline" size="sm" onClick={clearAll} className="text-gray-400">
                  Alle abwählen
                </Button>
                <Badge className="ml-auto bg-green-500/20 text-green-400">
                  {selectedCountries.length} ausgewählt
                </Badge>
              </div>

              {/* EU Countries */}
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-gray-300 flex items-center gap-2">
                  <span className="text-lg">🇪🇺</span> EU/EWR-Länder (Cookie-Consent erforderlich)
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 p-3 bg-gray-900/30 rounded-lg border border-gray-700">
                  {EU_COUNTRIES.map(country => (
                    <label 
                      key={country.code}
                      className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                        selectedCountries.includes(country.code) 
                          ? 'bg-green-500/20 border border-green-500/50' 
                          : 'bg-gray-800/50 hover:bg-gray-700/50'
                      }`}
                    >
                      <Checkbox
                        checked={selectedCountries.includes(country.code)}
                        onCheckedChange={() => toggleCountry(country.code)}
                      />
                      <span className="text-sm text-gray-300">{country.code}</span>
                      <span className="text-xs text-gray-500 truncate">{country.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Other Countries */}
              <div className="space-y-3">
                <h4 className="text-sm font-medium text-gray-300 flex items-center gap-2">
                  🌍 Andere Länder (optional)
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 p-3 bg-gray-900/30 rounded-lg border border-gray-700">
                  {OTHER_COUNTRIES.map(country => (
                    <label 
                      key={country.code}
                      className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                        selectedCountries.includes(country.code) 
                          ? 'bg-green-500/20 border border-green-500/50' 
                          : 'bg-gray-800/50 hover:bg-gray-700/50'
                      }`}
                    >
                      <Checkbox
                        checked={selectedCountries.includes(country.code)}
                        onCheckedChange={() => toggleCountry(country.code)}
                      />
                      <span className="text-sm text-gray-300">{country.code}</span>
                      <span className="text-xs text-gray-500 truncate">{country.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Info */}
              <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <div className="flex items-start gap-2">
                  <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-gray-300">
                    <strong className="text-blue-300">Hinweis:</strong> Die Ländererkennung basiert auf der IP-Adresse 
                    des Besuchers. Bei Nutzung von VPNs kann das erkannte Land abweichen.
                  </p>
                </div>
              </div>
            </>
          )}

          {/* Save Button */}
          <div className="flex justify-end pt-4">
            <Button
              onClick={handleSave}
              disabled={saving}
              className="bg-green-500 hover:bg-green-600"
            >
              {saving ? 'Speichern...' : saved ? '✓ Gespeichert' : 'Einstellungen speichern'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
