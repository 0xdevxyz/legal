/**
 * Integration Guide Component
 * Shows code snippets and installation instructions
 */

import React, { useState } from 'react';
import {
  Copy,
  Check,
  Code,
  Globe,
  Mail,
  Terminal,
  FileCode,
  Zap,
  CheckCircle2,
  ChevronRight,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface IntegrationGuideProps {
  siteId: string;
  config: any;
}

const IntegrationGuide: React.FC<IntegrationGuideProps> = ({ siteId, config }) => {
  const [copied, setCopied] = useState(false);
  
  const API_BASE = 'https://api.complyo.tech';
  
  const scriptCode = `<!-- Complyo Cookie Compliance Widget -->
<script 
  src="${API_BASE}/api/widgets/cookie-compliance.js" 
  data-site-id="${siteId}"
  data-complyo-site-id="${siteId}"
  async
></script>`;

  const manualCode = `<script>
  // Manually initialize Complyo Cookie Banner
  window.complyoConfig = {
    siteId: '${siteId}',
    layout: '${config?.layout || 'banner_bottom'}',
    primaryColor: '${config?.primary_color || '#f97316'}',
    // ... weitere Optionen
  };
</script>
<script src="${API_BASE}/api/widgets/cookie-compliance.js"></script>`;

  const nextJsCode = `// Next.js _document.tsx
import Script from 'next/script'

export default function Document() {
  return (
    <Html>
      <Head>
        <Script 
          src="${API_BASE}/api/widgets/cookie-compliance.js"
          data-site-id="${siteId}"
          strategy="beforeInteractive"
        />
      </Head>
      <body>...</body>
    </Html>
  )
}`;
  
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-2">Integration</h3>
        <p className="text-sm text-gray-400">
          Fügen Sie das Cookie-Banner zu Ihrer Website hinzu.
        </p>
      </div>
      
      {/* Quick Start */}
      <Card className="border-green-500/30 bg-gradient-to-br from-green-500/10 to-green-600/5 backdrop-blur-sm">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-white">
              <Zap className="w-5 h-5 text-green-400" />
              Quick Start
            </CardTitle>
            <Badge className="bg-green-500 text-white">
              Empfohlen
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-gray-300">
            Fügen Sie diesen Code-Snippet in den <code className="px-2 py-1 bg-gray-800 rounded text-orange-400">&lt;head&gt;</code> Bereich Ihrer Website ein:
          </p>
          
          <div className="relative">
            <div className="bg-gray-950 border border-gray-800 rounded-lg p-4 font-mono text-sm overflow-x-auto">
              <pre className="text-green-400">{scriptCode}</pre>
            </div>
            
            <Button
              size="sm"
              variant="secondary"
              onClick={() => copyToClipboard(scriptCode)}
              className="absolute top-2 right-2 bg-gray-800 hover:bg-gray-700 text-white"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 mr-1" />
                  Kopiert!
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4 mr-1" />
                  Kopieren
                </>
              )}
            </Button>
          </div>
          
          <div className="flex items-start gap-2 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <Terminal className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-gray-300">
              Das <code className="px-1.5 py-0.5 bg-gray-800 rounded text-blue-400">async</code> Attribut sorgt dafür, dass das Banner Ihre Website nicht verlangsamt.
            </p>
          </div>
        </CardContent>
      </Card>
      
      {/* Platform-specific Instructions */}
      <Card className="border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Globe className="w-5 h-5 text-orange-400" />
            Platform-spezifische Anleitungen
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="wordpress" className="w-full">
            <TabsList className="grid w-full grid-cols-4 bg-gray-900/50">
              <TabsTrigger value="wordpress" className="data-[state=active]:bg-orange-500">
                WordPress
              </TabsTrigger>
              <TabsTrigger value="html" className="data-[state=active]:bg-orange-500">
                HTML
              </TabsTrigger>
              <TabsTrigger value="react" className="data-[state=active]:bg-orange-500">
                React/Next.js
              </TabsTrigger>
              <TabsTrigger value="shopify" className="data-[state=active]:bg-orange-500">
                Shopify
              </TabsTrigger>
            </TabsList>
            
            {/* WordPress */}
            <TabsContent value="wordpress" className="space-y-4 mt-6">
              <div className="flex items-center gap-2 mb-4">
                <FileCode className="w-5 h-5 text-orange-400" />
                <h4 className="font-semibold text-white">WordPress Installation</h4>
              </div>
              <ol className="space-y-3">
                {[
                  'Gehen Sie zu Design → Theme-Editor',
                  'Öffnen Sie die header.php Datei',
                  'Fügen Sie den Code vor dem schließenden </head> Tag ein',
                  'Speichern Sie die Änderungen'
                ].map((step, idx) => (
                  <li key={idx} className="flex items-start gap-3 text-sm text-gray-300">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-orange-500/20 text-orange-400 font-semibold flex-shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
              
              <div className="flex items-start gap-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg mt-4">
                <CheckCircle2 className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-gray-300">
                  <strong className="text-yellow-300">Alternative:</strong> Nutzen Sie ein Plugin wie "Header and Footer Scripts" um Code ohne Theme-Bearbeitung einzufügen.
                </p>
              </div>
            </TabsContent>
            
            {/* HTML */}
            <TabsContent value="html" className="space-y-4 mt-6">
              <div className="flex items-center gap-2 mb-4">
                <Code className="w-5 h-5 text-orange-400" />
                <h4 className="font-semibold text-white">Statische HTML-Website</h4>
              </div>
              <ol className="space-y-3">
                {[
                  'Öffnen Sie Ihre HTML-Datei(en) in einem Editor',
                  'Fügen Sie den Code im <head> Bereich ein',
                  'Wiederholen Sie dies für alle Seiten oder nutzen Sie ein Template',
                  'Laden Sie die Dateien auf Ihren Server hoch'
                ].map((step, idx) => (
                  <li key={idx} className="flex items-start gap-3 text-sm text-gray-300">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-orange-500/20 text-orange-400 font-semibold flex-shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </TabsContent>
            
            {/* React/Next.js */}
            <TabsContent value="react" className="space-y-4 mt-6">
              <div className="flex items-center gap-2 mb-4">
                <Terminal className="w-5 h-5 text-orange-400" />
                <h4 className="font-semibold text-white">React / Next.js Integration</h4>
              </div>
              <ol className="space-y-3">
                {[
                  'Für Next.js: Fügen Sie den Code in _document.tsx oder _app.tsx ein',
                  'Für React: Fügen Sie den Code in public/index.html ein',
                  'Alternativ: Nutzen Sie react-helmet oder next/head'
                ].map((step, idx) => (
                  <li key={idx} className="flex items-start gap-3 text-sm text-gray-300">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-orange-500/20 text-orange-400 font-semibold flex-shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
              
              <div className="relative mt-4">
                <div className="bg-gray-950 border border-gray-800 rounded-lg p-4 font-mono text-xs overflow-x-auto">
                  <pre className="text-green-400">{nextJsCode}</pre>
                </div>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => copyToClipboard(nextJsCode)}
                  className="absolute top-2 right-2 bg-gray-800 hover:bg-gray-700 text-white text-xs"
                >
                  {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                </Button>
              </div>
            </TabsContent>
            
            {/* Shopify */}
            <TabsContent value="shopify" className="space-y-4 mt-6">
              <div className="flex items-center gap-2 mb-4">
                <Globe className="w-5 h-5 text-orange-400" />
                <h4 className="font-semibold text-white">Shopify Installation</h4>
              </div>
              <ol className="space-y-3">
                {[
                  'Gehen Sie zu Online Store → Themes',
                  'Klicken Sie auf Actions → Edit code',
                  'Öffnen Sie theme.liquid',
                  'Fügen Sie den Code vor dem </head> Tag ein',
                  'Speichern Sie die Datei'
                ].map((step, idx) => (
                  <li key={idx} className="flex items-start gap-3 text-sm text-gray-300">
                    <span className="flex items-center justify-center w-6 h-6 rounded-full bg-orange-500/20 text-orange-400 font-semibold flex-shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
      
      {/* Testing */}
      <Card className="border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <CheckCircle2 className="w-5 h-5 text-orange-400" />
            Testing
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-gray-300">
            So überprüfen Sie, ob das Cookie-Banner funktioniert:
          </p>
          
          <ol className="space-y-3">
            {[
              'Öffnen Sie Ihre Website in einem Inkognito/Privat-Fenster',
              'Das Cookie-Banner sollte automatisch erscheinen',
              'Testen Sie alle Buttons (Akzeptieren, Ablehnen, Einstellungen)',
              'Prüfen Sie in den Browser DevTools (Console) auf Fehler',
              'Öffnen Sie die Website erneut - das Banner sollte nicht mehr erscheinen'
            ].map((step, idx) => (
              <li key={idx} className="flex items-start gap-3 text-sm text-gray-300">
                <ChevronRight className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
                <span>{step}</span>
              </li>
            ))}
          </ol>
          
          <div className="flex items-start gap-2 p-3 bg-green-500/10 border border-green-500/30 rounded-lg mt-4">
            <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-gray-300">
              <strong className="text-green-300">Tipp:</strong> Löschen Sie Cookies & LocalStorage um das Banner erneut zu testen.
            </p>
          </div>
        </CardContent>
      </Card>
      
      {/* Support */}
      <Card className="border-blue-500/30 bg-gradient-to-r from-blue-500/10 to-blue-600/5">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Mail className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h4 className="font-semibold text-white mb-1">Brauchen Sie Hilfe?</h4>
              <p className="text-sm text-gray-300 mb-3">
                Unser Support-Team hilft Ihnen gerne bei der Integration.
              </p>
              <Button
                variant="outline"
                size="sm"
                className="border-blue-500 text-blue-400 hover:bg-blue-500/10"
                onClick={() => window.open('mailto:support@complyo.tech', '_blank')}
              >
                <Mail className="w-4 h-4 mr-2" />
                support@complyo.tech
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default IntegrationGuide;
