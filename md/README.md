# 🛡️ Complyo – Plattform für Website-Compliance & Automatisierte Rechtsprüfung

Complyo ist eine moderne SaaS-Lösung zur automatisierten Prüfung von Websites auf rechtliche Konformität (DSGVO, TMG, TTDSG, Barrierefreiheit) mit KI-Unterstützung, Dashboard, Report-Generator und integriertem Payment.

---

## 📦 Projektstruktur

```
/opt/projects/saas-project-2/
├── backend/              # FastAPI Backend (API, Auth, Payment, Reports)
│   ├── main_production.py  # Haupt-Einstiegspunkt
│   ├── auth_service.py     # Authentifizierung (bcrypt + JWT)
│   ├── compliance_engine/  # KI-Compliance-Scanner
│   ├── payment/            # Stripe-Integration
│   ├── requirements.txt
│   └── ...
├── dashboard-react/      # Next.js Dashboard (Frontend)
│   ├── src/
│   ├── next.config.js
│   └── ...
├── landing-react/        # Next.js Landing Page
│   ├── src/
│   └── ...
├── simple-admin/         # Admin Panel (Nginx)
├── docs/                 # Dokumentation
│   └── ENV_CONFIGURATION.md  # 🔐 Erforderliche Umgebungsvariablen
├── docker-compose.yml    # Orchestrierung aller Services
├── .env                  # Zentrale Konfiguration (NICHT committen!)
└── README.md
```

> ⚠️ **WICHTIG:** Erstelle vor dem Start eine `.env` Datei!  
> Siehe [`docs/ENV_CONFIGURATION.md`](docs/ENV_CONFIGURATION.md) für alle erforderlichen Variablen.

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

### Mit Docker (empfohlen)

```bash
# 1. .env Datei erstellen (siehe docs/ENV_CONFIGURATION.md)
cp docs/ENV_CONFIGURATION.md .env  # Dann Werte anpassen!

# 2. Generiere sichere Secrets
echo "JWT_SECRET=$(openssl rand -base64 64 | tr -d '\n')" >> .env
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d '\n')" >> .env

# 3. Services starten
docker-compose up -d --build

# 4. Status prüfen
docker-compose ps
docker-compose logs -f backend
```

### Lokale Entwicklung

1. **Backend lokal starten:**
   ```bash
   cd backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   
   # Erforderliche Umgebungsvariablen setzen!
   export JWT_SECRET="your-dev-secret-min-64-chars"
   export DATABASE_URL="postgresql://user:pass@localhost:5432/complyo_db"
   
   uvicorn main_production:app --reload --host 0.0.0.0 --port 8002
   ```

2. **Dashboard lokal starten:**
   ```bash
   cd dashboard-react
   npm install
   npm run dev
   ```

3. **Landing Page lokal starten:**
   ```bash
   cd landing-react
   npm install
   npm run dev
   ```

4. **Datenbank initialisieren:**
   ```bash
   # PostgreSQL starten (Docker oder lokal)
   docker run -d --name complyo-db \
     -e POSTGRES_PASSWORD=devpass \
     -p 5432:5432 postgres:15-alpine
   
   # Schema anwenden
   psql -h localhost -U postgres -f backend/database_setup.sql
   ```

---

## 🛠️ Weiterentwicklung & Hinweise

- **Neue Features:** Siehe TODOs & Issues im Repo
- **Tests:** Unit- und Integrationstests ergänzen empfohlen!
- **Deployment:** Für Produktion alle Secrets & Domains anpassen, SSL aktivieren
- **Support:** Bei Fragen: [admin@complyo.tech](mailto:admin@complyo.tech)

---

**Letztes Update:** 13.08.2025

---
