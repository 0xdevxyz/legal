'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, Copy, Sparkles } from 'lucide-react';

interface WidgetFixStepProps {
  fixData: {
    title: string;
    description: string;
    code_snippet: string;
    integration_instructions: string;
    widget_script_url?: string;
  };
  onComplete: () => void;
}

export const WidgetFixStep: React.FC<WidgetFixStepProps> = ({ fixData, onComplete }) => {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = () => {
    navigator.clipboard.writeText(fixData.code_snippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  return (
    <Card className="border-green-200 shadow-md">
      <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50">
        <CardTitle className="flex items-center gap-3 text-xl">
          <Sparkles className="w-6 h-6 text-green-600" />
          {fixData.title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 mt-4">
        <p className="text-gray-700">{fixData.description}</p>
        
        <div className="bg-green-50 border-2 border-green-300 rounded-lg p-4">
          <h4 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
            <Sparkles className="w-5 h-5" />
            Complyo Widget - Automatische Installation
          </h4>
          <p className="text-sm text-green-800 mb-3">
            Dieses Widget wird automatisch auf Ihrer Website geladen und konfiguriert.
            Keine zusätzliche Programmierung erforderlich!
          </p>
        </div>
        
        <div className="bg-gray-900 rounded-lg p-4 relative">
          <Button
            onClick={handleCopy}
            variant="outline"
            size="sm"
            className="absolute top-2 right-2 bg-white hover:bg-gray-100"
          >
            {copied ? (
              <>
                <CheckCircle className="w-4 h-4 mr-1 text-green-600" />
                Kopiert
              </>
            ) : (
              <>
                <Copy className="w-4 h-4 mr-1" />
                Kopieren
              </>
            )}
          </Button>
          <pre className="text-sm text-white overflow-x-auto mt-8">
            <code>{fixData.code_snippet}</code>
          </pre>
        </div>
        
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-blue-900 mb-2">📋 Anleitung zur Integration:</h4>
          <p className="text-sm text-blue-800">{fixData.integration_instructions}</p>
          {fixData.widget_script_url && (
            <p className="text-sm text-blue-700 mt-2">
              <strong>Widget-URL:</strong> <code className="bg-white px-2 py-1 rounded text-xs">{fixData.widget_script_url}</code>
            </p>
          )}
        </div>
        
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <p className="text-xs text-yellow-800">
            💡 <strong>Tipp:</strong> Das Widget muss nur einmal im <code>&lt;head&gt;</code>-Bereich Ihrer Website eingefügt werden.
            Es funktioniert dann automatisch auf allen Seiten.
          </p>
        </div>
        
        <div className="flex justify-end mt-6">
          <Button 
            onClick={onComplete}
            className="bg-gradient-to-r from-green-500 to-teal-600 hover:from-green-600 hover:to-teal-700 text-white"
          >
            <CheckCircle className="w-4 h-4 mr-2" />
            Widget integriert, weiter
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

