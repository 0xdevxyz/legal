/**
 * Cookie Banner Designer Component
 * Live preview and design customization
 */

import React, { useState, useEffect } from 'react';
import { Save, Eye, EyeOff, Check, Palette, Type, Settings2, Sparkles, Link, Globe, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface CookieBannerDesignerProps {
  config: any;
  siteId: string;
  onSave: (config: any) => Promise<boolean>;
}

const DEFAULT_CONFIG = {
  layout: 'banner_bottom',
  primary_color: '#7c3aed',
  accent_color: '#9333ea',
  text_color: '#1f2937',
  bg_color: '#ffffff',
  button_style: 'rounded',
  position: 'bottom',
  width_mode: 'full',
  show_branding: true,
  cookie_lifetime_days: 365,
  consent_mode_enabled: true,
  gtm_container_id: '',
  privacy_policy_url: '/datenschutz',
  cookie_policy_url: '/cookie-richtlinie',
  imprint_url: '/impressum',
  texts: {
    de: {
      title: 'Datenschutz-Präferenz',
      description: 'Wir benötigen Ihre Einwilligung, bevor Sie unsere Website weiter besuchen können.\n\nWir verwenden Cookies und andere Technologien auf unserer Website. Einige von ihnen sind essenziell, während andere uns helfen, diese Website und Ihre Erfahrung zu verbessern.',
      accept_all: 'Alle akzeptieren',
      reject_all: 'Nur essenzielle Cookies akzeptieren',
      accept_selected: 'Speichern',
      settings: 'Individuelle Datenschutzeinstellungen',
      privacy_policy: 'Datenschutzerklärung',
      imprint: 'Impressum',
    },
    en: {
      title: 'Privacy Preference',
      description: 'We need your consent before you can continue visiting our website.\n\nWe use cookies and other technologies on our website. Some of them are essential, while others help us improve this website and your experience.',
      accept_all: 'Accept all',
      reject_all: 'Accept essential cookies only',
      accept_selected: 'Save',
      settings: 'Individual privacy settings',
      privacy_policy: 'Privacy Policy',
      imprint: 'Imprint',
    },
  },
};

const CookieBannerDesigner: React.FC<CookieBannerDesignerProps> = ({
  config: initialConfig,
  siteId,
  onSave,
}) => {
  const [config, setConfig] = useState({ ...DEFAULT_CONFIG, ...(initialConfig || {}) });
  const [colorPreset, setColorPreset] = useState('custom');
  const [saving, setSaving] = useState(false);
  const [showPreview, setShowPreview] = useState(true);
  const [saved, setSaved] = useState(false);
  const [textLang, setTextLang] = useState<'de' | 'en'>('de');

  useEffect(() => {
    if (initialConfig) {
      setConfig((prev: any) => ({ ...DEFAULT_CONFIG, ...initialConfig, texts: { ...DEFAULT_CONFIG.texts, ...initialConfig.texts } }));
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
    setConfig((prev: any) => ({ ...prev, [key]: value }));
  };

  const updateTexts = (language: string, key: string, value: string) => {
    setConfig((prev: any) => ({
      ...prev,
      texts: {
        ...prev.texts,
        [language]: {
          ...(prev.texts?.[language] || {}),
          [key]: value,
        },
      },
    }));
  };

  // 22 Design Presets
  const colorPresets: Record<string, { name: string; primary_color: string; accent_color: string; text_color: string; bg_color: string }> = {
    modern:      { name: 'Modern Orange',      primary_color: '#f97316', accent_color: '#ea580c', text_color: '#1f2937', bg_color: '#ffffff' },
    professional: { name: 'Professional Blue', primary_color: '#0ea5e9', accent_color: '#0284c7', text_color: '#1e293b', bg_color: '#ffffff' },
    elegant:     { name: 'Elegant Purple',     primary_color: '#8b5cf6', accent_color: '#7c3aed', text_color: '#1f2937', bg_color: '#ffffff' },
    minimal:     { name: 'Minimal Dark',       primary_color: '#1f2937', accent_color: '#374151', text_color: '#111827', bg_color: '#ffffff' },
    nature:      { name: 'Nature Green',       primary_color: '#22c55e', accent_color: '#16a34a', text_color: '#14532d', bg_color: '#f0fdf4' },
    sunset:      { name: 'Sunset Rose',        primary_color: '#f43f5e', accent_color: '#e11d48', text_color: '#1f2937', bg_color: '#fff1f2' },
    ocean:       { name: 'Ocean Teal',         primary_color: '#25bac8', accent_color: '#1597a3', text_color: '#134e4a', bg_color: '#f0fdfa' },
    coral:       { name: 'Coral Warm',         primary_color: '#fb7185', accent_color: '#f43f5e', text_color: '#1f2937', bg_color: '#fffbeb' },
    lavender:    { name: 'Lavender',           primary_color: '#a78bfa', accent_color: '#8b5cf6', text_color: '#4c1d95', bg_color: '#faf5ff' },
    mint:        { name: 'Mint Fresh',         primary_color: '#34d399', accent_color: '#10b981', text_color: '#065f46', bg_color: '#ecfdf5' },
    darkElegant: { name: 'Dark Elegant',       primary_color: '#818cf8', accent_color: '#6366f1', text_color: '#e2e8f0', bg_color: '#1e1b4b' },
    darkModern:  { name: 'Dark Modern',        primary_color: '#f97316', accent_color: '#ea580c', text_color: '#f3f4f6', bg_color: '#18181b' },
    darkForest:  { name: 'Dark Forest',        primary_color: '#4ade80', accent_color: '#22c55e', text_color: '#dcfce7', bg_color: '#14532d' },
    darkOcean:   { name: 'Dark Ocean',         primary_color: '#38bdf8', accent_color: '#0ea5e9', text_color: '#e0f2fe', bg_color: '#0c4a6e' },
    darkRuby:    { name: 'Dark Ruby',          primary_color: '#fb7185', accent_color: '#f43f5e', text_color: '#fecdd3', bg_color: '#4c0519' },
    corporate:   { name: 'Corporate Blue',     primary_color: '#1d4ed8', accent_color: '#1e40af', text_color: '#1e3a8a', bg_color: '#ffffff' },
    trust:       { name: 'Trust & Security',   primary_color: '#059669', accent_color: '#047857', text_color: '#064e3b', bg_color: '#ffffff' },
    tech:        { name: 'Tech Startup',       primary_color: '#7c3aed', accent_color: '#6d28d9', text_color: '#1f2937', bg_color: '#faf5ff' },
    finance:     { name: 'Finance',            primary_color: '#0891b2', accent_color: '#0e7490', text_color: '#164e63', bg_color: '#ecfeff' },
    health:      { name: 'Healthcare',         primary_color: '#1597a3', accent_color: '#0f766e', text_color: '#134e4a', bg_color: '#f0fdfa' },
    candy:       { name: 'Candy Pop',          primary_color: '#ec4899', accent_color: '#db2777', text_color: '#831843', bg_color: '#fdf2f8' },
    sunshine:    { name: 'Sunshine',           primary_color: '#fbbf24', accent_color: '#f59e0b', text_color: '#78350f', bg_color: '#fffbeb' },
  };

  const applyColorPreset = (preset: string) => {
    setColorPreset(preset);
    if (preset !== 'custom' && colorPresets[preset]) {
      const colors = colorPresets[preset];
      setConfig((prev: any) => ({ ...prev, ...colors }));
    }
  };

  const layouts = [
    { key: 'banner_bottom', label: 'Unten',     preview: <div className="w-14 h-11 border-2 border-orange-400 rounded relative overflow-hidden bg-gray-900/50"><div className="absolute bottom-0 left-0 right-0 h-3 bg-orange-500"></div></div> },
    { key: 'banner_top',    label: 'Oben',      preview: <div className="w-14 h-11 border-2 border-orange-400 rounded relative overflow-hidden bg-gray-900/50"><div className="absolute top-0 left-0 right-0 h-3 bg-orange-500"></div></div> },
    { key: 'box_modal',     label: 'Zentriert', preview: <div className="w-14 h-11 border-2 border-orange-400 rounded relative overflow-hidden bg-gray-900/50 flex items-center justify-center"><div className="w-9 h-6 bg-orange-500 rounded-sm"></div></div> },
    { key: 'floating_widget', label: 'Floating', preview: <div className="w-14 h-11 border-2 border-orange-400 rounded relative overflow-hidden bg-gray-900/50"><div className="absolute bottom-1 right-1 w-5 h-5 bg-orange-500 rounded-full"></div></div> },
  ];

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
            <div className="grid grid-cols-4 gap-3">
              {layouts.map(({ key, label, preview }) => (
                <button
                  key={key}
                  onClick={() => setConfig((prev: any) => ({
                    ...prev,
                    layout: key,
                    // position kohärent zum Layout halten — sonst rendert das
                    // Widget z.B. 'banner_bottom' mit veraltetem position:'center'
                    // ohne passende CSS-Regel (unsichtbar/falsch positioniert).
                    position: key === 'banner_top' ? 'top'
                            : key === 'box_modal' ? 'center'
                            : 'bottom',
                  }))}
                  className={`p-3 rounded-lg border-2 transition-all duration-200 ${
                    config.layout === key
                      ? 'border-orange-500 bg-orange-500/10 shadow-lg shadow-orange-500/20'
                      : 'border-gray-600 hover:border-orange-400 bg-gray-700/50'
                  }`}
                >
                  <div className="flex flex-col items-center gap-2">
                    {preview}
                    <span className="text-xs font-semibold text-gray-200">{label}</span>
                    {config.layout === key && (
                      <Badge className="bg-orange-500 text-white text-[10px] px-1 py-0">
                        <Check className="w-3 h-3" />
                      </Badge>
                    )}
                  </div>
                </button>
              ))}
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
            <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-1">
              {Object.entries(colorPresets).map(([key, preset]) => (
                <button
                  key={key}
                  onClick={() => applyColorPreset(key)}
                  className={`p-2 rounded-lg border-2 transition-all duration-200 ${
                    colorPreset === key
                      ? 'border-orange-500 bg-orange-500/10'
                      : 'border-gray-600 hover:border-orange-400 bg-gray-700/50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-4 h-4 rounded border border-gray-600" style={{ backgroundColor: preset.primary_color }}></div>
                      <div className="w-4 h-4 rounded border border-gray-600" style={{ backgroundColor: preset.bg_color }}></div>
                    </div>
                    <span className="text-xs font-medium text-gray-200 truncate">{preset.name}</span>
                  </div>
                </button>
              ))}
            </div>

            {/* Custom Colors */}
            <div className="pt-4 border-t border-gray-700 space-y-3">
              <Label className="text-sm font-medium text-gray-200 block">Individuelle Farben</Label>
              {[
                { label: 'Primärfarbe', key: 'primary_color' },
                { label: 'Hintergrund', key: 'bg_color' },
                { label: 'Textfarbe',   key: 'text_color' },
              ].map(({ label, key }) => (
                <div key={key} className="flex items-center gap-3">
                  <Label className="text-xs text-gray-400 w-24">{label}</Label>
                  <input
                    type="color"
                    value={config[key] || '#000000'}
                    onChange={(e) => { updateConfig(key, e.target.value); setColorPreset('custom'); }}
                    className="w-10 h-8 rounded border border-gray-600 bg-gray-700 cursor-pointer"
                  />
                  <Input
                    value={config[key] || ''}
                    onChange={(e) => { updateConfig(key, e.target.value); setColorPreset('custom'); }}
                    className="flex-1 bg-gray-700 border-gray-600 text-white text-sm h-8"
                  />
                </div>
              ))}
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
            <div className="flex gap-2">
              <button
                onClick={() => setTextLang('de')}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${textLang === 'de' ? 'bg-orange-500 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}
              >
                Deutsch
              </button>
              <button
                onClick={() => setTextLang('en')}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${textLang === 'en' ? 'bg-orange-500 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}`}
              >
                English
              </button>
            </div>

            <div className="space-y-2">
              <Label className="text-sm text-gray-200">Titel</Label>
              <Input
                value={config.texts?.[textLang]?.title || ''}
                onChange={(e) => updateTexts(textLang, 'title', e.target.value)}
                className="bg-gray-700 border-gray-600 text-white placeholder:text-gray-400"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-sm text-gray-200">Beschreibung</Label>
              <Textarea
                value={config.texts?.[textLang]?.description || ''}
                onChange={(e) => updateTexts(textLang, 'description', e.target.value)}
                rows={4}
                className="bg-gray-700 border-gray-600 text-white placeholder:text-gray-400"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs text-gray-300">Alle akzeptieren</Label>
                <Input value={config.texts?.[textLang]?.accept_all || ''} onChange={(e) => updateTexts(textLang, 'accept_all', e.target.value)} className="bg-gray-700 border-gray-600 text-white text-sm" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-gray-300">Nur essenziell</Label>
                <Input value={config.texts?.[textLang]?.reject_all || ''} onChange={(e) => updateTexts(textLang, 'reject_all', e.target.value)} className="bg-gray-700 border-gray-600 text-white text-sm" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-gray-300">Auswahl speichern</Label>
                <Input value={config.texts?.[textLang]?.accept_selected || ''} onChange={(e) => updateTexts(textLang, 'accept_selected', e.target.value)} className="bg-gray-700 border-gray-600 text-white text-sm" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-gray-300">Einstellungen-Link</Label>
                <Input value={config.texts?.[textLang]?.settings || ''} onChange={(e) => updateTexts(textLang, 'settings', e.target.value)} className="bg-gray-700 border-gray-600 text-white text-sm" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Legal Links */}
        <Card className="border-gray-700 bg-gray-800/50 backdrop-blur-sm hover:bg-gray-800/70 transition-all duration-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Link className="w-5 h-5 text-orange-400" />
              Rechtliche Links
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { label: 'Datenschutz-URL',  key: 'privacy_policy_url',  placeholder: '/datenschutz' },
              { label: 'Cookie-Policy-URL', key: 'cookie_policy_url',  placeholder: '/cookie-richtlinie' },
              { label: 'Impressum-URL',     key: 'imprint_url',        placeholder: '/impressum' },
            ].map(({ label, key, placeholder }) => (
              <div key={key} className="space-y-1">
                <Label className="text-xs text-gray-300">{label}</Label>
                <Input
                  value={config[key] || ''}
                  onChange={(e) => updateConfig(key, e.target.value)}
                  placeholder={placeholder}
                  className="bg-gray-700 border-gray-600 text-white text-sm placeholder:text-gray-500"
                />
              </div>
            ))}
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
          <CardContent className="space-y-4">
            {/* Cookie Lifetime */}
            <div className="space-y-1">
              <Label className="text-sm text-gray-200 flex items-center gap-2">
                <Clock className="w-4 h-4 text-orange-400" />
                Cookie-Laufzeit (Tage)
              </Label>
              <Input
                type="number"
                min={1}
                max={730}
                value={config.cookie_lifetime_days || 365}
                onChange={(e) => updateConfig('cookie_lifetime_days', parseInt(e.target.value) || 365)}
                className="bg-gray-700 border-gray-600 text-white w-32"
              />
              <p className="text-xs text-gray-500">Empfehlung: 365 Tage (1 Jahr)</p>
            </div>

            {/* Google Consent Mode */}
            <div className="flex items-center justify-between py-2 border-t border-gray-700">
              <div className="space-y-0.5">
                <Label className="text-sm text-gray-200 flex items-center gap-2">
                  <Globe className="w-4 h-4 text-orange-400" />
                  Google Consent Mode v2
                </Label>
                <p className="text-xs text-gray-400">Pflicht seit März 2024 für Google-Dienste</p>
              </div>
              <Switch
                checked={config.consent_mode_enabled !== false}
                onCheckedChange={(checked) => updateConfig('consent_mode_enabled', checked)}
              />
            </div>

            {/* GTM Container ID */}
            <div className="space-y-1">
              <Label className="text-xs text-gray-300">GTM Container ID (optional)</Label>
              <Input
                value={config.gtm_container_id || ''}
                onChange={(e) => updateConfig('gtm_container_id', e.target.value)}
                placeholder="GTM-XXXXXXX"
                className="bg-gray-700 border-gray-600 text-white text-sm placeholder:text-gray-500"
              />
            </div>

            {/* Branding */}
            <div className="flex items-center justify-between py-2 border-t border-gray-700">
              <div className="space-y-0.5">
                <Label className="text-sm text-gray-200">Complyo Branding anzeigen</Label>
                <p className="text-xs text-gray-400">White-Label ist im Expert Plan verfügbar</p>
              </div>
              <Switch
                checked={config.show_branding !== false}
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
            <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></div>Speichert...</>
          ) : saved ? (
            <><Check className="w-5 h-5 mr-2" />Gespeichert!</>
          ) : (
            <><Save className="w-5 h-5 mr-2" />Konfiguration speichern</>
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
              <div className="bg-gradient-to-br from-gray-900 to-gray-800 p-4 rounded-lg min-h-[500px] relative border-2 border-dashed border-gray-600 overflow-hidden">
                {/* Simulated website content */}
                <div className="space-y-3 opacity-40 mb-4">
                  <div className="h-5 bg-gray-600 rounded w-3/4"></div>
                  <div className="h-3 bg-gray-700 rounded w-full"></div>
                  <div className="h-3 bg-gray-700 rounded w-5/6"></div>
                  <div className="h-3 bg-gray-700 rounded w-4/5"></div>
                  <div className="h-20 bg-gray-700 rounded w-full mt-2"></div>
                </div>

                {/* Simulated Banner Preview */}
                {config.layout === 'box_modal' ? (
                  <>
                    <div className="absolute inset-0 bg-black/50 rounded-lg"></div>
                    <div
                      className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-xl shadow-2xl w-[85%] max-w-sm"
                      style={{ backgroundColor: config.bg_color, color: config.text_color }}
                    >
                      <div className="p-5 space-y-3">
                        <h3 className="font-bold text-sm">{config.texts?.de?.title || 'Datenschutz-Präferenz'}</h3>
                        <p className="text-xs opacity-75 line-clamp-3">{config.texts?.de?.description || 'Beschreibung...'}</p>
                        <div className="flex flex-col gap-2">
                          <button className="px-3 py-2 text-xs font-semibold text-white rounded-md" style={{ backgroundColor: config.primary_color }}>
                            {config.texts?.de?.accept_all || 'Alle akzeptieren'}
                          </button>
                          <button className="px-3 py-2 text-xs font-medium rounded-md border-2" style={{ borderColor: config.primary_color, color: config.primary_color }}>
                            {config.texts?.de?.reject_all || 'Nur essenziell'}
                          </button>
                        </div>
                        {config.show_branding !== false && (
                          <p className="text-center text-[9px] opacity-40">Powered by Complyo</p>
                        )}
                      </div>
                    </div>
                  </>
                ) : config.layout === 'floating_widget' ? (
                  <div
                    className="absolute bottom-4 right-4 w-12 h-12 rounded-full shadow-xl flex items-center justify-center text-white font-bold text-lg cursor-pointer"
                    style={{ backgroundColor: config.primary_color }}
                    title="Cookie-Einstellungen"
                  >
                    🍪
                  </div>
                ) : (
                  <div
                    className={`absolute left-0 right-0 shadow-lg ${config.layout === 'banner_top' ? 'top-0 rounded-t-lg' : 'bottom-0 rounded-b-lg'}`}
                    style={{ backgroundColor: config.bg_color, color: config.text_color }}
                  >
                    <div className="p-4 space-y-2">
                      <h3 className="font-bold text-xs">{config.texts?.de?.title || 'Datenschutz-Präferenz'}</h3>
                      <p className="text-[10px] opacity-70 line-clamp-2">{config.texts?.de?.description || ''}</p>
                      <div className="flex gap-2">
                        <button className="flex-1 px-2 py-1.5 text-[10px] font-semibold text-white rounded" style={{ backgroundColor: config.primary_color }}>
                          {config.texts?.de?.accept_all || 'Alle akzeptieren'}
                        </button>
                        <button className="flex-1 px-2 py-1.5 text-[10px] rounded border" style={{ borderColor: config.primary_color, color: config.primary_color }}>
                          {config.texts?.de?.reject_all || 'Ablehnen'}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
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
