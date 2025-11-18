/**
 * Complyo Widget Integration Card
 * 
 * Zeigt dem User den Code zum Einbinden des Barrierefreiheits-Widgets
 */

import React, { useState } from 'react';
import { 
  Code, 
  Copy, 
  CheckCircle, 
  Eye,
  Sparkles,
  ExternalLink,
  BookOpen
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface WidgetIntegrationCardProps {
  siteId: string;
  websiteUrl?: string;
  isWidgetActive?: boolean;
}

export const WidgetIntegrationCard: React.FC<WidgetIntegrationCardProps> = ({
  siteId,
  websiteUrl = '',
  isWidgetActive = false
}) => {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('html');

  const widgetCode = `<script 
  src="https://api.complyo.tech/api/widgets/accessibility.js" 
  data-site-id="${siteId}"
  data-auto-fix="true"
  data-show-toolbar="true">
</script>`;

  const wordpressCode = `<?php
// Complyo Barrierefreiheits-Widget
// In functions.php oder via Code Snippets Plugin einfügen

add_action('wp_footer', 'complyo_accessibility_widget');
function complyo_accessibility_widget() {
  ?>
  <script 
    src="https://api.complyo.tech/api/widgets/accessibility.js" 
    data-site-id="${siteId}"
    data-auto-fix="true"
    data-show-toolbar="true">
  </script>
  <?php
}
?>`;

  const handleCopy = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-white">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-500 rounded-lg">
              <Code className="w-6 h-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl">⚡ Widget auf Website einbinden</CardTitle>
              <CardDescription>
                In 60 Sekunden zu barrierefreiem Web
              </CardDescription>
            </div>
          </div>
          {isWidgetActive ? (
            <Badge className="bg-green-500">
              <CheckCircle className="w-3 h-3 mr-1" />
              Aktiv
            </Badge>
          ) : (
            <Badge variant="outline" className="bg-yellow-50 border-yellow-300 text-yellow-700">
              Nicht eingebunden
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Status Alert */}
        {!isWidgetActive && (
          <Alert className="bg-blue-50 border-blue-200">
            <Sparkles className="h-4 w-4 text-blue-600" />
            <AlertTitle className="text-blue-900">Widget noch nicht aktiv</AlertTitle>
            <AlertDescription className="text-blue-700">
              Fügen Sie den Code unten auf Ihrer Website ein, damit das Widget erscheint.
              Die Alt-Texte und Features sind bereits vorbereitet!
            </AlertDescription>
          </Alert>
        )}

        {isWidgetActive && (
          <Alert className="bg-green-50 border-green-200">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertTitle className="text-green-900">Widget ist aktiv! ✅</AlertTitle>
            <AlertDescription className="text-green-700">
              Besucher Ihrer Website können jetzt Barrierefreiheits-Features nutzen.
            </AlertDescription>
          </Alert>
        )}

        {/* Tabs für verschiedene Einbindungs-Methoden */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="html">HTML / Standard</TabsTrigger>
            <TabsTrigger value="wordpress">WordPress</TabsTrigger>
          </TabsList>

          {/* HTML Tab */}
          <TabsContent value="html" className="space-y-3">
            <div>
              <h4 className="text-sm font-semibold mb-2 text-gray-700">
                📋 Code-Snippet (vor &lt;/body&gt; einfügen):
              </h4>
              <div className="relative">
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-xs leading-relaxed">
                  <code>{widgetCode}</code>
                </pre>
                <Button
                  size="sm"
                  variant="secondary"
                  className="absolute top-2 right-2"
                  onClick={() => handleCopy(widgetCode)}
                >
                  {copied ? (
                    <>
                      <CheckCircle className="w-4 h-4 mr-1" />
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
            </div>

            <div className="space-y-2 text-sm">
              <h5 className="font-semibold text-gray-700">🛠️ Anleitung:</h5>
              <ol className="list-decimal list-inside space-y-1 text-gray-600">
                <li>Öffnen Sie Ihre HTML-Datei oder Theme-Editor</li>
                <li>Suchen Sie nach dem <code className="bg-gray-100 px-1 rounded">&lt;/body&gt;</code> Tag</li>
                <li>Fügen Sie den Code direkt <strong>davor</strong> ein</li>
                <li>Speichern Sie die Datei</li>
                <li>Widget erscheint automatisch auf allen Seiten!</li>
              </ol>
            </div>
          </TabsContent>

          {/* WordPress Tab */}
          <TabsContent value="wordpress" className="space-y-3">
            <div>
              <h4 className="text-sm font-semibold mb-2 text-gray-700">
                🔌 WordPress-Integration:
              </h4>
              <div className="relative">
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-xs leading-relaxed">
                  <code>{wordpressCode}</code>
                </pre>
                <Button
                  size="sm"
                  variant="secondary"
                  className="absolute top-2 right-2"
                  onClick={() => handleCopy(wordpressCode)}
                >
                  {copied ? (
                    <>
                      <CheckCircle className="w-4 h-4 mr-1" />
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
            </div>

            <div className="space-y-2 text-sm">
              <h5 className="font-semibold text-gray-700">🛠️ Anleitung:</h5>
              <ol className="list-decimal list-inside space-y-1 text-gray-600">
                <li>WordPress-Backend → Design → Theme-Editor</li>
                <li>Öffnen Sie <code className="bg-gray-100 px-1 rounded">functions.php</code></li>
                <li>Fügen Sie den Code am <strong>Ende</strong> der Datei ein</li>
                <li>Klicken Sie auf "Datei aktualisieren"</li>
                <li>Widget ist sofort aktiv auf allen Seiten!</li>
              </ol>
              
              <Alert className="bg-yellow-50 border-yellow-200">
                <AlertDescription className="text-yellow-800 text-xs">
                  <strong>Tipp:</strong> Noch einfacher mit dem Plugin "Code Snippets" - 
                  dann müssen Sie die functions.php nicht anfassen!
                </AlertDescription>
              </Alert>
            </div>
          </TabsContent>
        </Tabs>

        {/* Widget-Features Vorschau */}
        <div className="p-3 bg-white rounded-lg border">
          <h5 className="font-semibold text-sm text-gray-900 mb-2">
            ✨ Was das Widget macht:
          </h5>
          <ul className="space-y-1 text-xs text-gray-600">
            <li className="flex items-center">
              <CheckCircle className="w-3 h-3 mr-2 text-green-500" />
              Fügt {siteId ? 'AI-generierte ' : ''}Alt-Texte runtime ein
            </li>
            <li className="flex items-center">
              <CheckCircle className="w-3 h-3 mr-2 text-green-500" />
              Kontrast-Modus für bessere Lesbarkeit
            </li>
            <li className="flex items-center">
              <CheckCircle className="w-3 h-3 mr-2 text-green-500" />
              Schriftgrößen-Anpassung
            </li>
            <li className="flex items-center">
              <CheckCircle className="w-3 h-3 mr-2 text-green-500" />
              Link-Highlighting für bessere Navigation
            </li>
            <li className="flex items-center">
              <CheckCircle className="w-3 h-3 mr-2 text-green-500" />
              Tastatur-Navigation optimiert
            </li>
          </ul>
        </div>

        {/* Site-ID Info */}
        <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs text-gray-500">Ihre Site-ID:</span>
              <div className="font-mono text-sm font-semibold text-gray-900">{siteId}</div>
            </div>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => handleCopy(siteId)}
            >
              <Copy className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Test-Button */}
        {websiteUrl && (
          <div className="flex space-x-2">
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => window.open(websiteUrl, '_blank')}
            >
              <Eye className="w-4 h-4 mr-2" />
              Website ansehen
            </Button>
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => window.open('https://docs.complyo.tech/widget', '_blank')}
            >
              <BookOpen className="w-4 h-4 mr-2" />
              Dokumentation
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default WidgetIntegrationCard;

