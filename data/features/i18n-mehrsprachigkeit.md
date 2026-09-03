# i18n / Mehrsprachigkeit

**Stand:** 2026-07-17 · **Status:** ⚪ verworfen (Ruine — API defekt, Widget-Locales tot)

## Ziel
Geplant: Übersetzungs-API für Frontend/Widget plus mehrsprachige Cookie-Banner-Texte.
**Ist-Zustand:** von drei Bausteinen funktioniert genau einer, und der wird an der API vorbei
genutzt. Die Datei dokumentiert den Trümmerstand, damit er nicht als Basis missverstanden wird.

## Architektur (end-to-end)
- **`backend/i18n_api.py`** (220 Z.), `APIRouter(prefix="/api/i18n")`, registriert in
  `backend/main_production.py:68` + `:604`. 7 Endpunkte, im Live-OpenAPI vorhanden:
  `GET /languages`, `/translations`, `/text/{key}`, `/form-validation`, `/email-templates`,
  `POST /set-language`, `GET /detect-language`.
  - **Alle 7 sind defekt.** Der Router greift auf 6 Symbole von `i18n_service` zu, die es
    **nicht gibt**: `default_language`, `set_default_language`, `get_language_from_request`,
    `get_text`, `get_form_validation_messages`, `get_email_template`.
  - Live verifiziert: `GET /api/i18n/languages` → `500`, `GET /api/i18n/translations` → `500`.
    Container-Log: `AttributeError: 'I18nService' object has no attribute 'default_language'`
    (`i18n_api.py:22` bzw. `:71`). Kein Endpunkt kann durchlaufen.
- **`backend/i18n_service.py`** (166 Z.) — Singleton `i18n_service = I18nService()`.
  - `supported_languages = ["de","en","fr","it","pl"]`, `translations` als **hartkodiertes
    Dict im Konstruktor** (E-Mail-Betreffs, Grußformeln, ein paar Scan-Meldungen).
  - Öffentlich: `get_translation(key, language)`, `translate(language, key)`,
    `detect_language_from_url()` (prüft nur, ob `.de` im String vorkommt),
    `get_supported_languages()`, `load_translations_from_file()` (**wird nirgends aufgerufen**).
  - **Einziger lebender Konsument:** `backend/email_service.py` (`get_translation` für
    Verifikations-/Report-Mails) — geht direkt am Router vorbei. Der Service ist also
    benutzt, die API darüber ist es nicht.
- **`backend/widgets/locales/translations.js`** (475 Z., **17 Sprachen**: de, en, fr, es, it,
  nl, pl, pt, sv, da, fi, no, cs, hu, ro, el, ru) — setzt am Ende
  `window.COMPLYO_TRANSLATIONS`.
  - `backend/widgets/cookie_banner_v2.js:576-577` liest `window.COMPLYO_TRANSLATIONS[browserLang]`
    und merged es in `config.texts`.
  - **Die Datei wird von keiner Route ausgeliefert** und von keinem Script-Tag geladen →
    `window.COMPLYO_TRANSLATIONS` ist zur Laufzeit immer `undefined`, der Merge-Zweig läuft nie.
    i18n im Widget ist damit tot; der Banner bleibt bei seinen Default-Texten
    (siehe [[cookie-consent-widget]]).
- **Frontend:** `grep -rn "api/i18n"` über `dashboard-react/src` und `landing-react/src`:
  **null Treffer**. Kein Konsument, weder Dashboard noch Landing.

## Bekannte Lücken / Offen
- **`i18n_api.py` ist nicht reparabel-ohne-Entscheidung.** Es fehlt die halbe Service-Klasse.
  Entweder die 6 Symbole nachziehen oder — angesichts null Konsumenten — Router
  entfernen und `i18n_service` auf den E-Mail-Pfad reduzieren. Letzteres ist der ehrlichere Weg:
  ein Router, der bei jedem Aufruf 500 wirft, ist nur Angriffsfläche und Rauschen im OpenAPI
  (und wird über [[mcp-server]] zusätzlich als MCP-Tool exponiert).
- **`POST /set-language` hat keine Auth**, obwohl der Docstring „Admin endpoint" sagt, und
  würde — falls er liefe — globalen Prozess-State ändern. Aktuell nur deshalb harmlos,
  weil `set_default_language` gar nicht existiert.
- **Widget-Locales anschließen ist billig und ungetan:** eine Route, die
  `widgets/locales/translations.js` ausliefert, plus Script-Tag/Inline vor dem Banner →
  17 Sprachen wären sofort live. Aktuell 475 Zeilen ungenutzter Übersetzungen.
- **Zwei unabhängige Sprachlisten** ohne Bezug zueinander: Service 5, Widget 17. Keine
  gemeinsame Quelle.
- **Bezug [[jurisdiction-kontext]]:** dessen `eu`-Profil sieht `language: en` vor
  (`profile_language()`), aber es gibt keine EN-Oberfläche, auf die das zeigen könnte.
  Plan-Item **A1 (Frontend-i18n, next-intl, ~300–500 Strings)** ist offen und würde neben
  diesen Bausteinen neu gebaut — nicht auf ihnen. Kein Baustein hier ist dafür Vorarbeit.
