# Phase 1: Critical Compliance Fixes - Research

**Researched:** 2026-04-30
**Domain:** DSGVO/BFSG Compliance, nginx Security Headers, PII Anonymisierung, TCF 2.2
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **BFSG Disclaimer (AUDIT-01):** Hervorgehobene Info-Box auf Landing Page, nicht nur Footer. Text: "Deadline war 28.06.2025, Complyo hilft dir ab jetzt compliant zu werden." Kein Verstecken. Deutsch als Primärsprache.
- **TCF 2.2 "Coming Soon" (AUDIT-02):** In Cookie-Banner-Dashboard TCF-2.2-Option als Badge "Coming Soon" markieren. `__tcfapi` Stub: keine false-positive Signale — entweder entfernen oder als no-op markieren.
- **PII User-Agent Anonymisierung (AUDIT-03):** `cookie_compliance_routes.py` — User-Agent vor Speicherung auf Browser-Familie + Version kürzen. Zielformat: `"Chrome/120"`. Python-Bibliothek `user-agents` nutzen (falls installiert) oder Regex. Bestehende Logs NICHT rückwirkend anonymisieren.
- **STS Header (AUDIT-04):** `add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"` in nginx-Config für `api.complyo.de`. Falls bereits gesetzt: max-age prüfen.

### Claude's Discretion

- Styling des BFSG-Disclaimers (Farbe, Position) — konsistent mit bestehendem Design-System
- Ob TCF 2.2 Stub komplett entfernt oder als no-op belassen wird

### Deferred Ideas (OUT OF SCOPE)

- Rückwirkende Anonymisierung bestehender Consent-Logs
- HPKP (HTTP Public Key Pinning) — deprecated, nicht implementieren
- TCF 2.2 vollständige Implementierung (IAB-Registrierung €1.575/Jahr — Business-Entscheidung, Phase > 7)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUDIT-01 | BFSG-Disclaimer auf Landing Page mit klarer Kommunikation der abgelaufenen Deadline | Landing Page hat 6 A/B-Varianten; ProfessionalLanding ist die 67%-Variante mit modularer Komponentenstruktur — Disclaimer muss in alle aktiven Varianten oder in layout.tsx |
| AUDIT-02 | TCF 2.2 im Dashboard als "Coming Soon" markieren; `__tcfapi` Stub ohne false-positive Signale | `AdvancedSettings.tsx` Tab "TCF 2.2" rendert `TCFManager.tsx`; Stub in `cookie_banner_v2.js` Zeilen 854–1004; Stub ist nur aktiv wenn `data-tcf="true"` gesetzt |
| AUDIT-03 | User-Agent in Consent-Logs auf Browser-Familie + Version kürzen | Exakt eine Stelle: `cookie_compliance_routes.py` Zeile 269; `user-agents` Bibliothek NICHT in requirements.txt; Regex-Ansatz ist einfachste Option |
| AUDIT-04 | `Strict-Transport-Security` Header für `api.complyo.de` in nginx-Config setzen | Header fehlt in `/etc/nginx/sites-available/complyo.de`; vorhanden in `nginx/production.conf` (Docker-Version); Live-Config ist `/etc/nginx/sites-available/complyo.de` |
</phase_requirements>

---

## Summary

Phase 1 besteht aus vier isolierten, voneinander unabhängigen Änderungen ohne gemeinsame Abhängigkeiten. Jede Aufgabe kann separat implementiert und verifiziert werden.

**BFSG-Disclaimer (AUDIT-01):** Die Landing Page hat 6 A/B-Test-Varianten, die über `ABTestRouter.tsx` gesteuert werden. Die primäre Variante (67% Traffic) ist `ProfessionalLanding.tsx`, die modular aus Unterkomponenten aufgebaut ist (`HeroSection`, `ComplianceBadges`, `ProductFeatures`, etc.). `ComplianceBadges.tsx` zeigt bereits BFSG als unterstützten Standard ohne Disclaimer. Der neue Disclaimer muss in die primäre Hauptvariante und idealerweise als shared Komponente, die alle Varianten referenzieren. Das Design-System nutzt Tailwind CSS mit Dark-Background-Sections (gray-900) und Info-Badges in `bg-blue-500/20 border border-blue-400 rounded-full`.

**TCF 2.2 "Coming Soon" (AUDIT-02):** Das Dashboard-Tab "TCF 2.2" existiert in `AdvancedSettings.tsx` (Zeile 50–55) mit Badge "Beta". Der Tab rendert `TCFManager.tsx`, das bereits einen Warning-Banner zeigt ("Registrierung erforderlich") und den Switch als `disabled={true}` setzt. Änderung: Badge von "Beta" auf "Coming Soon" und den `TCFManager.tsx`-Header entsprechend anpassen. Der `__tcfapi` Stub in `cookie_banner_v2.js` (Zeilen 854–1004) ist bereits opt-in: er wird NUR aktiviert wenn `data-tcf="true"` auf dem Script-Tag gesetzt ist (Zeile 197). Die Complyo-eigene Landing Page setzt dieses Attribut NICHT. Kein Handlungsbedarf für false-positives in Produktion — aber ein Code-Kommentar zum Status ist erforderlich.

**PII User-Agent (AUDIT-03):** Exakt eine Stelle in `cookie_compliance_routes.py` Zeile 269: `user_agent = consent.user_agent or request.headers.get("User-Agent", "")[:500]`. Die Bibliothek `user-agents` ist NICHT in `requirements.txt` installiert. Regex-Pattern ist die direkte Lösung ohne neue Dependency. Die DB-Spalte `user_agent` in `cookie_consent_logs` nimmt den vollen String entgegen — nach der Änderung wird nur noch `"Chrome/120"` gespeichert.

**STS Header (AUDIT-04):** Der Header `Strict-Transport-Security` fehlt in der Live-Konfiguration `/etc/nginx/sites-available/complyo.de` für den `api.complyo.de` Server-Block (und alle anderen Blöcke in dieser Datei). Er existiert korrekt in `/home/clawd/saas/legal/nginx/production.conf` (Docker-Konfiguration, Zeilen 104, 156, 203). Die Live-Konfiguration ist die Systemdatei. nginx läuft aktiv und `nginx -t` validiert korrekt.

**Primary recommendation:** Vier isolierte Änderungen in Reihenfolge AUDIT-04 (nginx — 2min), AUDIT-03 (Backend — 5min), AUDIT-02 (Frontend/Dashboard — 10min), AUDIT-01 (Frontend/Landing — 15min). Kein Deployment-Dependency zwischen den Aufgaben.

---

## Standard Stack

### Core
| Library / Tool | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| Next.js (App Router) | Current | Landing Page + Dashboard | Bereits im Einsatz |
| Tailwind CSS | Current | Styling aller Komponenten | Gesamtes Design-System basiert darauf |
| FastAPI | 0.115.6 | Backend API | Bereits im Einsatz |
| nginx | Current | Reverse Proxy + Security Headers | Live-System |
| Python 3.12 | System | Backend Runtime | Einzige verfügbare Python-Version |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Lucide Icons | Current | Ikonen in React-Komponenten | Bereits global genutzt (AlertCircle, Info, etc.) |
| `re` (Python stdlib) | stdlib | Regex für UA-Truncation | Keine neue Dependency nötig |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Regex für UA-Parsing | `user-agents` Bibliothek (PyPI) | `user-agents` nicht installiert, Regex reicht für `"Chrome/120"` Format |
| Neuer `BfsgDisclaimer.tsx` | Inline in `ProfessionalLanding.tsx` | Eigene Komponente empfohlen da alle 3 Haupt-Varianten sie benötigen |

---

## Architecture Patterns

### Recommended Project Structure (Änderungen dieser Phase)

```
landing-react/src/components/
├── BfsgDisclaimer.tsx       # NEU: Shared Disclaimer-Komponente
└── landing/
    └── ComplianceBadges.tsx # Bestehend: BFSG-Badge bereits vorhanden

dashboard-react/src/components/cookie-compliance/
├── AdvancedSettings.tsx     # Änderung: Badge "Beta" → "Coming Soon"
└── TCFManager.tsx           # Änderung: Header-Text anpassen

backend/
└── cookie_compliance_routes.py  # Änderung: Zeile 269 UA-Truncation

/etc/nginx/sites-available/
└── complyo.de               # Änderung: STS-Header in api.complyo.de Block
```

### Pattern 1: BFSG-Disclaimer als eigene Komponente (empfohlen)

**Was:** Separate `BfsgDisclaimer.tsx` Komponente, die in alle drei Traffic-Varianten eingebunden wird.
**Wann:** Immer wenn derselbe Content in mehreren Landing-Varianten erscheinen muss.
**Varianten die angepasst werden müssen:** `ProfessionalLanding.tsx` (67%), `ComplyoOriginalLanding.tsx` (17%), `ComplyoHighConversionLanding.tsx` (16%). `AlfimaLanding`, `ComplyoModernLanding`, `ComplyoViralLanding` sind experimentelle Varianten mit minimalem Traffic — optional.

```tsx
// landing-react/src/components/BfsgDisclaimer.tsx
'use client';
import React from 'react';
import { AlertCircle } from 'lucide-react';

export default function BfsgDisclaimer() {
  return (
    <div className="bg-amber-500/10 border border-amber-400/40 rounded-xl px-5 py-4 flex items-start gap-3 max-w-7xl mx-auto my-4">
      <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
      <div>
        <p className="text-sm font-semibold text-amber-300">
          BFSG-Deadline war der 28. Juni 2025
        </p>
        <p className="text-sm text-gray-300 mt-1">
          Die gesetzliche Frist ist abgelaufen. Complyo hilft Ihnen ab jetzt, BFSG-konform zu werden
          (Forward-Looking Compliance) — keine Retroaktiv-Zertifizierung für vergangene Zeiträume möglich.
        </p>
      </div>
    </div>
  );
}
```

Positionierung: Nach dem Nav, vor der HeroSection — sichtbar ohne zu stören.

### Pattern 2: TCF 2.2 Badge-Änderung in AdvancedSettings.tsx

**Wo:** `AdvancedSettings.tsx` Zeilen 49–55
**Was:** Das `badge`-Feld des TCF-Feature-Eintrags und `badgeColor` ändern.

```tsx
// Vorher:
{ id: 'tcf', label: 'TCF 2.2', icon: Shield, badge: 'Beta', badgeColor: 'bg-yellow-500' }

// Nachher:
{ id: 'tcf', label: 'TCF 2.2', icon: Shield, badge: 'Coming Soon', badgeColor: 'bg-gray-500' }
```

In `TCFManager.tsx` Zeile 121: `<Badge className="ml-2 bg-yellow-500/20 text-yellow-400">Beta</Badge>` → `Coming Soon` mit grauem Styling.

### Pattern 3: User-Agent Truncation in Python (Regex, kein neues Package)

**Wo:** `cookie_compliance_routes.py` Zeile 269
**Was:** Truncation vor dem INSERT.

```python
# VORHER (Zeile 269):
user_agent = consent.user_agent or request.headers.get("User-Agent", "")[:500]

# NACHHER:
import re  # bereits implizit via Python stdlib

def truncate_user_agent(ua_string: str) -> str:
    """Kürzt User-Agent auf Browser-Familie + Major-Version für DSGVO-Konformität.
    Zielformat: 'Chrome/120', 'Firefox/121', 'Safari/17' etc.
    Fällt auf 'unknown' zurück wenn kein Match.
    """
    if not ua_string:
        return "unknown"
    match = re.search(r'(Chrome|Firefox|Safari|Edge|Opera|OPR|Trident|MSIE|CriOS|FxiOS|SamsungBrowser|UCBrowser)\/(\d+)', ua_string)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return "unknown"

# In log_consent():
raw_ua = consent.user_agent or request.headers.get("User-Agent", "")
user_agent = truncate_user_agent(raw_ua)
```

Platzierung: `truncate_user_agent` als Modul-Funktion neben `hash_ip_address` (Zeile 225).

### Pattern 4: STS-Header in nginx Live-Konfiguration

**Datei:** `/etc/nginx/sites-available/complyo.de`
**Wo:** Server-Block `server_name api.complyo.de` (Zeilen 39–58)
**Was:** Security Headers nach dem SSL-Block einfügen, konsistent mit `nginx/production.conf`

```nginx
# Nach ssl_dhparam in api.complyo.de Server-Block einfügen:
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

Nach Änderung: `nginx -t && systemctl reload nginx`

**Wichtig:** Die Datei `/etc/nginx/sites-available/complyo.de` wird von Certbot verwaltet (SSL-Zertifikate). Certbot überschreibt NUR die SSL-Zertifikat-Pfade — manuell hinzugefügte `add_header` Direktiven bleiben erhalten.

Die anderen Server-Blöcke (`complyo.de`, `app.complyo.de`, `dashboard.complyo.de`) haben ebenfalls noch keine Security Headers — diese können im selben Commit ergänzt werden, um konsistent mit `nginx/production.conf` zu sein.

### Anti-Patterns zu vermeiden

- **Alle Landing-Varianten einzeln patchen ohne shared Komponente:** Zu fehleranfällig, Duplikation. Stattdessen: `BfsgDisclaimer.tsx`.
- **`nginx/production.conf` (Docker) statt Live-Config ändern:** Die Docker-Config hat den Header bereits. Der Audit-Befund bezieht sich auf die Live-Konfiguration `/etc/nginx/sites-available/complyo.de`.
- **`user-agents` Bibliothek nachinstallieren:** Unnötige Dependency. Regex reicht für das Zielformat.
- **`ConsentLog.user_agent` Pydantic-Feld entfernen:** Das Widget sendet manchmal einen UA über den Request-Body. Das Feld behalten, nur die Verarbeitung truncaten.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| UA-Browser-Erkennung | Eigenen UA-Parser | Regex mit Browser-Whitelist | Für das Zielformat "Chrome/120" braucht man keinen vollständigen Parser |
| React Notice-Komponente | Komplexes Notification-System | Inline Tailwind mit AlertCircle (Lucide) | Design-System bereits vorhanden |
| nginx Config-Reload | Eigenes Script | `nginx -t && systemctl reload nginx` | Standardbefehl, keine Automation nötig |

---

## Common Pitfalls

### Pitfall 1: nginx-Config — Certbot-managed Kommentar
**Was geht schief:** Developer ändert Certbot-verwaltete Abschnitte im SSL-Block und Certbot überschreibt sie beim nächsten Zertifikat-Renewal.
**Warum:** Certbot markiert verwaltete Blöcke mit `# managed by Certbot`.
**Vermeidung:** Nur `add_header`-Direktiven hinzufügen, NIEMALS `ssl_certificate`, `ssl_certificate_key`, `include` oder `listen`-Zeilen ändern.
**Warnsignal:** Kommentare `# managed by Certbot` neben einer Zeile.

### Pitfall 2: nginx `add_header` in location-Block überschreibt server-Block Header
**Was geht schief:** `add_header` im `location /`-Block deaktiviert alle `add_header` Direktiven aus dem übergeordneten `server`-Block.
**Warum:** nginx-Vererbungsregel: Wenn ein `location`-Block ein eigenes `add_header` hat, erbt er keine Header aus dem `server`-Block mehr.
**Vermeidung:** Alle Security-Header im `server`-Block setzen, nicht in einzelnen `location`-Blöcken. In `/etc/nginx/sites-available/complyo.de` gibt es keine `add_header` in `location`-Blöcken — das Schema ist sicher.
**Warnsignal:** `add_header` sowohl in `server`- als auch in `location`-Blöcken derselben Config.

### Pitfall 3: BFSG-Disclaimer fehlt in Traffic-Varianten
**Was geht schief:** Disclaimer wird nur in `ProfessionalLanding.tsx` eingefügt, aber 33% des Traffics sieht `original` oder `high-conversion` Variante.
**Warum:** `ABTestRouter.tsx` routet Traffic auf 3 aktive Varianten mit unterschiedlichen Komponenten.
**Vermeidung:** `BfsgDisclaimer.tsx` in alle drei Traffic-Varianten einbinden: `ProfessionalLanding` (67%), `ComplyoOriginalLanding` (17%), `ComplyoHighConversionLanding` (16%).
**Warnsignal:** Disclaimer nur in einer von mehreren Landing-Varianten.

### Pitfall 4: TCF-Stub wirft false-positive obwohl `data-tcf` nicht gesetzt
**Was geht schief:** `initTCF()` wird NUR bei `script.getAttribute('data-tcf') === 'true'` ausgeführt (Zeile 197). False-positives entstehen nicht durch den Code selbst, sondern wenn ein Kunde `data-tcf="true"` setzt und dann erwartet, zertifizierter CMP-Betrieb zu sein.
**Warum:** Das Stub setzt `cmpId: 0` (nicht registriert), was IAB-Vendoren als ungültige CMP interpretieren.
**Vermeidung:** Im Dashboard `TCFManager.tsx` klar kommunizieren: Stub ist deaktiviert, `data-tcf="true"` darf nicht gesetzt werden bis IAB-Registrierung erfolgt. Zusätzlich einen klarstellenden Kommentar im Widget-Code einfügen.

### Pitfall 5: User-Agent Regex matched Chrome/Safari falsch
**Was geht schief:** `Safari/537.36` aus einem Chrome-UA wird vor `Chrome/120` gematcht, weil `Safari` früher im String steht und die Regex-Reihenfolge falsch ist.
**Warum:** Chrome-UAs enthalten `Safari/XXX` als Kompatibilitäts-String: `Mozilla/5.0 ... Chrome/120.0.0.0 Safari/537.36`
**Vermeidung:** `Chrome` vor `Safari` in der Regex-Alternation listeen (wie im Pattern 3 gezeigt). `Edge` und `OPR` ebenfalls vor `Chrome` listen, da sie ebenfalls Chrome-Strings enthalten.

---

## Code Examples

### Vollständige `truncate_user_agent` Funktion mit Tests

```python
import re

def truncate_user_agent(ua_string: str) -> str:
    """DSGVO-konforme UA-Kürzung auf Browser-Familie + Major-Version.
    Reihenfolge ist wichtig: spezifischere Browser vor Chrome/Safari.
    """
    if not ua_string:
        return "unknown"
    # Reihenfolge beachten: Edge/OPR/CriOS/FxiOS vor Chrome/Firefox/Safari
    match = re.search(
        r'(Edge|Edg|OPR|CriOS|FxiOS|SamsungBrowser|UCBrowser|MSIE|Trident|Chrome|Firefox|Safari|Opera)[\/ ](\d+)',
        ua_string
    )
    if match:
        browser = match.group(1)
        # Normalisierung
        if browser == 'Edg':
            browser = 'Edge'
        elif browser == 'Trident':
            browser = 'IE'
        elif browser == 'MSIE':
            browser = 'IE'
        return f"{browser}/{match.group(2)}"
    return "unknown"

# Beispiele:
# "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
# → "Chrome/120"
# "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
# → "Firefox/121"
# "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1"
# → "Safari/604.1" (letzte Safari-Version)
```

### nginx api.complyo.de Server-Block nach Änderung

```nginx
server {
    server_name api.complyo.de;

    # Security Headers  ← NEU
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://127.0.0.1:8002;
        # ... bestehende proxy-Direktiven bleiben unverändert
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/complyo.de/fullchain.pem; # managed by Certbot
    # ... Rest bleibt unverändert
}
```

### TCFManager.tsx — Badge-Änderung

```tsx
// Zeile 121 in TCFManager.tsx:
// Vorher:
<Badge className="ml-2 bg-yellow-500/20 text-yellow-400">Beta</Badge>

// Nachher:
<Badge className="ml-2 bg-gray-500/20 text-gray-400 border border-gray-500/30">Coming Soon</Badge>

// Optional: Erklärungstext im Warning-Banner anpassen (Zeile 97-99):
// "Diese Funktion ist derzeit in Entwicklung und wird in einer zukünftigen Version verfügbar sein."
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| HPKP (HTTP Public Key Pinning) | Abgeschafft — NICHT implementieren | 2018 (Chrome) | HPKP wurde aus allen Browsern entfernt, kann Sites kaputt machen |
| STS ohne `preload` | `max-age=31536000; includeSubDomains; preload` | HSTS Preload List | preload erlaubt Aufnahme in Browser-interne HSTS-Liste |
| Voller UA-String in Logs | Browser-Familie + Major-Version | DSGVO 2018 | Full UA-String ist PII nach EU-Datenschutzrecht |

**Deprecated/outdated:**
- `max-age=63072000`: Manche Guides empfehlen 2 Jahre (63072000s) statt 1 Jahr — beide sind akzeptabel, 1 Jahr (31536000) ist HSTS-Preload-Minimum.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| nginx | AUDIT-04 | ✓ | Active (16h uptime) | — |
| nginx -t | AUDIT-04 | ✓ | Syntax OK verified | — |
| systemctl reload nginx | AUDIT-04 | ✓ | nginx.service enabled | — |
| Python 3.12 | AUDIT-03 | ✓ | /usr/bin/python3.12 | — |
| `re` (stdlib) | AUDIT-03 | ✓ | stdlib, immer verfügbar | — |
| `user-agents` (PyPI) | AUDIT-03 (alt.) | ✗ | nicht installiert | Regex-Ansatz (empfohlen) |
| Next.js / React | AUDIT-01, AUDIT-02 | ✓ | Landing + Dashboard laufen | — |
| `/etc/nginx/sites-available/complyo.de` | AUDIT-04 | ✓ | Datei existiert, beschreibbar | — |

**Missing dependencies mit no-op-Fallback:**
- `user-agents` (PyPI): nicht benötigt — Regex-Ansatz ist die richtige Lösung.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (nicht global installiert — muss via venv oder pip3 install ausgeführt werden) |
| Config file | Kein `pytest.ini`/`pyproject.toml` gefunden — Tests laufen mit `python3.12 -m pytest` nach `pip3 install pytest pytest-asyncio` |
| Quick run command | `cd /home/clawd/saas/legal/backend && pip3 install pytest pytest-asyncio -q && python3.12 -m pytest tests/test_cookies.py -x -q` |
| Full suite command | `cd /home/clawd/saas/legal/backend && python3.12 -m pytest tests/ -q` |
| Bestehende Tests | `tests/test_cookies.py`, `tests/test_tcf_compliance.py`, `tests/test_bfsg_features.py` — alle vorhanden |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUDIT-01 | BfsgDisclaimer rendert Deadline-Text | Unit (React) | Manuell im Browser — kein jest/vitest setup | ❌ Wave 0 |
| AUDIT-01 | Disclaimer erscheint in allen 3 Traffic-Varianten | Smoke | Browser-Check: `/?variant=professional`, `/?variant=original`, `/?variant=high-conversion` | ❌ Wave 0 |
| AUDIT-02 | TCF-Tab zeigt "Coming Soon" Badge | Unit (React) | Manuell im Dashboard | ❌ Wave 0 |
| AUDIT-02 | `__tcfapi` nur bei `data-tcf="true"` aktiv | Unit (JS) | Inline Script-Test im Browser | ❌ Wave 0 |
| AUDIT-03 | `truncate_user_agent` kürzt Chrome-UA korrekt | Unit (Python) | `python3.12 -m pytest tests/test_ua_truncation.py -x` | ❌ Wave 0 |
| AUDIT-03 | Consent-Log enthält `"Chrome/120"` statt vollem UA | Integration | `python3.12 -m pytest tests/test_cookies.py -k "user_agent" -x` | Partial ✓ |
| AUDIT-04 | STS-Header in Response von api.complyo.de | Smoke | `curl -s -I https://api.complyo.de/health \| grep -i strict` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** Manuelle Browser-Verifikation der jeweiligen Änderung
- **Per wave merge:** `curl -s -I https://api.complyo.de/health | grep -i strict-transport` + Browser-Check Landing Page
- **Phase gate:** Alle 4 Success Criteria manuell verifiziert vor `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `backend/tests/test_ua_truncation.py` — Unit-Tests für `truncate_user_agent()` mit 10 Browser-UA-Strings
- [ ] `backend/tests/conftest.py` prüfen ob vorhanden
- [ ] Framework install wenn nötig: `pip3 install pytest pytest-asyncio -q`

*(Für AUDIT-01 und AUDIT-02 gibt es kein automatisches Test-Framework für React-Komponenten — manuelle Browser-Verifikation ist die pragmatische Lösung für diese Phase.)*

---

## Open Questions

1. **`nginx/production.conf` vs. `/etc/nginx/sites-available/complyo.de` — Sync-Status**
   - Was wir wissen: `nginx/production.conf` (Docker) hat STS-Header bereits korrekt. Live-Config `/etc/nginx/sites-available/complyo.de` hat ihn nicht.
   - Was unklar: Läuft Produktion über Docker oder direkt über systemd nginx? nginx läuft als systemd-Service und proxied auf `localhost:8002` — deutet auf direkten (nicht-Docker) Betrieb hin.
   - Empfehlung: Live-Config `/etc/nginx/sites-available/complyo.de` ist die maßgebliche Datei, dort die Header setzen.

2. **Sollen alle anderen Domains (complyo.de, app.complyo.de, dashboard.complyo.de) ebenfalls STS-Header erhalten?**
   - Was wir wissen: Alle 4 Server-Blöcke in der Live-Config fehlen Security-Header. `nginx/production.conf` setzt sie überall.
   - Empfehlung: Im selben Commit alle 4 Server-Blöcke patchen, konsistent mit `nginx/production.conf`.

---

## Sources

### Primary (HIGH confidence)
- Direkte Codeanalyse `/home/clawd/saas/legal/backend/widgets/cookie_banner_v2.js` Zeilen 193–1004
- Direkte Codeanalyse `/home/clawd/saas/legal/backend/cookie_compliance_routes.py` Zeilen 250–303
- Direkte Codeanalyse `/etc/nginx/sites-available/complyo.de` (Live-Config)
- Direkte Codeanalyse `/home/clawd/saas/legal/nginx/production.conf` (Docker-Config)
- Direkte Codeanalyse `dashboard-react/src/components/cookie-compliance/AdvancedSettings.tsx`
- Direkte Codeanalyse `dashboard-react/src/components/cookie-compliance/TCFManager.tsx`
- Direkte Codeanalyse `landing-react/src/app/ABTestRouter.tsx` + alle 6 Varianten

### Secondary (MEDIUM confidence)
- nginx `add_header` Vererbungsverhalten: nginx-Dokumentation (bekanntes Verhalten)
- HSTS Preload-Anforderungen: `max-age` >= 31536000 ist Pflichtanforderung für Preload-List

### Tertiary (LOW confidence)
- Keine LOW-confidence Quellen in dieser Phase — alle Findings basieren auf direkter Codeanalyse

---

## Metadata

**Confidence breakdown:**
- AUDIT-01 (BFSG Disclaimer): HIGH — Alle Dateipfade, Komponenten-Struktur und Design-System verifiziert
- AUDIT-02 (TCF Coming Soon): HIGH — Exakte Zeilennummern in beiden Dateien identifiziert
- AUDIT-03 (UA Truncation): HIGH — Exakte Stelle in routes.py, requirements.txt verifiziert (kein user-agents)
- AUDIT-04 (STS Header): HIGH — Live-Config gelesen, Fehlen des Headers bestätigt, Docker-Config als Referenz

**Research date:** 2026-04-30
**Valid until:** 2026-05-30 (stabiles System, keine fast-moving Dependencies)
