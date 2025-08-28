# 🛡️ Complyo – Plattform für Website-Compliance & Automatisierte Rechtsprüfung

Complyo ist eine moderne SaaS-Lösung zur automatisierten Prüfung von Websites auf rechtliche Konformität (DSGVO, TMG, TTDSG, Barrierefreiheit) mit KI-Unterstützung, Dashboard, Report-Generator und integriertem Payment.

---

## 📦 Projektstruktur

```
/opt/projects/saas-project-2/
├── backend/              # FastAPI Backend (API, Auth, Payment, Reports)
│   ├── main.py
│   ├── payment_routes.py
│   ├── report_generator.py
│   ├── requirements.txt
│   ├── database_setup.sql
│   └── ...
├── dashboard/            # Next.js Dashboard (Frontend)
│   ├── pages/
│   ├── next.config.js
│   └── ...
├── docker-compose.yml    # Orchestrierung aller Services
├── .env                  # Zentrale Konfiguration (Secrets, Keys)
└── README.md
```

---

## 🚀 Deployment & Entwicklung

### Voraussetzungen

- Docker & Docker Compose
- Python 3.11+ (für lokale Backend-Entwicklung)
- Node.js 18+ (für das Dashboard)
- PostgreSQL & Redis (werden via Docker bereitgestellt)

### Starten (lokal & Produktion)

```bash
# Build & Start aller Services
docker-compose up -d --build

# Status prüfen
docker-compose ps

# Logs anzeigen
docker-compose logs -f [service]
```

### Wichtige Umgebungsvariablen (.env)

- `DATABASE_URL` – PostgreSQL-URL
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
- `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET` – für Zahlungen
- `OPENROUTER_API_KEY` – für KI-Analysen
- `SESSION_SECRET`, `JWT_SECRET` – für Authentifizierung

> **Hinweis:** Beispielwerte findest du in der `docker-compose.yml` und `.env`. Alle Secrets müssen für Produktion angepasst werden!

---

## 🌐 Services & Endpunkte

### Backend (FastAPI, Port 8002)

- **/api/auth/login** – Login (Session-basiert)
- **/api/auth/logout** – Logout
- **/api/auth/me** – Aktueller User
- **/api/analyze** – Website-Analyse (KI-gestützt, DSGVO, TMG, TTDSG, Barrierefreiheit)
- **/api/user/analyses** – Analysen des Users (Platzhalter)
- **/api/dashboard/overview** – Statistiken fürs Dashboard
- **/api/analytics/summary** – Analytics-Daten
- **/api/legal/news** – Aktuelle Rechtsnews
- **/api/payment/** – Stripe-Checkout, Verifizierung, Webhooks (siehe `payment_routes.py`)
- **/api/report/** – PDF-Report-Generierung (siehe `report_generator.py`)

### Frontend (Next.js Dashboard, Port 3002)

- **/dashboard/** – Nutzeroberfläche für Analysen, Reports, Account, Zahlungen

---

## 🧠 Features im Überblick

- **KI-Analyse:** Automatische Prüfung von Websites auf DSGVO, TMG, TTDSG, Barrierefreiheit inkl. Risikobewertung & Empfehlungen (OpenRouter/Claude-API).
- **User Auth:** Session-basierte Authentifizierung, User-DB, Rollen, Status.
- **Payment:** Stripe-Integration für Abos & Einmalzahlungen, Webhooks, DB-Update.
- **Reports:** PDF-Report-Generator mit Jinja2 & pdfkit, individuelle Empfehlungen.
- **Datenbank:** PostgreSQL mit ausgefeiltem Schema (User, Websites, Scans, Teams, Payments).
- **API-Gateway:** Nginx für Routing & SSL (siehe docker-compose).
- **Monitoring:** Health- & Status-Endpunkte, Logging.
- **Moderne Architektur:** Klare Trennung von Backend, Frontend, Gateway, Datenbank.

---

## 🗄️ Datenbankstruktur (PostgreSQL)

- **users:** User-Accounts, Abos, Limits, Security
- **websites:** Verwaltete Websites, Scan-Settings, Status
- **scans:** Scan-Resultate, Scores, Issues, Metadaten
- **teams/team_members:** Team-Features, Rollen, Rechte
- **expert_setups:** Experten-Setup-Zahlungen (Stripe)
- **Migration:** Siehe `backend/database_setup.sql` für vollständiges Schema & Beispiel-Admin

---

## 💳 Stripe Payment-Flow

- **/api/payment/create-checkout-session** – Erstellt Stripe-Session (Abo/Einmalzahlung)
- **/api/payment/verify/{session_id}** – Verifiziert Zahlung, aktualisiert Abo
- **/api/payment/webhook** – Webhook für Stripe-Events (Abo, Einmalzahlung, Experten-Setup)
- **Preis-IDs:** Im Stripe-Dashboard anlegen & in `payment_routes.py` pflegen

---

## 📝 Reports & Compliance-Empfehlungen

- **/api/report/** – PDF-Reports mit individuellen Empfehlungen, Risikobewertung, Score
- **Templates:** Jinja2-Templates im Backend, pdfkit für PDF-Export

---

## 👨‍💻 Entwickler-Quickstart

1. **Backend lokal starten:**
   ```bash
   cd backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn main.py --reload --host 0.0.0.0 --port 8002
   ```

2. **Frontend lokal starten:**
   ```bash
   cd dashboard
   npm install
   npm run dev
   ```

3. **Datenbank initialisieren:**
   - PostgreSQL starten (Docker oder lokal)
   - `backend/database_setup.sql` ausführen

4. **.env anpassen:** Alle Secrets & Keys setzen!

---

## 🛠️ Weiterentwicklung & Hinweise

- **Neue Features:** Siehe TODOs & Issues im Repo
- **Tests:** Unit- und Integrationstests ergänzen empfohlen!
- **Deployment:** Für Produktion alle Secrets & Domains anpassen, SSL aktivieren
- **Support:** Bei Fragen: [admin@complyo.tech](mailto:admin@complyo.tech)

---

**Letztes Update:** 13.08.2025

---
