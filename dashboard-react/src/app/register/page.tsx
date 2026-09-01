'use client';

import { useState, Suspense, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter, useSearchParams } from 'next/navigation';
import {
    Shield, CheckCircle, Loader2, AlertCircle, Eye, FileText, BarChart3,
    Mail, Lock, User, Building2, ArrowRight, CheckCircle2, EyeOff,
} from 'lucide-react';
import SocialLoginButtons from '@/components/SocialLoginButtons';
import { Logo } from '@/components/Logo';
import { apiClient } from '@/lib/api-client';
import {
    AuthBackground, AuthVertrauen, AUTH_KARTE, AUTH_VERLAUF, feldStil,
} from '@/components/AuthBackground';

const MODULES = [
    { id: 'cookie', name: 'Cookie & DSGVO', icon: Shield, description: 'Cookie-Banner, Consent-Management' },
    { id: 'accessibility', name: 'Barrierefreiheit', icon: Eye, description: 'WCAG 2.1 AA Scanner & Fixes' },
    { id: 'legal_texts', name: 'Rechtliche Texte', icon: FileText, description: 'Impressum, Datenschutz, AGB' },
    { id: 'monitoring', name: 'Monitoring', icon: BarChart3, description: 'Automatische Scans & Alerts' },
];

const TARIFE = [
    { id: 'free', name: 'Free', price: '0 €', hint: '1 Fix' },
    { id: 'single', name: 'Einzelsäule', price: '19 €/Monat', hint: 'je Säule' },
    { id: 'pro', name: 'Pro', price: '49 €/Monat', hint: '1 Domain', popular: true },
    { id: 'agency', name: 'Agentur', price: '299 €/Monat', hint: '25 Projekte' },
    { id: 'monitor', name: 'Monitoring', price: '19 €/Monat', hint: 'bis 10 Websites' },
];

// Nur diese Kennungen darf ?plan= setzen. Vorher wurde der Parameter roh
// uebernommen: ?plan=monitor war hier unbekannt, fiel in den Single-Zweig
// und waehlte alle vier Saeulen vor. Der Landing-Knopf "Monitoring buchen,
// 19 EUR" landete so bei 76 EUR/Monat unter "Einzelne Saeulen" (01.09.2026).
const BEKANNTE_TARIFE = new Set(TARIFE.map(t => t.id));

function RegisterForm() {
    const { register } = useAuth();
    const router = useRouter();
    const searchParams = useSearchParams();
    const planParam = searchParams?.get('plan') || 'pro';
    const initialPlan = BEKANNTE_TARIFE.has(planParam) ? planParam : 'pro';
    const initialModule = searchParams?.get('module') || '';

    const [plan, setPlan] = useState(initialPlan);
    const [selectedModules, setSelectedModules] = useState<string[]>(
        initialModule
            ? [initialModule]
            : (initialPlan === 'pro' || initialPlan === 'agency'
                ? ['cookie', 'accessibility', 'legal_texts', 'monitoring']
                : [])
    );

    const [formData, setFormData] = useState({
        email: '',
        password: '',
        full_name: '',
        company: '',
    });

    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    // Fokuszustaende je Feld — dieselbe Rueckmeldung wie auf der Anmeldeseite.
    const [fokus, setFokus] = useState<string | null>(null);

    useEffect(() => {
        if (plan === 'pro' || plan === 'agency') {
            setSelectedModules(['cookie', 'accessibility', 'legal_texts', 'monitoring']);
        }
    }, [plan]);

    const toggleModule = (moduleId: string) => {
        if (plan !== 'single') return;
        setSelectedModules(prev =>
            prev.includes(moduleId)
                ? prev.filter(m => m !== moduleId)
                : [...prev, moduleId]
        );
    };

    const calculatePrice = () => {
        if (plan === 'free') return { monthly: 0, yearly: 0, setup: 0 };
        if (plan === 'agency') return { monthly: 299, yearly: 2990, setup: 0 };
        if (plan === 'pro') return { monthly: 49, yearly: 490, setup: 0 };
        if (plan === 'monitor') return { monthly: 19, yearly: 190, setup: 0 };
        return { monthly: selectedModules.length * 19, yearly: 0, setup: 0 };
    };

    const price = calculatePrice();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (plan === 'single' && selectedModules.length === 0) {
            setError('Bitte wählen Sie mindestens ein Modul aus.');
            return;
        }

        setIsSubmitting(true);

        try {
            await register({ ...formData, plan, modules: selectedModules });

            // Free-Tarif: kein Checkout, direkt ins Dashboard.
            if (plan === 'free') {
                router.push('/dashboard');
                return;
            }

            const checkoutData = await apiClient.post('/api/stripe/create-checkout', {
                plan: plan,
                modules: selectedModules,
                billing_period: 'monthly',
                success_url: `${window.location.origin}/subscription?success=true&session_id={CHECKOUT_SESSION_ID}`,
                cancel_url: `${window.location.origin}/register`
            }) as any;

            if (!checkoutData.checkout_url) {
                throw new Error('Fehler beim Erstellen der Zahlungssitzung');
            }

            window.location.href = checkoutData.checkout_url;
        } catch (error: any) {
            console.error('Registration error:', error);
            setError(error.message || 'Registrierung fehlgeschlagen. Bitte versuchen Sie es erneut.');
            setIsSubmitting(false);
        }
    };

    const getPlanName = () => {
        if (plan === 'free') return 'Free';
        if (plan === 'agency') return 'Agentur';
        if (plan === 'pro') return 'Pro-Paket';
        if (plan === 'monitor') return 'Monitoring';
        return `Einzelne Säule${selectedModules.length > 1 ? 'n' : ''}`;
    };

    const getPriceDisplay = () => {
        if (plan === 'free') return 'Kostenlos';
        if (price.yearly > 0) return `${price.monthly}€/Monat oder ${price.yearly}€/Jahr`;
        return `${price.monthly}€/Monat`;
    };

    // Ein Feld — Beschriftung, Symbol, Fokuszustand. Vier Mal derselbe Aufbau
    // wie auf der Anmeldeseite, deshalb hier einmal beschrieben.
    //
    // BEWUSST eine Funktion, die JSX zurueckgibt, und KEINE Komponente:
    // eine Komponente, die im Rumpf einer anderen Komponente definiert wird,
    // ist bei jedem Rendern ein neuer Typ. React haengt das Eingabefeld dann
    // nach jedem Tastendruck ab und neu an — der Fokus waere nach jedem
    // Zeichen weg. Als Funktionsaufruf landet das JSX direkt im Baum und
    // nichts wird neu erzeugt.
    const feld = ({ id, label, typ, symbol: Symbol, platzhalter, autoComplete, pflicht, hinweis }: {
        id: 'email' | 'password' | 'full_name' | 'company';
        label: string;
        typ: string;
        symbol: React.ElementType;
        platzhalter: string;
        autoComplete: string;
        pflicht?: boolean;
        hinweis?: string;
    }) => {
        const aktiv = fokus === id;
        const gefuellt = formData[id].length > 0;
        const istPasswort = id === 'password';
        return (
            <div className="relative">
                <label
                    htmlFor={id}
                    className="block text-xs font-medium mb-2 transition-colors duration-200"
                    style={{ color: aktiv ? '#60a5fa' : 'rgba(148,163,184,0.7)' }}
                >
                    {label}
                    {hinweis && (
                        <span className="ml-1.5 font-normal" style={{ color: 'rgba(100,116,139,0.6)' }}>
                            {hinweis}
                        </span>
                    )}
                </label>
                <div className="relative">
                    <Symbol
                        className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors duration-200"
                        style={{ color: aktiv ? '#60a5fa' : 'rgba(100,116,139,0.7)' }}
                        aria-hidden="true"
                    />
                    <input
                        id={id}
                        name={id}
                        type={istPasswort && showPassword ? 'text' : typ}
                        autoComplete={autoComplete}
                        placeholder={platzhalter}
                        value={formData[id]}
                        onChange={(e) => setFormData({ ...formData, [id]: e.target.value })}
                        onFocus={() => setFokus(id)}
                        onBlur={() => setFokus(null)}
                        required={pflicht}
                        minLength={istPasswort ? 8 : undefined}
                        disabled={isSubmitting}
                        className="w-full pl-10 pr-10 py-3 rounded-xl text-sm text-white placeholder-slate-600 outline-none transition-all duration-200 disabled:opacity-40"
                        style={feldStil(aktiv)}
                    />
                    {istPasswort && gefuellt ? (
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3.5 top-1/2 -translate-y-1/2"
                            aria-label={showPassword ? 'Passwort verbergen' : 'Passwort anzeigen'}
                        >
                            {showPassword
                                ? <EyeOff className="w-4 h-4" style={{ color: 'rgba(100,116,139,0.7)' }} />
                                : <Eye className="w-4 h-4" style={{ color: 'rgba(100,116,139,0.7)' }} />}
                        </button>
                    ) : gefuellt && !isSubmitting ? (
                        <CheckCircle2 className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#34d399' }} aria-hidden="true" />
                    ) : null}
                </div>
            </div>
        );
    };

    return (
        <main
            role="main"
            aria-label="Registrierung"
            className="on-dark min-h-screen flex items-center justify-center relative overflow-hidden py-10"
            style={{ background: AUTH_VERLAUF }}
        >
            <AuthBackground />

            <div className="relative w-full max-w-lg mx-4 z-10">
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
                        aria-hidden="true"
                    />

                    <div className="mb-7">
                        <h1 className="text-2xl font-semibold text-white mb-1.5 tracking-tight">Konto anlegen</h1>
                        <p className="text-sm" style={{ color: 'rgba(148,163,184,0.6)' }}>
                            Wählen Sie Ihren Tarif und starten Sie in wenigen Minuten
                        </p>
                    </div>

                    {/* ---------------------------------------------- Tarif */}
                    <fieldset className="mb-6">
                        <legend className="block text-xs font-medium mb-2.5" style={{ color: 'rgba(148,163,184,0.7)' }}>
                            Tarif
                        </legend>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                            {TARIFE.map((p) => {
                                const gewaehlt = plan === p.id;
                                return (
                                    <button
                                        key={p.id}
                                        type="button"
                                        onClick={() => setPlan(p.id)}
                                        aria-pressed={gewaehlt}
                                        className="relative p-3 rounded-xl text-center transition-all duration-200"
                                        style={{
                                            background: gewaehlt ? 'rgba(59,130,246,0.10)' : 'rgba(255,255,255,0.03)',
                                            border: gewaehlt ? '1px solid rgba(59,130,246,0.45)' : '1px solid rgba(255,255,255,0.07)',
                                            boxShadow: gewaehlt ? '0 0 0 3px rgba(59,130,246,0.08)' : 'none',
                                        }}
                                    >
                                        {p.popular && (
                                            <span
                                                className="absolute -top-2 left-1/2 -translate-x-1/2 text-[10px] px-2 py-0.5 rounded-full whitespace-nowrap font-medium text-white"
                                                style={{ background: 'linear-gradient(135deg, #2563eb 0%, #4f46e5 100%)' }}
                                            >
                                                Beliebt
                                            </span>
                                        )}
                                        <div className="text-sm font-semibold" style={{ color: gewaehlt ? '#93c5fd' : 'rgba(226,232,240,0.85)' }}>
                                            {p.name}
                                        </div>
                                        <div className="text-xs mt-1" style={{ color: gewaehlt ? '#60a5fa' : 'rgba(148,163,184,0.7)' }}>
                                            {p.price}
                                        </div>
                                        <div className="text-[11px] mt-0.5" style={{ color: 'rgba(100,116,139,0.7)' }}>
                                            {p.hint}
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                        <p className="text-xs mt-3 leading-relaxed" style={{ color: 'rgba(100,116,139,0.75)' }}>
                            Komplettservice gesucht? Beim{' '}
                            <span className="font-semibold" style={{ color: 'rgba(203,213,225,0.9)' }}>Expert-Paket</span>{' '}
                            überarbeiten wir Ihre Website selbst — 3.990 € netto einmalig, danach 29 €/Monat
                            für laufende Updates.{' '}
                            <a
                                href="mailto:support@complyo.de?subject=Expert-Paket"
                                className="transition-colors duration-200 hover:opacity-80"
                                style={{ color: '#60a5fa' }}
                            >
                                Expert-Paket anfragen
                            </a>
                        </p>
                    </fieldset>

                    {/* --------------------------------------------- Module */}
                    {plan === 'single' && (
                        <fieldset className="mb-6">
                            <legend className="block text-xs font-medium mb-2.5" style={{ color: 'rgba(148,163,184,0.7)' }}>
                                Säulen wählen <span style={{ color: 'rgba(100,116,139,0.6)' }}>(19 € je Säule/Monat)</span>
                            </legend>
                            <div className="grid grid-cols-2 gap-2">
                                {MODULES.map((module) => {
                                    const Icon = module.icon;
                                    const gewaehlt = selectedModules.includes(module.id);
                                    return (
                                        <button
                                            key={module.id}
                                            type="button"
                                            onClick={() => toggleModule(module.id)}
                                            aria-pressed={gewaehlt}
                                            className="p-3 rounded-xl text-left transition-all duration-200"
                                            style={{
                                                background: gewaehlt ? 'rgba(59,130,246,0.08)' : 'rgba(255,255,255,0.03)',
                                                border: gewaehlt ? '1px solid rgba(59,130,246,0.4)' : '1px solid rgba(255,255,255,0.07)',
                                            }}
                                        >
                                            <div className="flex items-center gap-2 mb-1.5">
                                                <span
                                                    className="w-4 h-4 rounded flex items-center justify-center flex-shrink-0"
                                                    style={{
                                                        background: gewaehlt ? '#2563eb' : 'transparent',
                                                        border: gewaehlt ? '1px solid #2563eb' : '1px solid rgba(100,116,139,0.5)',
                                                    }}
                                                    aria-hidden="true"
                                                >
                                                    {gewaehlt && <CheckCircle className="w-3 h-3 text-white" />}
                                                </span>
                                                <Icon
                                                    className="w-4 h-4"
                                                    style={{ color: gewaehlt ? '#60a5fa' : 'rgba(100,116,139,0.7)' }}
                                                    aria-hidden="true"
                                                />
                                            </div>
                                            <div className="text-sm font-medium" style={{ color: gewaehlt ? '#fff' : 'rgba(203,213,225,0.85)' }}>
                                                {module.name}
                                            </div>
                                            <div className="text-xs mt-0.5" style={{ color: 'rgba(100,116,139,0.75)' }}>
                                                {module.description}
                                            </div>
                                        </button>
                                    );
                                })}
                            </div>
                        </fieldset>
                    )}

                    {/* -------------------------------------- Zusammenfassung */}
                    <div
                        className="rounded-xl p-4 mb-6 flex justify-between items-center gap-4"
                        style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
                    >
                        <div>
                            <div className="text-xs" style={{ color: 'rgba(148,163,184,0.7)' }}>Ihr Tarif</div>
                            <div className="text-base font-semibold text-white mt-0.5">{getPlanName()}</div>
                            {plan === 'single' && selectedModules.length > 0 && (
                                <div className="text-xs mt-1" style={{ color: 'rgba(100,116,139,0.75)' }}>
                                    {selectedModules.map(m => MODULES.find(mod => mod.id === m)?.name).join(', ')}
                                </div>
                            )}
                        </div>
                        <div className="text-right flex-shrink-0">
                            <div className="text-xl font-bold" style={{ color: '#60a5fa' }}>{getPriceDisplay()}</div>
                            {plan !== 'free' && (
                                <div className="text-xs" style={{ color: 'rgba(100,116,139,0.6)' }}>zzgl. MwSt.</div>
                            )}
                        </div>
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

                    <div className="mb-5">
                        <SocialLoginButtons plan={plan} modules={selectedModules} mode="register" />
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {feld({ id: "email", label: "E-Mail-Adresse", typ: "email", symbol: Mail, platzhalter: "ihre@email.com", autoComplete: "email", pflicht: true })}
                        {feld({ id: "password", label: "Passwort", typ: "password", symbol: Lock, platzhalter: "Mindestens 8 Zeichen", autoComplete: "new-password", pflicht: true })}
                        {feld({ id: "full_name", label: "Vollständiger Name", typ: "text", symbol: User, platzhalter: "Max Mustermann", autoComplete: "name", pflicht: true })}
                        {feld({ id: "company", label: "Firma", typ: "text", symbol: Building2, platzhalter: "Ihr Unternehmen", autoComplete: "organization", hinweis: "(optional)" })}

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
                                aria-hidden="true"
                            />
                            <span className="relative flex items-center gap-2.5">
                                {isSubmitting ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        {plan === 'free' ? 'Konto wird angelegt…' : 'Weiterleitung zur Zahlung…'}
                                    </>
                                ) : (
                                    <>
                                        <CheckCircle className="w-4 h-4" />
                                        {plan === 'free' ? 'Kostenlos starten' : 'Weiter zur Zahlung'}
                                        <ArrowRight className="w-3.5 h-3.5 opacity-0 -ml-1 group-hover:opacity-100 group-hover:ml-0 transition-all duration-200" />
                                    </>
                                )}
                            </span>
                        </button>
                    </form>

                    <div className="mt-6 pt-5" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                        <p className="text-center text-xs" style={{ color: 'rgba(100,116,139,0.6)' }}>
                            Bereits registriert?{' '}
                            <a
                                href="/login"
                                className="font-medium transition-colors duration-200 hover:opacity-80"
                                style={{ color: '#60a5fa' }}
                            >
                                Jetzt anmelden
                            </a>
                        </p>
                        {/* Absolute Adressen: die Pfade /agb und /datenschutz gibt es im
                            Dashboard nicht, die Middleware leitete sie auf die
                            ANMELDESEITE um — Rechtstexte, die man vor Vertragsschluss
                            lesen koennen muss, hinter einer Anmeldung. */}
                        <p className="text-center text-xs mt-3 leading-relaxed" style={{ color: 'rgba(100,116,139,0.5)' }}>
                            Mit der Registrierung stimmen Sie unseren{' '}
                            <a href="https://complyo.de/agb" target="_blank" rel="noopener noreferrer"
                               className="transition-colors duration-200 hover:opacity-80" style={{ color: 'rgba(96,165,250,0.75)' }}>
                                AGB
                            </a>{' '}und der{' '}
                            <a href="https://complyo.de/datenschutz" target="_blank" rel="noopener noreferrer"
                               className="transition-colors duration-200 hover:opacity-80" style={{ color: 'rgba(96,165,250,0.75)' }}>
                                Datenschutzerklärung
                            </a>{' '}zu.
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
                @media (prefers-reduced-motion: reduce) {
                    .animate-errorfade { animation: none; }
                }
            `}</style>
        </main>
    );
}

export default function RegisterPage() {
    return (
        <Suspense fallback={
            <main
                role="main"
                aria-label="Registrierung wird geladen"
                className="on-dark min-h-screen flex items-center justify-center"
                style={{ background: AUTH_VERLAUF }}
            >
                <Loader2 className="w-8 h-8 animate-spin" style={{ color: '#60a5fa' }} />
            </main>
        }>
            <RegisterForm />
        </Suspense>
    );
}
