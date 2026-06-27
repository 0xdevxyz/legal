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
  impressum:   { label: 'Impressum',            short: 'Impressum',   emoji: '📋', backendType: 'imprint',       slug: 'impressum',  legalBasis: 'nach § 5 TMG' },
  datenschutz: { label: 'Datenschutzerklärung', short: 'Datenschutz', emoji: '🔒', backendType: 'privacy',       slug: 'datenschutz', legalBasis: 'nach DSGVO' },
  agb:         { label: 'AGB',                   short: 'AGB',         emoji: '📜', backendType: 'tos',           slug: 'agb',        legalBasis: 'nach BGB §305 ff.' },
  cookie:      { label: 'Cookie-Richtlinie',     short: 'Cookies',     emoji: '🍪', backendType: 'cookie-policy', slug: 'cookie-richtlinie', legalBasis: 'nach TTDSG & DSGVO' },
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
      console.error('Fehler bei Rechtstext-Generierung:', error);
      const content = generateLocalContent();
      setFinalContent(content);
      setStep(5);
    } finally {
      setIsGenerating(false);
    }
  };

  const generateLocalContent = () => {
    switch (documentType) {
      case 'impressum': return generateImpressum();
      case 'datenschutz': return generateDatenschutz();
      case 'agb': return generateAGB();
      case 'cookie': return generateCookie();
      case 'widerruf': return generateWiderruf();
      default: return generateImpressum();
    }
  };

  // Minimaler lokaler Fallback (nur falls die KI-Generierung fehlschlägt).
  const localDocShell = (title: string, body: string) => `<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>${title} - ${companyData.company_name || ''}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; }
    h1 { color: #1a1a1a; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }
    h2 { color: #0066cc; margin-top: 30px; }
    p, li { margin: 10px 0; }
  </style>
</head>
<body>
${body}
  <p style="margin-top: 40px; font-size: 12px; color: #666;"><em>Stand: ${new Date().toLocaleDateString('de-DE')}</em></p>
</body>
</html>`;

  const generateAGB = () => localDocShell('AGB', `
  <h1>Allgemeine Geschäftsbedingungen</h1>
  <h2>1. Anbieter</h2>
  <p>${companyData.company_name || '[Firmenname]'} ${companyData.legal_form || ''}<br>
  ${companyData.address || ''}, ${companyData.postal_code || ''} ${companyData.city || ''}<br>
  E-Mail: ${companyData.email || '[E-Mail]'}</p>
  ${companyData.service_description ? `<h2>2. Leistungsbeschreibung</h2><p>${companyData.service_description}</p>` : ''}
  ${companyData.pricing_model ? `<h2>3. Preise</h2><p>${companyData.pricing_model}</p>` : ''}
  ${companyData.payment_methods ? `<h2>4. Zahlungsarten</h2><p>${companyData.payment_methods}</p>` : ''}
  ${(companyData.min_contract_duration || companyData.cancellation_period || companyData.auto_renewal) ? `<h2>5. Vertragslaufzeit & Kündigung</h2><p>Mindestlaufzeit: ${companyData.min_contract_duration || '–'}<br>Kündigungsfrist: ${companyData.cancellation_period || '–'}<br>Automatische Verlängerung: ${companyData.auto_renewal || '–'}</p>` : ''}
  <h2>6. Widerrufsrecht</h2>
  <p>Verbraucher haben ein Widerrufsrecht von 14 Tagen. Details siehe Widerrufsbelehrung.</p>
  <h2>7. Anwendbares Recht & Gerichtsstand</h2>
  <p>Es gilt deutsches Recht.${companyData.jurisdiction ? ` Gerichtsstand (B2B): ${companyData.jurisdiction}.` : ''}</p>`);

  const generateCookie = () => localDocShell('Cookie-Richtlinie', `
  <h1>Cookie-Richtlinie</h1>
  <h2>Verantwortlicher</h2>
  <p>${companyData.company_name || '[Firmenname]'}<br>E-Mail: ${companyData.email || '[E-Mail]'}</p>
  <h2>Verwendete Cookie-Kategorien</h2>
  <ul>
    <li><strong>Technisch notwendige Cookies</strong> – keine Einwilligung erforderlich (§ 25 Abs. 2 TTDSG)</li>
    <li><strong>Funktionale Cookies</strong> – Einwilligung erforderlich</li>
    <li><strong>Analyse-/Statistik-Cookies</strong> – Einwilligung erforderlich</li>
    <li><strong>Marketing-/Tracking-Cookies</strong> – Einwilligung erforderlich</li>
  </ul>
  ${companyData.consent_tool ? `<h2>Einwilligungsmanagement</h2><p>Consent-Tool: ${companyData.consent_tool}. Die Einwilligung kann jederzeit widerrufen werden.</p>` : ''}
  ${companyData.third_party_services ? `<h2>Drittanbieter</h2><p>${companyData.third_party_services}</p>` : ''}
  ${companyData.privacy_url ? `<p>Weitere Informationen in unserer <a href="${companyData.privacy_url}">Datenschutzerklärung</a>.</p>` : ''}`);

  const generateWiderruf = () => localDocShell('Widerrufsbelehrung', `
  <h1>Widerrufsbelehrung</h1>
  <h2>Widerrufsrecht</h2>
  <p>Sie haben das Recht, binnen vierzehn Tagen ohne Angabe von Gründen diesen Vertrag zu widerrufen.</p>
  <p>Um Ihr Widerrufsrecht auszuüben, müssen Sie uns (${companyData.company_name || '[Firmenname]'}, ${companyData.address || ''}, ${companyData.postal_code || ''} ${companyData.city || ''}, E-Mail: ${companyData.email || '[E-Mail]'}) mittels einer eindeutigen Erklärung über Ihren Entschluss informieren.</p>
  ${companyData.withdrawal_exceptions ? `<h2>Erlöschen / Ausnahmen</h2><p>${companyData.withdrawal_exceptions}</p>` : ''}
  <h2>Muster-Widerrufsformular</h2>
  <p>An: ${companyData.company_name || '[Firmenname]'}, ${companyData.address || ''}, ${companyData.postal_code || ''} ${companyData.city || ''}, E-Mail: ${companyData.email || '[E-Mail]'}<br>
  – Hiermit widerrufe(n) ich/wir den von mir/uns abgeschlossenen Vertrag<br>
  – Bestellt am / erhalten am<br>
  – Name des/der Verbraucher(s)<br>
  – Anschrift des/der Verbraucher(s)<br>
  – Datum</p>`);

  const generateImpressum = () => {
    return `<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>Impressum - ${companyData.company_name || ''}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; }
    h1 { color: #1a1a1a; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }
    h2 { color: #0066cc; margin-top: 30px; }
    p { margin: 10px 0; }
  </style>
</head>
<body>
  <h1>Impressum</h1>
  
  <h2>Angaben gemäß § 5 TMG</h2>
  <p>
    ${companyData.company_name || '[Firmenname]'}<br>
    ${companyData.legal_form || ''}<br>
    ${companyData.address || '[Straße und Hausnummer]'}<br>
    ${companyData.postal_code || '[PLZ]'} ${companyData.city || '[Stadt]'}<br>
    ${companyData.country || 'Deutschland'}
  </p>
  
  <h2>Vertreten durch</h2>
  <p>${companyData.representative || '[Geschäftsführer/Vertretungsberechtigter]'}</p>
  
  <h2>Kontakt</h2>
  <p>
    E-Mail: ${companyData.email || '[E-Mail-Adresse]'}<br>
    ${companyData.phone ? `Telefon: ${companyData.phone}<br>` : ''}
    ${companyData.website ? `Website: ${companyData.website}` : ''}
  </p>
  
  ${companyData.ust_id ? `
  <h2>Umsatzsteuer-ID</h2>
  <p>Umsatzsteuer-Identifikationsnummer gemäß § 27 a Umsatzsteuergesetz:<br>
  ${companyData.ust_id}</p>
  ` : ''}
  
  ${companyData.registration_number ? `
  <h2>Registereintrag</h2>
  <p>Handelsregisternummer: ${companyData.registration_number}</p>
  ` : ''}
  
  ${features.has_shop ? `
  <h2>Online-Streitbeilegung (OS)</h2>
  <p>Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: 
  <a href="https://ec.europa.eu/consumers/odr" target="_blank" rel="noopener">https://ec.europa.eu/consumers/odr</a></p>
  <p>Unsere E-Mail-Adresse finden Sie oben im Impressum.</p>
  
  <h2>Verbraucherstreitbeilegung/Universalschlichtungsstelle</h2>
  <p>Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer 
  Verbraucherschlichtungsstelle teilzunehmen.</p>
  ` : `
  <h2>EU-Streitschlichtung</h2>
  <p>Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: 
  <a href="https://ec.europa.eu/consumers/odr" target="_blank" rel="noopener">https://ec.europa.eu/consumers/odr</a></p>
  `}
  
  <p style="margin-top: 40px; font-size: 12px; color: #666;">
    <em>Stand: ${new Date().toLocaleDateString('de-DE')}</em>
  </p>
</body>
</html>`;
  };

  const generateDatenschutz = () => {
    return `<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>Datenschutzerklärung - ${companyData.company_name || ''}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; color: #333; }
    h1 { color: #1a1a1a; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }
    h2 { color: #0066cc; margin-top: 30px; }
    h3 { color: #444; margin-top: 20px; }
    p, li { margin: 10px 0; }
    ul { padding-left: 20px; }
  </style>
</head>
<body>
  <h1>Datenschutzerklärung</h1>
  
  <h2>1. Datenschutz auf einen Blick</h2>
  <h3>Allgemeine Hinweise</h3>
  <p>Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren personenbezogenen Daten 
  passiert, wenn Sie diese Website besuchen.</p>
  
  <h2>2. Verantwortliche Stelle</h2>
  <p>Die verantwortliche Stelle für die Datenverarbeitung auf dieser Website ist:</p>
  <p>
    ${companyData.company_name || '[Firmenname]'}<br>
    ${companyData.address || '[Straße und Hausnummer]'}<br>
    ${companyData.postal_code || '[PLZ]'} ${companyData.city || '[Stadt]'}
  </p>
  <p>
    ${companyData.phone ? `Telefon: ${companyData.phone}<br>` : ''}
    E-Mail: ${companyData.email || '[E-Mail-Adresse]'}
  </p>
  
  <h2>3. Datenerfassung auf dieser Website</h2>
  
  <h3>Cookies</h3>
  <p>Unsere Website verwendet Cookies. Dabei handelt es sich um kleine Textdateien, die Ihr Webbrowser 
  auf Ihrem Endgerät speichert.</p>
  
  <h3>Server-Log-Dateien</h3>
  <p>Der Provider der Seiten erhebt und speichert automatisch Informationen in sogenannten Server-Log-Dateien.</p>
  
  ${features.has_contact_form ? `
  <h3>Kontaktformular</h3>
  <p>Wenn Sie uns per Kontaktformular Anfragen zukommen lassen, werden Ihre Angaben aus dem Anfrageformular 
  inklusive der von Ihnen dort angegebenen Kontaktdaten zwecks Bearbeitung der Anfrage und für den Fall 
  von Anschlussfragen bei uns gespeichert. Diese Daten geben wir nicht ohne Ihre Einwilligung weiter.</p>
  <p>Rechtsgrundlage: Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung) bzw. Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse).</p>
  ` : ''}
  
  ${features.has_newsletter ? `
  <h3>Newsletter</h3>
  <p>Wenn Sie den auf der Website angebotenen Newsletter beziehen möchten, benötigen wir von Ihnen eine 
  E-Mail-Adresse sowie Informationen, welche uns die Überprüfung gestatten, dass Sie der Inhaber der 
  angegebenen E-Mail-Adresse sind und mit dem Empfang des Newsletters einverstanden sind (Double-Opt-In).</p>
  <p>Rechtsgrundlage: Art. 6 Abs. 1 lit. a DSGVO (Einwilligung).</p>
  ` : ''}
  
  ${features.has_user_accounts ? `
  <h3>Registrierung/Kundenkonto</h3>
  <p>Sie können sich auf unserer Website registrieren, um zusätzliche Funktionen nutzen zu können. 
  Die dabei eingegebenen Daten verwenden wir nur zum Zwecke der Nutzung des jeweiligen Angebotes.</p>
  <p>Rechtsgrundlage: Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung).</p>
  ` : ''}
  
  ${features.has_shop ? `
  <h2>4. Online-Shop / E-Commerce</h2>
  <h3>Bestellungen</h3>
  <p>Für die Abwicklung Ihrer Bestellung benötigen wir Ihre persönlichen Daten. Diese Daten 
  werden zur Vertragsabwicklung gespeichert und nach Ablauf der gesetzlichen Aufbewahrungsfristen gelöscht.</p>
  <p>Rechtsgrundlage: Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung).</p>
  
  ${features.has_payment ? `
  <h3>Zahlungsdienstleister</h3>
  <p>Wir nutzen externe Zahlungsdienstleister. Dabei werden Ihre Zahlungsdaten direkt an den 
  jeweiligen Dienstleister übermittelt. Diese Anbieter unterliegen ebenfalls den Datenschutzbestimmungen.</p>
  ` : ''}
  ` : ''}
  
  ${features.has_analytics ? `
  <h2>${features.has_shop ? '5' : '4'}. Analyse-Tools</h2>
  ${features.analytics_tools.includes('Google Analytics') ? `
  <h3>Google Analytics</h3>
  <p>Diese Website nutzt Funktionen des Webanalysedienstes Google Analytics. Anbieter ist die 
  Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland.</p>
  <p>Google Analytics verwendet sog. "Cookies". Die durch das Cookie erzeugten Informationen über 
  Ihre Benutzung dieser Website werden in der Regel an einen Server von Google in den USA übertragen.</p>
  <p>Wir haben die IP-Anonymisierung aktiviert. Dadurch wird Ihre IP-Adresse von Google innerhalb 
  der EU gekürzt.</p>
  <p>Rechtsgrundlage: Art. 6 Abs. 1 lit. a DSGVO (Einwilligung via Cookie-Banner).</p>
  ` : `
  <h3>Webanalyse</h3>
  <p>Diese Website nutzt Webanalyse-Tools zur statistischen Auswertung der Besucherzugriffe. 
  Die Analyse erfolgt erst nach Ihrer Einwilligung über unseren Cookie-Banner.</p>
  `}
  ` : ''}
  
  ${features.has_social_media ? `
  <h2>${features.has_shop ? (features.has_analytics ? '6' : '5') : (features.has_analytics ? '5' : '4')}. Social Media</h2>
  <h3>Social Media Plugins</h3>
  <p>Auf unserer Website können Social-Media-Plugins eingebunden sein. Diese Plugins werden erst 
  nach Ihrer Einwilligung aktiviert (2-Klick-Lösung oder Cookie-Consent).</p>
  ` : ''}
  
  <h2>${features.has_shop ? (features.has_analytics ? (features.has_social_media ? '7' : '6') : (features.has_social_media ? '6' : '5')) : (features.has_analytics ? (features.has_social_media ? '6' : '5') : (features.has_social_media ? '5' : '4'))}. Ihre Rechte</h2>
  <p>Sie haben folgende Rechte:</p>
  <ul>
    <li><strong>Auskunftsrecht (Art. 15 DSGVO)</strong>: Sie können Auskunft über Ihre von uns verarbeiteten personenbezogenen Daten verlangen.</li>
    <li><strong>Berichtigung (Art. 16 DSGVO)</strong>: Sie können die Berichtigung unrichtiger Daten verlangen.</li>
    <li><strong>Löschung (Art. 17 DSGVO)</strong>: Sie können die Löschung Ihrer Daten verlangen.</li>
    <li><strong>Einschränkung (Art. 18 DSGVO)</strong>: Sie können die Einschränkung der Verarbeitung verlangen.</li>
    <li><strong>Datenübertragbarkeit (Art. 20 DSGVO)</strong>: Sie können Ihre Daten in maschinenlesbarem Format erhalten.</li>
    <li><strong>Widerspruch (Art. 21 DSGVO)</strong>: Sie können der Verarbeitung widersprechen.</li>
    <li><strong>Widerruf (Art. 7 Abs. 3 DSGVO)</strong>: Sie können Ihre Einwilligung jederzeit widerrufen.</li>
    <li><strong>Beschwerde (Art. 77 DSGVO)</strong>: Sie können sich bei einer Aufsichtsbehörde beschweren.</li>
  </ul>
  
  <p style="margin-top: 40px; font-size: 12px; color: #666;">
    <em>Stand: ${new Date().toLocaleDateString('de-DE')}</em>
  </p>
</body>
</html>`;
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
        <h1 className="text-2xl font-bold text-white mb-2">
          {DOC_CONFIG[documentType].emoji} {DOC_CONFIG[documentType].label} Generator
        </h1>
        <p className="text-zinc-400">
          Erstellen Sie rechtssichere {DOC_CONFIG[documentType].label} {DOC_CONFIG[documentType].legalBasis} für Ihre Website
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-center gap-2 mb-8">
        {['Website', 'Firma', 'Kontakt', 'Prüfen', 'Fertig'].map((label, idx) => (
          <React.Fragment key={idx}>
            <div className={`flex flex-col items-center ${step > idx ? 'text-emerald-400' : step === idx + 1 ? 'text-blue-400' : 'text-zinc-600'}`}>
              <div className={`flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm ${
                step > idx + 1 ? 'bg-emerald-500 text-white' : step === idx + 1 ? 'bg-blue-500 text-white' : 'bg-zinc-700 text-zinc-400'
              }`}>
                {step > idx + 1 ? <CheckCircle className="w-5 h-5" /> : idx + 1}
              </div>
              <span className="text-xs mt-1 hidden sm:block">{label}</span>
            </div>
            {idx < 4 && <div className={`w-8 h-0.5 ${step > idx + 1 ? 'bg-emerald-500' : 'bg-zinc-700'}`} />}
          </React.Fragment>
        ))}
      </div>

      {/* Step 1: Website Features */}
      {step === 1 && (
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-white">
              <Globe className="w-6 h-6 text-blue-400" />
              Schritt 1: Website-Eigenschaften
            </CardTitle>
            <p className="text-sm text-zinc-400">
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
                <p className="text-white font-semibold">
                  {CMS_TYPES[features.cms_type as keyof typeof CMS_TYPES]?.icon} {CMS_TYPES[features.cms_type as keyof typeof CMS_TYPES]?.name || features.cms_type}
                </p>
              </div>
            )}

            {/* Feature Checkboxes */}
            <div className="space-y-4">
              <p className="text-sm font-medium text-zinc-300">Welche Funktionen hat Ihre Website?</p>
              
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
                        : 'bg-zinc-800 border-2 border-zinc-700 hover:border-zinc-600'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={features[key as keyof WebsiteFeatures] as boolean}
                      onChange={() => handleFeatureToggle(key as keyof WebsiteFeatures)}
                      className="mt-1 w-4 h-4 text-emerald-500 rounded border-zinc-600 focus:ring-emerald-500"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Icon className="w-4 h-4 text-zinc-400" />
                        <span className="font-medium text-white">{label}</span>
                      </div>
                      <p className="text-xs text-zinc-500 mt-1">{desc}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className="flex justify-between pt-4">
              <Button onClick={onBack} variant="outline" className="gap-2 border-zinc-700 text-zinc-300 hover:bg-zinc-800">
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
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-white">
              <Building className="w-6 h-6 text-blue-400" />
              Schritt 2: Unternehmensdaten
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-2">
                Firmenname <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={companyData.company_name || ''}
                onChange={(e) => handleInputChange('company_name', e.target.value)}
                placeholder="z.B. Musterfirma GmbH"
                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-2">
                Rechtsform <span className="text-red-400">*</span>
              </label>
              <select
                value={companyData.legal_form || 'GmbH'}
                onChange={(e) => handleInputChange('legal_form', e.target.value)}
                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white focus:ring-2 focus:ring-blue-500"
              >
                {LEGAL_FORMS.map(form => (
                  <option key={form.value} value={form.value}>{form.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-2">
                Geschäftsführer / Vertretungsberechtigter <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={companyData.representative || ''}
                onChange={(e) => handleInputChange('representative', e.target.value)}
                placeholder="z.B. Max Mustermann"
                className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex justify-between pt-4">
              <Button onClick={() => setStep(1)} variant="outline" className="gap-2 border-zinc-700 text-zinc-300 hover:bg-zinc-800">
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
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-white">
              <MapPin className="w-6 h-6 text-blue-400" />
              Schritt 3: Adresse & Kontakt
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-zinc-300 mb-2">Straße und Hausnummer <span className="text-red-400">*</span></label>
                <input type="text" value={companyData.address || ''} onChange={(e) => handleInputChange('address', e.target.value)}
                  placeholder="z.B. Musterstraße 123" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-2">PLZ <span className="text-red-400">*</span></label>
                <input type="text" value={companyData.postal_code || ''} onChange={(e) => handleInputChange('postal_code', e.target.value)}
                  placeholder="z.B. 12345" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-2">Stadt <span className="text-red-400">*</span></label>
                <input type="text" value={companyData.city || ''} onChange={(e) => handleInputChange('city', e.target.value)}
                  placeholder="z.B. Berlin" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-zinc-300 mb-2">E-Mail-Adresse <span className="text-red-400">*</span></label>
                <input type="email" value={companyData.email || ''} onChange={(e) => handleInputChange('email', e.target.value)}
                  placeholder="z.B. info@musterfirma.de" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-2">Telefon (optional)</label>
                <input type="tel" value={companyData.phone || ''} onChange={(e) => handleInputChange('phone', e.target.value)}
                  placeholder="z.B. +49 30 12345678" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-2">USt-IdNr. (optional)</label>
                <input type="text" value={companyData.ust_id || ''} onChange={(e) => handleInputChange('ust_id', e.target.value)}
                  placeholder="z.B. DE123456789" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-zinc-300 mb-2">Handelsregister-Nr. (optional)</label>
                <input type="text" value={companyData.registration_number || ''} onChange={(e) => handleInputChange('registration_number', e.target.value)}
                  placeholder="z.B. HRB 12345, Amtsgericht Berlin" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
              </div>

              {/* Impressum-spezifische Zusatzangaben */}
              {documentType === 'impressum' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Berufsbezeichnung (optional)</label>
                    <input type="text" value={companyData.profession || ''} onChange={(e) => handleInputChange('profession', e.target.value)}
                      placeholder="z.B. Rechtsanwalt, Steuerberater" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Zuständige Aufsichtsbehörde (optional)</label>
                    <input type="text" value={companyData.regulatory_authority || ''} onChange={(e) => handleInputChange('regulatory_authority', e.target.value)}
                      placeholder="z.B. Rechtsanwaltskammer Berlin" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Inhaltlich Verantwortlicher § 18 Abs. 2 MStV (optional)</label>
                    <input type="text" value={companyData.content_responsible || ''} onChange={(e) => handleInputChange('content_responsible', e.target.value)}
                      placeholder="Name, falls abweichend vom Vertreter" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
                  </div>
                </>
              )}

              {/* Datenschutz-spezifische Zusatzangaben */}
              {documentType === 'datenschutz' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Hosting-Anbieter (optional)</label>
                    <input type="text" value={companyData.hosting_provider || ''} onChange={(e) => handleInputChange('hosting_provider', e.target.value)}
                      placeholder="z.B. Hetzner Online GmbH" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Server-Standort (optional)</label>
                    <input type="text" value={companyData.server_location || ''} onChange={(e) => handleInputChange('server_location', e.target.value)}
                      placeholder="z.B. Deutschland (Nürnberg)" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
                  </div>
                </>
              )}

              {/* AGB-spezifische Angaben */}
              {documentType === 'agb' && (
                <>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Leistungsbeschreibung</label>
                    <textarea value={companyData.service_description || ''} onChange={(e) => handleInputChange('service_description', e.target.value)}
                      placeholder="Was bieten Sie an? z.B. SaaS-Abo für Compliance-Scans" rows={2} className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Zielgruppe (optional)</label>
                    <select value={companyData.target_audience || ''} onChange={(e) => handleInputChange('target_audience', e.target.value)}
                      className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white">
                      <option value="">Bitte wählen…</option>
                      <option value="Verbraucher (B2C)">Verbraucher (B2C)</option>
                      <option value="Unternehmen (B2B)">Unternehmen (B2B)</option>
                      <option value="B2C und B2B">B2C und B2B</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Preismodell (optional)</label>
                    <input type="text" value={companyData.pricing_model || ''} onChange={(e) => handleInputChange('pricing_model', e.target.value)}
                      placeholder="z.B. monatliches Abo, Festpreis" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Zahlungsarten (optional)</label>
                    <input type="text" value={companyData.payment_methods || ''} onChange={(e) => handleInputChange('payment_methods', e.target.value)}
                      placeholder="z.B. Kreditkarte, SEPA, PayPal" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Mindestlaufzeit (optional)</label>
                    <input type="text" value={companyData.min_contract_duration || ''} onChange={(e) => handleInputChange('min_contract_duration', e.target.value)}
                      placeholder="z.B. 1 Monat, 12 Monate" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Kündigungsfrist (optional)</label>
                    <input type="text" value={companyData.cancellation_period || ''} onChange={(e) => handleInputChange('cancellation_period', e.target.value)}
                      placeholder="z.B. 14 Tage zum Monatsende" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Automatische Verlängerung (optional)</label>
                    <input type="text" value={companyData.auto_renewal || ''} onChange={(e) => handleInputChange('auto_renewal', e.target.value)}
                      placeholder="z.B. um jeweils 1 Monat" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Gerichtsstand B2B (optional)</label>
                    <input type="text" value={companyData.jurisdiction || ''} onChange={(e) => handleInputChange('jurisdiction', e.target.value)}
                      placeholder="z.B. Berlin" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
                  </div>
                </>
              )}

              {/* Cookie-spezifische Angaben */}
              {documentType === 'cookie' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Consent-Tool (optional)</label>
                    <input type="text" value={companyData.consent_tool || ''} onChange={(e) => handleInputChange('consent_tool', e.target.value)}
                      placeholder="z.B. Usercentrics, Cookiebot, eigenes Banner" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Link zur Datenschutzerklärung (optional)</label>
                    <input type="text" value={companyData.privacy_url || ''} onChange={(e) => handleInputChange('privacy_url', e.target.value)}
                      placeholder="z.B. /datenschutz" className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-zinc-300 mb-2">Eingesetzte Drittanbieter-Dienste (optional)</label>
                    <textarea value={companyData.third_party_services || ''} onChange={(e) => handleInputChange('third_party_services', e.target.value)}
                      placeholder="z.B. Google Analytics, Meta Pixel, YouTube" rows={2} className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
                  </div>
                </>
              )}

              {/* Widerruf-spezifische Angaben */}
              {documentType === 'widerruf' && (
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-zinc-300 mb-2">Hinweis zu Ausschluss/Erlöschen des Widerrufsrechts (optional)</label>
                  <textarea value={companyData.withdrawal_exceptions || ''} onChange={(e) => handleInputChange('withdrawal_exceptions', e.target.value)}
                    placeholder="z.B. bei sofort beginnenden Dienstleistungen mit ausdrücklicher Zustimmung; bei digitalen Inhalten" rows={3} className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500" />
                </div>
              )}
            </div>

            <div className="flex justify-between pt-4">
              <Button onClick={() => setStep(2)} variant="outline" className="gap-2 border-zinc-700 text-zinc-300 hover:bg-zinc-800">
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
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-white">
              <Shield className="w-6 h-6 text-blue-400" />
              Schritt 4: Zusammenfassung
            </CardTitle>
            <p className="text-sm text-zinc-400">Bitte prüfen Sie Ihre Angaben vor der Generierung.</p>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Summary */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <h4 className="font-semibold text-white">Unternehmen</h4>
                <div className="text-sm text-zinc-400 space-y-1">
                  <p><strong className="text-zinc-300">Firma:</strong> {companyData.company_name} {companyData.legal_form}</p>
                  <p><strong className="text-zinc-300">Vertreter:</strong> {companyData.representative}</p>
                  <p><strong className="text-zinc-300">Adresse:</strong> {companyData.address}, {companyData.postal_code} {companyData.city}</p>
                  <p><strong className="text-zinc-300">E-Mail:</strong> {companyData.email}</p>
                </div>
              </div>
              
              <div className="space-y-3">
                <h4 className="font-semibold text-white">Website-Funktionen</h4>
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

            <div className="flex justify-between pt-4">
              <Button onClick={() => setStep(3)} variant="outline" className="gap-2 border-zinc-700 text-zinc-300 hover:bg-zinc-800">
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
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="bg-gradient-to-r from-emerald-500/10 to-green-500/10 border-b border-emerald-500/30">
            <CardTitle className="flex items-center gap-3 text-white">
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
              <Button onClick={handleCopy} variant="outline" className="flex-1 gap-2 border-zinc-700 text-zinc-300 hover:bg-zinc-800">
                <Copy className="w-4 h-4" /> {copied ? '✅ Kopiert!' : 'HTML kopieren'}
              </Button>
              <Button onClick={handleDownload} variant="outline" className="flex-1 gap-2 border-zinc-700 text-zinc-300 hover:bg-zinc-800">
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

            <div className="flex justify-between pt-4 border-t border-zinc-800">
              <Button onClick={() => setStep(4)} variant="outline" className="gap-2 border-zinc-700 text-zinc-300 hover:bg-zinc-800">
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
