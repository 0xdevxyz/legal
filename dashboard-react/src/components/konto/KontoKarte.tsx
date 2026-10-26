'use client';

/**
 * Der gemeinsame Rahmen der Kontoseiten.
 *
 * Passwort vergessen, Passwort neu setzen und E-Mail bestätigen sind drei
 * Seiten mit derselben Aufgabe: eine Karte, eine Überschrift, ein Feld, ein
 * Knopf. Seit dem 26.10.2026 sitzen sie auf derselben Bühne wie Anmeldung und
 * Registrierung (AuthHero, auth-neu.css), damit der Weg "Passwort vergessen?"
 * nicht mitten im Ablauf das Design wechselt.
 */

import { ReactNode } from 'react';
import { AuthHero } from '@/components/AuthHero';

export function KontoKarte({
    titel,
    unterzeile,
    fehler,
    erfolg,
    children,
    fusszeile,
}: {
    titel: string;
    unterzeile: string;
    fehler?: string;
    erfolg?: string;
    children: ReactNode;
    fusszeile?: ReactNode;
}) {
    return (
        <main role="main" aria-label={titel} className="lg">
            <AuthHero />

            <section className="lg-card" aria-labelledby="lg-h1">
                <div className="lg-form">
                    <h1 id="lg-h1" className="lg-h1 lg-in" style={{ ['--d' as any]: '.45s' }}>{titel}</h1>
                    <p className="lg-lead lg-in" style={{ ['--d' as any]: '.52s' }}>{unterzeile}</p>

                    {fehler && (
                        <div role="alert" aria-live="assertive" className="lg-alert">
                            <svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8" /><path d="M10 6v5M10 14h.01" /></svg>
                            <span>{fehler}</span>
                        </div>
                    )}

                    {erfolg && (
                        <div role="status" aria-live="polite" className="lg-alert lg-ok">
                            <svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8" /><path d="M6.5 10.5l2.5 2.5 4.5-5.5" /></svg>
                            <span>{erfolg}</span>
                        </div>
                    )}

                    <div className="lg-konto lg-in" style={{ ['--d' as any]: '.6s' }}>{children}</div>

                    {fusszeile && (
                        <p className="lg-foot lg-in" style={{ ['--d' as any]: '.8s' }}>{fusszeile}</p>
                    )}
                </div>
            </section>
        </main>
    );
}

/** Der Knopf der Kontoseiten. Gleiche Gestalt wie der Anmeldeknopf. */
export function KontoKnopf({
    laeuft,
    laeuftText,
    children,
    disabled,
}: {
    laeuft: boolean;
    laeuftText: string;
    children: ReactNode;
    disabled?: boolean;
}) {
    return (
        <button type="submit" disabled={laeuft || disabled} className="lg-submit">
            {laeuft ? laeuftText : children}
        </button>
    );
}

export const API_BASIS = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

/**
 * Die Fehlermeldung des Backends herausholen.
 *
 * FastAPI antwortet bei Prüffehlern mit `detail` als Liste von Objekten, sonst
 * mit einer Zeichenkette. Wer das nicht trennt, zeigt dem Nutzer
 * "[object Object]" — im Zweifel lieber ein allgemeiner Satz.
 */
export async function fehlertext(antwort: Response, rueckfall: string): Promise<string> {
    try {
        const daten = await antwort.json();
        if (typeof daten?.detail === 'string') return daten.detail;
    } catch {
        /* keine oder kaputte JSON-Antwort */
    }
    return rueckfall;
}
