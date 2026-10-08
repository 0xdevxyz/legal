/**
 * Herkunft eines Kaufs: die utm-Parameter, mit denen der Besucher auf
 * complyo.de ankam.
 *
 * Die Landing haengt sie an jeden Buchen-Knopf an (landing-react/src/lib/
 * herkunft.ts). Die Registrierung liest sie hier aus der Adresszeile, legt
 * sie fuer die Dauer der Sitzung ab (ein Google-Login verlaesst die Seite
 * per Popup, ein Neuladen darf sie nicht verlieren) und gibt sie an
 * /api/stripe/create-checkout mit. Dort landen sie in den Metadaten der
 * Checkout-Sitzung und des Abos.
 *
 * Anlass (28.09.2026): Die Entscheidungsregel nach Woche 45 zaehlt Kaeufe je
 * Kanal. Ohne diese Strecke war ein Kauf keinem Kanal zuzuordnen.
 *
 * Dieselbe Positivliste und dasselbe Zeichenmuster wie im Backend
 * (stripe_routes._herkunft_metadaten); das Backend prueft ein zweites Mal.
 */
const SCHLUESSEL = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'] as const;
const MUSTER = /^[A-Za-z0-9_.:-]{1,120}$/;
const ABLAGE = 'complyo_herkunft';

export type Herkunft = Partial<Record<(typeof SCHLUESSEL)[number], string>>;

export function herkunftAusParametern(p: { get(name: string): string | null } | null | undefined): Herkunft {
  const h: Herkunft = {};
  if (!p) return h;
  for (const k of SCHLUESSEL) {
    const v = p.get(k);
    if (v && MUSTER.test(v)) h[k] = v;
  }
  return h;
}

/** Merkt sich eine gefundene Herkunft; eine leere ueberschreibt nichts. */
export function herkunftMerken(h: Herkunft): void {
  if (Object.keys(h).length === 0) return;
  try { sessionStorage.setItem(ABLAGE, JSON.stringify(h)); } catch { /* privat: dann eben ohne */ }
}

export function gemerkteHerkunft(): Herkunft {
  try {
    const roh = sessionStorage.getItem(ABLAGE);
    if (!roh) return {};
    const obj = JSON.parse(roh);
    return herkunftAusParametern({ get: (k: string) => (typeof obj?.[k] === 'string' ? obj[k] : null) });
  } catch {
    return {};
  }
}
