'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, ArrowRight, ArrowLeft, Copy, Download, AlertCircle, Building, Mail, Phone, MapPin, User, Globe } from 'lucide-react';

interface LegalTextWizardProps {
  fixType: 'impressum' | 'datenschutz' | 'agb' | 'widerruf';
  generatedContent?: string;
  onComplete: (data: any) => void;
  onBack: () => void;
}

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
}

export const LegalTextWizard: React.FC<LegalTextWizardProps> = ({ 
  fixType, 
  generatedContent,
  onComplete, 
  onBack 
}) => {
  const [step, setStep] = useState(generatedContent ? 3 : 1);
  const [companyData, setCompanyData] = useState<Partial<CompanyData>>({
    country: 'Deutschland',
    legal_form: 'GmbH'
  });
  const [isGenerating, setIsGenerating] = useState(false);
  const [finalContent, setFinalContent] = useState(generatedContent || '');
  const [copied, setCopied] = useState(false);

  const getTitleForType = () => {
    switch (fixType) {
      case 'impressum': return 'Impressum erstellen';
      case 'datenschutz': return 'Datenschutzerklärung erstellen';
      case 'agb': return 'AGB erstellen';
      case 'widerruf': return 'Widerrufsbelehrung erstellen';
      default: return 'Rechtstext erstellen';
    }
  };

  const handleInputChange = (field: keyof CompanyData, value: string) => {
    setCompanyData(prev => ({ ...prev, [field]: value }));
  };

  const isStepValid = () => {
    if (step === 1) {
      return companyData.company_name && companyData.legal_form;
    }
    if (step === 2) {
      return companyData.address && companyData.city && companyData.email;
    }
    return true;
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    
    try {
      // Call eRecht24 API to generate personalized legal text
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v2/legal/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          text_type: fixType === 'datenschutz' ? 'datenschutz' : fixType,
          company_data: companyData,
          language: 'de'
        })
      });
      
      if (!response.ok) {
        throw new Error('Rechtstext-Generierung fehlgeschlagen');
      }
      
      const data = await response.json();
      setFinalContent(data.html || data.content || '');
      setStep(3);
    } catch (error) {
      console.error('Fehler bei Rechtstext-Generierung:', error);
      // Fallback to local generation if API fails
      const content = generatePersonalizedContent(companyData);
      setFinalContent(content);
      setStep(3);
    } finally {
      setIsGenerating(false);
    }
  };

  const generatePersonalizedContent = (data: Partial<CompanyData>) => {
    if (fixType === 'impressum') {
      return `<h1>Impressum</h1>

<h2>Angaben gemäß § 5 TMG</h2>

<p>
${data.company_name || '[Firmenname]'}<br>
${data.legal_form || '[Rechtsform]'}<br>
${data.address || '[Straße und Hausnummer]'}<br>
${data.postal_code || '[PLZ]'} ${data.city || '[Stadt]'}<br>
${data.country || 'Deutschland'}
</p>

<h2>Vertreten durch</h2>
<p>${data.representative || '[Geschäftsführer/Vertretungsberechtigter]'}</p>

<h2>Kontakt</h2>
<p>
E-Mail: ${data.email || '[E-Mail-Adresse]'}<br>
Telefon: ${data.phone || '[Telefonnummer]'}<br>
Website: ${data.website || '[Website-URL]'}
</p>

${data.ust_id ? `<h2>Umsatzsteuer-ID</h2>
<p>Umsatzsteuer-Identifikationsnummer gemäß §27 a Umsatzsteuergesetz:<br>
${data.ust_id}</p>` : ''}

${data.registration_number ? `<h2>Registereintrag</h2>
<p>Handelsregisternummer: ${data.registration_number}</p>` : ''}

<h2>EU-Streitschlichtung</h2>
<p>Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: 
<a href="https://ec.europa.eu/consumers/odr" target="_blank">https://ec.europa.eu/consumers/odr</a><br>
Unsere E-Mail-Adresse finden Sie oben im Impressum.</p>

<h2>Verbraucherstreitbeilegung/Universalschlichtungsstelle</h2>
<p>Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer 
Verbraucherschlichtungsstelle teilzunehmen.</p>

<p><small><em>Erstellt mit Complyo - Ihrer Compliance-Plattform</em></small></p>`;
    } else if (fixType === 'datenschutz') {
      return `<h1>Datenschutzerklärung</h1>

<h2>1. Datenschutz auf einen Blick</h2>

<h3>Allgemeine Hinweise</h3>
<p>Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren personenbezogenen Daten 
passiert, wenn Sie diese Website besuchen. Personenbezogene Daten sind alle Daten, mit denen Sie 
persönlich identifiziert werden können.</p>

<h3>Datenerfassung auf dieser Website</h3>
<p><strong>Wer ist verantwortlich für die Datenerfassung auf dieser Website?</strong></p>
<p>Die Datenverarbeitung auf dieser Website erfolgt durch den Websitebetreiber. Dessen Kontaktdaten 
können Sie dem Abschnitt „Hinweis zur Verantwortlichen Stelle" in dieser Datenschutzerklärung entnehmen.</p>

<h2>2. Hosting</h2>
<p>Wir hosten die Inhalte unserer Website bei folgendem Anbieter:</p>
<p>[Hosting-Provider-Details hier einfügen]</p>

<h2>3. Allgemeine Hinweise und Pflichtinformationen</h2>

<h3>Datenschutz</h3>
<p>Die Betreiber dieser Seiten nehmen den Schutz Ihrer persönlichen Daten sehr ernst. Wir behandeln Ihre 
personenbezogenen Daten vertraulich und entsprechend den gesetzlichen Datenschutzvorschriften sowie 
dieser Datenschutzerklärung.</p>

<h3>Hinweis zur verantwortlichen Stelle</h3>
<p>Die verantwortliche Stelle für die Datenverarbeitung auf dieser Website ist:</p>

<p>
${data.company_name || '[Firmenname]'}<br>
${data.address || '[Straße und Hausnummer]'}<br>
${data.postal_code || '[PLZ]'} ${data.city || '[Stadt]'}
</p>

<p>
Telefon: ${data.phone || '[Telefonnummer]'}<br>
E-Mail: ${data.email || '[E-Mail-Adresse]'}
</p>

<h2>4. Datenerfassung auf dieser Website</h2>

<h3>Cookies</h3>
<p>Unsere Internetseiten verwenden so genannte „Cookies". Cookies sind kleine Textdateien und richten auf 
Ihrem Endgerät keinen Schaden an. Sie werden entweder vorübergehend für die Dauer einer Sitzung 
(Session-Cookies) oder dauerhaft (permanente Cookies) auf Ihrem Endgerät gespeichert.</p>

<h3>Server-Log-Dateien</h3>
<p>Der Provider der Seiten erhebt und speichert automatisch Informationen in so genannten Server-Log-Dateien, 
die Ihr Browser automatisch an uns übermittelt.</p>

<h2>5. Analyse-Tools und Werbung</h2>
<p>[Details zu genutzten Analyse-Tools hier einfügen, z.B. Google Analytics]</p>

<h2>6. Plugins und Tools</h2>
<p>[Details zu genutzten Plugins hier einfügen]</p>

<h2>7. Ihre Rechte</h2>
<p>Sie haben jederzeit das Recht:</p>
<ul>
<li>gemäß Art. 15 DSGVO Auskunft über Ihre von uns verarbeiteten personenbezogenen Daten zu verlangen</li>
<li>gemäß Art. 16 DSGVO unverzüglich die Berichtigung unrichtiger oder Vervollständigung Ihrer bei uns gespeicherten personenbezogenen Daten zu verlangen</li>
<li>gemäß Art. 17 DSGVO die Löschung Ihrer bei uns gespeicherten personenbezogenen Daten zu verlangen</li>
<li>gemäß Art. 18 DSGVO die Einschränkung der Verarbeitung Ihrer personenbezogenen Daten zu verlangen</li>
<li>gemäß Art. 20 DSGVO Ihre personenbezogenen Daten, die Sie uns bereitgestellt haben, in einem strukturierten, gängigen und maschinenlesebaren Format zu erhalten</li>
<li>gemäß Art. 7 Abs. 3 DSGVO Ihre einmal erteilte Einwilligung jederzeit gegenüber uns zu widerrufen</li>
<li>gemäß Art. 77 DSGVO sich bei einer Aufsichtsbehörde zu beschweren</li>
</ul>

<p><small><em>Stand: ${new Date().toLocaleDateString('de-DE')}<br>
Erstellt mit Complyo - Ihrer Compliance-Plattform</em></small></p>`;
    }
    return generatedContent || '<p>Rechtstext wird generiert...</p>';
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
    a.download = `${fixType}-${companyData.company_name?.toLowerCase().replace(/\s+/g, '-') || 'rechtstext'}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Progress Steps */}
      <div className="flex items-center justify-center gap-4 mb-8">
        {[1, 2, 3].map((s) => (
          <React.Fragment key={s}>
            <div className={`flex items-center justify-center w-10 h-10 rounded-full font-bold ${
              step >= s ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
            }`}>
              {step > s ? <CheckCircle className="w-6 h-6" /> : s}
            </div>
            {s < 3 && (
              <div className={`w-16 h-1 ${step > s ? 'bg-blue-600' : 'bg-gray-200'}`} />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Step 1: Company Basics */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <Building className="w-6 h-6 text-blue-600" />
              Schritt 1: Unternehmensdaten
            </CardTitle>
            <p className="text-sm text-gray-600">Geben Sie Ihre grundlegenden Firmendaten ein</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Firmenname <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={companyData.company_name || ''}
                onChange={(e) => handleInputChange('company_name', e.target.value)}
                placeholder="z.B. Musterfirma GmbH"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Rechtsform <span className="text-red-500">*</span>
              </label>
              <select
                value={companyData.legal_form || 'GmbH'}
                onChange={(e) => handleInputChange('legal_form', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="GmbH">GmbH</option>
                <option value="UG">UG (haftungsbeschränkt)</option>
                <option value="AG">AG</option>
                <option value="GbR">GbR</option>
                <option value="OHG">OHG</option>
                <option value="KG">KG</option>
                <option value="Einzelunternehmen">Einzelunternehmen</option>
                <option value="Freiberufler">Freiberufler</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Geschäftsführer/Vertretungsberechtigter <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={companyData.representative || ''}
                onChange={(e) => handleInputChange('representative', e.target.value)}
                placeholder="z.B. Max Mustermann"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div className="flex justify-between pt-4">
              <Button
                onClick={onBack}
                variant="outline"
                className="flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Zurück
              </Button>
              <Button
                onClick={() => setStep(2)}
                disabled={!isStepValid()}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white"
              >
                Weiter
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Contact & Address */}
      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <MapPin className="w-6 h-6 text-blue-600" />
              Schritt 2: Adresse & Kontakt
            </CardTitle>
            <p className="text-sm text-gray-600">Vervollständigen Sie Ihre Kontaktinformationen</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Straße und Hausnummer <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={companyData.address || ''}
                  onChange={(e) => handleInputChange('address', e.target.value)}
                  placeholder="z.B. Musterstraße 123"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  PLZ <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={companyData.postal_code || ''}
                  onChange={(e) => handleInputChange('postal_code', e.target.value)}
                  placeholder="z.B. 12345"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Stadt <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={companyData.city || ''}
                  onChange={(e) => handleInputChange('city', e.target.value)}
                  placeholder="z.B. Berlin"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  E-Mail-Adresse <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  value={companyData.email || ''}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  placeholder="z.B. info@musterfirma.de"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Telefon
                </label>
                <input
                  type="tel"
                  value={companyData.phone || ''}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  placeholder="z.B. +49 30 12345678"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Website
                </label>
                <input
                  type="url"
                  value={companyData.website || ''}
                  onChange={(e) => handleInputChange('website', e.target.value)}
                  placeholder="z.B. www.musterfirma.de"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  USt-IdNr. (optional)
                </label>
                <input
                  type="text"
                  value={companyData.ust_id || ''}
                  onChange={(e) => handleInputChange('ust_id', e.target.value)}
                  placeholder="z.B. DE123456789"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Handelsregister-Nr. (optional)
                </label>
                <input
                  type="text"
                  value={companyData.registration_number || ''}
                  onChange={(e) => handleInputChange('registration_number', e.target.value)}
                  placeholder="z.B. HRB 12345"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="flex justify-between pt-4">
              <Button
                onClick={() => setStep(1)}
                variant="outline"
                className="flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Zurück
              </Button>
              <Button
                onClick={handleGenerate}
                disabled={!isStepValid() || isGenerating}
                className="flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white"
              >
                {isGenerating ? (
                  <>
                    <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                    Generiere...
                  </>
                ) : (
                  <>
                    {getTitleForType()}
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Review & Download */}
      {step === 3 && finalContent && (
        <Card>
          <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50">
            <CardTitle className="flex items-center gap-3">
              <CheckCircle className="w-6 h-6 text-green-600" />
              ✅ {getTitleForType()} erfolgreich generiert!
            </CardTitle>
            <p className="text-sm text-gray-600">
              Ihr personalisierter Rechtstext ist fertig. Kopieren oder downloaden Sie ihn jetzt.
            </p>
          </CardHeader>
          <CardContent className="space-y-6 pt-6">
            {/* Preview */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 max-h-96 overflow-y-auto">
              <div 
                className="prose prose-sm max-w-none"
                dangerouslySetInnerHTML={{ __html: finalContent }}
              />
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button
                onClick={handleCopy}
                variant="outline"
                className="flex-1 flex items-center justify-center gap-2"
              >
                <Copy className="w-4 h-4" />
                {copied ? '✅ Kopiert!' : 'HTML kopieren'}
              </Button>
              <Button
                onClick={handleDownload}
                variant="outline"
                className="flex-1 flex items-center justify-center gap-2"
              >
                <Download className="w-4 h-4" />
                Als HTML downloaden
              </Button>
            </div>

            {/* Integration Instructions */}
            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
              <h4 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                📋 Integrations-Anleitung:
              </h4>
              <ol className="text-sm text-blue-800 space-y-2 ml-6 list-decimal">
                <li>Erstellen Sie eine neue Seite auf Ihrer Website (z.B. <code>/impressum.html</code>)</li>
                <li>Fügen Sie den generierten HTML-Code ein</li>
                <li>Verlinken Sie die Seite im Footer Ihrer Website</li>
                <li>Prüfen Sie, dass die Seite für alle Besucher erreichbar ist</li>
              </ol>
            </div>

            {/* Footer Actions */}
            <div className="flex justify-between pt-4 border-t border-gray-200">
              <Button
                onClick={() => setStep(2)}
                variant="outline"
                className="flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Daten bearbeiten
              </Button>
              <Button
                onClick={() => onComplete({ companyData, content: finalContent })}
                className="flex items-center gap-2 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white"
              >
                <CheckCircle className="w-4 h-4" />
                Fertig
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

