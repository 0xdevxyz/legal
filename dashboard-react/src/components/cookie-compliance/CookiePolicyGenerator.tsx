/**
 * Cookie Policy Generator
 * Automatische Generierung einer Cookie-Richtlinie aus den Services
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { FileText, Download, Copy, CheckCircle, RefreshCw, ExternalLink, Eye } from 'lucide-react';

interface CookiePolicyGeneratorProps {
  siteId: string;
  config: any;
}

export default function CookiePolicyGenerator({ siteId, config }: CookiePolicyGeneratorProps) {
  const [policy, setPolicy] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [language, setLanguage] = useState('de');

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

  const generatePolicy = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/cookie-compliance/policy/${siteId}?lang=${language}`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setPolicy(data.policy);
        }
      }
    } catch (error) {
      console.error('Error generating policy:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (siteId) {
      generatePolicy();
    }
  }, [siteId, language]);

  const copyToClipboard = () => {
    if (!policy) return;
    
    let text = `# ${policy.title}\n\n`;
    text += `Letzte Aktualisierung: ${new Date(policy.last_updated).toLocaleDateString('de-DE')}\n\n`;
    
    policy.sections?.forEach((section: any) => {
      text += `## ${section.title}\n\n`;
      if (section.content) {
        text += `${section.content}\n\n`;
      }
      if (section.services) {
        section.services.forEach((service: any) => {
          text += `### ${service.name}\n`;
          text += `- Anbieter: ${service.provider || 'Nicht angegeben'}\n`;
          text += `- Beschreibung: ${service.description || 'Keine Beschreibung'}\n`;
          if (service.cookies?.length) {
            text += `- Cookies: ${service.cookies.join(', ')}\n`;
          }
          text += '\n';
        });
      }
    });
    
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  const downloadAsHtml = () => {
    if (!policy) return;
    
    let html = `<!DOCTYPE html>
<html lang="${language}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${policy.title}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; line-height: 1.6; }
    h1 { color: #1f2937; border-bottom: 2px solid #f97316; padding-bottom: 0.5rem; }
    h2 { color: #374151; margin-top: 2rem; }
    h3 { color: #4b5563; }
    .meta { color: #6b7280; font-size: 0.875rem; margin-bottom: 2rem; }
    .service { background: #f9fafb; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
    .cookies { background: #fef3c7; padding: 0.5rem 1rem; border-radius: 0.25rem; font-family: monospace; font-size: 0.875rem; }
  </style>
</head>
<body>
  <h1>${policy.title}</h1>
  <p class="meta">Letzte Aktualisierung: ${new Date(policy.last_updated).toLocaleDateString('de-DE')}</p>
`;
    
    policy.sections?.forEach((section: any) => {
      html += `  <h2>${section.title}</h2>\n`;
      if (section.content) {
        html += `  <p>${section.content}</p>\n`;
      }
      if (section.services) {
        section.services.forEach((service: any) => {
          html += `  <div class="service">\n`;
          html += `    <h3>${service.name}</h3>\n`;
          html += `    <p><strong>Anbieter:</strong> ${service.provider || 'Nicht angegeben'}</p>\n`;
          html += `    <p>${service.description || 'Keine Beschreibung'}</p>\n`;
          if (service.cookies?.length) {
            html += `    <p class="cookies">Cookies: ${service.cookies.join(', ')}</p>\n`;
          }
          html += `  </div>\n`;
        });
      }
    });
    
    html += `</body></html>`;
    
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cookie-policy-${siteId}.html`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-orange-400" />
            Cookie-Richtlinie Generator
          </CardTitle>
          <CardDescription>
            Generieren Sie automatisch eine Cookie-Richtlinie aus Ihren konfigurierten Services
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Language & Actions */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Sprache:</span>
              <select 
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm text-white"
              >
                <option value="de">Deutsch</option>
                <option value="en">English</option>
              </select>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={generatePolicy}
                disabled={loading}
                className="gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Neu generieren
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={copyToClipboard}
                disabled={!policy}
                className="gap-2"
              >
                {copied ? <CheckCircle className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                {copied ? 'Kopiert!' : 'Kopieren'}
              </Button>
              <Button
                size="sm"
                onClick={downloadAsHtml}
                disabled={!policy}
                className="gap-2 bg-orange-500 hover:bg-orange-600"
              >
                <Download className="w-4 h-4" />
                HTML
              </Button>
            </div>
          </div>

          {/* Preview Tabs */}
          {policy && (
            <Tabs defaultValue="preview" className="mt-6">
              <TabsList className="bg-gray-900/50">
                <TabsTrigger value="preview" className="gap-2 data-[state=active]:bg-orange-500">
                  <Eye className="w-4 h-4" />
                  Vorschau
                </TabsTrigger>
                <TabsTrigger value="json" className="data-[state=active]:bg-orange-500">
                  JSON
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="preview" className="mt-4">
                <div className="bg-white text-gray-800 rounded-lg p-6 max-h-[500px] overflow-y-auto">
                  <h1 className="text-2xl font-bold text-gray-900 border-b-2 border-orange-500 pb-2 mb-4">
                    {policy.title}
                  </h1>
                  <p className="text-sm text-gray-500 mb-6">
                    Letzte Aktualisierung: {new Date(policy.last_updated).toLocaleDateString('de-DE')}
                  </p>
                  
                  {policy.sections?.map((section: any, idx: number) => (
                    <div key={idx} className="mb-6">
                      <h2 className="text-xl font-semibold text-gray-800 mb-2">{section.title}</h2>
                      {section.content && (
                        <p className="text-gray-600 mb-3">{section.content}</p>
                      )}
                      {section.services && (
                        <div className="space-y-3">
                          {section.services.map((service: any, sIdx: number) => (
                            <div key={sIdx} className="bg-gray-50 p-4 rounded-lg">
                              <h3 className="font-medium text-gray-800">{service.name}</h3>
                              <p className="text-sm text-gray-500">Anbieter: {service.provider || 'Nicht angegeben'}</p>
                              <p className="text-sm text-gray-600 mt-1">{service.description || 'Keine Beschreibung'}</p>
                              {service.cookies?.length > 0 && (
                                <div className="mt-2 p-2 bg-yellow-50 rounded text-xs font-mono">
                                  Cookies: {service.cookies.join(', ')}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </TabsContent>
              
              <TabsContent value="json" className="mt-4">
                <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-auto max-h-[500px] text-xs">
                  {JSON.stringify(policy, null, 2)}
                </pre>
              </TabsContent>
            </Tabs>
          )}

          {!policy && !loading && (
            <div className="text-center py-8 text-gray-400">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Keine Services konfiguriert.</p>
              <p className="text-sm">Fügen Sie Services hinzu, um eine Cookie-Richtlinie zu generieren.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
