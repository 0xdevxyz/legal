/**
 * Serverseitige Verlängerung des Backend-Access-Tokens, mit Sperre.
 *
 * Warum serverseitig: Die Anmeldung läuft über den Dashboard-Server (NextAuth
 * `authorize` ruft das Backend). Das `refresh_token`-Cookie, das das Backend
 * dabei setzt, erreicht den Browser nie. Der clientseitige Weg über
 * /api/auth/refresh-cookie endete deshalb immer mit 204, und bis zum
 * 11.09.2026 lief jede Sitzung nach Ablauf des Access-Tokens in 401 und
 * Abmeldung. Der Refresh-Token liegt aber im NextAuth-JWT, und der
 * jwt-Rückruf läuft auf dem Server: dort kann verlängert werden.
 *
 * Warum eine Sperre: Das Backend dreht den Refresh-Token bei jeder
 * Verlängerung und erkennt Wiederverwendung. Wer denselben Refresh-Token
 * zweimal einlöst, beendet ALLE Sitzungen des Kontos (auth_service
 * `beende_sitzungskette`), denn ein zweites Einlösen ist der Abdruck eines
 * gestohlenen Tokens. Der jwt-Rückruf läuft aber für jede Sitzungsabfrage,
 * und ein Browser mit drei Tabs stellt drei gleichzeitig. Ohne Sperre hätte
 * die erste Verlängerung die zweite zum Angriff gemacht.
 *
 * Deshalb zwei Tabellen, prozessweit (das Dashboard läuft in einem Prozess):
 *   - `laufende`: je Refresh-Token höchstens ein Aufruf ans Backend; wer
 *     parallel kommt, wartet auf dasselbe Versprechen.
 *   - `erledigte`: das Ergebnis bleibt zwei Minuten unter dem ALTEN Token
 *     abrufbar. Eine Anfrage, die mit dem alten Cookie startet, nachdem die
 *     Verlängerung fertig ist, aber bevor der Browser das neue Cookie hat,
 *     bekommt so dasselbe neue Paar statt eines zweiten Backend-Aufrufs.
 *
 * "nicht_erreichbar" (Netz, 5xx, Drossel) wird bewusst NICHT gemerkt: beim
 * nächsten Aufruf darf es noch einmal versucht werden, und bis dahin gilt
 * das alte Token weiter. "ungueltig" (401) wird gemerkt: die Kette ist tot,
 * jede weitere Anfrage mit diesem Token soll dasselbe hören.
 */

export type TokenPaar = {
  accessToken: string;
  refreshToken: string;
  expiresAt: number;
};

export type Erneuerung =
  | { status: "erneuert"; paar: TokenPaar }
  | { status: "ungueltig" }
  | { status: "nicht_erreichbar" };

type Antwort = { status: number; ok: boolean; json: () => Promise<any> };
type Abruf = (url: string, init: Record<string, unknown>) => Promise<Antwort>;

export const NACHWIRKZEIT_MS = 120_000;

const laufende = new Map<string, Promise<Erneuerung>>();
const erledigte = new Map<string, { ergebnis: Erneuerung; zeit: number }>();

function aufraeumen(jetzt: number): void {
  for (const [token, eintrag] of erledigte) {
    if (jetzt - eintrag.zeit > NACHWIRKZEIT_MS) erledigte.delete(token);
  }
}

export async function erneuereToken(
  refreshToken: string,
  apiUrl: string,
  laufzeitMs: number,
  abruf: Abruf = fetch as unknown as Abruf,
  jetzt: () => number = Date.now,
): Promise<Erneuerung> {
  aufraeumen(jetzt());

  const fertig = erledigte.get(refreshToken);
  if (fertig) return fertig.ergebnis;

  const laufend = laufende.get(refreshToken);
  if (laufend) return laufend;

  const versprechen = (async (): Promise<Erneuerung> => {
    try {
      const res = await abruf(`${apiUrl}/api/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (res.status === 401) return { status: "ungueltig" };
      if (!res.ok) return { status: "nicht_erreichbar" };
      const daten = await res.json();
      if (!daten?.access_token || !daten?.refresh_token) return { status: "nicht_erreichbar" };
      return {
        status: "erneuert",
        paar: {
          accessToken: daten.access_token,
          refreshToken: daten.refresh_token,
          expiresAt: jetzt() + laufzeitMs,
        },
      };
    } catch {
      return { status: "nicht_erreichbar" };
    }
  })();

  laufende.set(refreshToken, versprechen);
  try {
    const ergebnis = await versprechen;
    if (ergebnis.status !== "nicht_erreichbar") {
      erledigte.set(refreshToken, { ergebnis, zeit: jetzt() });
    }
    return ergebnis;
  } finally {
    laufende.delete(refreshToken);
  }
}

/** Nur für Tests: beide Tabellen leeren. */
export function _zuruecksetzen(): void {
  laufende.clear();
  erledigte.clear();
}
