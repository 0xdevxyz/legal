# Complyo Internationalisierung — Stufe 1 (EU-Englisch) Umsetzungsplan

> Ziel von Stufe 1: Das **bestehende** Compliance-Produkt an englischsprachige EU-Kunden
> verkaufen, ohne neue Rechtsräume zu bauen. Profile: `de` (Status quo) + `eu` (generisch, EN, GDPR).
> Auslieferung auf `complyo.de/[locale]`. Stufe 2 (FR/UK/US auf complyo.tech) baut hierauf auf.

## Architektur-Entscheidungen (verbindlich)
- **ScanContext-Objekt** wird durch Engine + alle Checks gereicht (nicht Einzelparameter).
- **`jurisdiction` auf Website-Ebene**, Default vom Account (`user_limits`).
- **Ein Codebase, jurisdiction als Config** — `complyo.tech` wird späteres Deployment desselben Codes, kein Fork.
- **Stufe 1 nur `de` + `eu`.** Engine muss aber generisch für N Profile gebaut sein.

---

## EPIC B0 — Jurisdiction-Fundament  *(Keystone — zuerst, blockiert alles)*

### B0.1 — `ScanContext` einführen  · S
- Neu: `backend/compliance_engine/context.py`
  ```python
  @dataclass
  class ScanContext:
      url: str
      jurisdiction: str = "de"   # "de" | "eu" (Stufe 1)
      language: str = "de"       # "de" | "en"
      session: Optional[aiohttp.ClientSession] = None
  ```
- AC: Objekt existiert, von Engine instanziierbar, keine Verhaltensänderung.

### B0.2 — Jurisdiction-Profil-Registry  · M
- Neu: `backend/compliance_engine/jurisdictions.py`
  ```python
  JURISDICTION_PROFILES = {
    "de": {"language": "de", "checks": ["datenschutz","cookie","impressum",
            "barrierefreiheit","agb","uwg","pangv","widerruf","tcf"],
            "pillars": ["accessibility","gdpr","legal","cookies"]},
    "eu": {"language": "en", "checks": ["datenschutz","cookie",
            "barrierefreiheit","tcf"],   # DE-only Checks deaktiviert
            "pillars": ["accessibility","gdpr","cookies"]},
  }
  ```
- AC: `active_checks(jurisdiction)` + `active_pillars(jurisdiction)` Helper, getestet.

### B0.3 — DB-Migration: `jurisdiction`-Feld  · S
- `backend/alembic/versions/2026MMDD_xxxx_add_jurisdiction.py` (Muster: `20251125_0001_initial_schema.py`)
- `user_limits.jurisdiction VARCHAR(10) DEFAULT 'DE'` (Account-Default)
- `websites.jurisdiction VARCHAR(10) NULL` (Pro-Site-Override, NULL = Account-Default erben)
- AC: `upgrade()`/`downgrade()` laufen sauber gegen Baseline.

### B0.4 — Persistieren & Lesen  · M
- `auth_routes.py` `init_user_limits()` (~Z.59): setzt `jurisdiction='DE'`.
- Website-Create/Edit nimmt `jurisdiction` entgegen.
- Helper `get_effective_jurisdiction(website_id)` → `websites.jurisdiction or user_limits.jurisdiction`.
- AC: Default greift; Override pro Site funktioniert.

---

## EPIC B1 — Engine jurisdiction-aware

### B1.1 — `scan_website` akzeptiert jurisdiction  · S
- `compliance_engine/scanner.py:98`: `scan_website(url, jurisdiction="de")` → baut `ScanContext`.
- Result-Dict erhält Key `"jurisdiction"`.
- AC: Default `"de"` reproduziert heutiges Ergebnis byte-gleich.

### B1.2 — Check-Aktivierung nach Profil  · M
- `scanner.py:201-220`: Task-Liste dynamisch aus `active_checks(ctx.jurisdiction)`.
- `eu`-Profil überspringt Impressum/UWG/PAngV/Widerruf/AGB.
- AC: EU-Scan erzeugt keine DE-only Issues; DE-Scan unverändert.

### B1.3 — Context durch alle Checks  · M
- 9 Checks in `compliance_engine/checks/*.py` nehmen `context` als Parameter.
- Aufrufe im Scanner angepasst. Checks dürfen `context` zunächst ignorieren (mechanisch).
- AC: Signaturen einheitlich; Regressionstest grün für `de`.

### B1.4 — Score-Calculator nach aktiven Säulen  · M
- `score_calculator.py`: nur `active_pillars(jurisdiction)` werten — EU bekommt keine `legal`-Säule (kein Impressum-Penalty).
- AC: EU-Score nicht durch fehlende DE-Pflichten verfälscht.

---

## EPIC B2 — Issue-Text-Lokalisierung  *(größter Inhaltsblock — braucht juristisches EN-Review)*

### B2.1 — Stabile Issue-Codes  · L
- `ComplianceIssue` (scanner.py:54) bekommt Feld `code: str` (z.B. `COOKIE_NO_BANNER`, `GDPR_NO_PRIVACY_POLICY`).
- Alle Checks setzen Codes statt nur deutscher Freitexte.
- AC: Jedes Issue hat einen eindeutigen, stabilen Code.

### B2.2 — Message-Katalog (de/en) + legal_basis-Mapping  · XL
- Neu: `backend/compliance_engine/messages/{de,en}.yaml`, Key = Issue-Code → title/description/recommendation.
- `legal_basis` jurisdiction-abhängig: `de` → "DSGVO Art. 13", `eu` → "GDPR Art. 13" (nutzt vorhandenes `knowledge/laws/_mapping.yaml`).
- Rendering: Engine löst Texte über `context.language` auf.
- AC: EU-Scan liefert englische Texte + GDPR-Zitate. **Juristisches EN-Review erforderlich.**

### B2.3 — `risk_euro` jurisdiction-kalibriert  · M
- Umstellen auf `risk_amount` + `currency`; EU-Werte auf generische GDPR-Bußgeldlogik beziehen.
- AC: Keine DE-spezifischen Euro-Beträge im EU-Profil.

---

## EPIC A1 — Frontend i18n (next-intl)

### A1.1 — next-intl im Dashboard  · L
- `dashboard-react`: next-intl + `app/[locale]/`-Routing + Middleware + Provider.
- Sprachumschalter in `TopNav.tsx`.
- AC: `/de` und `/en` routen; Locale persistiert.

### A1.2 — Strings extrahieren (Dashboard)  · XL
- ~300–500 hardcoded DE-Strings → `messages/de.json` + `en.json`.
- AC: Keine hardcoded UI-Strings mehr in Komponenten (Lint/Grep-Gate).

### A1.3 — Landing: Eigenbau → next-intl  · L
- `landing-react/LanguageProvider.tsx` ablösen; EN-Marketing **professionell** übersetzt.
- AC: Landing voll zweisprachig über next-intl.

### A1.4 — Backend-Antworten & Mails lokalisieren  · M
- API-Fehler/Antworten honorieren `Accept-Language`/User-Sprache.
- Deutsche Hardcoded-Mails (`legal_notification_service.py`, `gdpr_retention_service.py`) an `i18n_service.py` (de/en vorhanden) anbinden.
- AC: EU-User bekommt englische System-Mails.

---

## EPIC A2 — Multi-Currency Billing  *(für reines EU-Englisch aufschiebbar — EUR ist EU-weit ok)*

### A2.1 — Währung entkoppeln  · L
- Hardcoded `'eur'` ersetzen: `payment/stripe_service.py:147`, `addon_payment_routes.py` (6×).
- Stripe Price-IDs pro Währung; Steuerlogik (EU-VAT/Reverse-Charge).
- AC: Preis + Währung konfigurierbar. **Hinweis: Stufe-1-MVP kann EUR-only bleiben.**

---

## EPIC A3 — hreflang / Locale-SEO

### A3.1 — hreflang + per-locale Metadata  · M
- `generateMetadata` pro Locale; `hreflang`-Alternates + `x-default`; Locale-Sitemaps.
- AC: Korrekte hreflang-Tags; Google Search Console ohne Locale-Fehler.

---

## Kritischer Pfad & MVP-Schnitt

```
B0 (Fundament) ──► B1 (Engine) ──► B2 (Texte, längster Pol)
                          └────────► A1 (Frontend i18n) ──► A3 (SEO)
A2 (Billing) : aufschiebbar — EUR-only für MVP
```

**Minimaler verkaufsfähiger EU-Englisch-Stand:**
B0 + B1 + B2.1/B2.2 (mind. Cookie/DSGVO/A11y in EN) + A1.1–A1.3 + A3. Billing bleibt EUR.

**Längste Pole:** B2.2 (Inhalte + EN-Rechtsreview) und A1.2 (String-Extraktion). Beide früh starten, laufen parallel.
