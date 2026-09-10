'use client';

/**
 * Passwort vergessen — Schritt 2: neues Passwort setzen.
 *
 * Hierhin zeigt der Link aus der Mail (`/konto/passwort-neu?token=...`).
 *
 * Die Passwortregel steht im Backend (backend/passwort_richtlinie.py) und wird
 * dort auch durchgesetzt. Was hier steht, ist ein Vorabhinweis, damit der
 * Nutzer nicht erst nach dem Absenden erfährt, was gefordert ist — bewusst
 * KEINE zweite Umsetzung derselben Regel. Zwei Regelwerke laufen auseinander,
 * und dann gilt das schwächere.
 */

import { Suspense, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Lock, Eye, EyeOff, KeyRound } from 'lucide-react';
import { KontoKarte, KontoKnopf, API_BASIS, fehlertext } from '@/components/konto/KontoKarte';
import { feldStil } from '@/components/AuthBackground';

const MIN_LAENGE = 12;

function PasswortNeu() {
    const suchparameter = useSearchParams();
    const router = useRouter();
    const token = suchparameter.get('token') || '';

    const [passwort, setPasswort] = useState('');
    const [sichtbar, setSichtbar] = useState(false);
    const [fokussiert, setFokussiert] = useState(false);
    const [laeuft, setLaeuft] = useState(false);
    const [fehler, setFehler] = useState('');
    const [fertig, setFertig] = useState(false);

    const absenden = async (e: React.FormEvent) => {
        e.preventDefault();
        setFehler('');
        setLaeuft(true);
        try {
            const antwort = await fetch(`${API_BASIS}/api/auth/passwort-neu`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, passwort }),
            });
            if (antwort.ok) {
                setFertig(true);
                // Kurz stehen lassen, damit die Bestaetigung gelesen werden
                // kann, dann zur Anmeldung. Automatisch anmelden waere hier
                // falsch: das Zuruecksetzen hat gerade alle Sitzungen beendet.
                setTimeout(() => router.push('/login'), 2500);
            } else {
                setFehler(await fehlertext(antwort, 'Das Passwort konnte nicht gesetzt werden.'));
            }
        } catch {
            setFehler('Die Anfrage konnte nicht gesendet werden. Besteht eine Verbindung?');
        } finally {
            setLaeuft(false);
        }
    };

    if (!token) {
        return (
            <KontoKarte
                titel="Link unvollständig"
                unterzeile="In dieser Adresse fehlt der Teil, der Sie ausweist. Vermutlich hat das E-Mail-Programm den Link umgebrochen."
                fehler="Kein gültiger Zurücksetz-Link."
                fusszeile={
                    <a href="/passwort-vergessen" className="font-medium hover:opacity-80" style={{ color: '#60a5fa' }}>
                        Neuen Link anfordern
                    </a>
                }
            >
                <p className="text-sm leading-relaxed" style={{ color: 'rgba(148,163,184,0.7)' }}>
                    Bitte den Link aus der Mail vollständig kopieren und in die Adresszeile
                    einfügen — oder gleich einen neuen anfordern.
                </p>
            </KontoKarte>
        );
    }

    if (fertig) {
        return (
            <KontoKarte
                titel="Passwort geändert"
                unterzeile="Alle bestehenden Sitzungen wurden beendet. Bitte melden Sie sich mit dem neuen Passwort an."
                erfolg="Das neue Passwort gilt ab sofort."
                fusszeile={
                    <a href="/login" className="font-medium hover:opacity-80" style={{ color: '#60a5fa' }}>
                        Zur Anmeldung
                    </a>
                }
            >
                <p className="text-sm leading-relaxed" style={{ color: 'rgba(148,163,184,0.7)' }}>
                    Sie werden gleich weitergeleitet. Falls nicht, hilft der Link unten.
                </p>
            </KontoKarte>
        );
    }

    const zuKurz = passwort.length > 0 && passwort.length < MIN_LAENGE;

    return (
        <KontoKarte
            titel="Neues Passwort setzen"
            unterzeile="Mit dem Speichern werden alle bestehenden Sitzungen dieses Kontos beendet."
            fehler={fehler}
        >
            <form onSubmit={absenden} className="space-y-4">
                <div className="relative">
                    <label
                        htmlFor="passwort"
                        className="block text-xs font-medium mb-2 transition-colors duration-200"
                        style={{ color: fokussiert ? '#60a5fa' : 'rgba(148,163,184,0.7)' }}
                    >
                        Neues Passwort
                    </label>
                    <div className="relative">
                        <Lock
                            className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors duration-200"
                            style={{ color: fokussiert ? '#60a5fa' : 'rgba(100,116,139,0.7)' }}
                        />
                        <input
                            id="passwort"
                            type={sichtbar ? 'text' : 'password'}
                            autoComplete="new-password"
                            autoFocus
                            placeholder="••••••••••••"
                            value={passwort}
                            onChange={(e) => setPasswort(e.target.value)}
                            onFocus={() => setFokussiert(true)}
                            onBlur={() => setFokussiert(false)}
                            required
                            disabled={laeuft}
                            className="w-full pl-10 pr-10 py-3 rounded-xl text-sm text-white placeholder-slate-600 outline-none transition-all duration-200 disabled:opacity-40"
                            style={feldStil(fokussiert)}
                        />
                        {passwort.length > 0 && (
                            <button
                                type="button"
                                onClick={() => setSichtbar(!sichtbar)}
                                className="absolute right-3.5 top-1/2 -translate-y-1/2 hover:opacity-80"
                                style={{ color: 'rgba(100,116,139,0.7)' }}
                                tabIndex={-1}
                                aria-label={sichtbar ? 'Passwort verbergen' : 'Passwort anzeigen'}
                            >
                                {sichtbar ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </button>
                        )}
                    </div>

                    <div
                        className="mt-3 p-3 rounded-xl text-xs leading-relaxed"
                        style={{
                            background: 'rgba(255,255,255,0.02)',
                            border: `1px solid ${zuKurz ? 'rgba(239,68,68,0.2)' : 'rgba(255,255,255,0.05)'}`,
                            color: 'rgba(148,163,184,0.75)',
                        }}
                    >
                        Mindestens {MIN_LAENGE} Zeichen. Vier zufällige Wörter hintereinander sind
                        sicherer und leichter zu merken als ein kurzes Passwort mit Sonderzeichen.
                        Nicht erlaubt sind verbreitete Passwörter, Tastaturreihen und Ihr eigener
                        Name.
                    </div>
                </div>

                <KontoKnopf laeuft={laeuft} laeuftText="Wird gespeichert..." disabled={passwort.length < MIN_LAENGE}>
                    <KeyRound className="w-4 h-4" />
                    Passwort speichern
                </KontoKnopf>
            </form>
        </KontoKarte>
    );
}

export default function PasswortNeuPage() {
    // useSearchParams verlangt in Next 14 eine Suspense-Grenze, sonst faellt
    // die ganze Seite auf Rendern im Browser zurueck (Build-Warnung, und die
    // Seite flackert).
    return (
        <Suspense fallback={null}>
            <PasswortNeu />
        </Suspense>
    );
}
