'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, ArrowRight, ArrowLeft, Copy, Download, AlertCircle, Building, Mail, Phone, MapPin, User, Globe } from 'lucide-react';
import { sanitizeHtml } from '@/lib/sanitize';
import { generateLegalText, type LegalDocumentType } from '@/lib/api';

interface LegalTextWizardProps {
  fixType: 'impressum' | 'datenschutz' | 'agb' | 'widerruf';
  generatedContent?: string;
  onComplete: (data: any) => void;
  onBack: () => void;
}

// Mapping Wizard-Typ -> Dokumenttyp des internen Rechtstexte-Generators
// (/api/legal-texts/{type}/generate)
const BACKEND_TYPE: Record<LegalTextWizardProps['fixType'], LegalDocumentType> = {
  impressum: 'imprint',
  datenschutz: 'privacy',
  agb: 'tos',
  widerruf: 'withdrawal',
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
  const [generationError, setGenerationError] = useState<string | null>(null);

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
    setGenerationError(null);

    try {
      // Interner Rechtstexte-Generator (KI + Vorlagen + Disclaimer).
      // Die Firmendaten werden auf das user_data-Schema des Backends gemappt.
      const data = await generateLegalText(BACKEND_TYPE[fixType], {
        user_data: {
          company_name: companyData.company_name || '',
          legal_form: companyData.legal_form,
          address: companyData.address,
          zip_city: [companyData.postal_code, companyData.city].filter(Boolean).join(' '),
          country: companyData.country,
          phone: companyData.phone,
          email: companyData.email,
          website: companyData.website,
          represented_by: companyData.representative,
          vat_id: companyData.ust_id,
          registration_number: companyData.registration_number,
        },
        language: 'de',
      });
      setFinalContent(data.html_content || data.plain_text || '');
      setStep(3);
    } catch (error) {
      // Kein stiller Fallback auf ein lokales Platzhalter-Template: ein
      // Platzhaltertext ohne Disclaimer darf niemals als Ergebnis erscheinen.
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

            {/* Sichtbarer Fehlerzustand — es gibt bewusst KEINEN lokalen Fallback-Text */}
            {generationError && (
              <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-red-800">Generierung fehlgeschlagen</p>
                  <p className="text-sm text-red-700 mt-1">{generationError}</p>
                  <p className="text-xs text-red-600 mt-2">
                    Es wurde kein Dokument erstellt. Bitte prüfen Sie Ihre Angaben und versuchen Sie es erneut.
                  </p>
                </div>
              </div>
            )}

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
                dangerouslySetInnerHTML={{ __html: sanitizeHtml(finalContent || '') }}
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

