/**
 * Das Early-Access-Angebot und der Agentur-Tarif, an einer Stelle.
 *
 * Bis zum 28.09.2026 standen die drei Early-Access-Werte nur in
 * EarlyAccessKampagne.tsx. Seit die Preistabelle (PricingSection) und die
 * Kampagnenseite dieselben Zahlen lesen, gibt es sie nur hier. Zwei Kopien
 * waeren die naechste "49 gezeigt, 89 gebucht"-Falle.
 *
 * Die Grenze von 100 Plaetzen prueft das Backend selbst
 * (EARLY_ACCESS_PLAETZE in stripe_routes._hat_early_access_platz); hier ist
 * sie Anzeige. Der Nachlass laeuft als Stripe-Gutschein ueber zwoelf Monate
 * auf den regulaeren Preis, siehe Memory complyo-tarifmodell.
 */
export const PLAETZE = 100;
export const PREIS_EARLY = '49 €';
export const PREIS_REGULAER = '89 €';

/**
 * Agentur-Tarif. Seit dem 19.10.2026 steht er auch auf der Early-Access-
 * Startseite (AgenturAbschnitt), weil Agenturen buchen koennen sollen,
 * waehrend Inhaber auf der Warteliste stehen. Preistabelle und Abschnitt
 * lesen dieselben Werte; Stripe fuehrt den Preis unter agency_monthly /
 * agency_yearly, die Registrierung holt ihn aus GET /api/stripe/plans.
 */
export const AGENTUR_PREIS_MONAT = '599 €';
export const AGENTUR_PREIS_JAHR = '5.990 €';
export const AGENTUR_PROJEKTE = 25;
