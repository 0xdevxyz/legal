'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth, ZweiterFaktorNoetig } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import SocialLoginButtons from '@/components/SocialLoginButtons';
import { isFirebaseEnabled } from '@/lib/firebase';
import { zielAusAdresse } from '@/lib/weiterleitung';
import { AuthHero, PasswortAuge } from '@/components/AuthHero';

const loadingMessages = [
    'Sicherheitsprotokolle werden geladen...',
    'Compliance-Daten werden abgerufen...',
    'Ihre Identität wird verifiziert...',
    'Dashboard wird vorbereitet...',
    'Fast geschafft...',
];

const MERKEN_SCHLUESSEL = 'complyo_login_email';

function merkenLesen(): string {
    try { return window.localStorage.getItem(MERKEN_SCHLUESSEL) || ''; } catch { return ''; }
}
function merkenSchreiben(email: string | null) {
    try {
        if (email) window.localStorage.setItem(MERKEN_SCHLUESSEL, email);
        else window.localStorage.removeItem(MERKEN_SCHLUESSEL);
    } catch { /* Speicher gesperrt: dann eben nicht merken */ }
}

export default function LoginPage() {
    const { login, isAuthenticated } = useAuth();
    const router = useRouter();

    const [formData, setFormData] = useState({ email: '', password: '' });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [merken, setMerken] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState(loadingMessages[0]);
    const [loadingProgress, setLoadingProgress] = useState(0);
    // Zweiter Faktor. `codeSchritt` schaltet die Karte um: statt E-Mail und
    // Passwort steht dann nur noch das Codefeld da. Passwort und Adresse
    // bleiben im Zustand, weil die Anmeldung beides zusammen mit dem Code
    // schickt, der Nutzer soll nicht alles noch einmal tippen.
    const [codeSchritt, setCodeSchritt] = useState(false);
    const [code, setCode] = useState('');

    useEffect(() => {
        const gemerkt = merkenLesen();
        if (gemerkt) {
            setFormData((f) => ({ ...f, email: gemerkt }));
            setMerken(true);
        }
    }, []);

    useEffect(() => {
        if (!isSubmitting) return;
        let messageIndex = 0;
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 95) progress = 95;
            setLoadingProgress(progress);
        }, 200);
        const messageInterval = setInterval(() => {
            messageIndex = (messageIndex + 1) % loadingMessages.length;
            setLoadingMessage(loadingMessages[messageIndex]);
        }, 1500);
        return () => {
            clearInterval(progressInterval);
            clearInterval(messageInterval);
        };
    }, [isSubmitting]);

    // Schon angemeldet? Dann dorthin, wohin der Nutzer eigentlich wollte.
    // `replace` statt `push`, damit "Zurueck" nicht wieder auf dieser Seite
    // landet und von hier sofort erneut weitergeschickt wird.
    useEffect(() => {
        if (isAuthenticated && !isSubmitting) {
            router.replace(zielAusAdresse());
        }
    }, [isAuthenticated, isSubmitting, router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsSubmitting(true);
        setLoadingProgress(0);
        try {
            await login(formData.email, formData.password, codeSchritt ? code : undefined);
            merkenSchreiben(merken ? formData.email : null);
            setLoadingProgress(100);
            setTimeout(() => router.replace(zielAusAdresse()), 500);
        } catch (error: any) {
            if (error instanceof ZweiterFaktorNoetig) {
                // Passwort stimmt, es fehlt nur der zweite Faktor. Kein Fehler
                // beim ersten Mal, nur ein Schritt weiter.
                setCodeSchritt(true);
                setCode('');
                setError(error.codeWarFalsch ? error.message : '');
            } else {
                setError(error.message || 'Login fehlgeschlagen. Bitte prüfen Sie Ihre Zugangsdaten.');
            }
            setIsSubmitting(false);
            setLoadingProgress(0);
        }
    };

    return (
        <main role="main" aria-label="Login" className="lg">
            <AuthHero />

            <section className="lg-card" aria-labelledby="lg-h1">
                <div className="lg-form">
                    <h1 id="lg-h1" className="lg-h1 lg-in" style={{ ['--d' as any]: '.45s' }}>
                        {codeSchritt ? 'Noch ein Schritt' : 'Willkommen zurück!'}
                    </h1>
                    <p className="lg-lead lg-in" style={{ ['--d' as any]: '.52s' }}>
                        {codeSchritt
                            ? 'Bitte den sechsstelligen Code aus Ihrer Authenticator-App eingeben.'
                            : 'Melden Sie sich an, um Ihre Website-Prüfung fortzusetzen.'}
                    </p>

                    {error && (
                        <div role="alert" aria-live="assertive" className="lg-alert">
                            <svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8" /><path d="M10 6v5M10 14h.01" /></svg>
                            <span>{error}</span>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="lg-fields">
                        {codeSchritt && (
                            <>
                                <p className="lg-note">
                                    Angemeldet als <strong>{formData.email}</strong>
                                </p>
                                <div className="lg-field">
                                    <label htmlFor="code">Code aus der App</label>
                                    <input
                                        id="code"
                                        /* one-time-code laesst iOS und Android den Code aus der
                                           Zwischenablage bzw. der Mitteilung vorschlagen. */
                                        autoComplete="one-time-code"
                                        inputMode="text"
                                        autoFocus
                                        type="text"
                                        placeholder="123456"
                                        value={code}
                                        onChange={(e) => setCode(e.target.value)}
                                        required
                                        disabled={isSubmitting}
                                        className="lg-input lg-code"
                                    />
                                    <p className="lg-hint">
                                        Kein Zugriff auf die App? Hier funktioniert auch einer Ihrer Wiederherstellungscodes.
                                    </p>
                                </div>
                            </>
                        )}

                        <div className="lg-field lg-in" style={{ ['--d' as any]: '.6s' }} hidden={codeSchritt}>
                            <label htmlFor="email">E-Mail</label>
                            <input
                                id="email"
                                autoComplete="username"
                                type="email"
                                placeholder="Ihre E-Mail-Adresse"
                                value={formData.email}
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                required={!codeSchritt}
                                disabled={isSubmitting}
                                className="lg-input"
                            />
                        </div>

                        <div className="lg-field lg-in" style={{ ['--d' as any]: '.68s' }} hidden={codeSchritt}>
                            <label htmlFor="password">Passwort</label>
                            <div className="lg-pw">
                                <input
                                    id="password"
                                    autoComplete="current-password"
                                    type={showPassword ? 'text' : 'password'}
                                    placeholder="Ihr Passwort"
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                    required={!codeSchritt}
                                    disabled={isSubmitting}
                                    className="lg-input"
                                />
                                <button
                                    type="button"
                                    className="lg-eye"
                                    onClick={() => setShowPassword(!showPassword)}
                                    aria-label={showPassword ? 'Passwort verbergen' : 'Passwort anzeigen'}
                                    aria-pressed={showPassword}
                                >
                                    <PasswortAuge sichtbar={showPassword} />
                                </button>
                            </div>
                        </div>

                        <div className="lg-row lg-in" style={{ ['--d' as any]: '.76s' }} hidden={codeSchritt}>
                            <label className="lg-check">
                                <input
                                    type="checkbox"
                                    checked={merken}
                                    onChange={(e) => setMerken(e.target.checked)}
                                />
                                <span className="lg-box" aria-hidden="true">
                                    <svg viewBox="0 0 16 16"><path d="M3.5 8.5l3 3 6-7" /></svg>
                                </span>
                                <span>E-Mail merken</span>
                            </label>
                            <a href="/passwort-vergessen" className="lg-link">Passwort vergessen?</a>
                        </div>

                        <button type="submit" disabled={isSubmitting} className="lg-submit lg-in" style={{ ['--d' as any]: '.84s' }}>
                            {isSubmitting ? 'Anmeldung läuft...' : codeSchritt ? 'Bestätigen' : 'Anmelden'}
                        </button>

                        {isSubmitting && (
                            <div className="lg-status" role="status">
                                <span>{loadingMessage}</span>
                                <div className="lg-bar-track"><div style={{ width: `${loadingProgress}%` }} /></div>
                            </div>
                        )}

                        {codeSchritt && !isSubmitting && (
                            <button
                                type="button"
                                className="lg-textbtn"
                                onClick={() => { setCodeSchritt(false); setCode(''); setError(''); }}
                            >
                                Zurück zur Anmeldung
                            </button>
                        )}
                    </form>

                    {!codeSchritt && isFirebaseEnabled && (
                        <>
                            <div className="lg-or lg-in" style={{ ['--d' as any]: '.92s' }}>
                                <span>Oder weiter mit:</span>
                            </div>
                            <div className="lg-in" style={{ ['--d' as any]: '.98s' }}>
                                <SocialLoginButtons mode="login" darstellung="pille" />
                            </div>
                        </>
                    )}

                    <p className="lg-foot lg-in" style={{ ['--d' as any]: '1.04s' }}>
                        Noch kein Konto? <a href="/register" className="lg-link lg-link-b">Jetzt registrieren</a>
                    </p>
                </div>
            </section>
        </main>
    );
}
