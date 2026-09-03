'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  CheckCircle, ArrowRight, ArrowLeft, Copy, Download, AlertCircle, 
  Building, Mail, Phone, MapPin, User, Globe, ShoppingCart, 
  BarChart3, MessageSquare, CreditCard, Shield, FileText, Code,
  Loader2, Info, ExternalLink
} from 'lucide-react';
import { useDashboardStore } from '@/stores/dashboard';
import { sanitizeHtml } from '@/lib/sanitize';
import { generateLegalText, type LegalDocumentType } from '@/lib/api';

export type WizardDocType = 'impressum' | 'datenschutz' | 'agb' | 'cookie' | 'widerruf';

interface LegalDocumentGeneratorProps {
  documentType: WizardDocType;
  onComplete: (data: any) => void;
  onBack: () => void;
}

// Zentrale Konfiguration je Dokumenttyp (Labels, Backend-Mapping, Datei-Slug)
const DOC_CONFIG: Record<WizardDocType, {
  label: string;        // voller Name
  short: string;        // kurzer Name (z.B. für Footer-Link)
  emoji: string;
  backendType: LegalDocumentType;
  slug: string;         // Dateiname/URL-Pfad
  legalBasis: string;
}> = {
  impressum:   { label: 'Impressum',            short: 'Impressum',   emoji: '📋', backendType: 'imprint',       slug: 'impressum',  legalBasis: 'nach § 5 DDG' },
  datenschutz: { label: 'Datenschutzerklärung', short: 'Datenschutz', emoji: '🔒', backendType: 'privacy',       slug: 'datenschutz', legalBasis: 'nach DSGVO' },
  agb:         { label: 'AGB',                   short: 'AGB',         emoji: '📜', backendType: 'tos',           slug: 'agb',        legalBasis: 'nach BGB §305 ff.' },
  cookie:      { label: 'Cookie-Richtlinie',     short: 'Cookies',     emoji: '🍪', backendType: 'cookie-policy', slug: 'cookie-richtlinie', legalBasis: 'nach TDDDG & DSGVO' },
  widerruf:    { label: 'Widerrufsbelehrung',    short: 'Widerruf',    emoji: '↩️', backendType: 'withdrawal',    slug: 'widerruf',   legalBasis: 'nach § 312g, § 355 BGB' },
};

interface CompanyData {
  company_name: string;
  legal_form: string;
  address: string;
  postal_code: string;
  city: string;
  country: string;
  representative: string;
  email: string;
  phone: string;
  website: string;
  ust_id: string;
  registration_number: string;
  // Impressum — berufsrechtliche & inhaltliche Verantwortung (optional)
  profession: string;
  regulatory_authority: string;
  content_responsible: string;
  // Datenschutz — Hosting (optional)
  hosting_provider: string;
  server_location: string;
  // AGB — Leistung, Preise, Laufzeit
  target_audience: string;
  service_description: string;
  pricing_model: string;
  payment_methods: string;
  min_contract_duration: string;
  cancellation_period: string;
  auto_renewal: string;
  jurisdiction: string;
  // Cookie-Richtlinie
  consent_tool: string;
  third_party_services: string;
  privacy_url: string;
  // Widerruf
  has_withdrawal_right: string;
  withdrawal_exceptions: string;
}

interface WebsiteFeatures {
  has_shop: boolean;
  has_contact_form: boolean;
  has_newsletter: boolean;
  has_user_accounts: boolean;
  has_analytics: boolean;
  has_social_media: boolean;
  has_payment: boolean;
  has_comments: boolean;
  analytics_tools: string[];
  payment_providers: string[];
  cms_type: string | null;
}

const LEGAL_FORMS = [
  { value: 'GmbH', label: 'GmbH' },
  { value: 'UG', label: 'UG (haftungsbeschränkt)' },
  { value: 'AG', label: 'AG' },
  { value: 'GbR', label: 'GbR' },
  { value: 'OHG', label: 'OHG' },
  { value: 'KG', label: 'KG' },
  { value: 'Einzelunternehmen', label: 'Einzelunternehmen' },
  { value: 'Freiberufler', label: 'Freiberufler' },
  { value: 'e.V.', label: 'eingetragener Verein (e.V.)' },
  { value: 'Stiftung', label: 'Stiftung' },
];

const CMS_TYPES = {
  wordpress: { name: 'WordPress', icon: '🔷' },
  shopify: { name: 'Shopify', icon: '🛒' },
  woocommerce: { name: 'WooCommerce', icon: '🛍️' },
  wix: { name: 'Wix', icon: '✨' },
  squarespace: { name: 'Squarespace', icon: '⬛' },
  joomla: { name: 'Joomla', icon: '🟠' },
  typo3: { name: 'TYPO3', icon: '🔶' },
  magento: { name: 'Magento', icon: '🟧' },
  custom: { name: 'Eigene Website', icon: '💻' },
};

export const LegalDocumentGenerator: React.FC<LegalDocumentGeneratorProps> = ({
  documentType,
  onComplete,
  onBack
}) => {
  const { analysisData, currentWebsite } = useDashboardStore();
  
  const [step, setStep] = useState(1);
  const [isGenerating, setIsGenerating] = useState(false);
  const [finalContent, setFinalContent] = useState('');
  const [copied, setCopied] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  
  // Company Data
  const [companyData, setCompanyData] = useState<Partial<CompanyData>>({
    country: 'Deutschland',
    legal_form: 'GmbH',
    website: currentWebsite?.url || ''
  });
  
  // Website Features - Initialisiert aus Analyse-Daten
  const [features, setFeatures] = useState<WebsiteFeatures>({
    has_shop: false,
    has_contact_form: false,
    has_newsletter: false,
    has_user_accounts: false,
    has_analytics: false,
    has_social_media: false,
    has_payment: false,
    has_comments: false,
    analytics_tools: [],
    payment_providers: [],
    cms_type: null
  });

  // ✅ Erkenne Website-Features aus Analyse-Daten
  useEffect(() => {
    if (analysisData) {
      const detectedFeatures: Partial<WebsiteFeatures> = {
        cms_type: null,
        analytics_tools: [],
        has_analytics: false,
        has_shop: false,
        has_payment: false,
      };

      // CMS-Typ erkennen
      const techStack = (analysisData as any).tech_stack;
      if (techStack?.cms) {
        detectedFeatures.cms_type = techStack.cms.type;
      }

      // Services erkennen (aus Cookie-Scan)
      const services = (analysisData as any).detected_services || [];
      
      // Analytics
      if (services.some((s: string) => 
        s.includes('analytics') || s.includes('gtag') || s.includes('google')
      )) {
        detectedFeatures.has_analytics = true;
        if (services.includes('google_analytics_ga4') || services.includes('google_analytics')) {
          detectedFeatures.analytics_tools = [...(detectedFeatures.analytics_tools || []), 'Google Analytics'];
        }
      }

      // Shop-Erkennung
      if (services.some((s: string) => 
        s.includes('woocommerce') || s.includes('shopify') || s.includes('magento') || s.includes('stripe') || s.includes('paypal')
      )) {
        detectedFeatures.has_shop = true;
        detectedFeatures.has_payment = true;
      }

      // Social Media
      if (services.some((s: string) => 
        s.includes('facebook') || s.includes('instagram') || s.includes('twitter') || s.includes('linkedin')
      )) {
        detectedFeatures.has_social_media = true;
      }

      setFeatures(prev => ({ ...prev, ...detectedFeatures }));
    }
  }, [analysisData]);

  const handleInputChange = (field: keyof CompanyData, value: string) => {
    setCompanyData(prev => ({ ...prev, [field]: value }));
  };

  const handleFeatureToggle = (feature: keyof WebsiteFeatures) => {
    setFeatures(prev => ({
      ...prev,
      [feature]: !prev[feature]
    }));
  };

  const isStepValid = () => {
    if (step === 1) return true; // Features-Step ist immer gültig
    if (step === 2) return companyData.company_name && companyData.legal_form && companyData.representative;
    if (step === 3) return companyData.address && companyData.city && companyData.email;
    return true;
  };

  const getTitleForType = () => `${DOC_CONFIG[documentType].label} erstellen`;

  const handleGenerate = async () => {
    setIsGenerating(true);
    setGenerationError(null);

    try {
      const type: LegalDocumentType = DOC_CONFIG[documentType].backendType;

      // CompanyData -> user_data des internen Rechtstexte-Generators mappen
      const userData = {
        company_name: companyData.company_name || '',
        legal_form: companyData.legal_form,
        address: companyData.address,
        zip_city: [companyData.postal_code, companyData.city].filter(Boolean).join(' '),
        country: companyData.country,
        phone: companyData.phone,
        email: companyData.email,
        website: currentWebsite?.url || companyData.website,
        represented_by: companyData.representative,
        vat_id: companyData.ust_id,
        registration_number: companyData.registration_number,
        // Impressum-spezifisch
        profession: companyData.profession || undefined,
        regulatory_authority: companyData.regulatory_authority || undefined,
        content_responsible: companyData.content_responsible || undefined,
        // Datenschutz-spezifisch
        hosting_provider: companyData.hosting_provider || undefined,
        server_location: companyData.server_location || undefined,
        // AGB-spezifisch
        target_audience: companyData.target_audience || undefined,
        service_description: companyData.service_description || undefined,
        pricing_model: companyData.pricing_model || undefined,
        payment_methods: companyData.payment_methods || undefined,
        min_contract_duration: companyData.min_contract_duration || undefined,
        cancellation_period: companyData.cancellation_period || undefined,
        auto_renewal: companyData.auto_renewal || undefined,
        jurisdiction: companyData.jurisdiction || undefined,
        // Cookie-spezifisch
        consent_tool: companyData.consent_tool || undefined,
        third_party_services: companyData.third_party_services || undefined,
        privacy_url: companyData.privacy_url || undefined,
        // Widerruf-spezifisch
        has_withdrawal_right: companyData.has_withdrawal_right || undefined,
        withdrawal_exceptions: companyData.withdrawal_exceptions || undefined,
      };

      // Aktivierte Website-Features als genutzte Dienste übergeben (für Datenschutz)
      const servicesUsed: string[] = [
        ...(features.analytics_tools || []),
        ...(features.payment_providers || []),
        features.has_shop ? 'Online-Shop' : '',
        features.has_contact_form ? 'Kontaktformular' : '',
        features.has_newsletter ? 'Newsletter' : '',
        features.has_user_accounts ? 'Nutzerkonten' : '',
        features.has_social_media ? 'Social-Media-Einbindung' : '',
        features.has_comments ? 'Kommentarfunktion' : '',
      ].filter(Boolean);

      const data = await generateLegalText(type, {
        user_data: userData,
        services_used: servicesUsed,
        language: 'de',
      });

      setFinalContent(data.html_content || data.plain_text || '');
      setStep(5);
    } catch (error) {
      // Kein stiller Fallback auf ein lokales Platzhalter-Template: der Nutzer
      // bekommt einen sichtbaren Fehlerzustand statt eines untergeschobenen
      // Dokuments ohne Disclaimer.
      console.error('Fehler bei Rechtstext-Generierung:', error);
      setGenerationError(
        error instanceof Error
          ? error.message
          : 'Generierung fehlgeschlagen. Bitte versuchen Sie es erneut.'
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(finalContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([finalContent], { type: 'text/html; charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${DOC_CONFIG[documentType].slug}-${companyData.company_name?.toLowerCase().replace(/\s+/g, '-') || 'dokument'}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getIntegrationGuide = () => {
    const cms = features.cms_type || 'custom';
    const label = DOC_CONFIG[documentType].label;
    const short = DOC_CONFIG[documentType].short;
    const slug = DOC_CONFIG[documentType].slug;

    const guides: Record<string, { title: string; steps: string[] }> = {
      wordpress: {
        title: 'WordPress Integration',
        steps: [
          'Gehen Sie zu "Seiten" → "Erstellen" im WordPress-Admin',
          `Erstellen Sie eine neue Seite mit dem Titel "${label}"`,
          'Wechseln Sie zum "Code-Editor" (Text-Tab oder Block-Editor → Code)',
          'Fügen Sie den HTML-Code ein',
          'Veröffentlichen Sie die Seite',
          'Gehen Sie zu "Design" → "Menüs" und fügen Sie die Seite zum Footer-Menü hinzu'
        ]
      },
      shopify: {
        title: 'Shopify Integration',
        steps: [
          'Gehen Sie zu "Online Store" → "Pages" im Shopify-Admin',
          'Klicken Sie auf "Add page"',
          `Titel: "${label}"`,
          'Klicken Sie auf "<>" um zur HTML-Ansicht zu wechseln',
          'Fügen Sie den Code ein und speichern Sie',
          'Unter "Online Store" → "Navigation" fügen Sie die Seite zum Footer hinzu'
        ]
      },
      wix: {
        title: 'Wix Integration',
        steps: [
          'Öffnen Sie den Wix Editor',
          'Klicken Sie auf "Seite hinzufügen"',
          `Benennen Sie die Seite "${label}"`,
          'Fügen Sie ein "HTML iframe" oder "Embed Code" Element hinzu',
          'Fügen Sie den HTML-Code ein',
          'Verlinken Sie die Seite im Footer'
        ]
      },
      custom: {
        title: 'Standard HTML Integration',
        steps: [
          `Erstellen Sie eine neue Datei: ${slug}.html`,
          'Fügen Sie den generierten HTML-Code ein',
          'Laden Sie die Datei auf Ihren Webserver hoch',
          `Verlinken Sie im Footer aller Seiten: <a href="/${slug}.html">${short}</a>`,
          'Testen Sie den Link auf allen Unterseiten'
        ]
      }
    };

    return guides[cms] || guides.custom;
  };

  // Erkannte Features als Badges
  const DetectedFeaturesBadge = ({ detected, label }: { detected: boolean; label: string }) => (
    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
      detected ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
    }`}>
      {detected ? '✓' : '○'} {label}
    </span>
  );

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          {DOC_CONFIG[documentType].emoji} {DOC_CONFIG[documentType].label} Generator
        </h1>
        <p className="text-gray-600 dark:text-zinc-400">
          Vorlage: {DOC_CONFIG[documentType].label} {DOC_CONFIG[documentType].legalBasis}, erzeugt aus Ihren Angaben. Bitte vor der Veröffentlichung prüfen.
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-center gap-2 mb-8">
        {['Website', 'Firma', 'Kontakt', 'Prüfen', 'Fertig'].map((label, idx) => (
          <React.Fragment key={idx}>
            <div className={`flex flex-col items-center ${step > idx ? 'text-emerald-400' : step === idx + 1 ? 'text-blue-400' : 'dark:text-zinc-600 text-gray-600'}`}>
              <div className={`flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm ${
                step > idx + 1 ? 'bg-emerald-500 text-white' : step === idx + 1 ? 'bg-blue-500 text-white' : 'dark:bg-zinc-700 bg-gray-100 text-zinc-400'
              }`}>
                {step > idx + 1 ? <CheckCircle className="w-5 h-5" /> : idx + 1}
              </div>
              <span className="text-xs mt-1 hidden sm:block">{label}</span>
            </div>
            {idx < 4 && <div className={`w-8 h-0.5 ${step > idx + 1 ? 'bg-emerald-500' : 'dark:bg-zinc-700 bg-gray-100'}`} />}
          </React.Fragment>
        ))}
      </div>

      {/* Step 1: Website Features */}
      {step === 1 && (
        <Card className="dark:bg-zinc-900 bg-white dark:border-zinc-800 border-gray-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-gray-900 dark:text-white">
              <Globe className="w-6 h-6 text-blue-400" />
              Schritt 1: Website-Eigenschaften
            </CardTitle>
            <p className="text-sm text-gray-600 dark:text-zinc-400">
              Wir haben Ihre Website analysiert. Bitte bestätigen oder ergänzen Sie die erkannten Funktionen.
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Erkannter CMS-Typ */}
            {features.cms_type && (
              <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <div className="flex items-center gap-2 text-blue-300 mb-2">
                  <Info className="w-4 h-4" />
                  <span className="font-medium">Erkanntes System</span>
                </div>
                <p className="text-gray-900 dark:text-white font-semibold">
                  {CMS_TYPES[features.cms_type as keyof typeof CMS_TYPES]?.icon} {CMS_TYPES[features.cms_type as keyof typeof CMS_TYPES]?.name || features.cms_type}
                </p>
              </div>
            )}

            {/* Feature Checkboxes */}
            <div className="space-y-4">
              <p className="text-sm font-medium text-gray-700 dark:text-zinc-300">Welche Funktionen hat Ihre Website?</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[
                  { key: 'has_shop', label: 'Online-Shop / E-Commerce', icon: ShoppingCart, desc: 'Produkte werden online verkauft' },
                  { key: 'has_contact_form', label: 'Kontaktformular', icon: MessageSquare, desc: 'Besucher können Nachrichten senden' },
                  { key: 'has_newsletter', label: 'Newsletter-Anmeldung', icon: Mail, desc: 'E-Mail-Adressen werden gesammelt' },
                  { key: 'has_user_accounts', label: 'Benutzerkonten / Login', icon: User, desc: 'Besucher können sich registrieren' },
                  { key: 'has_analytics', label: 'Analyse-Tools (Analytics)', icon: BarChart3, desc: 'Besucherstatistiken werden erfasst' },
                  { key: 'has_payment', label: 'Zahlungsabwicklung', icon: CreditCard, desc: 'Online-Bezahlung möglich' },
                  { key: 'has_social_media', label: 'Social Media Integration', icon: Globe, desc: 'Facebook, Instagram, etc. eingebunden' },
                  { key: 'has_comments', label: 'Kommentarfunktion', icon: MessageSquare, desc: 'Besucher können kommentieren' },
                ].map(({ key, label, icon: Icon, desc }) => (
                  <label 
                    key={key}
                    className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-all ${
                      features[key as keyof WebsiteFeatures] 
                        ? 'bg-emerald-500/20 border-2 border-emerald-500/50' 
                        : 'dark:bg-zinc-800 bg-gray-50 border-2 dark:border-zinc-700 border-gray-200 hover:border-zinc-600'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={features[key as keyof WebsiteFeatures] as boolean}
                      onChange={() => handleFeatureToggle(key as keyof WebsiteFeatures)}
                      className="mt-1 w-4 h-4 text-emerald-500 rounded dark:border-zinc-600 border-gray-300 focus:ring-emerald-500"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Icon className="w-4 h-4 text-gray-600 dark:text-zinc-400" />
                        <span className="font-medium text-gray-900 dark:text-white">{label}</span>
                      </div>
                      <p className="text-xs text-zinc-500 mt-1">{desc}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex justify-between pt-4">
              <Button onClick={onBack} variant="outline" className="gap-2 dark:border-zinc-700 border-gray-200 text-gray-700 dark:text-zinc-300 hover:bg-gray-100 dark:hover:bg-zinc-800">
                <ArrowLeft className="w-4 h-4" /> Zurück
              </Button>
              <Button onClick={() => setStep(2)} className="gap-2 bg-blue-600 hover:bg-blue-700">
                Weiter <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Company Basics */}
      {step === 2 && (
        <Card className="dark:bg-zinc-900 bg-white dark:border-zinc-800 border-gray-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-gray-900 dark:text-white">
              <Building className="w-6 h-6 text-blue-400" />
              Schritt 2: Unternehmensdaten
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">
                Firmenname <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={companyData.company_name || ''}
                onChange={(e) => handleInputChange('company_name', e.target.value)}
                placeholder="z.B. Musterfirma GmbH"
                className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">
                Rechtsform <span className="text-red-400">*</span>
              </label>
              <select
                value={companyData.legal_form || 'GmbH'}
                onChange={(e) => handleInputChange('legal_form', e.target.value)}
                className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              >
                {LEGAL_FORMS.map(form => (
                  <option key={form.value} value={form.value}>{form.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">
                Geschäftsführer / Vertretungsberechtigter <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={companyData.representative || ''}
                onChange={(e) => handleInputChange('representative', e.target.value)}
                placeholder="z.B. Max Mustermann"
                className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500 focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex justify-between pt-4">
              <Button onClick={() => setStep(1)} variant="outline" className="gap-2 dark:border-zinc-700 border-gray-200 text-gray-700 dark:text-zinc-300 hover:bg-gray-100 dark:hover:bg-zinc-800">
                <ArrowLeft className="w-4 h-4" /> Zurück
              </Button>
              <Button onClick={() => setStep(3)} disabled={!isStepValid()} className="gap-2 bg-blue-600 hover:bg-blue-700">
                Weiter <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Contact & Address */}
      {step === 3 && (
        <Card className="dark:bg-zinc-900 bg-white dark:border-zinc-800 border-gray-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-gray-900 dark:text-white">
              <MapPin className="w-6 h-6 text-blue-400" />
              Schritt 3: Adresse & Kontakt
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Straße und Hausnummer <span className="text-red-400">*</span></label>
                <input type="text" value={companyData.address || ''} onChange={(e) => handleInputChange('address', e.target.value)}
                  placeholder="z.B. Musterstraße 123" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">PLZ <span className="text-red-400">*</span></label>
                <input type="text" value={companyData.postal_code || ''} onChange={(e) => handleInputChange('postal_code', e.target.value)}
                  placeholder="z.B. 12345" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Stadt <span className="text-red-400">*</span></label>
                <input type="text" value={companyData.city || ''} onChange={(e) => handleInputChange('city', e.target.value)}
                  placeholder="z.B. Berlin" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">E-Mail-Adresse <span className="text-red-400">*</span></label>
                <input type="email" value={companyData.email || ''} onChange={(e) => handleInputChange('email', e.target.value)}
                  placeholder="z.B. info@musterfirma.de" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Telefon (optional)</label>
                <input type="tel" value={companyData.phone || ''} onChange={(e) => handleInputChange('phone', e.target.value)}
                  placeholder="z.B. +49 30 12345678" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">USt-IdNr. (optional)</label>
                <input type="text" value={companyData.ust_id || ''} onChange={(e) => handleInputChange('ust_id', e.target.value)}
                  placeholder="z.B. DE123456789" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Handelsregister-Nr. (optional)</label>
                <input type="text" value={companyData.registration_number || ''} onChange={(e) => handleInputChange('registration_number', e.target.value)}
                  placeholder="z.B. HRB 12345, Amtsgericht Berlin" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
              </div>

              {/* Impressum-spezifische Zusatzangaben */}
              {documentType === 'impressum' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Berufsbezeichnung (optional)</label>
                    <input type="text" value={companyData.profession || ''} onChange={(e) => handleInputChange('profession', e.target.value)}
                      placeholder="z.B. Rechtsanwalt, Steuerberater" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Zuständige Aufsichtsbehörde (optional)</label>
                    <input type="text" value={companyData.regulatory_authority || ''} onChange={(e) => handleInputChange('regulatory_authority', e.target.value)}
                      placeholder="z.B. Rechtsanwaltskammer Berlin" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Inhaltlich Verantwortlicher § 18 Abs. 2 MStV (optional)</label>
                    <input type="text" value={companyData.content_responsible || ''} onChange={(e) => handleInputChange('content_responsible', e.target.value)}
                      placeholder="Name, falls abweichend vom Vertreter" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
                  </div>
                </>
              )}

              {/* Datenschutz-spezifische Zusatzangaben */}
              {documentType === 'datenschutz' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Hosting-Anbieter (optional)</label>
                    <input type="text" value={companyData.hosting_provider || ''} onChange={(e) => handleInputChange('hosting_provider', e.target.value)}
                      placeholder="z.B. Hetzner Online GmbH" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Server-Standort (optional)</label>
                    <input type="text" value={companyData.server_location || ''} onChange={(e) => handleInputChange('server_location', e.target.value)}
                      placeholder="z.B. Deutschland (Nürnberg)" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
                  </div>
                </>
              )}

              {/* AGB-spezifische Angaben */}
              {documentType === 'agb' && (
                <>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Leistungsbeschreibung</label>
                    <textarea value={companyData.service_description || ''} onChange={(e) => handleInputChange('service_description', e.target.value)}
                      placeholder="Was bieten Sie an? z.B. SaaS-Abo für Compliance-Scans" rows={2} className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Zielgruppe (optional)</label>
                    <select value={companyData.target_audience || ''} onChange={(e) => handleInputChange('target_audience', e.target.value)}
                      className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white">
                      <option value="">Bitte wählen…</option>
                      <option value="Verbraucher (B2C)">Verbraucher (B2C)</option>
                      <option value="Unternehmen (B2B)">Unternehmen (B2B)</option>
                      <option value="B2C und B2B">B2C und B2B</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Preismodell (optional)</label>
                    <input type="text" value={companyData.pricing_model || ''} onChange={(e) => handleInputChange('pricing_model', e.target.value)}
                      placeholder="z.B. monatliches Abo, Festpreis" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Zahlungsarten (optional)</label>
                    <input type="text" value={companyData.payment_methods || ''} onChange={(e) => handleInputChange('payment_methods', e.target.value)}
                      placeholder="z.B. Kreditkarte, SEPA, PayPal" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Mindestlaufzeit (optional)</label>
                    <input type="text" value={companyData.min_contract_duration || ''} onChange={(e) => handleInputChange('min_contract_duration', e.target.value)}
                      placeholder="z.B. 1 Monat, 12 Monate" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Kündigungsfrist (optional)</label>
                    <input type="text" value={companyData.cancellation_period || ''} onChange={(e) => handleInputChange('cancellation_period', e.target.value)}
                      placeholder="z.B. 14 Tage zum Monatsende" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Automatische Verlängerung (optional)</label>
                    <input type="text" value={companyData.auto_renewal || ''} onChange={(e) => handleInputChange('auto_renewal', e.target.value)}
                      placeholder="z.B. um jeweils 1 Monat" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Gerichtsstand B2B (optional)</label>
                    <input type="text" value={companyData.jurisdiction || ''} onChange={(e) => handleInputChange('jurisdiction', e.target.value)}
                      placeholder="z.B. Berlin" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
                  </div>
                </>
              )}

              {/* Cookie-spezifische Angaben */}
              {documentType === 'cookie' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Consent-Tool (optional)</label>
                    <input type="text" value={companyData.consent_tool || ''} onChange={(e) => handleInputChange('consent_tool', e.target.value)}
                      placeholder="z.B. Usercentrics, Cookiebot, eigenes Banner" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Link zur Datenschutzerklärung (optional)</label>
                    <input type="text" value={companyData.privacy_url || ''} onChange={(e) => handleInputChange('privacy_url', e.target.value)}
                      placeholder="z.B. /datenschutz" className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Eingesetzte Drittanbieter-Dienste (optional)</label>
                    <textarea value={companyData.third_party_services || ''} onChange={(e) => handleInputChange('third_party_services', e.target.value)}
                      placeholder="z.B. Google Analytics, Meta Pixel, YouTube" rows={2} className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
                  </div>
                </>
              )}

              {/* Widerruf-spezifische Angaben */}
              {documentType === 'widerruf' && (
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-2">Hinweis zu Ausschluss/Erlöschen des Widerrufsrechts (optional)</label>
                  <textarea value={companyData.withdrawal_exceptions || ''} onChange={(e) => handleInputChange('withdrawal_exceptions', e.target.value)}
                    placeholder="z.B. bei sofort beginnenden Dienstleistungen mit ausdrücklicher Zustimmung; bei digitalen Inhalten" rows={3} className="w-full px-4 py-2 dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg text-gray-900 dark:text-white placeholder-zinc-500" />
                </div>
              )}
            </div>

            <div className="flex justify-between pt-4">
              <Button onClick={() => setStep(2)} variant="outline" className="gap-2 dark:border-zinc-700 border-gray-200 text-gray-700 dark:text-zinc-300 hover:bg-gray-100 dark:hover:bg-zinc-800">
                <ArrowLeft className="w-4 h-4" /> Zurück
              </Button>
              <Button onClick={() => setStep(4)} disabled={!isStepValid()} className="gap-2 bg-blue-600 hover:bg-blue-700">
                Weiter <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 4: Review */}
      {step === 4 && (
        <Card className="dark:bg-zinc-900 bg-white dark:border-zinc-800 border-gray-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-gray-900 dark:text-white">
              <Shield className="w-6 h-6 text-blue-400" />
              Schritt 4: Zusammenfassung
            </CardTitle>
            <p className="text-sm text-gray-600 dark:text-zinc-400">Bitte prüfen Sie Ihre Angaben vor der Generierung.</p>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <h4 className="font-semibold text-gray-900 dark:text-white">Unternehmen</h4>
                <div className="text-sm text-gray-600 dark:text-zinc-400 space-y-1">
                  <p><strong className="text-gray-700 dark:text-zinc-300">Firma:</strong> {companyData.company_name} {companyData.legal_form}</p>
                  <p><strong className="text-gray-700 dark:text-zinc-300">Vertreter:</strong> {companyData.representative}</p>
                  <p><strong className="text-gray-700 dark:text-zinc-300">Adresse:</strong> {companyData.address}, {companyData.postal_code} {companyData.city}</p>
                  <p><strong className="text-gray-700 dark:text-zinc-300">E-Mail:</strong> {companyData.email}</p>
                </div>
              </div>
              
              <div className="space-y-3">
                <h4 className="font-semibold text-gray-900 dark:text-white">Website-Funktionen</h4>
                <div className="flex flex-wrap gap-2">
                  {features.has_shop && <DetectedFeaturesBadge detected={true} label="Online-Shop" />}
                  {features.has_contact_form && <DetectedFeaturesBadge detected={true} label="Kontaktformular" />}
                  {features.has_newsletter && <DetectedFeaturesBadge detected={true} label="Newsletter" />}
                  {features.has_user_accounts && <DetectedFeaturesBadge detected={true} label="Benutzerkonten" />}
                  {features.has_analytics && <DetectedFeaturesBadge detected={true} label="Analytics" />}
                  {features.has_payment && <DetectedFeaturesBadge detected={true} label="Zahlungen" />}
                  {features.has_social_media && <DetectedFeaturesBadge detected={true} label="Social Media" />}
                  {!features.has_shop && !features.has_contact_form && !features.has_newsletter && 
                   !features.has_analytics && <span className="text-zinc-500 text-sm">Keine speziellen Funktionen ausgewählt</span>}
                </div>
              </div>
            </div>

            <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
              <p className="text-sm text-amber-200">
                <AlertCircle className="w-4 h-4 inline mr-2" />
                Das generierte Dokument basiert auf Ihren Angaben. Bitte prüfen Sie es vor der Veröffentlichung 
                und passen Sie es bei Bedarf an Ihre spezifische Situation an.
              </p>
            </div>

            {/* Sichtbarer Fehlerzustand — es gibt bewusst KEINEN lokalen Fallback-Text */}
            {generationError && (
              <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                <p className="text-sm font-semibold text-red-300 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Generierung fehlgeschlagen
                </p>
                <p className="text-sm text-red-200 mt-1">{generationError}</p>
                <p className="text-xs text-red-300/80 mt-2">
                  Es wurde kein Dokument erstellt. Bitte prüfen Sie Ihre Angaben und versuchen Sie es erneut.
                </p>
              </div>
            )}

            <div className="flex justify-between pt-4">
              <Button onClick={() => setStep(3)} variant="outline" className="gap-2 dark:border-zinc-700 border-gray-200 text-gray-700 dark:text-zinc-300 hover:bg-gray-100 dark:hover:bg-zinc-800">
                <ArrowLeft className="w-4 h-4" /> Zurück
              </Button>
              <Button onClick={handleGenerate} disabled={isGenerating} className="gap-2 bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-600 hover:to-green-700">
                {isGenerating ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Generiere...</>
                ) : (
                  <><FileText className="w-4 h-4" /> {getTitleForType()}</>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 5: Result */}
      {step === 5 && finalContent && (
        <Card className="dark:bg-zinc-900 bg-white dark:border-zinc-800 border-gray-200">
          <CardHeader className="bg-gradient-to-r from-emerald-500/10 to-green-500/10 border-b border-emerald-500/30">
            <CardTitle className="flex items-center gap-3 text-gray-900 dark:text-white">
              <CheckCircle className="w-6 h-6 text-emerald-400" />
              ✅ {DOC_CONFIG[documentType].label} erfolgreich erstellt!
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6 pt-6">
            {/* Preview */}
            <div className="bg-white rounded-lg p-6 max-h-80 overflow-y-auto">
              <div className="prose prose-sm max-w-none" dangerouslySetInnerHTML={{ __html: sanitizeHtml(finalContent || '') }} />
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button onClick={handleCopy} variant="outline" className="flex-1 gap-2 dark:border-zinc-700 border-gray-200 text-gray-700 dark:text-zinc-300 hover:bg-gray-100 dark:hover:bg-zinc-800">
                <Copy className="w-4 h-4" /> {copied ? '✅ Kopiert!' : 'HTML kopieren'}
              </Button>
              <Button onClick={handleDownload} variant="outline" className="flex-1 gap-2 dark:border-zinc-700 border-gray-200 text-gray-700 dark:text-zinc-300 hover:bg-gray-100 dark:hover:bg-zinc-800">
                <Download className="w-4 h-4" /> Als HTML downloaden
              </Button>
            </div>

            {/* Integration Guide */}
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
              <h4 className="font-semibold text-blue-300 mb-3 flex items-center gap-2">
                <Code className="w-5 h-5" />
                {getIntegrationGuide().title}
              </h4>
              <ol className="text-sm text-blue-200 space-y-2 list-decimal list-inside">
                {getIntegrationGuide().steps.map((step, idx) => (
                  <li key={idx}>{step}</li>
                ))}
              </ol>
            </div>

            <div className="flex justify-between pt-4 border-t dark:border-zinc-800 border-gray-200">
              <Button onClick={() => setStep(4)} variant="outline" className="gap-2 dark:border-zinc-700 border-gray-200 text-gray-700 dark:text-zinc-300 hover:bg-gray-100 dark:hover:bg-zinc-800">
                <ArrowLeft className="w-4 h-4" /> Daten bearbeiten
              </Button>
              <Button onClick={() => onComplete({ companyData, features, content: finalContent })} className="gap-2 bg-gradient-to-r from-blue-500 to-purple-600">
                <CheckCircle className="w-4 h-4" /> Fertig
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default LegalDocumentGenerator;
