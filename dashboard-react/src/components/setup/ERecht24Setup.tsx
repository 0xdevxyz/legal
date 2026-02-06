'use client';

import React, { useState } from 'react';
import { 
  Check, 
  ChevronRight, 
  ChevronLeft, 
  Shield, 
  ExternalLink, 
  AlertCircle,
  CheckCircle2,
  Loader2,
  Key,
  Globe,
  Building,
  Mail,
  Phone,
  MapPin,
  Sparkles
} from 'lucide-react';
import { useToast } from '@/components/ui/Toast';

// ============================================================================
// Types
// ============================================================================

interface CompanyInfo {
  company_name: string;
  address: string;
  postal_code: string;
  city: string;
  email: string;
  phone: string;
  vat_id?: string;
  registration_court?: string;
  registration_number?: string;
}

interface ERecht24SetupProps {
  domain: string;
  onComplete?: (projectData: any) => void;
  onSkip?: () => void;
  className?: string;
}

type SetupStep = 'intro' | 'choice' | 'api-key' | 'company-info' | 'confirm' | 'success';

// ============================================================================
// Main Component
// ============================================================================

export const ERecht24Setup: React.FC<ERecht24SetupProps> = ({
  domain,
  onComplete,
  onSkip,
  className = ''
}) => {
  const { showToast } = useToast();
  
  const [currentStep, setCurrentStep] = useState<SetupStep>('intro');
  const [hasERecht24Account, setHasERecht24Account] = useState<boolean | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo>({
    company_name: '',
    address: '',
    postal_code: '',
    city: '',
    email: '',
    phone: '',
    vat_id: '',
    registration_court: '',
    registration_number: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [projectData, setProjectData] = useState<any>(null);

  const handleSetup = async () => {
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/v2/erecht24/setup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          domain,
          company_info: hasERecht24Account ? null : companyInfo
        })
      });

      if (!response.ok) {
        throw new Error('Setup fehlgeschlagen');
      }

      const data = await response.json();
      setProjectData(data.project);
      setCurrentStep('success');
      showToast('eRecht24-Integration erfolgreich!', 'success');
      
      if (onComplete) {
        onComplete(data.project);
      }
    } catch (error) {
      showToast('Setup fehlgeschlagen. Bitte versuchen Sie es erneut.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkipSetup = () => {
    if (onSkip) {
      onSkip();
    }
    showToast('Setup übersprungen - AI-generierte Texte werden verwendet', 'info');
  };

  return (
    <div className={`max-w-4xl mx-auto ${className}`}>
      <div className="bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6 text-white">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">eRecht24-Integration</h2>
              <p className="text-blue-100 text-sm">Rechtssichere Texte automatisch generieren</p>
            </div>
          </div>
        </div>

        {/* Progress Indicator */}
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {['Einführung', 'Auswahl', 'Konfiguration', 'Bestätigung', 'Fertig'].map((label, index) => {
              const stepNumber = index + 1;
              const isActive = getStepNumber(currentStep) === stepNumber;
              const isCompleted = getStepNumber(currentStep) > stepNumber;
              
              return (
                <React.Fragment key={label}>
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm transition-all ${
                        isCompleted
                          ? 'bg-green-500 text-white'
                          : isActive
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 text-gray-500'
                      }`}
                    >
                      {isCompleted ? <Check className="w-5 h-5" /> : stepNumber}
                    </div>
                    <span className={`text-xs mt-2 ${isActive ? 'text-blue-600 font-medium' : 'text-gray-500'}`}>
                      {label}
                    </span>
                  </div>
                  {index < 4 && (
                    <div className={`flex-1 h-1 mx-2 ${isCompleted ? 'bg-green-500' : 'bg-gray-200'}`} />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="p-8">
          {currentStep === 'intro' && (
            <IntroStep onNext={() => setCurrentStep('choice')} onSkip={handleSkipSetup} />
          )}

          {currentStep === 'choice' && (
            <ChoiceStep
              onChoice={(hasAccount) => {
                setHasERecht24Account(hasAccount);
                setCurrentStep(hasAccount ? 'api-key' : 'company-info');
              }}
              onBack={() => setCurrentStep('intro')}
            />
          )}

          {currentStep === 'api-key' && (
            <ApiKeyStep
              apiKey={apiKey}
              onApiKeyChange={setApiKey}
              onNext={() => setCurrentStep('confirm')}
              onBack={() => setCurrentStep('choice')}
            />
          )}

          {currentStep === 'company-info' && (
            <CompanyInfoStep
              companyInfo={companyInfo}
              onCompanyInfoChange={setCompanyInfo}
              onNext={() => setCurrentStep('confirm')}
              onBack={() => setCurrentStep('choice')}
            />
          )}

          {currentStep === 'confirm' && (
            <ConfirmStep
              hasERecht24Account={hasERecht24Account}
              apiKey={apiKey}
              companyInfo={companyInfo}
              domain={domain}
              isLoading={isLoading}
              onConfirm={handleSetup}
              onBack={() => setCurrentStep(hasERecht24Account ? 'api-key' : 'company-info')}
            />
          )}

          {currentStep === 'success' && (
            <SuccessStep projectData={projectData} domain={domain} />
          )}
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// Step Components
// ============================================================================

const IntroStep: React.FC<{ onNext: () => void; onSkip: () => void }> = ({ onNext, onSkip }) => {
  return (
    <div className="text-center max-w-2xl mx-auto">
      <div className="w-20 h-20 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-6">
        <Shield className="w-10 h-10 text-blue-600" />
      </div>
      
      <h3 className="text-2xl font-bold text-gray-900 mb-4">
        Willkommen zur eRecht24-Integration
      </h3>
      
      <p className="text-gray-600 mb-6 text-lg">
        Mit eRecht24 erhalten Sie anwaltlich geprüfte, rechtssichere Texte für Ihre Website.
      </p>

      <div className="grid md:grid-cols-2 gap-4 mb-8 text-left">
        <div className="p-4 bg-green-50 rounded-lg border border-green-200">
          <h4 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5" />
            Mit eRecht24
          </h4>
          <ul className="space-y-2 text-sm text-green-800">
            <li>✓ Anwaltlich geprüfte Texte</li>
            <li>✓ Automatische Updates bei Gesetzesänderungen</li>
            <li>✓ Höchste Rechtssicherheit</li>
            <li>✓ Vollständig DSGVO-konform</li>
          </ul>
        </div>

        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <h4 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
            <Sparkles className="w-5 h-5" />
            Ohne eRecht24 (AI-Fallback)
          </h4>
          <ul className="space-y-2 text-sm text-blue-800">
            <li>✓ KI-generierte Basis-Texte</li>
            <li>✓ Schnelle Generierung</li>
            <li>✓ Kostenlos</li>
            <li>⚠️ Sollte rechtlich geprüft werden</li>
          </ul>
        </div>
      </div>

      <div className="flex gap-3 justify-center">
        <button
          onClick={onSkip}
          className="px-6 py-3 border-2 border-gray-300 hover:border-gray-400 text-gray-700 rounded-lg font-semibold transition-all"
        >
          Später einrichten
        </button>
        <button
          onClick={onNext}
          className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-semibold transition-all flex items-center gap-2"
        >
          Setup starten
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

const ChoiceStep: React.FC<{ 
  onChoice: (hasAccount: boolean) => void; 
  onBack: () => void 
}> = ({ onChoice, onBack }) => {
  return (
    <div className="max-w-3xl mx-auto">
      <h3 className="text-2xl font-bold text-gray-900 mb-6 text-center">
        Haben Sie bereits einen eRecht24-Account?
      </h3>

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <button
          onClick={() => onChoice(true)}
          className="p-6 border-2 border-gray-200 hover:border-blue-500 rounded-lg transition-all group"
        >
          <div className="w-16 h-16 rounded-full bg-green-100 group-hover:bg-green-200 flex items-center justify-center mx-auto mb-4 transition-colors">
            <CheckCircle2 className="w-8 h-8 text-green-600" />
          </div>
          <h4 className="font-semibold text-lg mb-2">Ja, ich habe eRecht24</h4>
          <p className="text-sm text-gray-600">
            Ich besitze bereits einen eRecht24-Account und möchte meine API-Daten eingeben.
          </p>
        </button>

        <button
          onClick={() => onChoice(false)}
          className="p-6 border-2 border-gray-200 hover:border-purple-500 rounded-lg transition-all group"
        >
          <div className="w-16 h-16 rounded-full bg-purple-100 group-hover:bg-purple-200 flex items-center justify-center mx-auto mb-4 transition-colors">
            <Sparkles className="w-8 h-8 text-purple-600" />
          </div>
          <h4 className="font-semibold text-lg mb-2">Nein, AI-Fallback nutzen</h4>
          <p className="text-sm text-gray-600">
            Ich möchte die kostenlose KI-basierte Generierung verwenden.
          </p>
        </button>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-800">
            <strong>Hinweis:</strong> Sie können eRecht24 auch später noch einrichten. 
            Die KI-generierten Texte dienen als solide Basis, sollten aber von einem Anwalt geprüft werden.
          </div>
        </div>
      </div>

      <div className="flex justify-between">
        <button
          onClick={onBack}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium flex items-center gap-2"
        >
          <ChevronLeft className="w-5 h-5" />
          Zurück
        </button>
        
        <a
          href="https://www.e-recht24.de"
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-2"
        >
          eRecht24 Website besuchen
          <ExternalLink className="w-4 h-4" />
        </a>
      </div>
    </div>
  );
};

const ApiKeyStep: React.FC<{
  apiKey: string;
  onApiKeyChange: (key: string) => void;
  onNext: () => void;
  onBack: () => void;
}> = ({ apiKey, onApiKeyChange, onNext, onBack }) => {
  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-4">
          <Key className="w-8 h-8 text-blue-600" />
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-2">
          eRecht24 API-Key eingeben
        </h3>
        <p className="text-gray-600">
          Geben Sie Ihren eRecht24 API-Key ein, um die Integration zu aktivieren.
        </p>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          API-Key
        </label>
        <input
          type="text"
          value={apiKey}
          onChange={(e) => onApiKeyChange(e.target.value)}
          placeholder="Ihr eRecht24 API-Key"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
        <h4 className="font-semibold text-yellow-900 mb-2">Wie finde ich meinen API-Key?</h4>
        <ol className="list-decimal list-inside space-y-2 text-sm text-yellow-800">
          <li>Loggen Sie sich in Ihren eRecht24-Account ein</li>
          <li>Gehen Sie zu Einstellungen → API-Zugang</li>
          <li>Kopieren Sie den API-Key</li>
          <li>Fügen Sie ihn hier ein</li>
        </ol>
      </div>

      <div className="flex justify-between">
        <button
          onClick={onBack}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium flex items-center gap-2"
        >
          <ChevronLeft className="w-5 h-5" />
          Zurück
        </button>
        <button
          onClick={onNext}
          disabled={!apiKey.trim()}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg font-semibold flex items-center gap-2 transition-all"
        >
          Weiter
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

const CompanyInfoStep: React.FC<{
  companyInfo: CompanyInfo;
  onCompanyInfoChange: (info: CompanyInfo) => void;
  onNext: () => void;
  onBack: () => void;
}> = ({ companyInfo, onCompanyInfoChange, onNext, onBack }) => {
  const isValid = companyInfo.company_name && companyInfo.email && companyInfo.address;

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <div className="w-16 h-16 rounded-full bg-purple-100 flex items-center justify-center mx-auto mb-4">
          <Building className="w-8 h-8 text-purple-600" />
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-2">
          Unternehmensdaten
        </h3>
        <p className="text-gray-600">
          Diese Daten werden für die Generierung rechtssicherer Texte verwendet.
        </p>
      </div>

      <div className="space-y-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Firmenname *
          </label>
          <input
            type="text"
            value={companyInfo.company_name}
            onChange={(e) => onCompanyInfoChange({ ...companyInfo, company_name: e.target.value })}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Mail className="w-4 h-4 inline mr-1" />
              E-Mail *
            </label>
            <input
              type="email"
              value={companyInfo.email}
              onChange={(e) => onCompanyInfoChange({ ...companyInfo, email: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <Phone className="w-4 h-4 inline mr-1" />
              Telefon
            </label>
            <input
              type="tel"
              value={companyInfo.phone}
              onChange={(e) => onCompanyInfoChange({ ...companyInfo, phone: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <MapPin className="w-4 h-4 inline mr-1" />
            Adresse *
          </label>
          <input
            type="text"
            value={companyInfo.address}
            onChange={(e) => onCompanyInfoChange({ ...companyInfo, address: e.target.value })}
            placeholder="Straße und Hausnummer"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              PLZ
            </label>
            <input
              type="text"
              value={companyInfo.postal_code}
              onChange={(e) => onCompanyInfoChange({ ...companyInfo, postal_code: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Stadt
            </label>
            <input
              type="text"
              value={companyInfo.city}
              onChange={(e) => onCompanyInfoChange({ ...companyInfo, city: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>
        </div>

        <details className="group">
          <summary className="cursor-pointer text-sm font-medium text-gray-700 mb-2">
            Optionale Angaben (für Impressum)
          </summary>
          <div className="mt-4 space-y-4 pl-4 border-l-2 border-gray-200">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                USt-ID
              </label>
              <input
                type="text"
                value={companyInfo.vat_id}
                onChange={(e) => onCompanyInfoChange({ ...companyInfo, vat_id: e.target.value })}
                placeholder="DE123456789"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Registergericht
              </label>
              <input
                type="text"
                value={companyInfo.registration_court}
                onChange={(e) => onCompanyInfoChange({ ...companyInfo, registration_court: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Registernummer (HRB/HRA)
              </label>
              <input
                type="text"
                value={companyInfo.registration_number}
                onChange={(e) => onCompanyInfoChange({ ...companyInfo, registration_number: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
          </div>
        </details>
      </div>

      <div className="flex justify-between">
        <button
          onClick={onBack}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 font-medium flex items-center gap-2"
        >
          <ChevronLeft className="w-5 h-5" />
          Zurück
        </button>
        <button
          onClick={onNext}
          disabled={!isValid}
          className="px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg font-semibold flex items-center gap-2 transition-all"
        >
          Weiter
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

const ConfirmStep: React.FC<{
  hasERecht24Account: boolean | null;
  apiKey: string;
  companyInfo: CompanyInfo;
  domain: string;
  isLoading: boolean;
  onConfirm: () => void;
  onBack: () => void;
}> = ({ hasERecht24Account, apiKey, companyInfo, domain, isLoading, onConfirm, onBack }) => {
  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
          <CheckCircle2 className="w-8 h-8 text-green-600" />
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-2">
          Setup bestätigen
        </h3>
        <p className="text-gray-600">
          Bitte überprüfen Sie Ihre Angaben vor der Aktivierung.
        </p>
      </div>

      <div className="bg-gray-50 rounded-lg p-6 mb-6 space-y-4">
        <div className="flex items-center gap-3">
          <Globe className="w-5 h-5 text-gray-600" />
          <div>
            <span className="text-sm text-gray-600">Domain:</span>
            <p className="font-semibold">{domain}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Shield className="w-5 h-5 text-gray-600" />
          <div>
            <span className="text-sm text-gray-600">Integration:</span>
            <p className="font-semibold">
              {hasERecht24Account ? 'eRecht24 API' : 'AI-Fallback (Complyo)'}
            </p>
          </div>
        </div>

        {hasERecht24Account ? (
          <div className="flex items-center gap-3">
            <Key className="w-5 h-5 text-gray-600" />
            <div>
              <span className="text-sm text-gray-600">API-Key:</span>
              <p className="font-mono text-sm">
                {apiKey.substring(0, 10)}...{apiKey.substring(apiKey.length - 4)}
              </p>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-3">
            <Building className="w-5 h-5 text-gray-600" />
            <div>
              <span className="text-sm text-gray-600">Firma:</span>
              <p className="font-semibold">{companyInfo.company_name}</p>
            </div>
          </div>
        )}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h4 className="font-semibold text-blue-900 mb-2">Was passiert jetzt?</h4>
        <ul className="space-y-2 text-sm text-blue-800">
          <li>✓ Projekt wird in Complyo angelegt</li>
          {hasERecht24Account && <li>✓ Verbindung zu eRecht24 wird hergestellt</li>}
          <li>✓ Rechtssichere Texte werden vorbereitet</li>
          <li>✓ Sie können Texte sofort abrufen</li>
        </ul>
      </div>

      <div className="flex justify-between">
        <button
          onClick={onBack}
          disabled={isLoading}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50 font-medium flex items-center gap-2"
        >
          <ChevronLeft className="w-5 h-5" />
          Zurück
        </button>
        <button
          onClick={onConfirm}
          disabled={isLoading}
          className="px-8 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-gray-300 disabled:to-gray-300 disabled:cursor-not-allowed text-white rounded-lg font-semibold flex items-center gap-2 transition-all"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Wird eingerichtet...
            </>
          ) : (
            <>
              <Check className="w-5 h-5" />
              Jetzt aktivieren
            </>
          )}
        </button>
      </div>
    </div>
  );
};

const SuccessStep: React.FC<{ projectData: any; domain: string }> = ({ projectData, domain }) => {
  return (
    <div className="text-center max-w-2xl mx-auto">
      <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
        <CheckCircle2 className="w-10 h-10 text-green-600" />
      </div>
      
      <h3 className="text-2xl font-bold text-gray-900 mb-4">
        🎉 Setup erfolgreich abgeschlossen!
      </h3>
      
      <p className="text-gray-600 mb-8 text-lg">
        Die eRecht24-Integration für <strong>{domain}</strong> ist jetzt aktiv.
      </p>

      <div className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6 mb-8">
        <h4 className="font-semibold text-green-900 mb-4">Was Sie jetzt tun können:</h4>
        <div className="grid md:grid-cols-2 gap-4 text-left">
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-green-200 flex items-center justify-center flex-shrink-0">
              <span className="text-green-700 font-bold">1</span>
            </div>
            <div>
              <p className="font-medium text-green-900">Impressum generieren</p>
              <p className="text-sm text-green-700">Erstellen Sie Ihr rechtssicheres Impressum</p>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-green-200 flex items-center justify-center flex-shrink-0">
              <span className="text-green-700 font-bold">2</span>
            </div>
            <div>
              <p className="font-medium text-green-900">Datenschutz abrufen</p>
              <p className="text-sm text-green-700">Holen Sie sich Ihre DSGVO-Erklärung</p>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-green-200 flex items-center justify-center flex-shrink-0">
              <span className="text-green-700 font-bold">3</span>
            </div>
            <div>
              <p className="font-medium text-green-900">AGB generieren</p>
              <p className="text-sm text-green-700">Erstellen Sie Ihre Geschäftsbedingungen</p>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-green-200 flex items-center justify-center flex-shrink-0">
              <span className="text-green-700 font-bold">4</span>
            </div>
            <div>
              <p className="font-medium text-green-900">Auto-Updates</p>
              <p className="text-sm text-green-700">Texte bleiben automatisch aktuell</p>
            </div>
          </div>
        </div>
      </div>

      <button
        onClick={() => window.location.reload()}
        className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-semibold transition-all"
      >
        Zum Dashboard
      </button>
    </div>
  );
};

// ============================================================================
// Helper Functions
// ============================================================================

function getStepNumber(step: SetupStep): number {
  const stepMap: Record<SetupStep, number> = {
    'intro': 1,
    'choice': 2,
    'api-key': 3,
    'company-info': 3,
    'confirm': 4,
    'success': 5
  };
  return stepMap[step] || 1;
}

export default ERecht24Setup;

