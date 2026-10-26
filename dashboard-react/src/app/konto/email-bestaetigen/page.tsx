'use client';

/**
 * E-Mail-Adresse bestätigen.
 *
 * Hierhin zeigt der Link aus der Registrierungsmail
 * (`/konto/email-bestaetigen?token=...`).
 *
 * Die Seite löst den Token beim Aufruf selbst ein und zeigt nur das Ergebnis.
 * Ein Knopf "jetzt bestätigen" wäre ein Klick ohne Entscheidung: wer den Link
 * geöffnet hat, hat sich bereits entschieden.
 */

import { Suspense, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { KontoKarte, API_BASIS, fehlertext } from '@/components/konto/KontoKarte';

type Stand = 'laeuft' | 'fertig' | 'fehler' | 'kein-token';

function EmailBestaetigen() {
    const token = useSearchParams().get('token') || '';
    const [stand, setStand] = useState<Stand>(token ? 'laeuft' : 'kein-token');
    const [fehler, setFehler] = useState('');
    // React 18 ruft Effekte im Entwicklungsmodus doppelt auf. Der Token gilt
    // genau einmal — ohne diese Sperre bestaetigt der erste Aufruf und der
    // zweite meldet dem Nutzer "bereits benutzt".
    const schonGelaufen = useRef(false);

    useEffect(() => {
        if (!token || schonGelaufen.current) return;
        schonGelaufen.current = true;

        (async () => {
            try {
                const antwort = await fetch(`${API_BASIS}/api/auth/email-bestaetigen`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token }),
                });
                if (antwort.ok) {
                    setStand('fertig');
                } else {
                    setFehler(await fehlertext(antwort, 'Die Bestätigung hat nicht geklappt.'));
                    setStand('fehler');
                }
            } catch {
                setFehler('Der Server war nicht erreichbar. Bitte später noch einmal versuchen.');
                setStand('fehler');
            }
        })();
    }, [token]);

    const zurAnmeldung = (
        <a href="/login" className="lg-link lg-link-b">Zur Anmeldung</a>
    );

    if (stand === 'kein-token') {
        return (
            <KontoKarte
                titel="Link unvollständig"
                unterzeile="In dieser Adresse fehlt der Teil, der Sie ausweist. Vermutlich hat das E-Mail-Programm den Link umgebrochen."
                fehler="Kein gültiger Bestätigungslink."
                fusszeile={zurAnmeldung}
            >
                <p className="lg-body">
                    Melden Sie sich an und fordern Sie in den Einstellungen eine neue
                    Bestätigungsmail an.
                </p>
            </KontoKarte>
        );
    }

    if (stand === 'laeuft') {
        return (
            <KontoKarte titel="Einen Moment" unterzeile="Die Bestätigung wird geprüft.">
                <div className="lg-body lg-wait" role="status">
                    <span className="lg-spinner" aria-hidden="true" />
                    Wird geprüft...
                </div>
            </KontoKarte>
        );
    }

    if (stand === 'fehler') {
        return (
            <KontoKarte
                titel="Bestätigung fehlgeschlagen"
                unterzeile="Der Link war entweder abgelaufen oder wurde schon einmal benutzt."
                fehler={fehler}
                fusszeile={zurAnmeldung}
            >
                <p className="lg-body">
                    Ein Bestätigungslink gilt 72 Stunden und lässt sich einmal verwenden. Melden
                    Sie sich an und fordern Sie in den Einstellungen eine neue Mail an. Ist Ihre
                    Adresse bereits bestätigt, brauchen Sie nichts weiter zu tun.
                </p>
            </KontoKarte>
        );
    }

    return (
        <KontoKarte
            titel="Adresse bestätigt"
            unterzeile="Danke. Hinweise zu Fristen und Rechtsänderungen erreichen Sie jetzt zuverlässig."
            erfolg="Ihre E-Mail-Adresse ist bestätigt."
            fusszeile={zurAnmeldung}
        >
            <p className="lg-body">Sie können dieses Fenster schließen.</p>
        </KontoKarte>
    );
}

export default function EmailBestaetigenPage() {
    return (
        <Suspense fallback={null}>
            <EmailBestaetigen />
        </Suspense>
    );
}
