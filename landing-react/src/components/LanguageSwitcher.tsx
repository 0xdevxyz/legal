'use client';

import React, { useState, useEffect } from 'react';

interface Language {
  code: string;
  name: string;
  native_name: string;
  flag: string;
}

export default function LanguageSwitcher() {
  const [currentLanguage, setCurrentLanguage] = useState('de');
  const [availableLanguages, setAvailableLanguages] = useState<Record<string, Language>>({});
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const loadLanguages = async () => {
      try {
        const response = await fetch('/api/i18n/languages');
        const data = await response.json();
        setAvailableLanguages(data.languages);
        setCurrentLanguage(data.default_language);
      } catch (error) {
        console.error('Error loading languages:', error);
        setAvailableLanguages({
          'de': { code: 'de', name: 'Deutsch', native_name: 'Deutsch', flag: '🇩🇪' },
          'en': { code: 'en', name: 'English', native_name: 'English', flag: '🇬🇧' }
        });
      }
    };
    loadLanguages();
  }, []);

  const handleLanguageChange = (languageCode: string) => {
    setCurrentLanguage(languageCode);
    setIsOpen(false);
    localStorage.setItem('complyo_language', languageCode);
    document.documentElement.lang = languageCode;
    window.location.reload();
  };

  const currentLang = availableLanguages[currentLanguage];
  
  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
      >
        <span className="text-lg">{currentLang?.flag}</span>
        <span className="text-sm font-medium">{currentLang?.native_name}</span>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-20">
          <div className="py-1">
            {Object.values(availableLanguages).map((language) => (
              <button
                key={language.code}
                onClick={() => handleLanguageChange(language.code)}
                className={`w-full flex items-center space-x-3 px-4 py-2 text-left hover:bg-gray-50 ${
                  currentLanguage === language.code ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                }`}
              >
                <span className="text-lg">{language.flag}</span>
                <div>
                  <div className="text-sm font-medium">{language.native_name}</div>
                  <div className="text-xs text-gray-500">{language.name}</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}