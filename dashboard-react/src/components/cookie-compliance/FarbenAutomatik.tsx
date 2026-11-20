/**
 * Farben automatisch: der Banner übernimmt die Farben Ihrer Website.
 *
 * complyo liest die Farben beim Scan aus Ihrer Seite (Knöpfe, Kopfbereich, Flächen)
 * und zieht sie nach, wenn sich das Design der Website ändert. Wer im Designer eigene
 * Farben speichert, schaltet das automatisch ab; hier lässt es sich wieder einschalten.
 * Nichts wird überschrieben, solange der Schalter aus ist.
 */

import React, { useEffect, useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Palette } from 'lucide-react';

interface FarbenAutomatikProps {
  config: any;
  onSave: (config: any) => Promise<boolean>;
}

export default function FarbenAutomatik({ config, onSave }: FarbenAutomatikProps) {
  // Ältere Server kennen das Feld nicht: dann gibt es nichts umzuschalten.
  const bekannt = typeof config?.farben_automatisch === 'boolean';
  const [automatisch, setAutomatisch] = useState<boolean>(config?.farben_automatisch === true);
  const [saving, setSaving] = useState(false);
  const [fehler, setFehler] = useState(false);

  // Wechselt die Website (Agentur) oder lädt die Konfiguration neu, gilt der Wert vom Server.
  useEffect(() => {
    setAutomatisch(config?.farben_automatisch === true);
  }, [config?.site_id, config?.farben_automatisch]);

  if (!bekannt) return null;

  const aendern = async (neu: boolean) => {
    const alt = automatisch;
    setAutomatisch(neu);
    setSaving(true);
    setFehler(false);
    const ok = await onSave({ ...config, farben_automatisch: neu });
    setSaving(false);
    if (!ok) {
      setAutomatisch(alt);
      setFehler(true);
    }
  };

  return (
    <Card className="mb-6 bg-gray-100/50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700">
      <CardHeader>
        <CardTitle className="text-gray-900 dark:text-white flex items-center gap-2">
          <Palette className="w-5 h-5" aria-hidden="true" />
          Farben der Website übernehmen
        </CardTitle>
        <CardDescription className="text-gray-600 dark:text-zinc-400">
          complyo liest die Farben Ihrer Website beim Scan selbst aus und passt den Banner an, wenn sich
          Ihr Design ändert.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center justify-between p-4 bg-white/50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="pr-4">
            <Label htmlFor="farben-automatisch" className="text-gray-900 dark:text-white font-medium">
              Farben automatisch übernehmen
            </Label>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Eigene Farben, die Sie unten speichern, schalten das ab. Einschalten übernimmt die
              Farben Ihrer Website beim nächsten Scan.
            </p>
          </div>
          <Switch
            id="farben-automatisch"
            checked={automatisch}
            disabled={saving}
            onCheckedChange={aendern}
          />
        </div>
        <p className="text-xs text-gray-600 dark:text-gray-400" role="status" aria-live="polite">
          {fehler ? 'Speichern fehlgeschlagen. Die Einstellung wurde nicht geändert.' : ''}
        </p>
      </CardContent>
    </Card>
  );
}
