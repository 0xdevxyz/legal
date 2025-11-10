# ComploAI Guard - EU AI Act Compliance Modul

## Übersicht

Das **ComploAI Guard** Modul erweitert Complyo um vollständige EU AI Act Compliance-Funktionalität. Es ermöglicht Unternehmen, ihre KI-Systeme auf Compliance mit der EU KI-Verordnung zu prüfen.

## Features

### ✅ Kernfunktionen

1. **Automatische Risiko-Klassifizierung**
   - Klassifizierung in 4 Kategorien: Verboten, Hochrisiko, Begrenztes Risiko, Minimales Risiko
   - KI-gestützte Analyse basierend auf Verwendungszweck und Kontext
   - Confidence-Score für Transparenz

2. **Compliance-Checks**
   - Automatische Prüfung gegen AI Act Anforderungen (Art. 8-15)
   - Identifikation erfüllter und nicht erfüllter Requirements
   - Konkrete Handlungsempfehlungen

3. **AI-System-Inventar**
   - Zentrale Verwaltung aller KI-Systeme
   - Tracking von Deployment-Daten, Vendor, Zweck
   - Status-Übersicht (aktiv, pausiert, archiviert)

4. **Dokumentations-Management**
   - Automatische Generierung erforderlicher Dokumentation
   - Versionierung und Approval-Workflow
   - Download als PDF

5. **Dashboard & Reporting**
   - Übersicht aller KI-Systeme
   - Risiko-Distribution-Charts
   - Compliance-Score-Tracking
   - Scan-Historie

## Installation

### 1. Datenbank-Migration

Für **bestehende** Complyo-Installationen:

```bash
cd /opt/projects/saas-project-2/backend
psql -U complyo_user -d complyo_db -f migration_ai_compliance.sql
```

Für **neue** Installationen ist die Migration bereits in `database_setup.sql` enthalten.

### 2. Environment Variables

Füge folgende Variablen zur `.env` hinzu:

```bash
# OpenRouter API für KI-Analysen
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Stripe Price IDs für Add-ons (erstelle diese im Stripe Dashboard)
STRIPE_PRICE_COMPLOAI_GUARD=price_xxxxx
STRIPE_PRICE_PRIORITY_SUPPORT=price_xxxxx
STRIPE_PRICE_EXPERT_AUDIT=price_xxxxx
STRIPE_PRICE_IMPLEMENTATION=price_xxxxx
STRIPE_PRICE_CUSTOM_INTEGRATION=price_xxxxx

# Stripe Webhook Secret für Add-ons
STRIPE_WEBHOOK_SECRET_ADDONS=whsec_xxxxx
```

### 3. Stripe-Konfiguration

#### 3.1 Produkte und Preise erstellen

Erstelle folgende Produkte im [Stripe Dashboard](https://dashboard.stripe.com/products):

**Monatliche Add-ons:**

1. **ComploAI Guard**
   - Name: "ComploAI Guard - EU AI Act Compliance"
   - Preis: 99€/Monat (recurring)
   - Billing-Intervall: Monatlich
   - Kopiere die Price ID → `STRIPE_PRICE_COMPLOAI_GUARD`

2. **Priority Support**
   - Name: "Priority Support - 24/7 Premium Support"
   - Preis: 49€/Monat (recurring)
   - Billing-Intervall: Monatlich
   - Kopiere die Price ID → `STRIPE_PRICE_PRIORITY_SUPPORT`

**Einmalige Add-ons:**

3. **Expert AI Act Audit**
   - Name: "Expert AI Act Audit"
   - Preis: 2.999€ (one-time)
   - Kopiere die Price ID → `STRIPE_PRICE_EXPERT_AUDIT`

4. **Implementation Support**
   - Name: "AI Act Implementation Support"
   - Preis: 1.999€ (one-time)
   - Kopiere die Price ID → `STRIPE_PRICE_IMPLEMENTATION`

5. **Custom Integration**
   - Name: "Custom Integration Service"
   - Preis: 3.999€ (one-time)
   - Kopiere die Price ID → `STRIPE_PRICE_CUSTOM_INTEGRATION`

#### 3.2 Webhooks konfigurieren

Erstelle einen Webhook-Endpoint im Stripe Dashboard:

- URL: `https://api.complyo.tech/api/addons/webhook`
- Events auswählen:
  - `checkout.session.completed`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_succeeded`
  - `invoice.payment_failed`
- Kopiere den Signing Secret → `STRIPE_WEBHOOK_SECRET_ADDONS`

### 4. Server neu starten

```bash
cd /opt/projects/saas-project-2
docker-compose restart backend
```

## API-Endpunkte

### AI Systems Management

#### Neues KI-System registrieren
```http
POST /api/ai/systems
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "ChatBot für Kundenservice",
  "description": "KI-gestützter Chatbot zur Beantwortung von Kundenfragen",
  "vendor": "OpenAI",
  "purpose": "Automatisierung des Kundensupports",
  "domain": "customer_service",
  "deployment_date": "2024-01-15",
  "data_types": ["customer_messages", "support_tickets"],
  "affected_persons": ["customers", "support_agents"]
}
```

#### Alle KI-Systeme abrufen
```http
GET /api/ai/systems
Authorization: Bearer {token}
```

#### KI-System Details
```http
GET /api/ai/systems/{system_id}
Authorization: Bearer {token}
```

#### KI-System aktualisieren
```http
PUT /api/ai/systems/{system_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "paused",
  "description": "Aktualisierte Beschreibung"
}
```

#### KI-System löschen
```http
DELETE /api/ai/systems/{system_id}
Authorization: Bearer {token}
```

### Compliance Scanning

#### Compliance-Scan starten
```http
POST /api/ai/systems/{system_id}/scan
Authorization: Bearer {token}
Content-Type: application/json

{
  "force_rescan": false
}
```

Response:
```json
{
  "scan_id": "uuid",
  "ai_system_id": "uuid",
  "compliance_score": 75,
  "overall_risk_score": 6.5,
  "risk_category": "high",
  "status": "completed",
  "created_at": "2025-01-03T10:30:00Z"
}
```

#### Scan-Ergebnisse abrufen
```http
GET /api/ai/scans/{scan_id}
Authorization: Bearer {token}
```

#### Alle Scans eines Systems
```http
GET /api/ai/systems/{system_id}/scans?limit=10
Authorization: Bearer {token}
```

### AI Act Knowledge Base

#### Alle Requirements abrufen
```http
GET /api/ai/act/requirements
```

#### Requirements nach Risikokategorie
```http
GET /api/ai/act/requirements/{risk_category}
```

Mögliche Kategorien: `prohibited`, `high`, `limited`, `minimal`

### Dokumentation

#### Erforderliche Dokumentation abrufen
```http
GET /api/ai/systems/{system_id}/documentation
Authorization: Bearer {token}
```

### Statistics

#### AI Compliance Dashboard-Stats
```http
GET /api/ai/stats
Authorization: Bearer {token}
```

Response:
```json
{
  "total_systems": 5,
  "risk_distribution": {
    "high": 2,
    "limited": 2,
    "minimal": 1
  },
  "average_compliance_score": 72.5,
  "scans_last_30_days": 12
}
```

## Add-On Management

### Add-ons Katalog abrufen
```http
GET /api/addons/catalog
```

### Eigene Add-ons abrufen
```http
GET /api/addons/my-addons
Authorization: Bearer {token}
```

### Add-on abonnieren (monatlich)
```http
POST /api/addons/subscribe/comploai_guard
Authorization: Bearer {token}
Content-Type: application/json

{
  "addon_key": "comploai_guard",
  "user_plan": "professional"
}
```

Response:
```json
{
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_xxxxx"
}
```

### Einmaliges Add-on kaufen
```http
POST /api/addons/purchase/expert_ai_audit
Authorization: Bearer {token}
```

### Add-on kündigen
```http
POST /api/addons/cancel/comploai_guard
Authorization: Bearer {token}
```

## Preismodell

### Monatliche Add-ons

| Add-on | Preis | Limits (nach Plan) |
|--------|-------|-------------------|
| **ComploAI Guard** | 99€/Monat | Starter/Professional: 10 AI-Systeme<br>Business: 25 AI-Systeme<br>Enterprise: Unbegrenzt |
| **Priority Support** | 49€/Monat | - |

### Einmalige Services

| Service | Preis | Dauer |
|---------|-------|-------|
| **Expert AI Act Audit** | 2.999€ | 2-3 Wochen |
| **Implementation Support** | 1.999€ | 4 Wochen |
| **Custom Integration** | 3.999€ | 4-6 Wochen |

## Architektur

### Komponenten

1. **ai_act_analyzer.py**
   - Risiko-Klassifizierung via Claude/GPT-4
   - Compliance-Checking gegen AI Act Requirements
   - Knowledge Base Management

2. **ai_compliance_routes.py**
   - REST API für AI Systems Management
   - Scan-Endpoints
   - Knowledge Base API

3. **addon_payment_routes.py**
   - Stripe Checkout für Add-ons
   - Webhook-Handling
   - Subscription-Management

4. **database_service.py** (erweitert)
   - Add-on-Prüfung und Limit-Checks
   - Usage-Tracking
   - Subscription-Verwaltung

### Datenbank-Schema

**ai_systems**
- Kernentität für KI-Systeme
- Risk classification & compliance score
- Metadata (vendor, purpose, domain)

**ai_compliance_scans**
- Scan-Ergebnisse
- Requirements met/failed
- Findings & recommendations

**ai_documentation**
- Erforderliche Dokumentation
- Versionierung & Approval
- File storage

**user_addons**
- Add-on-Subscriptions
- Stripe-Integration
- Limits & Usage-Tracking

## Testing

### Lokales Testing

1. **Mit Demo-Daten**:
```bash
# Demo AI-System erstellen
curl -X POST http://localhost:8002/api/ai/systems \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Chatbot",
    "description": "Demo AI System",
    "purpose": "Customer Support",
    "vendor": "OpenAI"
  }'

# Scan durchführen
curl -X POST http://localhost:8002/api/ai/systems/{system_id}/scan \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force_rescan": true}'
```

2. **Stripe Test-Mode**:
   - Verwende Stripe Test-Keys
   - Testkarten: `4242 4242 4242 4242` (Erfolg), `4000 0000 0000 0002` (Decline)

### Production-Testing

1. **Stripe Webhooks testen**:
```bash
stripe listen --forward-to https://api.complyo.tech/api/addons/webhook
```

2. **Health Check**:
```bash
curl https://api.complyo.tech/api/ai/act/requirements
```

## Troubleshooting

### Problem: "ComploAI Guard Add-on erforderlich"

**Lösung**: User hat kein aktives Add-on
```sql
-- Manuell Add-on aktivieren (für Testing)
INSERT INTO user_addons (id, user_id, addon_key, addon_name, price_monthly, limits, status)
VALUES (
  gen_random_uuid(),
  'USER_ID_HERE',
  'comploai_guard',
  'ComploAI Guard',
  99.00,
  '{"ai_systems": 10}',
  'active'
);
```

### Problem: "Error in risk classification"

**Lösung**: OpenRouter API Key prüfen
```bash
echo $OPENROUTER_API_KEY  # Sollte nicht leer sein
```

### Problem: Stripe Webhook Signature-Fehler

**Lösung**: Webhook Secret überprüfen
```bash
# Im Stripe Dashboard: Developers > Webhooks > Signing secret
```

## Monitoring

### Wichtige Metriken

1. **AI Systems**:
   ```sql
   SELECT COUNT(*) as total_systems,
          COUNT(*) FILTER (WHERE risk_category = 'high') as high_risk,
          AVG(compliance_score) as avg_compliance
   FROM ai_systems
   WHERE status = 'active';
   ```

2. **Scans**:
   ```sql
   SELECT DATE(created_at) as date,
          COUNT(*) as scans,
          AVG(compliance_score) as avg_score
   FROM ai_compliance_scans
   WHERE created_at >= NOW() - INTERVAL '30 days'
   GROUP BY DATE(created_at)
   ORDER BY date DESC;
   ```

3. **Add-on Subscriptions**:
   ```sql
   SELECT addon_key,
          COUNT(*) as subscribers,
          SUM(price_monthly) as mrr
   FROM user_addons
   WHERE status = 'active'
   GROUP BY addon_key;
   ```

## Support

Bei Fragen oder Problemen:

- **Email**: support@complyo.tech
- **Dokumentation**: https://docs.complyo.tech/ai-compliance
- **Slack**: #complyo-ai-guard

## Roadmap

- [ ] Frontend Dashboard (React)
- [ ] Automatische Report-Generierung (PDF)
- [ ] Multi-Language Support (EN, FR, ES)
- [ ] NIS2 Directive Compliance Module
- [ ] Cyber Resilience Act Module
- [ ] Digital Services Act Module

---

**Version**: 1.0.0  
**Last Updated**: 2025-01-03  
**Maintainer**: Complyo Development Team

