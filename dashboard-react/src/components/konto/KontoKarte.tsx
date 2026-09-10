'use client';

/**
 * Der gemeinsame Rahmen der Kontoseiten.
 *
 * Passwort vergessen, Passwort neu setzen und E-Mail bestätigen sind drei
 * Seiten mit derselben Aufgabe: eine Karte auf dunklem Grund, eine Überschrift,
 * ein Feld, ein Knopf. Anmeldung und Registrierung lagen bis Juli doppelt vor
 * und liefen auseinander; die Lehre steht als Kommentar in AuthBackground.tsx.
 * Deshalb hier von Anfang an eine Quelle für die drei neuen.
 */

import { ReactNode } from 'react';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { Logo } from '@/components/Logo';
import {
    AuthBackground, AuthVertrauen, AUTH_KARTE, AUTH_VERLAUF,
} from '@/components/AuthBackground';

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
        <main
            role="main"
            aria-label={titel}
            className="on-dark min-h-screen flex items-center justify-center relative overflow-hidden"
            style={{ background: AUTH_VERLAUF }}
        >
            <AuthBackground />

            <div className="relative w-full max-w-md mx-4 z-10">
                <div className="mb-8 text-center">
                    <div className="flex justify-center mb-4">
                        <Logo size="lg" variant="dark" />
                    </div>
                    <p className="text-sm" style={{ color: 'rgba(148,163,184,0.7)' }}>
                        Legal Compliance Platform
                    </p>
                </div>

                <section className="relative rounded-2xl p-8 overflow-hidden" style={AUTH_KARTE}>
                    <div
                        className="absolute top-0 left-0 right-0 h-px"
                        style={{ background: 'linear-gradient(90deg, transparent, rgba(99,179,237,0.3), transparent)' }}
                    />

                    <div className="mb-7">
                        <h1 className="text-2xl font-semibold text-white mb-1.5 tracking-tight">{titel}</h1>
                        <p className="text-sm leading-relaxed" style={{ color: 'rgba(148,163,184,0.6)' }}>
                            {unterzeile}
                        </p>
                    </div>

                    {fehler && (
                        <div
                            role="alert"
                            aria-live="assertive"
                            className="mb-5 p-3.5 rounded-xl flex items-start gap-3 text-sm"
                            style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}
                        >
                            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: '#f87171' }} />
                            <span style={{ color: '#fca5a5' }}>{fehler}</span>
                        </div>
                    )}

                    {erfolg && (
                        <div
                            role="status"
                            aria-live="polite"
                            className="mb-5 p-3.5 rounded-xl flex items-start gap-3 text-sm"
                            style={{ background: 'rgba(52,211,153,0.08)', border: '1px solid rgba(52,211,153,0.2)' }}
                        >
                            <CheckCircle2 className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: '#34d399' }} />
                            <span style={{ color: '#6ee7b7' }}>{erfolg}</span>
                        </div>
                    )}

                    {children}

                    {fusszeile && (
                        <div className="mt-6 pt-5" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                            <p className="text-center text-xs" style={{ color: 'rgba(100,116,139,0.6)' }}>
                                {fusszeile}
                            </p>
                        </div>
                    )}
                </section>

                <AuthVertrauen />
            </div>
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
        <button
            type="submit"
            disabled={laeuft || disabled}
            className="w-full py-3 rounded-xl text-sm font-semibold text-white flex items-center justify-center gap-2.5 transition-all duration-300 mt-2 group relative overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
                background: 'linear-gradient(135deg, #2563eb 0%, #4f46e5 100%)',
                boxShadow: laeuft ? 'none' : '0 4px 20px rgba(37,99,235,0.3)',
            }}
        >
            <div
                className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                style={{ background: 'linear-gradient(135deg, #1d4ed8 0%, #4338ca 100%)' }}
            />
            <span className="relative flex items-center gap-2.5">
                {laeuft ? (
                    <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        {laeuftText}
                    </>
                ) : (
                    children
                )}
            </span>
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
