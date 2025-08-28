'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

// Language context
interface LanguageContextType {
  language: string;
  setLanguage: (lang: string) => void;
  t: (key: string, params?: Record<string, any>) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

// Translations
const translations = {
  de: {
    'form.name_placeholder': 'Max Mustermann',
    'form.email_placeholder': 'max@beispiel.de',
    'form.company_placeholder': 'Mustermann GmbH',
    'form.website_placeholder': 'https://ihre-website.de',
    'form.analyze_button': 'Kostenlose Analyse starten',
    'form.name_label': 'Vollständiger Name',
    'form.email_label': 'E-Mail-Adresse',
    'form.company_label': 'Unternehmen (optional)',
    'form.website_label': 'Website-URL',
    'messages.analysis_started': 'Analyse läuft...',
    'messages.email_sent': 'Bestätigungs-E-Mail wurde versendet',
    'messages.error_occurred': 'Ein Fehler ist aufgetreten',
    'messages.invalid_url': 'Bitte geben Sie eine gültige URL ein',
    'messages.required_fields': 'Bitte füllen Sie alle Pflichtfelder aus',
    'nav.home': 'Startseite',
    'nav.features': 'Funktionen',
    'nav.pricing': 'Preise',
    'nav.contact': 'Kontakt',
    'nav.privacy': 'Datenschutz',
    'nav.gdpr': 'DSGVO',
    'nav.language': 'Sprache'
  },
  en: {
    'form.name_placeholder': 'John Doe',
    'form.email_placeholder': 'john@example.com',
    'form.company_placeholder': 'Acme Corp',
    'form.website_placeholder': 'https://your-website.com',
    'form.analyze_button': 'Start Free Analysis',
    'form.name_label': 'Full Name',
    'form.email_label': 'Email Address',
    'form.company_label': 'Company (optional)',
    'form.website_label': 'Website URL',
    'messages.analysis_started': 'Analysis running...',
    'messages.email_sent': 'Confirmation email sent',
    'messages.error_occurred': 'An error occurred',
    'messages.invalid_url': 'Please enter a valid URL',
    'messages.required_fields': 'Please fill in all required fields',
    'nav.home': 'Home',
    'nav.features': 'Features',
    'nav.pricing': 'Pricing',
    'nav.contact': 'Contact',
    'nav.privacy': 'Privacy',
    'nav.gdpr': 'GDPR',
    'nav.language': 'Language'
  }
};

// Language provider
export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState('de');

  useEffect(() => {
    // Detect language from URL or browser
    const urlLang = window.location.hostname.includes('.de') ? 'de' : 'en';
    const storedLang = localStorage.getItem('complyo-language');
    const browserLang = navigator.language.startsWith('de') ? 'de' : 'en';
    
    const selectedLang = storedLang || urlLang || browserLang;
    setLanguage(selectedLang);
  }, []);

  const handleSetLanguage = (lang: string) => {
    setLanguage(lang);
    localStorage.setItem('complyo-language', lang);
  };

  const t = (key: string, params?: Record<string, any>) => {
    const translation = translations[language as keyof typeof translations]?.[key as keyof typeof translations.de] || key;
    
    if (params) {
      return Object.keys(params).reduce((str, param) => {
        return str.replace(`{${param}}`, params[param]);
      }, translation);
    }
    
    return translation;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage: handleSetLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

// Hook to use language context
export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
}

// Language switcher component
export function LanguageSwitcher() {
  const { language, setLanguage } = useLanguage();

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => setLanguage('de')}
        className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
          language === 'de'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
      >
        🇩🇪 DE
      </button>
      <button
        onClick={() => setLanguage('en')}
        className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
          language === 'en'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
      >
        🇬🇧 EN
      </button>
    </div>
  );
}