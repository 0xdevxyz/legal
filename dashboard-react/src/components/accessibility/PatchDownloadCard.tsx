/**
 * Complyo Barrierefreiheits-Patches Download Card
 * 
 * Teil des Hybrid-Modells:
 * - Widget für sofortige Runtime-Fixes ✅
 * - Patches für permanente SEO-optimierte Lösung 🚀
 */

import React, { useState } from 'react';
import { 
  Download, 
  FileArchive, 
  CheckCircle, 
  AlertCircle, 
  Loader2,
  ExternalLink,
  Zap,
  TrendingUp,
  Code
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';

interface PatchDownloadCardProps {
  siteId: string;
  fixesCount: number;
  altTextCount?: number;
  contrastCount?: number;
  ariaCount?: number;
  onDownloadComplete?: () => void;
}

interface PatchStats {
  alt_text: number;
  contrast: number;
  aria: number;
  total: number;
}

export const PatchDownloadCard: React.FC<PatchDownloadCardProps> = ({
  siteId,
  fixesCount,
  altTextCount = 0,
  contrastCount = 0,
  ariaCount = 0,
  onDownloadComplete
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloadId, setDownloadId] = useState<string | null>(null);

  const handleGeneratePatches = async () => {
    setIsGenerating(true);
    setError(null);
    setDownloadUrl(null);

    try {
      const API_BASE = process.env.REACT_APP_API_BASE || 'https://api.complyo.tech';
      
      const response = await fetch(
        `${API_BASE}/api/accessibility/patches/generate?site_id=${siteId}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Fehler beim Generieren der Patches');
      }

      const data = await response.json();

      if (data.success) {
        setDownloadUrl(`${API_BASE}${data.download_url}`);
        setDownloadId(data.download_id);
        
        if (onDownloadComplete) {
          onDownloadComplete();
        }
      } else {
        throw new Error(data.error || 'Unbekannter Fehler');
      }
    } catch (err) {
      console.error('Error generating patches:', err);
      setError(err instanceof Error ? err.message : 'Fehler beim Generieren');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = () => {
    if (downloadUrl) {
      window.location.href = downloadUrl;
    }
  };

  const stats: PatchStats = {
    alt_text: altTextCount,
    contrast: contrastCount,
    aria: ariaCount,
    total: fixesCount
  };

  return (
    <Card className="border-blue-200 bg-gradient-to-br from-blue-50 to-white">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-500 rounded-lg">
              <FileArchive className="w-6 h-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl">🚀 SEO-Boost: HTML-Patches</CardTitle>
              <CardDescription>
                Permanente Barrierefreiheit für bessere Rankings
              </CardDescription>
            </div>
          </div>
          <Badge variant="outline" className="bg-white">
            <Zap className="w-3 h-3 mr-1" />
            Hybrid-Modell
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Status Info */}
        <Alert className="bg-blue-50 border-blue-200">
          <TrendingUp className="h-4 w-4 text-blue-600" />
          <AlertTitle className="text-blue-900">Widget läuft bereits ✅</AlertTitle>
          <AlertDescription className="text-blue-700">
            Ihre Besucher sehen bereits barrierefreie Inhalte (Runtime).
            Diese Patches machen die Fixes <strong>permanent</strong> für besseres SEO!
          </AlertDescription>
        </Alert>

        {/* Statistiken */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-white rounded-lg border">
            <div className="text-2xl font-bold text-purple-600">{stats.total}</div>
            <div className="text-sm text-gray-600">Gesamt-Fixes</div>
          </div>
          <div className="p-3 bg-white rounded-lg border">
            <div className="text-2xl font-bold text-green-600">{stats.alt_text}</div>
            <div className="text-sm text-gray-600">Alt-Texte</div>
          </div>
          <div className="p-3 bg-white rounded-lg border">
            <div className="text-2xl font-bold text-orange-600">{stats.contrast}</div>
            <div className="text-sm text-gray-600">Kontrast-Fixes</div>
          </div>
          <div className="p-3 bg-white rounded-lg border">
            <div className="text-2xl font-bold text-blue-600">{stats.aria}</div>
            <div className="text-sm text-gray-600">ARIA-Labels</div>
          </div>
        </div>

        {/* Vorteile */}
        <div className="space-y-2">
          <h4 className="font-semibold text-sm text-gray-700">📦 Paket enthält:</h4>
          <ul className="space-y-1 text-sm text-gray-600">
            <li className="flex items-center">
              <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
              HTML-Dateien mit Alt-Texten
            </li>
            <li className="flex items-center">
              <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
              CSS-Patches (Kontrast, Focus-Styles)
            </li>
            <li className="flex items-center">
              <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
              WordPress XML-Export (Mediathek)
            </li>
            <li className="flex items-center">
              <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
              FTP-Anleitung + README
            </li>
          </ul>
        </div>

        {/* Vergleich */}
        <div className="p-3 bg-white rounded-lg border border-green-200">
          <div className="flex items-start space-x-3">
            <Code className="w-5 h-5 text-green-600 mt-0.5" />
            <div>
              <h5 className="font-semibold text-sm text-gray-900">Runtime vs. Permanent</h5>
              <div className="text-xs text-gray-600 mt-1 space-y-1">
                <div>⚡ <strong>Widget (jetzt):</strong> Funktioniert sofort, SEO eingeschränkt</div>
                <div>🚀 <strong>Mit Patches:</strong> Permanente Lösung, maximales SEO</div>
              </div>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Fehler</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Success Display */}
        {downloadUrl && (
          <Alert className="bg-green-50 border-green-200">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertTitle className="text-green-900">Patches bereit!</AlertTitle>
            <AlertDescription className="text-green-700">
              Ihr Download-Paket wurde generiert und ist bereit.
              <br />
              <span className="text-xs">Download-ID: {downloadId}</span>
            </AlertDescription>
          </Alert>
        )}
      </CardContent>

      <CardFooter className="flex flex-col space-y-3">
        {!downloadUrl ? (
          <Button
            onClick={handleGeneratePatches}
            disabled={isGenerating}
            className="w-full bg-blue-600 hover:bg-blue-700"
            size="lg"
          >
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Generiere Patches...
              </>
            ) : (
              <>
                <Download className="mr-2 h-5 w-5" />
                Patches generieren (GRATIS)
              </>
            )}
          </Button>
        ) : (
          <Button
            onClick={handleDownload}
            className="w-full bg-green-600 hover:bg-green-700"
            size="lg"
          >
            <Download className="mr-2 h-5 w-5" />
            Jetzt herunterladen
          </Button>
        )}

        <div className="text-center space-y-2 w-full">
          <p className="text-xs text-gray-500">
            Zu technisch? Wir übernehmen das für Sie!
          </p>
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={() => window.open('https://complyo.tech/expertservice', '_blank')}
          >
            <ExternalLink className="mr-2 h-4 w-4" />
            Expertservice buchen (€3.000)
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
};

export default PatchDownloadCard;

