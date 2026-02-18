'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, Copy, FileText, Download } from 'lucide-react';
import { sanitizeHtml } from '@/lib/sanitize';

interface TextFixStepProps {
  fixData: {
    title: string;
    description: string;
    text_content: string;
    integration_instructions: string;
    target_url_path?: string;
  };
  onComplete: () => void;
}

export const TextFixStep: React.FC<TextFixStepProps> = ({ fixData, onComplete }) => {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = () => {
    // Create a temporary element to extract text from HTML
    const temp = document.createElement('div');
    temp.innerHTML = fixData.text_content;
    const textOnly = temp.textContent || temp.innerText || '';
    
    navigator.clipboard.writeText(fixData.text_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  const handleDownload = () => {
    const blob = new Blob([fixData.text_content], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${fixData.title.toLowerCase().replace(/\s+/g, '-')}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  return (
    <Card className="border-purple-200 shadow-md">
      <CardHeader className="bg-gradient-to-r from-purple-50 to-pink-50">
        <CardTitle className="flex items-center gap-3 text-xl">
          <FileText className="w-6 h-6 text-purple-600" />
          {fixData.title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 mt-4">
        <p className="text-gray-700">{fixData.description}</p>
        
        <div className="bg-white border border-gray-200 rounded-lg p-6 max-h-80 overflow-y-auto">
          <div 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: sanitizeHtml(fixData.text_content || '') }}
          />
        </div>
        
        <div className="flex gap-3">
          <Button
            onClick={handleCopy}
            variant="outline"
            className="flex-1"
          >
            {copied ? (
              <>
                <CheckCircle className="w-4 h-4 mr-2 text-green-600" />
                Kopiert
              </>
            ) : (
              <>
                <Copy className="w-4 h-4 mr-2" />
                HTML kopieren
              </>
            )}
          </Button>
          <Button
            onClick={handleDownload}
            variant="outline"
            className="flex-1"
          >
            <Download className="w-4 h-4 mr-2" />
            Als Datei herunterladen
          </Button>
        </div>
        
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <h4 className="font-semibold text-purple-900 mb-2">📋 Anleitung zur Integration:</h4>
          <p className="text-sm text-purple-800">{fixData.integration_instructions}</p>
          {fixData.target_url_path && (
            <p className="text-sm text-purple-700 mt-2">
              <strong>Empfohlene URL:</strong> <code className="bg-white px-2 py-1 rounded">{fixData.target_url_path}</code>
            </p>
          )}
        </div>
        
        <div className="flex justify-end mt-6">
          <Button 
            onClick={onComplete}
            className="bg-gradient-to-r from-green-500 to-teal-600 hover:from-green-600 hover:to-teal-700 text-white"
          >
            <CheckCircle className="w-4 h-4 mr-2" />
            Text integriert, weiter
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

