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
import { Mail, Send, ArrowLeft } from 'lucide-react';
import { KontoKarte, KontoKnopf, API_BASIS } from '@/components/konto/KontoKarte';
import { feldStil } from '@/components/AuthBackground';

export default function PasswortVergessenPage() {
    const [email, setEmail] = useState('');
    const [fokussiert, setFokussiert] = useState(false);
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
                    <a href="/login" className="font-medium hover:opacity-80" style={{ color: '#60a5fa' }}>
                        Zurück zur Anmeldung
                    </a>
                }
            >
                <p className="text-sm leading-relaxed" style={{ color: 'rgba(148,163,184,0.7)' }}>
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
                <a href="/login" className="font-medium hover:opacity-80 inline-flex items-center gap-1.5" style={{ color: '#60a5fa' }}>
                    <ArrowLeft className="w-3 h-3" />
                    Zurück zur Anmeldung
                </a>
            }
        >
            <form onSubmit={absenden} className="space-y-4">
                <div className="relative">
                    <label
                        htmlFor="email"
                        className="block text-xs font-medium mb-2 transition-colors duration-200"
                        style={{ color: fokussiert ? '#60a5fa' : 'rgba(148,163,184,0.7)' }}
                    >
                        E-Mail-Adresse
                    </label>
                    <div className="relative">
                        <Mail
                            className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors duration-200"
                            style={{ color: fokussiert ? '#60a5fa' : 'rgba(100,116,139,0.7)' }}
                        />
                        <input
                            id="email"
                            type="email"
                            autoComplete="username"
                            autoFocus
                            placeholder="ihre@email.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            onFocus={() => setFokussiert(true)}
                            onBlur={() => setFokussiert(false)}
                            required
                            disabled={laeuft}
                            className="w-full pl-10 pr-4 py-3 rounded-xl text-sm text-white placeholder-slate-600 outline-none transition-all duration-200 disabled:opacity-40"
                            style={feldStil(fokussiert)}
                        />
                    </div>
                </div>

                <KontoKnopf laeuft={laeuft} laeuftText="Wird gesendet...">
                    <Send className="w-4 h-4" />
                    Link anfordern
                </KontoKnopf>
            </form>
        </KontoKarte>
    );
}
