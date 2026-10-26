'use client';

/**
 * Passwort vergessen — Schritt 1: Adresse eingeben.
 *
 * Bis zum 10.09.2026 verwies die Anmeldeseite hier auf
 * `mailto:support@complyo.de`. Ein vergessenes Passwort war damit ein
 * Support-Vorgang, und im Backend gab es überhaupt keinen Weg, eines
 * zurückzusetzen.
 *
 * Wichtig an dieser Seite: **die Antwort ist immer dieselbe.** Ob es das Konto
 * gibt oder nicht, steht nicht auf dem Schirm — sonst wäre das Formular ein
 * Verzeichnis, mit dem sich prüfen lässt, wer complyo-Kunde ist.
 */

import { useState } from 'react';
import { KontoKarte, KontoKnopf, API_BASIS } from '@/components/konto/KontoKarte';

export default function PasswortVergessenPage() {
    const [email, setEmail] = useState('');
    const [laeuft, setLaeuft] = useState(false);
    const [gesendet, setGesendet] = useState(false);
    const [fehler, setFehler] = useState('');

    const absenden = async (e: React.FormEvent) => {
        e.preventDefault();
        setFehler('');
        setLaeuft(true);
        try {
            const antwort = await fetch(`${API_BASIS}/api/auth/passwort-vergessen`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });
            if (antwort.status === 429) {
                setFehler('Zu viele Versuche. Bitte in einer Stunde noch einmal probieren.');
            } else {
                // Auch bei einem Fehler im Hintergrund dieselbe Anzeige: die
                // Route antwortet bewusst immer gleich, und die Oberflaeche
                // darf das nicht unterlaufen.
                setGesendet(true);
            }
        } catch {
            setFehler('Die Anfrage konnte nicht gesendet werden. Besteht eine Verbindung?');
        } finally {
            setLaeuft(false);
        }
    };

    if (gesendet) {
        return (
            <KontoKarte
                titel="E-Mail unterwegs"
                unterzeile="Falls ein Konto zu dieser Adresse besteht, liegt gleich eine Nachricht mit einem Link im Postfach. Der Link gilt eine Stunde und lässt sich einmal verwenden."
                erfolg={`Anfrage für ${email} entgegengenommen.`}
                fusszeile={
                    <a href="/login" className="lg-link lg-link-b">Zurück zur Anmeldung</a>
                }
            >
                <p className="lg-body">
                    Nichts angekommen? Dann sehen Sie bitte im Spam-Ordner nach. Kommt auch
                    dort nichts an, besteht zu dieser Adresse vermutlich kein Konto.
                </p>
            </KontoKarte>
        );
    }

    return (
        <KontoKarte
            titel="Passwort vergessen"
            unterzeile="Wir schicken Ihnen einen Link, mit dem Sie ein neues Passwort setzen können."
            fehler={fehler}
            fusszeile={
                <a href="/login" className="lg-link lg-link-b">Zurück zur Anmeldung</a>
            }
        >
            <form onSubmit={absenden}>
                <div className="lg-field">
                    <label htmlFor="email">E-Mail</label>
                    <input
                        id="email"
                        type="email"
                        autoComplete="username"
                        autoFocus
                        placeholder="Ihre E-Mail-Adresse"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        disabled={laeuft}
                        className="lg-input"
                    />
                </div>

                <KontoKnopf laeuft={laeuft} laeuftText="Wird gesendet...">
                    Link anfordern
                </KontoKnopf>
            </form>
        </KontoKarte>
    );
}
