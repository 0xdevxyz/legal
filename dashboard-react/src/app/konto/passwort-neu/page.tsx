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
import { PasswortAuge } from '@/components/AuthHero';
import { KontoKarte, KontoKnopf, API_BASIS, fehlertext } from '@/components/konto/KontoKarte';

const MIN_LAENGE = 12;

function PasswortNeu() {
    const suchparameter = useSearchParams();
    const router = useRouter();
    const token = suchparameter.get('token') || '';

    const [passwort, setPasswort] = useState('');
    const [sichtbar, setSichtbar] = useState(false);
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
                    <a href="/passwort-vergessen" className="lg-link lg-link-b">Neuen Link anfordern</a>
                }
            >
                <p className="lg-body">
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
                    <a href="/login" className="lg-link lg-link-b">Zur Anmeldung</a>
                }
            >
                <p className="lg-body">
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
            <form onSubmit={absenden}>
                <div className="lg-field">
                    <label htmlFor="passwort">Neues Passwort</label>
                    <div className="lg-pw">
                        <input
                            id="passwort"
                            type={sichtbar ? 'text' : 'password'}
                            autoComplete="new-password"
                            autoFocus
                            placeholder={`Mindestens ${MIN_LAENGE} Zeichen`}
                            value={passwort}
                            onChange={(e) => setPasswort(e.target.value)}
                            required
                            disabled={laeuft}
                            className="lg-input"
                        />
                        <button
                            type="button"
                            className="lg-eye"
                            onClick={() => setSichtbar(!sichtbar)}
                            aria-label={sichtbar ? 'Passwort verbergen' : 'Passwort anzeigen'}
                            aria-pressed={sichtbar}
                        >
                            <PasswortAuge sichtbar={sichtbar} />
                        </button>
                    </div>

                    <p className={`lg-note${zuKurz ? ' is-warn' : ''}`}>
                        Mindestens {MIN_LAENGE} Zeichen. Vier zufällige Wörter hintereinander sind
                        sicherer und leichter zu merken als ein kurzes Passwort mit Sonderzeichen.
                        Nicht erlaubt sind verbreitete Passwörter, Tastaturreihen und Ihr eigener
                        Name.
                    </p>
                </div>

                <KontoKnopf laeuft={laeuft} laeuftText="Wird gespeichert..." disabled={passwort.length < MIN_LAENGE}>
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
