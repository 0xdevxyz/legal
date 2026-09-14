# Stripe auf Live umschalten

Stand 11.09.2026. Alles Technische ist vorbereitet; was fehlt, kann nur der
Kontoinhaber tun, weil es den Live-Geheimschlüssel und die Kontoaktivierung
im Stripe-Dashboard braucht. Dauer: etwa 30 Minuten, davon 25 im Dashboard.

Solange das nicht passiert ist, meldet der Betriebswächter einmal täglich
„Stripe läuft mit Testschlüssel: kein Kunde kann bezahlen."

## Warum das jetzt der wichtigste Schritt ist

Seit dem Launch-Audit vom 31.08.2026 kann niemand bezahlen. Alle Preise, der
Early-Access-Preis (49 statt 89 Euro für die ersten 100 bestätigten
Wartelistenplätze, `_hat_early_access_platz` in stripe_routes.py), der
Kaufweg, die Modul-Freischaltung und die Domainbindung sind gebaut und
getestet. Es fehlt nur der Schlüssel.

## Ablauf

1. **Stripe-Konto aktivieren** (Dashboard, Live-Modus): Unternehmensdaten,
   Vertretungsberechtigte, Bankkonto für Auszahlungen. Bis `charges_enabled`
   true ist, nimmt Stripe kein Geld an; das Skript unten sagt es, wenn es
   noch fehlt.
2. **Umsatzsteuer**: Die Preise sind netto angelegt (`tax_behavior=exclusive`,
   complyo verkauft nur an Unternehmer, AGB Ziffer 1). Entweder Stripe Tax
   aktivieren (Dashboard > Tax), dann rechnet Stripe die 19 % dazu und
   behandelt EU-Kunden mit USt-IdNr per Reverse Charge; oder die Rechnungen
   ohne Stripe Tax mit eigenem Steuersatz versehen. Ohne eine der beiden
   Entscheidungen stehen auf der ersten Rechnung 89,00 € ohne Steuer.
3. **Live-Geheimschlüssel holen**: Dashboard > Developers > API keys, Live
   mode, „Secret key" (`sk_live_...`). Er wird nirgends abgelegt ausser in der
   .env auf openclaw.
4. **Preise und Webhooks anlegen und eintragen** (auf openclaw, im Repo):

       cd /home/clawd/saas/legal && python3 scripts/stripe-live-umschalten.py anlegen --schreiben

   Das Skript fragt den Live-Schlüssel unsichtbar ab. Er steht damit weder in
   der Shell-Historie noch in der Prozessliste, und er muss durch keine
   Zwischenablage. Danach legt es 13 Produkte, 19 Preise und zwei
   Webhook-Endpunkte an, idempotent (vorhandene werden über `lookup_key`
   wiedererkannt, nicht doppelt angelegt), und trägt Schlüssel, Preis-IDs und
   Webhook-Geheimnisse in die `.env` ein. Eine Kopie der alten Fassung liegt
   vorher daneben, die alten Werte bleiben als Kommentar in der Datei.

   Ohne `--schreiben` gibt es den Block nur aus, zum Eintragen von Hand.

5. **Publishable Key** (optional): `STRIPE_PUBLISHABLE_KEY=pk_live_...` aus dem
   Dashboard. Das Backend benutzt ihn nicht, der Checkout läuft serverseitig.

6. **Backend neu bauen und starten** (der Code ist ins Image gebacken,
   `up -d` allein nimmt weder neuen Code noch neue Umgebungsvariablen mit):

       cd /home/clawd/saas/legal && docker compose build backend && docker compose up -d backend

7. **Prüfen**:

       python3 scripts/stripe-live-umschalten.py pruefen

   Muss „Alles stimmig" melden: Live-Modus, jede Preis-ID vorhanden, aktiv,
   richtiger Betrag und Intervall, beide Webhooks registriert, compose reicht
   jede Variable durch. Zusaetzlich vergleicht die Pruefung den angelegten
   Betrag mit dem, den die Oberflaeche anzeigt (12 der 19 Preise stehen als
   Zahl im Backend-Katalog): zeigt die Seite 49 und bucht Stripe 89, faellt
   das hier auf und nicht beim ersten Kunden. Der Betriebswächter hört dann von selbst auf zu
   melden.
8. **Testkauf mit echter Karte**: Pro monatlich buchen, im Dashboard prüfen,
   dass `user_limits.plan_type` auf pro steht und `user_modules` freigeschaltet
   ist, dann im Stripe-Dashboard erstatten und kündigen. Das ist der einzige
   Weg, den Webhook-Pfad live zu sehen.
9. **Startseite zurückdrehen**: Seit 02.09.2026 ist `/` die Early-Access-Seite,
   weil der Checkout echte Karten ablehnte. Die alte Startseite liegt unter
   `/produkt` (noindex). Beim Zurücklegen `noindex` und `canonical` mitziehen
   (siehe Kommentar in `landing-react/src/app/page.tsx`).

## Entschieden: 25 Projekte kosten 599 EUR (14.09.2026)

Es gab zwei Wege zu denselben 25 zusaetzlichen Agentur-Projekten, zu
verschiedenen Preisen: "Agency Plan 2" auf der Agentur-Seite fuer 599 EUR und
das "Extra Sites Paket" im Add-on-Katalog fuer 200 EUR. Wer die Add-on-Seite
fand, zahlte ein Drittel fuer dieselbe Leistung.

Daniel hat entschieden, das Extra-Sites-Paket auf **599 EUR/Monat**
anzuheben. Beide Wege kosten jetzt gleich viel; `test_25_projekte_kosten_
ueberall_gleich` haelt sie zusammen, damit sie nicht wieder auseinanderlaufen.

Der Zusatzplatz (+1 Website, 29 EUR/Monat) ist ein eigenes Produkt mit eigener
Kennung und davon unberuehrt.

## Was bewusst nicht im Skript steckt

- Der Testmodus bleibt unangetastet; die Test-Preise existieren weiter.
- Kein automatisches Eintragen in die .env: die Datei enthält alle
  Geheimnisse des Systems, sie wird von Hand geändert und vorher kopiert.
- Kein Wechsel der Startseite: das ist eine Marketingentscheidung, siehe 9.

## Rückweg

`.env.bak-...-vor-live` zurückkopieren, `docker compose up -d backend`. Die
Live-Preise bleiben in Stripe bestehen und stören nicht.
