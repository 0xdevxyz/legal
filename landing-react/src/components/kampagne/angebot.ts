/**
 * Das Early-Access-Angebot, an einer Stelle.
 *
 * Bis zum 28.09.2026 standen die drei Werte nur in EarlyAccessKampagne.tsx.
 * Seit die Startseite wieder verkauft und die Warteliste als zweiten Weg
 * darunter traegt, lesen zwei Komponenten dieselben Zahlen. Zwei Kopien
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
