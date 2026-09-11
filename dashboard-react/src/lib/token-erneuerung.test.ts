/**
 * Läuft ohne Testrahmen, mit Bordmitteln von Node 22:
 *     node --experimental-strip-types --test src/lib/token-erneuerung.test.ts
 * (npm run test:token). Kein jest im Projekt, und für sechs Fälle lohnt keiner.
 *
 * Der wichtigste Fall ist der erste: Wer denselben Refresh-Token zweimal ans
 * Backend schickt, beendet dort alle Sitzungen des Kontos.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { erneuereToken, NACHWIRKZEIT_MS, _zuruecksetzen } from "./token-erneuerung.ts";

function backendAttrappe(antworten: Array<{ status: number; body?: any; werfen?: boolean }>) {
  const aufrufe: any[] = [];
  const abruf = async (url: string, init: any) => {
    aufrufe.push({ url, body: JSON.parse(init.body) });
    const a = antworten.shift() ?? { status: 200, body: { access_token: "a-neu", refresh_token: "r-neu" } };
    if (a.werfen) throw new Error("Netz weg");
    return { status: a.status, ok: a.status >= 200 && a.status < 300, json: async () => a.body };
  };
  return { abruf, aufrufe };
}

test("fünf gleichzeitige Verlängerungen mit demselben Token: ein Backend-Aufruf, ein Paar", async () => {
  _zuruecksetzen();
  const { abruf, aufrufe } = backendAttrappe([]);
  const ergebnisse = await Promise.all(
    Array.from({ length: 5 }, () => erneuereToken("r-alt", "https://api", 1000, abruf)),
  );
  assert.equal(aufrufe.length, 1);
  assert.equal(aufrufe[0].body.refresh_token, "r-alt");
  for (const e of ergebnisse) {
    assert.equal(e.status, "erneuert");
    assert.equal((e as any).paar.refreshToken, "r-neu");
  }
});

test("Nachzügler mit dem alten Token bekommt das gemerkte Paar ohne zweiten Aufruf", async () => {
  _zuruecksetzen();
  const { abruf, aufrufe } = backendAttrappe([]);
  const erst = await erneuereToken("r-alt", "https://api", 1000, abruf);
  const spaet = await erneuereToken("r-alt", "https://api", 1000, abruf);
  assert.equal(aufrufe.length, 1);
  assert.deepEqual(spaet, erst);
});

test("nach der Nachwirkzeit wird der alte Token nicht mehr erinnert", async () => {
  _zuruecksetzen();
  let uhr = 1_000_000;
  const { abruf, aufrufe } = backendAttrappe([{ status: 200, body: { access_token: "a1", refresh_token: "r1" } }, { status: 401 }]);
  await erneuereToken("r-alt", "https://api", 1000, abruf, () => uhr);
  uhr += NACHWIRKZEIT_MS + 1;
  const spaet = await erneuereToken("r-alt", "https://api", 1000, abruf, () => uhr);
  assert.equal(aufrufe.length, 2);
  assert.equal(spaet.status, "ungueltig");
});

test("verschiedene Token werden getrennt verlängert", async () => {
  _zuruecksetzen();
  const { abruf, aufrufe } = backendAttrappe([]);
  await Promise.all([erneuereToken("r-a", "https://api", 1000, abruf), erneuereToken("r-b", "https://api", 1000, abruf)]);
  assert.equal(aufrufe.length, 2);
});

test("401 heißt ungültig und bleibt es für Nachzügler", async () => {
  _zuruecksetzen();
  const { abruf, aufrufe } = backendAttrappe([{ status: 401 }]);
  const a = await erneuereToken("r-tot", "https://api", 1000, abruf);
  const b = await erneuereToken("r-tot", "https://api", 1000, abruf);
  assert.equal(a.status, "ungueltig");
  assert.equal(b.status, "ungueltig");
  assert.equal(aufrufe.length, 1);
});

test("Netzfehler, Drossel und 5xx werden nicht gemerkt: der nächste Versuch darf laufen", async () => {
  _zuruecksetzen();
  const { abruf, aufrufe } = backendAttrappe([{ status: 0, werfen: true }, { status: 429 }, { status: 503 }, { status: 200, body: { access_token: "a", refresh_token: "r" } }]);
  const e1 = await erneuereToken("r-x", "https://api", 1000, abruf);
  const e2 = await erneuereToken("r-x", "https://api", 1000, abruf);
  const e3 = await erneuereToken("r-x", "https://api", 1000, abruf);
  const e4 = await erneuereToken("r-x", "https://api", 1000, abruf);
  assert.deepEqual([e1.status, e2.status, e3.status, e4.status], ["nicht_erreichbar", "nicht_erreichbar", "nicht_erreichbar", "erneuert"]);
  assert.equal(aufrufe.length, 4);
});

test("Ablaufzeit wird aus der Laufzeit gerechnet", async () => {
  _zuruecksetzen();
  const { abruf } = backendAttrappe([]);
  const e = await erneuereToken("r-z", "https://api", 60_000, abruf, () => 5_000);
  assert.equal((e as any).paar.expiresAt, 65_000);
});
