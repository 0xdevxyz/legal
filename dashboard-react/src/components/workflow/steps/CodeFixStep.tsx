'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, Copy, Code } from 'lucide-react';

interface CodeFixStepProps {
  fixData: {
    title: string;
    description: string;
    code_snippet: string;
    integration_instructions: string;
    file_path?: string;
    target_element_selector?: string;
  };
  onComplete: () => void;
}

export const CodeFixStep: React.FC<CodeFixStepProps> = ({ fixData, onComplete }) => {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = () => {
    navigator.clipboard.writeText(fixData.code_snippet);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  return (
    <Card className="border-blue-200 shadow-md">
      <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
        <CardTitle className="flex items-center gap-3 text-xl">
          <Code className="w-6 h-6 text-blue-600" />
          {fixData.title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 mt-4">
        <p className="text-gray-700">{fixData.description}</p>
        
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
          {fixData.file_path && (
            <p className="text-sm text-blue-700 mt-2">
              <strong>Datei:</strong> <code className="bg-white px-2 py-1 rounded">{fixData.file_path}</code>
            </p>
          )}
          {fixData.target_element_selector && (
            <p className="text-sm text-blue-700 mt-1">
              <strong>Ziel:</strong> <code className="bg-white px-2 py-1 rounded">{fixData.target_element_selector}</code>
            </p>
          )}
        </div>
        
        <div className="flex justify-end mt-6">
          <Button 
            onClick={onComplete}
            className="bg-gradient-to-r from-green-500 to-teal-600 hover:from-green-600 hover:to-teal-700 text-white"
          >
            <CheckCircle className="w-4 h-4 mr-2" />
            Code eingefügt, weiter
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

