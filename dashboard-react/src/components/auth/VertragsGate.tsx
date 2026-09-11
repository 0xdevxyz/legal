'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import { AlertCircle, Loader2 } from 'lucide-react';
import { getApiClient } from '@/lib/api-client';
import { AGB_VERSION, AVV_VERSION } from '@/lib/vertragsstand';

/**
 * Holt die Zustimmung zu AGB und Auftragsverarbeitungsvertrag nach.
 *
 * Seit dem 10.09.2026 nimmt die Registrierung beides an. Die Konten von davor
 * haben nie zugestimmt (am 11.09.2026: 16 Konten). Ohne AVV darf complyo fuer
 * sie keine Daten der Besucher ihrer Websites verarbeiten. Deshalb sperrt
 * dieses Gate den Inhalt hinter der Anmeldung, bis die Zustimmung vorliegt.
 *
 * Gesperrt wird NUR bei einer klaren Antwort `fehlt: true`. Solange die
 * Abfrage laeuft oder fehlschlaegt (503, Netz), bleibt der Inhalt frei: ein
 * Tabellenproblem darf nicht jeden Kunden aussperren, und ein Dialog, der beim
 * Laden kurz aufblitzt, waere ein Fehler in jeder Sitzung.
 *
 * Der Wortlaut ist derselbe wie auf der Registrierungsseite; die Fassungen
 * kommen aus lib/vertragsstand und werden mitgeschickt, damit das Backend
 * protokolliert, was tatsaechlich angezeigt wurde.
 */

interface Vertragsstand {
  agb_version_aktuell: string;
  avv_version_aktuell: string;
  agb_angenommen: string | null;
  avv_angenommen: string | null;
  agb_fehlt: boolean;
  avv_fehlt: boolean;
}

function fehlertext(err: unknown): string {
  const e = err as { response?: { status?: number; data?: { detail?: unknown } } };
  const status = e?.response?.status;
  const detail = e?.response?.data?.detail;
  if (typeof detail === 'string' && detail) return detail;
  if (status === 401 || status === 403) return 'Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.';
  if (status === 429) return 'Zu viele Versuche. Bitte warten Sie eine Minute.';
  if (status && status >= 500) return 'Der Server ist gerade nicht erreichbar. Bitte versuchen Sie es gleich noch einmal.';
  return 'Die Zustimmung konnte nicht gespeichert werden. Bitte versuchen Sie es noch einmal.';
}

export default function VertragsGate({ children }: { children: React.ReactNode }) {
  const api = getApiClient();
  const queryClient = useQueryClient();
  const [bestaetigt, setBestaetigt] = useState(false);
  const [laeuft, setLaeuft] = useState(false);
  const [fehler, setFehler] = useState<string | null>(null);

  const { data } = useQuery<Vertragsstand>({
    queryKey: ['vertragsstand'],
    queryFn: async () => (await api.get<Vertragsstand>('/api/auth/vertragsstand')).data,
    staleTime: 10 * 60_000,
    retry: 1,
  });

  const fehlt = data?.agb_fehlt === true || data?.avv_fehlt === true;
  // Zeigt das Dashboard eine andere Fassung als der Server, wuerde die Annahme
  // mit 400 abgewiesen. Dann lieber gleich sagen, was los ist.
  const fassungPasst =
    !data || (data.agb_version_aktuell === AGB_VERSION && data.avv_version_aktuell === AVV_VERSION);

  const annehmen = async () => {
    if (!bestaetigt || laeuft) return;
    setFehler(null);
    setLaeuft(true);
    try {
      await api.post('/api/auth/vertrag-annehmen', {
        unternehmer_bestaetigt: true,
        agb_version: AGB_VERSION,
        avv_version: AVV_VERSION,
      });
      await queryClient.invalidateQueries({ queryKey: ['vertragsstand'] });
    } catch (err) {
      setFehler(fehlertext(err));
    } finally {
      setLaeuft(false);
    }
  };

  return (
    <>
      {children}
      {/* Radix setzt role und aria-modal selbst; sie stehen hier trotzdem
          ausdruecklich, damit die Zusage im Quelltext nachlesbar ist. */}
      <DialogPrimitive.Root open={fehlt} onOpenChange={() => undefined}>
        <DialogPrimitive.Portal>
          <DialogPrimitive.Overlay className="fixed inset-0 z-[100] bg-black/75 backdrop-blur-sm" />
          {/* Radix setzt aria-labelledby/-describedby selbst auf seine
              Title-/Description-IDs. Eigene ids darauf ueberschrieben diese
              IDs, und Radix meldete im Browser "DialogContent requires a
              DialogTitle", obwohl der Titel da war (11.09.2026). */}
          <DialogPrimitive.Content
            role="dialog"
            aria-modal="true"
            onEscapeKeyDown={(e) => e.preventDefault()}
            onPointerDownOutside={(e) => e.preventDefault()}
            onInteractOutside={(e) => e.preventDefault()}
            className="fixed left-1/2 top-1/2 z-[101] w-[calc(100%-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-gray-200 bg-white p-6 text-gray-900 shadow-2xl outline-none dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
          >
            <DialogPrimitive.Title className="text-lg font-semibold leading-snug">
              Bevor es weitergeht: Ihre Zustimmung zu AGB und Auftragsverarbeitungsvertrag
            </DialogPrimitive.Title>
            <DialogPrimitive.Description className="mt-3 text-sm leading-relaxed text-gray-600 dark:text-zinc-400">
              Seit dem 10. September 2026 schließt complyo mit jedem Kunden einen
              Auftragsverarbeitungsvertrag. Ihr Konto besteht schon länger, deshalb holen
              wir Ihre Zustimmung jetzt nach. Ohne sie darf complyo die Daten der Besucher
              Ihrer Website nicht verarbeiten. Es gelten die{' '}
              <a href="https://complyo.de/agb" target="_blank" rel="noopener noreferrer"
                 className="underline text-blue-700 dark:text-blue-400">
                AGB
              </a>{' '}
              (Fassung vom {AGB_VERSION.split('-').reverse().join('.')}) und der{' '}
              <a href="https://complyo.de/avv" target="_blank" rel="noopener noreferrer"
                 className="underline text-blue-700 dark:text-blue-400">
                Auftragsverarbeitungsvertrag
              </a>{' '}
              (Fassung vom {AVV_VERSION.split('-').reverse().join('.')}).
            </DialogPrimitive.Description>

            <label htmlFor="vertragsgate-unternehmer"
                   className="mt-5 flex cursor-pointer items-start gap-3 text-sm leading-relaxed">
              <input
                id="vertragsgate-unternehmer"
                type="checkbox"
                checked={bestaetigt}
                onChange={(e) => setBestaetigt(e.target.checked)}
                className="mt-0.5 h-4 w-4 flex-shrink-0 cursor-pointer rounded"
                style={{ accentColor: '#2563eb' }}
              />
              <span>
                Ich handle bei diesem Vertrag als Unternehmer im Sinne des § 14 BGB und
                nicht als Verbraucher. complyo schließt keine Verträge mit Verbrauchern.
                Zugleich schließe ich den{' '}
                <a href="https://complyo.de/avv" target="_blank" rel="noopener noreferrer"
                   className="underline text-blue-700 dark:text-blue-400"
                   onClick={(e) => e.stopPropagation()}>
                  Auftragsverarbeitungsvertrag nach Art. 28 DSGVO
                </a>{' '}ab. Er ist nötig, weil complyo bei der Prüfung und beim Betrieb der
                Widgets Daten der Besucher meiner Website verarbeitet.
              </span>
            </label>

            {!fassungPasst && (
              <p role="alert" className="mt-4 flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200">
                <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden />
                <span>Diese Seite zeigt eine ältere Fassung der Vertragstexte als der Server.
                  Bitte laden Sie die Seite neu.</span>
              </p>
            )}
            {fehler && (
              <p role="alert" className="mt-4 flex items-start gap-2 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-200">
                <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden />
                <span>{fehler}</span>
              </p>
            )}

            <div className="mt-6 flex justify-end">
              <button
                type="button"
                onClick={annehmen}
                disabled={!bestaetigt || laeuft || !fassungPasst}
                className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 dark:focus:ring-offset-zinc-900"
              >
                {laeuft && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
                Zustimmen und weiter
              </button>
            </div>
          </DialogPrimitive.Content>
        </DialogPrimitive.Portal>
      </DialogPrimitive.Root>
    </>
  );
}
