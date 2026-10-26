'use client';

import { useState, Suspense, useEffect } from 'react';

// Fassungen der AGB und des Auftragsverarbeitungsvertrages (Art. 28 DSGVO),
// die bei der Registrierung angezeigt und protokolliert werden. Sie stehen
// seit dem 11.09.2026 in lib/vertragsstand, weil das Gate fuer Bestandskonten
// dieselben Werte braucht.
import { AGB_VERSION, AVV_VERSION } from '@/lib/vertragsstand';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter, useSearchParams } from 'next/navigation';
import { Shield, Eye, FileText, BarChart3 } from 'lucide-react';
import SocialLoginButtons from '@/components/SocialLoginButtons';
import { isFirebaseEnabled } from '@/lib/firebase';
import { AuthHero, PasswortAuge } from '@/components/AuthHero';
import { apiClient } from '@/lib/api-client';
import { herkunftAusParametern, herkunftMerken, gemerkteHerkunft } from '@/lib/herkunft';

const MODULES = [
    { id: 'cookie', name: 'Cookie & DSGVO', icon: Shield, description: 'Cookie-Banner, Consent-Management' },
    { id: 'accessibility', name: 'Barrierefreiheit', icon: Eye, description: 'WCAG 2.1 AA Scanner & Fixes' },
    { id: 'legal_texts', name: 'Rechtliche Texte', icon: FileText, description: 'Impressum, Datenschutz, AGB' },
    { id: 'monitoring', name: 'Monitoring', icon: BarChart3, description: 'Automatische Scans & Alerts' },
];

// Preis je einzelner Saeule. Deckungsgleich mit der Tarifkarte und mit
// STRIPE_PRICE_SINGLE_MODULE (29 EUR/Monat, geprueft am 10.09.2026).
const EINZELSAEULE_JE_MODUL = 29;

const TARIFE = [
    { id: 'free', name: 'Free', price: '0 €', hint: '1 Fix' },
    { id: 'single', name: 'Einzelsäule', price: '29 €/Monat', hint: 'je Säule' },
    { id: 'pro', name: 'Pro', price: '89 €/Monat', hint: '1 Domain', popular: true },
    { id: 'agency', name: 'Agentur', price: '599 €/Monat', hint: '25 Projekte' },
    { id: 'monitor', name: 'Monitoring', price: '39 €/Monat', hint: 'bis 10 Websites' },
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

    // Herkunft (utm) aus der Adresszeile fuer die Sitzung merken, damit sie
    // den Kauf erreicht, auch nach Neuladen oder Google-Popup.
    useEffect(() => {
        herkunftMerken(herkunftAusParametern(searchParams));
    }, [searchParams]);

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
    // Die AGB schliessen Verbrauchervertraege aus. Das muss aktiv bestaetigt
    // werden, sonst ist die Beschraenkung im Streitfall nicht zu belegen.
    const [istUnternehmer, setIstUnternehmer] = useState(false);

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

    // Die Zusammenfassung vor dem Kauf MUSS denselben Preis nennen, den Stripe
    // abbucht. Bis zum 10.09.2026 stand hier die alte Preisliste (Pro 49,
    // Agentur 299, Monitoring 19, Einzelsaeule 19 je Modul), waehrend die
    // Tarifkarten darueber und Stripe bereits die neue fuehrten (89 / 599 / 39
    // / 29). Der letzte Bildschirm vor "Weiter zur Zahlung" versprach damit
    // rund die Haelfte des Betrages, der dann eingezogen wurde.
    //
    // Deshalb kommen die Betraege jetzt aus derselben Quelle wie der Checkout:
    // GET /api/stripe/plans. Solange sie nicht geladen sind, steht ein
    // Gedankenstrich — lieber keine Zahl als eine falsche.
    const [tarifpreise, setTarifpreise] = useState<Record<string, { monthly: number; yearly: number }> | null>(null);

    useEffect(() => {
        let abgebrochen = false;
        fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.de'}/api/stripe/plans`)
            .then(r => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
            .then(d => {
                if (abgebrochen) return;
                const tabelle: Record<string, { monthly: number; yearly: number }> = {};
                for (const p of d.plans || []) {
                    tabelle[p.id] = { monthly: p.price_monthly, yearly: p.price_yearly };
                }
                // Die Einzelsaeule ist kein Stripe-Plan, sondern ein Preis je
                // Modul. Er steht in den Tarifkarten und in Stripe bei 29.
                tabelle.single = { monthly: EINZELSAEULE_JE_MODUL, yearly: 0 };
                setTarifpreise(tabelle);
            })
            .catch(() => { if (!abgebrochen) setTarifpreise(null); });
        return () => { abgebrochen = true; };
    }, []);

    const calculatePrice = (): { monthly: number | null; yearly: number | null; setup: number } => {
        if (plan === 'free') return { monthly: 0, yearly: 0, setup: 0 };
        if (!tarifpreise) return { monthly: null, yearly: null, setup: 0 };
        if (plan === 'single') {
            return { monthly: selectedModules.length * EINZELSAEULE_JE_MODUL, yearly: 0, setup: 0 };
        }
        const eintrag = tarifpreise[plan];
        if (!eintrag) return { monthly: null, yearly: null, setup: 0 };
        return { monthly: eintrag.monthly, yearly: eintrag.yearly, setup: 0 };
    };

    const price = calculatePrice();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (plan === 'single' && selectedModules.length === 0) {
            setError('Bitte wählen Sie mindestens ein Modul aus.');
            return;
        }

        if (!istUnternehmer) {
            setError('Bitte bestätigen Sie, dass Sie als Unternehmer handeln. complyo schließt keine Verträge mit Verbrauchern.');
            return;
        }

        setIsSubmitting(true);

        try {
            await register({
                ...formData,
                plan,
                modules: selectedModules,
                unternehmer_bestaetigt: istUnternehmer,
                agb_version: AGB_VERSION,
                avv_version: AVV_VERSION,
            });

            // Free-Tarif: kein Checkout, direkt ins Dashboard.
            if (plan === 'free') {
                router.push('/dashboard');
                return;
            }

            const checkoutData = await apiClient.post('/api/stripe/create-checkout', {
                plan: plan,
                modules: selectedModules,
                billing_period: 'monthly',
                herkunft: gemerkteHerkunft(),
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
        if (price.monthly === null) return 'Preis wird geladen …';
        if (price.yearly && price.yearly > 0) return `${price.monthly}€/Monat oder ${price.yearly}€/Jahr`;
        return `${price.monthly}€/Monat`;
    };

    // Ein Feld: Beschriftung und Eingabe, beim Passwort mit Umschalter. BEWUSST
    // eine Funktion, die JSX zurueckgibt, und KEINE Komponente: eine
    // Komponente, die im Rumpf einer anderen definiert wird, ist bei jedem
    // Rendern ein neuer Typ. React haengt das Eingabefeld dann nach jedem
    // Tastendruck ab und neu an, der Fokus waere nach jedem Zeichen weg.
    const feld = ({ id, label, typ, platzhalter, autoComplete, pflicht, hinweis, d }: {
        id: 'email' | 'password' | 'full_name' | 'company';
        label: string;
        typ: string;
        platzhalter: string;
        autoComplete: string;
        pflicht?: boolean;
        hinweis?: string;
        d: string;
    }) => {
        const istPasswort = id === 'password';
        const eingabe = (
            <input
                id={id}
                name={id}
                type={istPasswort && showPassword ? 'text' : typ}
                autoComplete={autoComplete}
                placeholder={platzhalter}
                value={formData[id]}
                onChange={(e) => setFormData({ ...formData, [id]: e.target.value })}
                required={pflicht}
                minLength={istPasswort ? 8 : undefined}
                disabled={isSubmitting}
                className="lg-input"
            />
        );
        return (
            <div className="lg-field lg-in" style={{ ['--d' as any]: d }}>
                <label htmlFor={id}>
                    {label}
                    {hinweis && <span className="lg-opt"> {hinweis}</span>}
                </label>
                {istPasswort ? (
                    <div className="lg-pw">
                        {eingabe}
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
                ) : eingabe}
            </div>
        );
    };

    return (
        <main role="main" aria-label="Registrierung" className="lg lg--reg">
            <AuthHero />

            <section className="lg-card" aria-labelledby="lg-h1">
                <div className="lg-form">
                    <h1 id="lg-h1" className="lg-h1 lg-in" style={{ ['--d' as any]: '.45s' }}>Konto anlegen</h1>
                    <p className="lg-lead lg-in" style={{ ['--d' as any]: '.52s' }}>
                        Wählen Sie Ihren Tarif und starten Sie in wenigen Minuten.
                    </p>

                    {/* ---------------------------------------------- Tarif */}
                    <fieldset className="lg-set lg-in" style={{ ['--d' as any]: '.58s' }}>
                        <legend>Tarif</legend>
                        <div className="lg-tarife">
                            {TARIFE.map((p) => (
                                <button
                                    key={p.id}
                                    type="button"
                                    onClick={() => setPlan(p.id)}
                                    aria-pressed={plan === p.id}
                                    className={`lg-tarif${plan === p.id ? ' is-on' : ''}`}
                                >
                                    {p.popular && <span className="lg-badge">Beliebt</span>}
                                    <span className="lg-tarif-n">{p.name}</span>
                                    <span className="lg-tarif-p">{p.price}</span>
                                    <span className="lg-tarif-h">{p.hint}</span>
                                </button>
                            ))}
                        </div>
                        <p className="lg-hint">
                            Komplettservice gesucht? Beim <strong>Expert-Paket</strong> überarbeiten wir Ihre
                            Website selbst, 3.990 € netto einmalig, danach 29 €/Monat für laufende Updates.{' '}
                            <a href="mailto:support@complyo.de?subject=Expert-Paket" className="lg-link lg-link-s">
                                Expert-Paket anfragen
                            </a>
                        </p>
                    </fieldset>

                    {/* --------------------------------------------- Module */}
                    {plan === 'single' && (
                        <fieldset className="lg-set">
                            <legend>Säulen wählen <span className="lg-opt">(29 € je Säule/Monat)</span></legend>
                            <div className="lg-moduls">
                                {MODULES.map((module) => {
                                    const Icon = module.icon;
                                    const gewaehlt = selectedModules.includes(module.id);
                                    return (
                                        <button
                                            key={module.id}
                                            type="button"
                                            onClick={() => toggleModule(module.id)}
                                            aria-pressed={gewaehlt}
                                            className={`lg-modul${gewaehlt ? ' is-on' : ''}`}
                                        >
                                            <span className="lg-modul-k">
                                                <span className="lg-modul-box" aria-hidden="true">
                                                    <svg viewBox="0 0 16 16"><path d="M3.5 8.5l3 3 6-7" /></svg>
                                                </span>
                                                <Icon aria-hidden="true" />
                                            </span>
                                            <span className="lg-tarif-n">{module.name}</span>
                                            <span className="lg-tarif-h">{module.description}</span>
                                        </button>
                                    );
                                })}
                            </div>
                        </fieldset>
                    )}

                    {/* -------------------------------------- Zusammenfassung */}
                    <div className="lg-sum lg-in" style={{ ['--d' as any]: '.64s' }}>
                        <div>
                            <div className="lg-sum-k">Ihr Tarif</div>
                            <div className="lg-sum-n">{getPlanName()}</div>
                            {plan === 'single' && selectedModules.length > 0 && (
                                <div className="lg-sum-k">
                                    {selectedModules.map(m => MODULES.find(mod => mod.id === m)?.name).join(', ')}
                                </div>
                            )}
                        </div>
                        <div className="lg-sum-r">
                            <div className="lg-sum-p">{getPriceDisplay()}</div>
                            {plan !== 'free' && <div className="lg-sum-k">zzgl. MwSt.</div>}
                        </div>
                    </div>

                    {error && (
                        <div role="alert" aria-live="assertive" className="lg-alert">
                            <svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="8" /><path d="M10 6v5M10 14h.01" /></svg>
                            <span>{error}</span>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="lg-fields lg-fields--reg">
                        {feld({ id: 'email', label: 'E-Mail', typ: 'email', platzhalter: 'Ihre E-Mail-Adresse', autoComplete: 'email', pflicht: true, d: '.7s' })}
                        {feld({ id: 'password', label: 'Passwort', typ: 'password', platzhalter: 'Mindestens 8 Zeichen', autoComplete: 'new-password', pflicht: true, d: '.76s' })}
                        {feld({ id: 'full_name', label: 'Vollständiger Name', typ: 'text', platzhalter: 'Max Mustermann', autoComplete: 'name', pflicht: true, d: '.82s' })}
                        {feld({ id: 'company', label: 'Firma', typ: 'text', platzhalter: 'Ihr Unternehmen', autoComplete: 'organization', hinweis: '(optional)', d: '.88s' })}

                        <label className="lg-check lg-check--text lg-in" htmlFor="unternehmer" style={{ ['--d' as any]: '.94s' }}>
                            <input
                                id="unternehmer"
                                type="checkbox"
                                required
                                checked={istUnternehmer}
                                onChange={(e) => setIstUnternehmer(e.target.checked)}
                            />
                            <span className="lg-box" aria-hidden="true">
                                <svg viewBox="0 0 16 16"><path d="M3.5 8.5l3 3 6-7" /></svg>
                            </span>
                            <span>
                                Ich handle bei diesem Vertrag als Unternehmer im Sinne des § 14 BGB und
                                nicht als Verbraucher. complyo schließt keine Verträge mit Verbrauchern.
                                Zugleich schließe ich den{' '}
                                <a href="https://complyo.de/avv" target="_blank" rel="noopener noreferrer"
                                   className="lg-link lg-link-s" onClick={(e) => e.stopPropagation()}>
                                    Auftragsverarbeitungsvertrag nach Art. 28 DSGVO
                                </a>{' '}ab. Er ist nötig, weil complyo bei der Prüfung und beim Betrieb der
                                Widgets Daten der Besucher meiner Website verarbeitet.
                            </span>
                        </label>

                        <button type="submit" disabled={isSubmitting || !istUnternehmer} className="lg-submit lg-in" style={{ ['--d' as any]: '1s' }}>
                            {isSubmitting
                                ? (plan === 'free' ? 'Konto wird angelegt…' : 'Weiterleitung zur Zahlung…')
                                : (plan === 'free' ? 'Kostenlos starten' : 'Weiter zur Zahlung')}
                        </button>
                    </form>

                    {isFirebaseEnabled && (
                        <>
                            <div className="lg-or lg-in" style={{ ['--d' as any]: '1.05s' }}>
                                <span>Oder weiter mit:</span>
                            </div>
                            <div className="lg-in" style={{ ['--d' as any]: '1.1s' }}>
                                <SocialLoginButtons plan={plan} modules={selectedModules} mode="register" darstellung="pille" />
                            </div>
                        </>
                    )}

                    <p className="lg-foot lg-in" style={{ ['--d' as any]: '1.15s' }}>
                        Bereits registriert? <a href="/login" className="lg-link lg-link-b">Jetzt anmelden</a>
                    </p>
                    {/* Absolute Adressen: die Pfade /agb und /datenschutz gibt es im
                        Dashboard nicht, die Middleware leitete sie auf die
                        ANMELDESEITE um, Rechtstexte, die man vor Vertragsschluss
                        lesen koennen muss, hinter einer Anmeldung. */}
                    <p className="lg-legal">
                        Mit der Registrierung stimmen Sie unseren{' '}
                        <a href="https://complyo.de/agb" target="_blank" rel="noopener noreferrer" className="lg-link lg-link-s">AGB</a>{' '}und der{' '}
                        <a href="https://complyo.de/datenschutz" target="_blank" rel="noopener noreferrer" className="lg-link lg-link-s">Datenschutzerklärung</a>{' '}zu und schließen den{' '}
                        <a href="https://complyo.de/avv" target="_blank" rel="noopener noreferrer" className="lg-link lg-link-s">Auftragsverarbeitungsvertrag</a>{' '}ab.
                    </p>
                </div>
            </section>
        </main>
    );
}

export default function RegisterPage() {
    return (
        <Suspense fallback={<main role="main" aria-label="Registrierung wird geladen" className="lg" />}>
            <RegisterForm />
        </Suspense>
    );
}
