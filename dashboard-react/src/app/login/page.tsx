'use client';

import { useState, useEffect } from 'react';
import { useAuth, ZweiterFaktorNoetig } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { LogIn, Loader2, AlertCircle, Lock, Mail, Eye, EyeOff, ArrowRight, CheckCircle2, ShieldCheck, KeyRound } from 'lucide-react';
import SocialLoginButtons from '@/components/SocialLoginButtons';
import { Logo } from '@/components/Logo';
import { zielAusAdresse } from '@/lib/weiterleitung';
// Gemeinsame Gestaltung mit der Registrierung. Vorher lagen Verlauf,
// Partikelfeld und Kartenstil doppelt vor — heute gleich, in drei Monaten
// nicht mehr. Eine Quelle, damit die beiden Seiten nicht auseinanderlaufen.
import {
    AuthBackground, AuthVertrauen, AUTH_KARTE, AUTH_VERLAUF, feldStil,
} from '@/components/AuthBackground';

const loadingMessages = [
    "Sicherheitsprotokolle werden geladen...",
    "Compliance-Daten werden abgerufen...",
    "Ihre Identität wird verifiziert...",
    "Dashboard wird vorbereitet...",
    "Fast geschafft..."
];

export default function LoginPage() {
    const { login, isAuthenticated } = useAuth();
    const router = useRouter();

    const [formData, setFormData] = useState({ email: '', password: '' });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState(loadingMessages[0]);
    const [loadingProgress, setLoadingProgress] = useState(0);
    const [emailFocused, setEmailFocused] = useState(false);
    const [passwordFocused, setPasswordFocused] = useState(false);
    // Zweiter Faktor. `codeSchritt` schaltet die Karte um: statt E-Mail und
    // Passwort steht dann nur noch das Codefeld da. Passwort und Adresse
    // bleiben im Zustand, weil die Anmeldung beides zusammen mit dem Code
    // schickt — der Nutzer soll nicht alles noch einmal tippen.
    const [codeSchritt, setCodeSchritt] = useState(false);
    const [code, setCode] = useState('');
    const [codeFocused, setCodeFocused] = useState(false);


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
    // Vorher stand hier fest `router.push('/')`: der `redirect`-Parameter, den
    // Middleware und Anmeldewache setzen, wurde nie gelesen. `replace` statt
    // `push`, damit "Zurueck" nicht wieder auf dieser Seite landet und von
    // hier sofort erneut weitergeschickt wird.
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
            setLoadingProgress(100);
            setTimeout(() => router.replace(zielAusAdresse()), 500);
        } catch (error: any) {
            if (error instanceof ZweiterFaktorNoetig) {
                // Passwort stimmt, es fehlt nur der zweite Faktor. Kein Fehler
                // beim ersten Mal — nur ein Schritt weiter.
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

    const emailHasValue = formData.email.length > 0;
    const passwordHasValue = formData.password.length > 0;

    return (
        <main
            role="main"
            aria-label="Login"
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

                <section
                    className="relative rounded-2xl p-8 overflow-hidden"
                    style={AUTH_KARTE}
                >
                    <div className="absolute top-0 left-0 right-0 h-px" style={{ background: 'linear-gradient(90deg, transparent, rgba(99,179,237,0.3), transparent)' }} />

                    <div className="mb-7">
                        <h1 className="text-2xl font-semibold text-white mb-1.5 tracking-tight">
                            {codeSchritt ? 'Noch ein Schritt' : 'Willkommen zurück'}
                        </h1>
                        <p className="text-sm" style={{ color: 'rgba(148,163,184,0.6)' }}>
                            {codeSchritt
                                ? 'Bitte den sechsstelligen Code aus Ihrer Authenticator-App eingeben.'
                                : 'Melden Sie sich an, um auf Ihr Dashboard zuzugreifen'}
                        </p>
                    </div>

                    {error && (
                        <div
                            role="alert"
                            aria-live="assertive"
                            className="mb-5 p-3.5 rounded-xl flex items-start gap-3 text-sm animate-errorfade"
                            style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}
                        >
                            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: '#f87171' }} />
                            <span style={{ color: '#fca5a5' }}>{error}</span>
                        </div>
                    )}

                    {isSubmitting && (
                        <div className="mb-5 space-y-2.5">
                            <div className="flex items-center gap-2.5">
                                <Loader2 className="w-3.5 h-3.5 animate-spin" style={{ color: '#60a5fa' }} />
                                <span className="text-xs" style={{ color: '#60a5fa' }}>{loadingMessage}</span>
                            </div>
                            <div className="h-0.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                                <div
                                    className="h-full rounded-full transition-all duration-300"
                                    style={{
                                        width: `${loadingProgress}%`,
                                        background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
                                        boxShadow: '0 0 8px rgba(59,130,246,0.5)',
                                    }}
                                />
                            </div>
                        </div>
                    )}

                    {!codeSchritt && (
                        <div className="mb-5">
                            <SocialLoginButtons mode="login" />
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {codeSchritt && (
                            <>
                                <div
                                    className="p-3.5 rounded-xl flex items-start gap-3 text-sm"
                                    style={{ background: 'rgba(52,211,153,0.06)', border: '1px solid rgba(52,211,153,0.18)' }}
                                >
                                    <ShieldCheck className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: '#34d399' }} />
                                    <span style={{ color: 'rgba(148,163,184,0.85)' }}>
                                        Angemeldet als <span className="text-white">{formData.email}</span>
                                    </span>
                                </div>

                                <div className="relative">
                                    <label
                                        htmlFor="code"
                                        className="block text-xs font-medium mb-2 transition-colors duration-200"
                                        style={{ color: codeFocused ? '#60a5fa' : 'rgba(148,163,184,0.7)' }}
                                    >
                                        Code aus der App
                                    </label>
                                    <div className="relative">
                                        <KeyRound
                                            className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors duration-200"
                                            style={{ color: codeFocused ? '#60a5fa' : 'rgba(100,116,139,0.7)' }}
                                        />
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
                                            onFocus={() => setCodeFocused(true)}
                                            onBlur={() => setCodeFocused(false)}
                                            required
                                            disabled={isSubmitting}
                                            className="w-full pl-10 pr-4 py-3 rounded-xl text-sm text-white placeholder-slate-600 outline-none transition-all duration-200 disabled:opacity-40 tracking-[0.3em]"
                                            style={feldStil(codeFocused)}
                                        />
                                    </div>
                                    <p className="mt-2 text-xs leading-relaxed" style={{ color: 'rgba(100,116,139,0.75)' }}>
                                        Kein Zugriff auf die App? Hier funktioniert auch einer Ihrer
                                        Wiederherstellungscodes.
                                    </p>
                                </div>
                            </>
                        )}

                        <div className="relative" hidden={codeSchritt}>
                            <label
                                htmlFor="email"
                                className="block text-xs font-medium mb-2 transition-colors duration-200"
                                style={{ color: emailFocused ? '#60a5fa' : 'rgba(148,163,184,0.7)' }}
                            >
                                E-Mail-Adresse
                            </label>
                            <div className="relative">
                                <Mail
                                    className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors duration-200"
                                    style={{ color: emailFocused ? '#60a5fa' : 'rgba(100,116,139,0.7)' }}
                                />
                                <input
                                    id="email"
                                    autoComplete="username"
                                    type="email"
                                    placeholder="ihre@email.com"
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                    onFocus={() => setEmailFocused(true)}
                                    onBlur={() => setEmailFocused(false)}
                                    required={!codeSchritt}
                                    disabled={isSubmitting}
                                    className="w-full pl-10 pr-10 py-3 rounded-xl text-sm text-white placeholder-slate-600 outline-none transition-all duration-200 disabled:opacity-40"
                                    style={feldStil(emailFocused)}
                                />
                                {emailHasValue && !isSubmitting && (
                                    <CheckCircle2 className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#34d399' }} />
                                )}
                            </div>
                        </div>

                        <div className="relative" hidden={codeSchritt}>
                            <div className="flex items-center justify-between mb-2">
                                <label
                                    htmlFor="password"
                                    className="block text-xs font-medium transition-colors duration-200"
                                    style={{ color: passwordFocused ? '#60a5fa' : 'rgba(148,163,184,0.7)' }}
                                >
                                    Passwort
                                </label>
                                <a
                                    href="/passwort-vergessen"
                                    className="text-xs transition-colors duration-200 hover:opacity-80"
                                    style={{ color: 'rgba(96,165,250,0.6)' }}
                                >
                                    Passwort vergessen?
                                </a>
                            </div>
                            <div className="relative">
                                <Lock
                                    className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors duration-200"
                                    style={{ color: passwordFocused ? '#60a5fa' : 'rgba(100,116,139,0.7)' }}
                                />
                                <input
                                    id="password"
                                    autoComplete="current-password"
                                    type={showPassword ? 'text' : 'password'}
                                    placeholder="••••••••••••"
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                    onFocus={() => setPasswordFocused(true)}
                                    onBlur={() => setPasswordFocused(false)}
                                    required={!codeSchritt}
                                    disabled={isSubmitting}
                                    className="w-full pl-10 pr-10 py-3 rounded-xl text-sm text-white placeholder-slate-600 outline-none transition-all duration-200 disabled:opacity-40"
                                    style={feldStil(passwordFocused)}
                                />
                                {passwordHasValue && (
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-3.5 top-1/2 -translate-y-1/2 transition-colors duration-200 hover:opacity-80"
                                        style={{ color: 'rgba(100,116,139,0.7)' }}
                                        tabIndex={-1}
                                    >
                                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                    </button>
                                )}
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="w-full py-3 rounded-xl text-sm font-semibold text-white flex items-center justify-center gap-2.5 transition-all duration-300 mt-2 group relative overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed"
                            style={{
                                background: 'linear-gradient(135deg, #2563eb 0%, #4f46e5 100%)',
                                boxShadow: isSubmitting ? 'none' : '0 4px 20px rgba(37,99,235,0.3)',
                            }}
                        >
                            <div
                                className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                                style={{ background: 'linear-gradient(135deg, #1d4ed8 0%, #4338ca 100%)' }}
                            />
                            <span className="relative flex items-center gap-2.5">
                                {isSubmitting ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        Anmeldung läuft...
                                    </>
                                ) : (
                                    <>
                                        {codeSchritt ? <ShieldCheck className="w-4 h-4" /> : <LogIn className="w-4 h-4" />}
                                        {codeSchritt ? 'Bestätigen' : 'Anmelden'}
                                        <ArrowRight className="w-3.5 h-3.5 opacity-0 -ml-1 group-hover:opacity-100 group-hover:ml-0 transition-all duration-200" />
                                    </>
                                )}
                            </span>
                        </button>

                        {codeSchritt && !isSubmitting && (
                            <button
                                type="button"
                                onClick={() => { setCodeSchritt(false); setCode(''); setError(''); }}
                                className="w-full text-xs transition-colors duration-200 hover:opacity-80"
                                style={{ color: 'rgba(148,163,184,0.6)' }}
                            >
                                Zurück zur Anmeldung
                            </button>
                        )}
                    </form>

                    <div className="mt-6 pt-5" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                        <p className="text-center text-xs" style={{ color: 'rgba(100,116,139,0.6)' }}>
                            Noch kein Konto?{' '}
                            <a
                                href="/register"
                                className="font-medium transition-colors duration-200 hover:opacity-80"
                                style={{ color: '#60a5fa' }}
                            >
                                Jetzt registrieren
                            </a>
                        </p>
                    </div>
                </section>

                <AuthVertrauen />
            </div>

            <style jsx>{`
                @keyframes errorfade {
                    from { opacity: 0; transform: translateY(-4px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .animate-errorfade {
                    animation: errorfade 0.2s ease-out forwards;
                }
            `}</style>
        </main>
    );
}
