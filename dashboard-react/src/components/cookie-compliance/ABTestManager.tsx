'use client';

/**
 * A/B-Tests für das Cookie-Banner.
 *
 * Zeigt die Tests einer Seite, legt neue an und wertet den laufenden aus.
 * Variante A ist die aktuelle Banner-Konfiguration (Kontrolle), Variante B die
 * Abwandlung. Getestet wird bewusst nur, was am Banner sichtbar ist — Layout,
 * Farbe, Buttonform, Position und die Texte.
 */

import React, { useCallback, useEffect, useState } from 'react';
import {
  BarChart3, Play, Square, Trash2, Plus, TrendingUp, AlertCircle,
  CheckCircle2, Loader2, FlaskConical,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import {
  listSiteTests, getTest, createTest, startTest, stopTest, deleteTest,
  type ABTestListItem, type ABTestDetail, type ABVariant, type ABVariantConfig,
} from '@/lib/ab-testing-api';

interface Props {
  siteId: string;
  /** Aktuelle Banner-Config — dient als Ausgangswert für Variante A. */
  config: ABVariantConfig | null;
}

const STATUS_LABEL: Record<string, string> = {
  draft: 'Entwurf',
  running: 'läuft',
  paused: 'pausiert',
  completed: 'beendet',
};

const STATUS_STYLE: Record<string, string> = {
  draft: 'bg-zinc-500/15 text-zinc-500',
  running: 'bg-emerald-500/15 text-emerald-500',
  paused: 'bg-amber-500/15 text-amber-500',
  completed: 'bg-blue-500/15 text-blue-500',
};

const LAYOUTS = [
  { wert: 'banner_bottom', label: 'Banner unten' },
  { wert: 'banner_top', label: 'Banner oben' },
  { wert: 'modal_center', label: 'Dialog mittig' },
  { wert: 'box_bottom_left', label: 'Box unten links' },
  { wert: 'box_bottom_right', label: 'Box unten rechts' },
];

const BUTTON_STYLES = [
  { wert: 'rounded', label: 'abgerundet' },
  { wert: 'square', label: 'eckig' },
  { wert: 'pill', label: 'Pille' },
];

function fehlertext(err: any, fallback: string): string {
  return err?.response?.data?.detail || err?.message || fallback;
}

export default function ABTestManager({ siteId, config }: Props) {
  const [tests, setTests] = useState<ABTestListItem[]>([]);
  const [detail, setDetail] = useState<ABTestDetail | null>(null);
  const [ladeListe, setLadeListe] = useState(true);
  const [ladeDetail, setLadeDetail] = useState(false);
  const [aktion, setAktion] = useState<number | null>(null);
  const [fehler, setFehler] = useState('');
  const [formularOffen, setFormularOffen] = useState(false);

  // Formularfelder
  const [name, setName] = useState('');
  const [hypothese, setHypothese] = useState('');
  const [split, setSplit] = useState(50);
  const [minSample, setMinSample] = useState(1000);
  const [variantB, setVariantB] = useState<ABVariantConfig>({});

  const ladeTests = useCallback(async () => {
    if (!siteId) return;
    setLadeListe(true);
    setFehler('');
    try {
      setTests(await listSiteTests(siteId));
    } catch (err: any) {
      setFehler(fehlertext(err, 'Tests konnten nicht geladen werden.'));
    } finally {
      setLadeListe(false);
    }
  }, [siteId]);

  useEffect(() => { ladeTests(); }, [ladeTests]);

  // Beim Öffnen des Formulars Variante B mit der aktuellen Config vorbelegen,
  // damit der Nutzer nur den zu testenden Unterschied ändern muss.
  useEffect(() => {
    if (!formularOffen) return;
    setVariantB({
      layout: (config?.layout as string) || 'banner_bottom',
      primary_color: (config?.primary_color as string) || '#6366f1',
      button_style: (config?.button_style as string) || 'rounded',
    });
  }, [formularOffen, config]);

  const oeffneDetail = async (testId: number) => {
    setLadeDetail(true);
    setFehler('');
    try {
      setDetail(await getTest(testId));
    } catch (err: any) {
      setFehler(fehlertext(err, 'Auswertung konnte nicht geladen werden.'));
    } finally {
      setLadeDetail(false);
    }
  };

  const varianteAAusConfig = (): ABVariantConfig => ({
    layout: (config?.layout as string) || 'banner_bottom',
    primary_color: (config?.primary_color as string) || '#6366f1',
    button_style: (config?.button_style as string) || 'rounded',
  });

  const anlegen = async () => {
    if (!name.trim()) { setFehler('Bitte einen Namen für den Test angeben.'); return; }
    setAktion(-1);
    setFehler('');
    try {
      await createTest({
        site_id: siteId,
        name: name.trim(),
        hypothesis: hypothese.trim() || undefined,
        variant_a_config: varianteAAusConfig(),
        variant_b_config: variantB,
        traffic_split: split,
        min_sample_size: minSample,
      });
      setFormularOffen(false);
      setName(''); setHypothese(''); setSplit(50); setMinSample(1000);
      await ladeTests();
    } catch (err: any) {
      setFehler(fehlertext(err, 'Test konnte nicht angelegt werden.'));
    } finally {
      setAktion(null);
    }
  };

  const fuehreAus = async (testId: number, fn: () => Promise<unknown>) => {
    setAktion(testId);
    setFehler('');
    try {
      await fn();
      await ladeTests();
      if (detail?.test.id === testId) await oeffneDetail(testId);
    } catch (err: any) {
      setFehler(fehlertext(err, 'Aktion fehlgeschlagen.'));
    } finally {
      setAktion(null);
    }
  };

  const laeuftBereits = tests.some((t) => t.status === 'running');

  return (
    <div className="space-y-6">
      {/* Kopf */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold dark:text-white text-gray-900 flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-teal-500" />
            A/B-Tests
          </h3>
          <p className="text-sm dark:text-zinc-400 text-gray-600 mt-1">
            Zwei Bannervarianten gegeneinander testen. Variante A ist Ihre aktuelle
            Konfiguration, Variante B die Abwandlung.
          </p>
        </div>
        <Button
          onClick={() => setFormularOffen((o) => !o)}
          disabled={!siteId}
          className="gap-2 bg-teal-500 hover:bg-teal-600 text-white"
        >
          <Plus className="w-4 h-4" />
          {formularOffen ? 'Abbrechen' : 'Neuer Test'}
        </Button>
      </div>

      {fehler && (
        <div className="flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-500">
          <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span>{fehler}</span>
        </div>
      )}

      {/* Formular */}
      {formularOffen && (
        <Card className="dark:bg-zinc-900/50 bg-white/70">
          <CardContent className="p-5 space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="ab-name">Name des Tests</Label>
                <Input
                  id="ab-name" value={name} onChange={(e) => setName(e.target.value)}
                  placeholder="z. B. Dialog mittig statt Banner unten"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ab-split">Anteil Variante A (%)</Label>
                <Input
                  id="ab-split" type="number" min={0} max={100} value={split}
                  onChange={(e) => setSplit(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="ab-hypothese">Hypothese (optional)</Label>
              <Textarea
                id="ab-hypothese" value={hypothese} onChange={(e) => setHypothese(e.target.value)}
                placeholder="Was erwarten Sie — und warum? z. B. „Ein mittiger Dialog erhöht die Zustimmungsquote, weil er schwerer zu übersehen ist.“"
                rows={2}
              />
            </div>

            <div className="rounded-lg border dark:border-zinc-800 border-gray-200 p-4 space-y-4">
              <p className="text-sm font-medium dark:text-white text-gray-900">
                Variante B — nur das ändern, was getestet werden soll
              </p>
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="space-y-2">
                  <Label>Layout</Label>
                  <Select
                    value={variantB.layout as string}
                    onValueChange={(v) => setVariantB((c) => ({ ...c, layout: v }))}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {LAYOUTS.map((l) => (
                        <SelectItem key={l.wert} value={l.wert}>{l.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Buttonform</Label>
                  <Select
                    value={variantB.button_style as string}
                    onValueChange={(v) => setVariantB((c) => ({ ...c, button_style: v }))}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {BUTTON_STYLES.map((b) => (
                        <SelectItem key={b.wert} value={b.wert}>{b.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ab-farbe">Hauptfarbe</Label>
                  <Input
                    id="ab-farbe" type="color"
                    value={(variantB.primary_color as string) || '#6366f1'}
                    onChange={(e) => setVariantB((c) => ({ ...c, primary_color: e.target.value }))}
                    className="h-10 p-1"
                  />
                </div>
              </div>
            </div>

            <div className="space-y-2 max-w-xs">
              <Label htmlFor="ab-sample">Mindest-Stichprobe je Variante</Label>
              <Input
                id="ab-sample" type="number" min={100} value={minSample}
                onChange={(e) => setMinSample(Number(e.target.value))}
              />
              <p className="text-xs dark:text-zinc-500 text-gray-500">
                Unter dieser Zahl gilt ein Ergebnis als nicht belastbar.
              </p>
            </div>

            <Button
              onClick={anlegen} disabled={aktion === -1}
              className="gap-2 bg-teal-500 hover:bg-teal-600 text-white"
            >
              {aktion === -1 ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Test anlegen
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Liste */}
      {ladeListe ? (
        <div className="flex items-center gap-2 text-sm dark:text-zinc-400 text-gray-600">
          <Loader2 className="w-4 h-4 animate-spin" /> Tests werden geladen …
        </div>
      ) : tests.length === 0 ? (
        <Card className="dark:bg-zinc-900/50 bg-white/70">
          <CardContent className="p-8 text-center">
            <BarChart3 className="w-10 h-10 mx-auto mb-3 dark:text-zinc-600 text-gray-400" />
            <p className="dark:text-zinc-300 text-gray-700 font-medium">Noch kein Test angelegt</p>
            <p className="text-sm dark:text-zinc-500 text-gray-500 mt-1">
              Ein Test läuft immer nur für eine Seite gleichzeitig.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {tests.map((t) => (
            <Card key={t.id} className="dark:bg-zinc-900/50 bg-white/70">
              <CardContent className="p-4 flex flex-wrap items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium dark:text-white text-gray-900">{t.name}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${STATUS_STYLE[t.status] ?? ''}`}>
                      {STATUS_LABEL[t.status] ?? t.status}
                    </span>
                    {t.winner && (
                      <span className="px-2 py-0.5 rounded text-xs bg-teal-500/15 text-teal-500">
                        Sieger: {t.winner}
                      </span>
                    )}
                  </div>
                  <p className="text-xs dark:text-zinc-500 text-gray-500 mt-1">
                    {t.total_impressions.toLocaleString('de-DE')} Einblendungen · Split {t.traffic_split}/{100 - t.traffic_split}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => oeffneDetail(t.id)}>
                    Auswertung
                  </Button>

                  {(t.status === 'draft' || t.status === 'paused') && (
                    <Button
                      size="sm" className="gap-1 bg-emerald-600 hover:bg-emerald-700 text-white"
                      // Das Backend lässt nur einen laufenden Test je Seite zu —
                      // hier schon sperren statt den Nutzer in den Fehler laufen zu lassen.
                      disabled={aktion === t.id || laeuftBereits}
                      title={laeuftBereits ? 'Es läuft bereits ein Test für diese Seite.' : undefined}
                      onClick={() => fuehreAus(t.id, () => startTest(t.id))}
                    >
                      {aktion === t.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                      Starten
                    </Button>
                  )}

                  {t.status === 'running' && (
                    <Button
                      size="sm" variant="outline" className="gap-1"
                      disabled={aktion === t.id}
                      onClick={() => fuehreAus(t.id, () => stopTest(t.id))}
                    >
                      {aktion === t.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Square className="w-3 h-3" />}
                      Beenden
                    </Button>
                  )}

                  {t.status !== 'running' && (
                    <Button
                      size="sm" variant="outline"
                      className="gap-1 text-red-500 hover:text-red-600"
                      disabled={aktion === t.id}
                      onClick={() => {
                        if (!window.confirm(`Test „${t.name}“ endgültig löschen? Die erfassten Ergebnisse gehen mit verloren.`)) return;
                        fuehreAus(t.id, () => deleteTest(t.id));
                      }}
                    >
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Auswertung */}
      {ladeDetail && (
        <div className="flex items-center gap-2 text-sm dark:text-zinc-400 text-gray-600">
          <Loader2 className="w-4 h-4 animate-spin" /> Auswertung wird geladen …
        </div>
      )}

      {detail && !ladeDetail && (
        <Card className="dark:bg-zinc-900/50 bg-white/70">
          <CardContent className="p-5 space-y-4">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <h4 className="font-semibold dark:text-white text-gray-900">
                Auswertung: {detail.test.name}
              </h4>
              <Button variant="ghost" size="sm" onClick={() => setDetail(null)}>schließen</Button>
            </div>

            {detail.test.hypothesis && (
              <p className="text-sm dark:text-zinc-400 text-gray-600 italic">
                „{detail.test.hypothesis}“
              </p>
            )}

            <div className="grid gap-4 sm:grid-cols-2">
              {(['variant_a', 'variant_b'] as const).map((schluessel) => {
                const v = detail.results[schluessel];
                const buchstabe: ABVariant = schluessel === 'variant_a' ? 'A' : 'B';
                const fuehrt = detail.results.leading_variant === buchstabe;
                return (
                  <div
                    key={schluessel}
                    className={`rounded-lg border p-4 ${
                      fuehrt
                        ? 'border-teal-500/50 bg-teal-500/5'
                        : 'dark:border-zinc-800 border-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium dark:text-white text-gray-900">
                        Variante {buchstabe}
                        {buchstabe === 'A' && (
                          <span className="ml-2 text-xs dark:text-zinc-500 text-gray-500">(aktuell)</span>
                        )}
                      </span>
                      {fuehrt && <TrendingUp className="w-4 h-4 text-teal-500" />}
                    </div>
                    <p className="text-2xl font-semibold dark:text-white text-gray-900 mt-2">
                      {v.rate.toLocaleString('de-DE', { maximumFractionDigits: 2 })} %
                    </p>
                    <p className="text-xs dark:text-zinc-500 text-gray-500">
                      Zustimmung · {v.accepted_all.toLocaleString('de-DE')} von{' '}
                      {v.impressions.toLocaleString('de-DE')} Einblendungen
                    </p>
                  </div>
                );
              })}
            </div>

            {/* Einordnung: erst Stichprobe, dann Signifikanz — in dieser Reihenfolge
                entscheidet auch das Backend. */}
            <div className="rounded-lg border dark:border-zinc-800 border-gray-200 p-4 space-y-2">
              {!detail.statistics.sample_reached ? (
                <p className="text-sm flex items-start gap-2 text-amber-500">
                  <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  Die Mindest-Stichprobe von{' '}
                  {detail.test.min_sample_size.toLocaleString('de-DE')} je Variante ist noch
                  nicht erreicht. Das Ergebnis ist noch nicht belastbar.
                </p>
              ) : detail.statistics.is_significant ? (
                <p className="text-sm flex items-start gap-2 text-emerald-500">
                  <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  Der Unterschied ist statistisch signifikant (p ={' '}
                  {detail.statistics.p_value.toLocaleString('de-DE', { maximumFractionDigits: 4 })}
                  , Konfidenz{' '}
                  {(detail.statistics.confidence_level * 100).toLocaleString('de-DE')} %).
                  {detail.results.leading_variant && (
                    <> Variante {detail.results.leading_variant} liegt um{' '}
                    {Math.abs(detail.results.improvement_percent).toLocaleString('de-DE', { maximumFractionDigits: 1 })} % vorn.</>
                  )}
                </p>
              ) : (
                <p className="text-sm flex items-start gap-2 dark:text-zinc-400 text-gray-600">
                  <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  Kein statistisch signifikanter Unterschied (p ={' '}
                  {detail.statistics.p_value.toLocaleString('de-DE', { maximumFractionDigits: 4 })}).
                  Der gemessene Abstand kann Zufall sein.
                </p>
              )}
            </div>

            {detail.test.status === 'running' && (
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm" variant="outline"
                  onClick={() => fuehreAus(detail.test.id, () => stopTest(detail.test.id, 'A'))}
                >
                  Beenden, Variante A behalten
                </Button>
                <Button
                  size="sm" variant="outline"
                  onClick={() => fuehreAus(detail.test.id, () => stopTest(detail.test.id, 'B'))}
                >
                  Beenden, Variante B behalten
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
