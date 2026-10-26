/**
 * Waechter gegen die Dauerschleife / <-> /login (26.10.2026).
 *
 * Eine Sitzung mit Fehlerflag (Token nicht mehr verlaengerbar) darf an KEINER
 * der drei Stellen als angemeldet gelten, sonst schickt die Middleware sie von
 * /login nach / und der Client von / zurueck nach /login. Reproduziert mit
 * einem Cookie mit RefreshAccessTokenError: ~40 Spruenge in 9 Sekunden.
 *
 * Der Test liest die Quelltexte, weil die drei Stellen (Middleware, authorized-
 * Rueckruf, Auth-Kontext) ohne laufenden Server nicht zusammen auszufuehren
 * sind. Die Messung mit echtem Browser steht im Faden complyo-login-neu.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const lies = (p: string) => readFileSync(new URL(`../${p}`, import.meta.url), 'utf8');

test('Middleware zaehlt eine Sitzung mit Fehlerflag nicht als angemeldet', () => {
  assert.match(lies('middleware.ts'), /isLoggedIn\s*=\s*!!session\s*&&\s*!\(session as any\)\.error/);
});

test('authorized-Rueckruf zaehlt eine Sitzung mit Fehlerflag nicht als angemeldet', () => {
  assert.match(lies('auth.config.ts'), /isLoggedIn\s*=\s*!!auth\?\.user\s*&&\s*!\(auth as any\)\.error/);
});

test('Auth-Kontext: tote Sitzung ist nicht angemeldet und springt nicht hart auf /login', () => {
  const quelle = lies('contexts/AuthContext.tsx');
  assert.match(quelle, /!sessionAbgelaufen\s*&&/);
  assert.match(quelle, /abmeldungGestartet/);
  // Nur der Zweig fuer die tote Sitzung: dort darf es keinen Hartsprung geben
  // (logout() weiter unten springt zu Recht auf /login).
  const von = quelle.indexOf("sessionError === 'RefreshAccessTokenError'");
  const bis = quelle.indexOf('abmeldungGestartet.current = false;');
  assert.ok(von > 0 && bis > von, 'Zweig fuer tote Sitzung nicht gefunden');
  assert.doesNotMatch(quelle.slice(von, bis), /window\.location\.href/);
});
