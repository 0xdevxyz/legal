/**
 * Cookie Banner Designer Component
 * Live preview and design customization
 */

import React, { useState, useEffect } from 'react';
import { Save, Eye, EyeOff, Check, Palette, Type, Settings2, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';

interface CookieBannerDesignerProps {
  config: any;
  siteId: string;
  onSave: (config: any) => Promise<boolean>;
}

const CookieBannerDesigner: React.FC<CookieBannerDesignerProps> = ({
  config: initialConfig,
  siteId,
  onSave,
}) => {
  const [config, setConfig] = useState(initialConfig || {
    layout: 'banner_bottom',
    primary_color: '#f97316',
    accent_color: '#ea580c',
    text_color: '#1f2937',
    bg_color: '#ffffff',
    button_style: 'rounded',
    position: 'bottom',
    width_mode: 'full',
    show_branding: true,
    texts: {
      de: {
        title: '🍪 Wir respektieren Ihre Privatsphäre',
        description: 'Wir verwenden Cookies und ähnliche Technologien, um Inhalte zu personalisieren und die Nutzung unserer Website zu analysieren. Einige davon sind essentiell, während andere uns helfen, die Website zu verbessern.',
        accept_all: 'Alle akzeptieren',
        reject_all: 'Nur notwendige',
        accept_selected: 'Auswahl speichern',
        settings: 'Einstellungen',
        privacy_policy: 'Datenschutzerklärung',
        imprint: 'Impressum',
      },
    },
  });
  
  const [colorPreset, setColorPreset] = useState('custom');
  const [saving, setSaving] = useState(false);
  const [showPreview, setShowPreview] = useState(true);
  const [saved, setSaved] = useState(false);
  
  useEffect(() => {
    if (initialConfig) {
      setConfig(initialConfig);
    }
  }, [initialConfig]);
  
  const handleSave = async () => {
    setSaving(true);
    const success = await onSave(config);
    setSaving(false);
    if (success) {
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    }
  };
  
  const updateConfig = (key: string, value: any) => {
    setConfig((prev: any) => ({
      ...prev,
      [key]: value,
    }));
  };
  
  const updateTexts = (language: string, key: string, value: string) => {
    setConfig((prev: any) => ({
      ...prev,
      texts: {
        ...prev.texts,
        [language]: {
          ...prev.texts[language],
          [key]: value,
        },
      },
    }));
  };
  
  const colorPresets = {
    modern: {
      name: 'Modern Orange',
      primary_color: '#f97316',
      accent_color: '#ea580c',
      text_color: '#1f2937',
      bg_color: '#ffffff',
    },
    professional: {
      name: 'Professional Blue',
      primary_color: '#0ea5e9',
      accent_color: '#0284c7',
      text_color: '#1e293b',
      bg_color: '#ffffff',
    },
    elegant: {
      name: 'Elegant Purple',
      primary_color: '#8b5cf6',
      accent_color: '#7c3aed',
      text_color: '#1f2937',
      bg_color: '#ffffff',
    },
    minimal: {
      name: 'Minimal Dark',
      primary_color: '#1f2937',
      accent_color: '#374151',
      text_color: '#111827',
      bg_color: '#ffffff',
    },
  };
  
  const applyColorPreset = (preset: string) => {
    setColorPreset(preset);
    if (preset !== 'custom' && colorPresets[preset as keyof typeof colorPresets]) {
      const colors = colorPresets[preset as keyof typeof colorPresets];
      setConfig((prev: any) => ({
        ...prev,
        primary_color: colors.primary_color,
        accent_color: colors.accent_color,
        text_color: colors.text_color,
        bg_color: colors.bg_color,
      }));
    }
  };
  
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Left Column - Settings */}
      <div className="space-y-6">
        {/* Layout Settings */}
        <Card className="border-gray-700 bg-gray-800/50 backdrop-blur-sm hover:bg-gray-800/70 transition-all duration-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Settings2 className="w-5 h-5 text-orange-400" />
              Layout wählen
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              {/* Banner Bottom */}
              <button
                onClick={() => updateConfig('layout', 'banner_bottom')}
                className={`p-4 rounded-lg border-2 transition-all duration-200 ${
                  config.layout === 'banner_bottom'
                    ? 'border-orange-500 bg-orange-500/10 shadow-lg shadow-orange-500/20'
                    : 'border-gray-600 hover:border-orange-400 bg-gray-700/50'
                }`}
              >
                <div className="flex flex-col items-center gap-2">
                  <div className="w-14 h-11 border-2 border-orange-400 rounded relative overflow-hidden bg-gray-900/50">
                    <div className="absolute bottom-0 left-0 right-0 h-3 bg-orange-500"></div>
                  </div>
                  <span className="text-xs font-semibold text-gray-200">Unten</span>
                  {config.layout === 'banner_bottom' && (
                    <Badge className="bg-orange-500 text-white text-[10px] px-1 py-0">
                      <Check className="w-3 h-3" />
                    </Badge>
                  )}
                </div>
              </button>

              {/* Box Modal */}
              <button
                onClick={() => updateConfig('layout', 'box_modal')}
                className={`p-4 rounded-lg border-2 transition-all duration-200 ${
                  config.layout === 'box_modal'
                    ? 'border-orange-500 bg-orange-500/10 shadow-lg shadow-orange-500/20'
                    : 'border-gray-600 hover:border-orange-400 bg-gray-700/50'
                }`}
              >
                <div className="flex flex-col items-center gap-2">
                  <div className="w-14 h-11 border-2 border-orange-400 rounded relative overflow-hidden bg-gray-900/50 flex items-center justify-center">
                    <div className="w-9 h-6 bg-orange-500 rounded-sm"></div>
                  </div>
                  <span className="text-xs font-semibold text-gray-200">Zentriert</span>
                  {config.layout === 'box_modal' && (
                    <Badge className="bg-orange-500 text-white text-[10px] px-1 py-0">
                      <Check className="w-3 h-3" />
                    </Badge>
                  )}
                </div>
              </button>

              {/* Coming Soon */}
              <div className="p-4 rounded-lg border-2 border-gray-700 bg-gray-800/30 opacity-50 cursor-not-allowed">
                <div className="flex flex-col items-center gap-2">
                  <div className="w-14 h-11 border-2 border-gray-600 rounded bg-gray-900/50"></div>
                  <span className="text-xs font-semibold text-gray-500">Bald</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Color Presets */}
        <Card className="border-gray-700 bg-gray-800/50 backdrop-blur-sm hover:bg-gray-800/70 transition-all duration-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Palette className="w-5 h-5 text-orange-400" />
              Farbauswahl
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(colorPresets).map(([key, preset]) => (
                <button
                  key={key}
                  onClick={() => applyColorPreset(key)}
                  className={`p-3 rounded-lg border-2 transition-all duration-200 ${
                    colorPreset === key
                      ? 'border-orange-500 bg-orange-500/10 shadow-lg shadow-orange-500/20'
                      : 'border-gray-600 hover:border-orange-400 bg-gray-700/50'
                  }`}
                >
                  <div className="flex flex-col gap-2">
                    <div className="flex gap-1">
                      <div
                        className="w-5 h-5 rounded border border-gray-600"
                        style={{ backgroundColor: preset.primary_color }}
                      ></div>
                      <div
                        className="w-5 h-5 rounded border border-gray-600"
                        style={{ backgroundColor: preset.accent_color }}
                      ></div>
                      <div
                        className="w-5 h-5 rounded border border-gray-600"
                        style={{ backgroundColor: preset.bg_color }}
                      ></div>
                    </div>
                    <span className="text-xs font-medium text-gray-200">{preset.name}</span>
                  </div>
                </button>
              ))}
            </div>

            {/* Custom Colors */}
            <div className="pt-4 border-t border-gray-700">
              <Label className="text-sm font-medium text-gray-200 mb-3 block">
                Individuelle Farben
              </Label>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <Label className="text-xs text-gray-400 w-24">Primärfarbe</Label>
                  <input
                    type="color"
                    value={config.primary_color}
                    onChange={(e) => {
                      updateConfig('primary_color', e.target.value);
                      setColorPreset('custom');
                    }}
                    className="w-12 h-10 rounded border border-gray-600 bg-gray-700 cursor-pointer"
                  />
                  <Input
                    value={config.primary_color}
                    onChange={(e) => {
                      updateConfig('primary_color', e.target.value);
                      setColorPreset('custom');
                    }}
                    className="flex-1 bg-gray-700 border-gray-600 text-white"
                  />
                </div>

                <div className="flex items-center gap-3">
                  <Label className="text-xs text-gray-400 w-24">Hintergrund</Label>
                  <input
                    type="color"
                    value={config.bg_color}
                    onChange={(e) => {
                      updateConfig('bg_color', e.target.value);
                      setColorPreset('custom');
                    }}
                    className="w-12 h-10 rounded border border-gray-600 bg-gray-700 cursor-pointer"
                  />
                  <Input
                    value={config.bg_color}
                    onChange={(e) => {
                      updateConfig('bg_color', e.target.value);
                      setColorPreset('custom');
                    }}
                    className="flex-1 bg-gray-700 border-gray-600 text-white"
                  />
                </div>

                <div className="flex items-center gap-3">
                  <Label className="text-xs text-gray-400 w-24">Textfarbe</Label>
                  <input
                    type="color"
                    value={config.text_color}
                    onChange={(e) => {
                      updateConfig('text_color', e.target.value);
                      setColorPreset('custom');
                    }}
                    className="w-12 h-10 rounded border border-gray-600 bg-gray-700 cursor-pointer"
                  />
                  <Input
                    value={config.text_color}
                    onChange={(e) => {
                      updateConfig('text_color', e.target.value);
                      setColorPreset('custom');
                    }}
                    className="flex-1 bg-gray-700 border-gray-600 text-white"
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Text Settings */}
        <Card className="border-gray-700 bg-gray-800/50 backdrop-blur-sm hover:bg-gray-800/70 transition-all duration-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Type className="w-5 h-5 text-orange-400" />
              Texte anpassen
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label className="text-sm text-gray-200">Titel</Label>
              <Input
                value={config.texts?.de?.title || ''}
                onChange={(e) => updateTexts('de', 'title', e.target.value)}
                placeholder="🍪 Wir respektieren Ihre Privatsphäre"
                className="bg-gray-700 border-gray-600 text-white placeholder:text-gray-400"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-sm text-gray-200">Beschreibung</Label>
              <Textarea
                value={config.texts?.de?.description || ''}
                onChange={(e) => updateTexts('de', 'description', e.target.value)}
                placeholder="Wir verwenden Cookies..."
                rows={4}
                className="bg-gray-700 border-gray-600 text-white placeholder:text-gray-400"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label className="text-xs text-gray-300">Button "Akzeptieren"</Label>
                <Input
                  value={config.texts?.de?.accept_all || ''}
                  onChange={(e) => updateTexts('de', 'accept_all', e.target.value)}
                  className="bg-gray-700 border-gray-600 text-white text-sm"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-xs text-gray-300">Button "Ablehnen"</Label>
                <Input
                  value={config.texts?.de?.reject_all || ''}
                  onChange={(e) => updateTexts('de', 'reject_all', e.target.value)}
                  className="bg-gray-700 border-gray-600 text-white text-sm"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Advanced Settings */}
        <Card className="border-gray-700 bg-gray-800/50 backdrop-blur-sm hover:bg-gray-800/70 transition-all duration-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Sparkles className="w-5 h-5 text-orange-400" />
              Erweiterte Einstellungen
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label className="text-sm text-gray-200">Complyo Branding anzeigen</Label>
                <p className="text-xs text-gray-400">
                  White-Label ist im Expert Plan verfügbar
                </p>
              </div>
              <Switch
                checked={config.show_branding}
                onCheckedChange={(checked) => updateConfig('show_branding', checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Save Button */}
        <Button
          onClick={handleSave}
          disabled={saving}
          className={`w-full h-12 text-base font-semibold transition-all duration-200 ${
            saved
              ? 'bg-green-600 hover:bg-green-700'
              : 'bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700'
          }`}
        >
          {saving ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></div>
              Speichert...
            </>
          ) : saved ? (
            <>
              <Check className="w-5 h-5 mr-2" />
              Gespeichert!
            </>
          ) : (
            <>
              <Save className="w-5 h-5 mr-2" />
              Konfiguration speichern
            </>
          )}
        </Button>
      </div>

      {/* Right Column - Live Preview */}
      <div className="lg:sticky lg:top-6 h-fit">
        <Card className="border-gray-700 bg-gray-800/50 backdrop-blur-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-white">
                <Eye className="w-5 h-5 text-orange-400" />
                Live-Vorschau
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowPreview(!showPreview)}
                className="text-gray-300 hover:text-white"
              >
                {showPreview ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {showPreview ? (
              <div className="bg-gradient-to-br from-gray-900 to-gray-800 p-8 rounded-lg min-h-[500px] relative border-2 border-dashed border-gray-600">
                <div className="text-center text-gray-400 text-sm mb-6">
                  Vorschau des Cookie-Banners
                </div>

                {/* Simulated Banner Preview */}
                <div
                  className={`absolute shadow-2xl ${
                    config.layout === 'banner_bottom'
                      ? 'bottom-0 left-0 right-0'
                      : 'left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 max-w-md w-full'
                  } ${config.layout === 'box_modal' ? 'rounded-lg' : ''}`}
                  style={{
                    backgroundColor: config.bg_color,
                    color: config.text_color,
                  }}
                >
                  <div className="p-6 space-y-4">
                    <h3 className="font-bold text-base">
                      {config.texts?.de?.title || 'Cookie Banner Titel'}
                    </h3>
                    <p className="text-sm opacity-80 line-clamp-3">
                      {config.texts?.de?.description || 'Beschreibung...'}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <button
                        className="px-4 py-2 text-sm font-medium text-white rounded-md transition-all hover:scale-105"
                        style={{ backgroundColor: config.primary_color }}
                      >
                        {config.texts?.de?.accept_all || 'Akzeptieren'}
                      </button>
                      <button
                        className="px-4 py-2 text-sm font-medium rounded-md border-2 transition-all hover:scale-105"
                        style={{
                          borderColor: config.primary_color,
                          color: config.primary_color,
                        }}
                      >
                        {config.texts?.de?.reject_all || 'Ablehnen'}
                      </button>
                    </div>
                    {config.show_branding && (
                      <div className="text-center pt-2 border-t opacity-50" style={{ borderColor: config.text_color + '30' }}>
                        <p className="text-[10px]">Powered by Complyo</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-64 text-gray-400">
                <div className="text-center">
                  <EyeOff className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>Vorschau ausgeblendet</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CookieBannerDesigner;
