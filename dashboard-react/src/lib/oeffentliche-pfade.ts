/**
 * Welche Seiten ohne Anmeldung erreichbar sind.
 *
 * Diese Liste stand bis zum 10.09.2026 an ZWEI Stellen: im `authorized`-Rückruf
 * in auth.config.ts und noch einmal in middleware.ts. Beide prüfen dasselbe,
 * aber der Rückruf läuft zuerst — wer nur die Middleware anfasst, ändert
 * nichts, und zwar ohne jede Fehlermeldung. Genau das ist beim Bau der
 * Kontoseiten passiert: die Seiten waren da, gebaut und ausgeliefert, und
 * jeder Aufruf landete trotzdem auf /login.
 *
 * Deshalb eine Quelle. Wer eine öffentliche Seite ergänzt, ergänzt sie hier.
 *
 * Die Kontowege gehören dazu, weil ihr Zweck es verlangt: wer sein Passwort
 * vergessen hat oder einen Bestätigungslink aus einer Mail anklickt, ist
 * gerade NICHT angemeldet. Eine Umleitung auf /login verlöre dabei den Token
 * aus der Adresse.
 */
export const OEFFENTLICHE_PFADE = [
  "/login",
  "/register",
  "/auth/callback",
  "/passwort-vergessen",
  "/konto/passwort-neu",
  "/konto/email-bestaetigen",
] as const;

/** Pfade, von denen ein bereits Angemeldeter auf das Dashboard geschickt wird. */
export const NUR_FUER_GAESTE = ["/login", "/register"] as const;

export function istOeffentlich(pfad: string): boolean {
  return OEFFENTLICHE_PFADE.some((p) => pfad.startsWith(p));
}

export function istNurFuerGaeste(pfad: string): boolean {
  return (NUR_FUER_GAESTE as readonly string[]).includes(pfad);
}

/**
 * Seiten, die ohne die App-Hülle rendern — ohne Seitenleiste und ohne
 * Anmeldewache.
 *
 * Das war die DRITTE Kopie derselben Liste (in
 * components/dashboard/SidebarLayout.tsx als `AUTH_ROUTES`). Sie entscheidet
 * etwas anderes als `OEFFENTLICHE_PFADE` — nämlich das Aussehen statt den
 * Zugang — und genau deshalb ist sie beim Bau der Kontoseiten übersehen
 * worden: die Seiten waren serverseitig längst freigegeben, und der Browser
 * hat sie trotzdem sofort auf /login geschoben.
 *
 * Fachlich fällt beides zusammen: was ohne Anmeldung erreichbar ist, kann
 * keine Seitenleiste brauchen. Der einzige Zusatz ist /privacy.
 */
export const OHNE_RAHMEN = [...OEFFENTLICHE_PFADE, "/privacy"] as const;

export function istOhneRahmen(pfad: string): boolean {
  return OHNE_RAHMEN.some((p) => pfad.startsWith(p));
}
