# Complyo Compliance WordPress Plugin

## Beschreibung

Das **Complyo Compliance** Plugin integriert sicher und automatisch die Complyo Cookie-Banner und Accessibility-Widgets in Ihre WordPress-Website.

### Features

- ✅ **DSGVO-konformes Cookie-Banner** - Automatisches Cookie-Consent-Management
- ✅ **WCAG 2.1 Level AA Accessibility-Widget** - Barrierefreiheits-Tools
- ✅ **Sichere Einbindung** - Scripts werden korrekt im Footer geladen
- ✅ **Automatische Site-ID-Generierung** - Aus Ihrer Domain
- ✅ **Einfache Konfiguration** - Über WordPress Admin-Bereich
- ✅ **Keine Performance-Beeinträchtigung** - Async-Loading

## Installation

### Über WordPress Admin

1. Laden Sie die Plugin-Datei `complyo-compliance.zip` hoch
2. Gehen Sie zu **Plugins** → **Installieren**
3. Aktivieren Sie das Plugin
4. Gehen Sie zu **Einstellungen** → **Complyo Compliance**

### Manuelle Installation

1. Laden Sie das Plugin-Verzeichnis in `/wp-content/plugins/complyo-compliance/` hoch
2. Aktivieren Sie das Plugin im WordPress Admin-Bereich
3. Konfigurieren Sie die Einstellungen unter **Einstellungen** → **Complyo Compliance**

## Konfiguration

### Site-ID

Die **Site-ID** wird automatisch aus Ihrer Domain generiert:
- `beispiel.de` → `beispiel-de`
- `www.beispiel.de` → `beispiel-de`
- `subdomain.beispiel.de` → `subdomain-beispiel-de`

Sie können die Site-ID auch manuell anpassen, falls nötig.

### Cookie-Banner

Das Cookie-Banner wird automatisch eingebunden und zeigt:
- DSGVO-konforme Cookie-Consent-Abfrage
- Granulare Kategorien (Notwendig, Funktional, Statistiken, Marketing)
- Individuelle Einstellungen
- Cookie-Einstellungen-Link im Footer

**Wichtig:** Die Cookie-Banner-Konfiguration (Farben, Texte, Services) erfolgt über Ihr [Complyo-Dashboard](https://app.complyo.tech).

### Accessibility-Widget

Das Accessibility-Widget bietet:
- WCAG 2.1 Level AA Konformität
- Barrierefreiheits-Toolbar
- Automatische Fixes für häufige Probleme
- Anpassbare Schriftgrößen, Kontraste, etc.

## Technische Details

### Script-Ladereihenfolge

Das Plugin lädt die Scripts in der korrekten Reihenfolge:

1. **Cookie Blocker** (muss zuerst geladen werden)
2. **Cookie Banner**
3. **Accessibility Widget**

### Einbindung

Die Scripts werden im `wp_footer` Hook eingefügt (Priorität 999), um sicherzustellen, dass sie nach allen anderen Scripts geladen werden.

### Code-Beispiel

```html
<!-- Complyo Cookie Blocker (muss ZUERST geladen werden) -->
<script src="https://api.complyo.tech/public/cookie-blocker.js" data-site-id="beispiel-de"></script>

<!-- Complyo Cookie Banner -->
<script src="https://api.complyo.tech/api/widgets/cookie-compliance.js" data-site-id="beispiel-de" async></script>

<!-- Complyo Accessibility Widget -->
<script src="https://api.complyo.tech/api/widgets/accessibility.js" data-site-id="beispiel-de" data-auto-fix="true" data-show-toolbar="true" async></script>
```

## Support

Bei Fragen oder Problemen kontaktieren Sie:
- **E-Mail:** support@complyo.tech
- **Website:** https://complyo.tech
- **Dashboard:** https://app.complyo.tech

## Changelog

### Version 1.0.0
- Initial Release
- Cookie-Banner Integration
- Accessibility-Widget Integration
- Automatische Site-ID-Generierung
- WordPress Admin-Interface

## Lizenz

GPL v2 or later

## Autor

Complyo - https://complyo.tech
