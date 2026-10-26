'use client';

import { useState, useEffect, useRef } from 'react';
import Image from 'next/image';
import { useAuth, ZweiterFaktorNoetig } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import SocialLoginButtons from '@/components/SocialLoginButtons';
import { isFirebaseEnabled } from '@/lib/firebase';
import { zielAusAdresse } from '@/lib/weiterleitung';
import './login.css';

const loadingMessages = [
    'Sicherheitsprotokolle werden geladen...',
    'Compliance-Daten werden abgerufen...',
    'Ihre Identität wird verifiziert...',
    'Dashboard wird vorbereitet...',
    'Fast geschafft...',
];

// Die drei Aussagen hinter den Punkten links. Jede beschreibt, was der Scan
// tatsaechlich misst, keinen Zustand der Kundenseite.
const AUSSAGEN = [
    {
        zeilen: ['Prüfen. Beheben.', 'Nachweisen.'],
        text: ['Complyo misst, was Ihre Website heute tatsächlich lädt', 'und zeigt, was sich davon beheben lässt.'],
    },
    {
        zeilen: ['Cookies im Griff.', 'Ohne Rätselraten.'],
        text: ['Der Scan öffnet Ihre Seite im Browser und zeigt,', 'welche Dienste wirklich geladen werden.'],
    },
    {
        zeilen: ['Barrierefreiheit,', 'Seite für Seite.'],
        text: ['Die Prüfung nach WCAG zeigt, an welchen Stellen', 'Besucher auf Ihrer Website scheitern.'],
    },
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

    const [aussage, setAussage] = useState(0);
    const [umgeschaltet, setUmgeschaltet] = useState(false);

    // Das Video nur dort, wo Bewegung erlaubt ist. Das Standbild steht immer.
    const [videoErlaubt, setVideoErlaubt] = useState(false);
    const [videoBereit, setVideoBereit] = useState(false);
    const videoRef = (v: HTMLVideoElement | null) => {
        // Bei zwischengespeichertem Video feuert loadeddata, bevor React den
        // Handler anhaengt, deshalb zusaetzlich der Stand beim Einhaengen.
        if (v && v.readyState >= 2) setVideoBereit(true);
    };

    useEffect(() => {
        const ruhe = window.matchMedia?.('(prefers-reduced-motion: reduce)');
        if (!ruhe?.matches) setVideoErlaubt(true);
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

    const a = AUSSAGEN[aussage];

    return (
        <main role="main" aria-label="Login" className="lg">
            <div className="lg-plate" aria-hidden="true" />
            {videoErlaubt && (
                <video
                    ref={videoRef}
                    className={`lg-video${videoBereit ? ' is-ready' : ''}`}
                    src="/login/loop.mp4"
                    autoPlay
                    muted
                    loop
                    playsInline
                    preload="auto"
                    aria-hidden="true"
                    tabIndex={-1}
                    onLoadedData={() => setVideoBereit(true)}
                />
            )}
            <div className="lg-shade lg-shade-l" aria-hidden="true" />
            <div className="lg-shade lg-shade-t" aria-hidden="true" />
            <div className="lg-shade lg-shade-b" aria-hidden="true" />

            <section className="lg-hero" aria-label="Complyo">
                <div className="lg-bar">
                    <a href="https://complyo.de" className="lg-logo lg-in" style={{ ['--d' as any]: '.1s' }} aria-label="Complyo, zur Website">
                        <Image src="/logo-light-trim.png" alt="Complyo" width={852} height={287} priority />
                    </a>
                    <a href="https://complyo.de" className="lg-back lg-in" style={{ ['--d' as any]: '.18s' }}>
                        <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M16 10H4m0 0 5-5m-5 5 5 5" /></svg>
                        Zurück zur Website
                    </a>
                </div>

                <div className="lg-pitch">
                    <div key={aussage} className={umgeschaltet ? 'is-sw' : undefined}>
                        <h2 className="lg-title" aria-live="polite">
                            {a.zeilen.map((z, i) => (
                                <span className="lg-line" key={z}>
                                    <span style={{ ['--d' as any]: `${0.5 + i * 0.12}s` }}>{z}</span>
                                </span>
                            ))}
                        </h2>
                        <p className="lg-sub lg-in" style={{ ['--d' as any]: '.85s' }}>
                            {a.text[0]}<br />{a.text[1]}
                        </p>
                    </div>
                    <div className="lg-dots lg-in" style={{ ['--d' as any]: '1s' }} role="group" aria-label="Aussage wählen">
                        {AUSSAGEN.map((_, i) => (
                            <button
                                key={i}
                                type="button"
                                className={i === aussage ? 'is-active' : undefined}
                                aria-label={`Aussage ${i + 1} von ${AUSSAGEN.length}`}
                                aria-current={i === aussage ? 'true' : undefined}
                                onClick={() => { setAussage(i); setUmgeschaltet(true); }}
                            />
                        ))}
                    </div>
                </div>
            </section>

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
                                    <svg viewBox="0 0 24 24" aria-hidden="true">
                                        <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" />
                                        <circle cx="12" cy="12" r="3" />
                                        <path className={`lg-slash${showPassword ? ' is-on' : ''}`} d="M4 4l16 16" />
                                    </svg>
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
