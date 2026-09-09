/**
 * Payload einer dokumentweiten Reparatur in lesbare Belegzeilen uebersetzen.
 *
 * Eigene Datei, weil die Uebersetzung ohne React pruefbar sein muss: sie laesst
 * sich so gegen die echten Payloads aus der Datenbank laufen, statt nur im
 * Browser "sieht gut aus" zu sein.
 */

export interface StrukturFix {
  selector?: string;
  attribut?: string;
  wert?: string;
  regel?: string;
  begruendung?: string;
}

export interface CssRegel {
  selector?: string;
  declarations?: string;
}

export const alsText = (v: unknown): string | null =>
  typeof v === 'string' && v.trim() ? v.trim() : null;

const alsListe = <T,>(v: unknown): T[] => (Array.isArray(v) ? (v as T[]) : []);

/** Ein Eingriff: was gesetzt wird, wo, und warum. */
export interface Eingriff {
  was: string;
  wo?: string;
  grund?: string;
}

export function eingriffeAus(fixType: string, p: Record<string, unknown>): Eingriff[] {
  switch (fixType) {
    case 'html-lang': {
      const wert = alsText(p.value) ?? alsText(p.lang);
      return wert ? [{ was: `lang="${wert}"`, wo: '<html>' }] : [];
    }
    case 'skip-link': {
      const label = alsText(p.label) ?? 'Zum Inhalt springen';
      const ziel = alsText(p.target);
      return [{ was: `Erster Link der Seite: „${label}“`, wo: ziel ? `Ziel ${ziel}` : undefined }];
    }
    case 'landmark-main': {
      const ziel = alsText(p.target);
      return ziel ? [{ was: 'role="main"', wo: ziel }] : [];
    }
    case 'css-rule': {
      const sel = alsText(p.selector);
      const decl = alsText(p.declarations);
      return sel && decl ? [{ was: decl, wo: sel }] : [];
    }
    case 'struktur': {
      const aus: Eingriff[] = alsListe<StrukturFix>(p.fixes).map((f) => ({
        was: f.attribut && f.wert ? `${f.attribut}="${f.wert}"` : (f.wert ?? f.regel ?? 'Änderung'),
        wo: f.selector,
        grund: f.begruendung,
      }));
      // Struktur-Fixes bringen oft nur CSS mit (z.B. Links im Fließtext
      // unterstreichen). Ohne die Regeln stünde die Karte leer da.
      return aus.concat(
        alsListe<CssRegel>(p.css_rules)
          .filter((r) => r.selector && r.declarations)
          .map((r): Eingriff => ({ was: r.declarations as string, wo: r.selector })),
      );
    }
    case 'kontrast-css':
      return alsListe<CssRegel>(p.rules)
        .filter((r) => r.selector && r.declarations)
        .map((r) => ({ was: r.declarations as string, wo: r.selector }));
    default:
      // Unbekannter Typ: lieber die flachen Werte zeigen als gar nichts. Eine
      // Karte ohne Beleg ist der Fehler, den dieser Block behebt.
      return Object.entries(p)
        .filter(([, v]) => typeof v === 'string' || typeof v === 'number')
        .map(([k, v]) => ({ was: String(v), wo: k }));
  }
}

/**
 * Die Messung, falls eine vorliegt: wie viele Verstöße vor der Reparatur
 * gezählt wurden und wie viele danach. Das ist der belastbarste Teil des
 * Belegs — er stammt aus dem Nachher-Lauf im Browser, nicht aus einer
 * Absichtserklärung des Verfahrens.
 */
export function messungAus(p: Record<string, unknown>): { regel: string; vorher: number; nachher: number }[] {
  const je = p.je_regel;
  if (!je || typeof je !== 'object' || Array.isArray(je)) return [];
  return Object.entries(je as Record<string, unknown>)
    .filter(([, paar]) => Array.isArray(paar) && paar.length >= 2)
    .map(([regel, paar]) => {
      const [v, n] = paar as [unknown, unknown];
      return { regel, vorher: Number(v) || 0, nachher: Number(n) || 0 };
    })
    .sort((a, b) => (b.vorher - b.nachher) - (a.vorher - a.nachher));
}

