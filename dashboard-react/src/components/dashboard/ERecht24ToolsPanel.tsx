'use client';

import React, { useState } from 'react';
import { FileText, CheckCircle, Download, ExternalLink, Shield, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { validateImpressum } from '@/lib/api';

export const ERecht24ToolsPanel: React.FC = () => {
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);

  const handleGenerateText = (type: 'impressum' | 'datenschutz' | 'agb') => {
    // TODO: Open LegalTextGenerator Modal
    alert(`📄 ${type.charAt(0).toUpperCase() + type.slice(1)}-Generator wird geöffnet...\n\n(Feature wird im nächsten Schritt implementiert)`);
  };

  const handleValidateImpressum = async () => {
    // TODO: Get impressum text from current website
    setIsValidating(true);
    try {
      // Demo: Get impressum from user
      const text = prompt('Fügen Sie Ihren Impressum-Text ein:');
      if (text) {
        const result = await validateImpressum(text);
        setValidationResult(result);
      }
    } catch (error) {
      console.error('Validation error:', error);
      alert('Fehler bei der Validierung. Bitte versuchen Sie es erneut.');
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <Card className="h-fit sticky top-4">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Shield className="w-5 h-5 text-purple-400" />
          eRecht24 Tools
        </CardTitle>
        <p className="text-xs text-gray-400 mt-1">
          Rechtssichere Texte & Validierung
        </p>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Rechtstext-Generator */}
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Rechtstexte generieren
          </h4>
          
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start text-left"
            onClick={() => handleGenerateText('impressum')}
          >
            <FileText className="w-4 h-4 mr-2 text-blue-400" />
            Impressum erstellen
          </Button>

          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start text-left"
            onClick={() => handleGenerateText('datenschutz')}
          >
            <Shield className="w-4 h-4 mr-2 text-green-400" />
            Datenschutzerklärung
          </Button>

          <Button
            variant="outline"
            size="sm"
            className="w-full justify-start text-left"
            onClick={() => handleGenerateText('agb')}
          >
            <FileText className="w-4 h-4 mr-2 text-purple-400" />
            AGB erstellen
          </Button>
        </div>

        {/* Divider */}
        <div className="border-t border-gray-700 my-4" />

        {/* Impressum-Validator */}
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
            <CheckCircle className="w-4 h-4" />
            Impressum prüfen
          </h4>

          <Button
            variant="secondary"
            size="sm"
            className="w-full"
            onClick={handleValidateImpressum}
            disabled={isValidating}
          >
            {isValidating ? (
              <>
                <div className="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Prüfe...
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4 mr-2" />
                Impressum validieren
              </>
            )}
          </Button>

          {/* Validation Result */}
          {validationResult && (
            <div className={`p-3 rounded-lg border ${
              validationResult.is_valid 
                ? 'bg-green-900/20 border-green-500/30' 
                : 'bg-yellow-900/20 border-yellow-500/30'
            }`}>
              <div className="flex items-center gap-2 mb-2">
                {validationResult.is_valid ? (
                  <CheckCircle className="w-4 h-4 text-green-400" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-yellow-400" />
                )}
                <span className="text-sm font-semibold">
                  Score: {validationResult.score}/100
                </span>
              </div>
              
              {validationResult.missing_fields && validationResult.missing_fields.length > 0 && (
                <div className="text-xs text-gray-300">
                  <p className="font-semibold mb-1">Fehlende Angaben:</p>
                  <ul className="list-disc list-inside space-y-1">
                    {validationResult.missing_fields.slice(0, 3).map((field: string, idx: number) => (
                      <li key={idx}>{field}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="border-t border-gray-700 my-4" />

        {/* Quick Actions */}
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-gray-300">Quick Links</h4>
          
          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start text-left"
            onClick={() => window.open('https://www.e-recht24.de', '_blank')}
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            eRecht24 öffnen
          </Button>

          <Button
            variant="ghost"
            size="sm"
            className="w-full justify-start text-left"
            onClick={() => {
              alert('📥 PDF-Report wird generiert...\n\n(Feature wird im nächsten Schritt implementiert)');
            }}
          >
            <Download className="w-4 h-4 mr-2" />
            PDF-Report
          </Button>
        </div>

        {/* Info Box */}
        <div className="mt-4 p-3 bg-purple-900/20 rounded-lg border border-purple-500/30">
          <p className="text-xs text-purple-200">
            💡 <strong>Hinweis:</strong> Nutzen Sie eRecht24-Rechtstexte für vollständigen Abmahnschutz bei 100% Compliance.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

