/**
 * Banner-Automatik: der Banner bleibt weg, wenn es nichts einzuwilligen gibt.
 *
 * Das Widget prüft beim Laden der Seite im Browser des Besuchers, ob Cookies,
 * Browser-Speicher, fremde Hosts oder vom Blocker zurückgehaltene Dienste im
 * Spiel sind. Nur wenn nichts davon auftaucht und der Scan keinen Dienst
 * gefunden hat, erscheint kein Banner. Im Zweifel erscheint er.
 *
 * Der Schalter hier ist der Ausweg: "Banner immer anzeigen".
 */

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { ShieldCheck } from 'lucide-react';

interface BannerAutomatikProps {
  config: any;
  onSave: (config: any) => Promise<boolean>;
}

export default function BannerAutomatik({ config, onSave }: BannerAutomatikProps) {
  const [erzwingen, setErzwingen] = useState<boolean>(config?.banner_erzwingen === true);
  const [saving, setSaving] = useState(false);
  const [fehler, setFehler] = useState(false);

  // Wechselt die Website (Agentur) oder lädt die Konfiguration neu, gilt der Wert vom Server.
  useEffect(() => {
    setErzwingen(config?.banner_erzwingen === true);
  }, [config?.site_id, config?.banner_erzwingen]);

  const aendern = async (neu: boolean) => {
    const alt = erzwingen;
    setErzwingen(neu);
    setSaving(true);
    setFehler(false);
    const ok = await onSave({ ...config, banner_erzwingen: neu });
    setSaving(false);
    if (!ok) {
      setErzwingen(alt);
      setFehler(true);
    }
  };

  const wirktJetzt = config?.banner_auto_aus_erlaubt === true && !erzwingen;

  return (
    <Card className="bg-gray-100/50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700">
      <CardHeader>
        <CardTitle className="text-gray-900 dark:text-white flex items-center gap-2">
          <ShieldCheck className="w-5 h-5" aria-hidden="true" />
          Banner-Automatik
          {wirktJetzt && (
            <Badge variant="outline" className="text-xs">
              Für diese Website aktiv
            </Badge>
          )}
        </CardTitle>
        <CardDescription>
          Der Banner erscheint nur, wenn auf Ihrer Seite etwas zu entscheiden ist. Beim Laden prüft das
          Widget im Browser des Besuchers, ob Cookies, Browser-Speicher, fremde Server oder zurückgehaltene
          Dienste im Spiel sind. Taucht nichts davon auf und hat der Scan keinen Dienst gefunden, bleibt der
          Banner weg. Im Zweifel wird er angezeigt.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between p-4 bg-white/50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="pr-4">
            <Label htmlFor="banner-erzwingen" className="text-gray-900 dark:text-white font-medium">
              Banner immer anzeigen
            </Label>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Schaltet die Automatik für diese Website ab. Sinnvoll, wenn bald ein Dienst dazukommt oder
              Sie den Banner unabhängig von der Prüfung zeigen möchten.
            </p>
          </div>
          <Switch
            id="banner-erzwingen"
            checked={erzwingen}
            disabled={saving}
            onCheckedChange={aendern}
          />
        </div>
        <p className="text-xs text-gray-500" role="status" aria-live="polite">
          {fehler
            ? 'Speichern fehlgeschlagen. Die Einstellung wurde nicht geändert.'
            : 'Die Automatik wirkt nur, wenn der Scan abgeschlossen ist und keinen Dienst gefunden hat. Websites mit Google Tag Manager oder selbst eingetragenen Diensten sind ausgenommen.'}
        </p>
      </CardContent>
    </Card>
  );
}
