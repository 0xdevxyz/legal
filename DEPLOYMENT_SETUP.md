# 🚀 Complyo Deployment Setup

## Zentrale Konfiguration

Das Projekt verwendet eine **zentrale `.env`-Datei** im Projekt-Root für alle Services (Backend, Frontend, Scripts).

### Setup-Schritte

1. **Environment-Datei erstellen:**
   ```bash
   cp .env.example .env
   nano .env
   ```

2. **Alle Secrets und API-Keys setzen:**
   - `DB_PASSWORD` - PostgreSQL Passwort
   - `REDIS_PASSWORD` - Redis Passwort
   - `JWT_SECRET_KEY` - JWT Secret für Authentication
   - `OPENROUTER_API_KEY` - OpenRouter API Key für KI-Analysen
   - `STRIPE_SECRET_KEY` - Stripe Secret Key
   - `STRIPE_WEBHOOK_SECRET` - Stripe Webhook Secret
   - `FIREBASE_*` - Firebase Konfiguration

3. **Services starten:**
   ```bash
   # Development
   docker-compose up -d --build

   # Production
   docker-compose -f docker-compose.production.yml up -d --build
   ```

4. **Deployment-Script ausführen:**
   ```bash
   sudo bash scripts/deploy-production.sh
   ```

### Wichtige Hinweise

- ✅ **Eine zentrale .env-Datei** für alle Services
- ✅ Keine separaten .env-Dateien mehr in Unterordnern
- ✅ Docker Compose liest automatisch die Root-.env-Datei
- ✅ Alle Scripts verwenden die zentrale .env
- ⚠️  Die .env-Datei ist in .gitignore und wird nicht committed
- ⚠️  Sichere Berechtigungen: `chmod 600 .env`

### Struktur

```
/opt/projects/saas-project-2/
├── .env                          # ← ZENTRALE KONFIGURATION
├── .env.example                  # Template für neue Deployments
├── docker-compose.yml            # Development Setup
├── docker-compose.production.yml # Production Setup
├── backend/                      # FastAPI Backend
├── dashboard-react/              # Next.js Dashboard
├── landing-react/                # Next.js Landing Page
├── gateway/                      # Nginx Gateway
├── scripts/                      # Deployment & Maintenance Scripts
└── ssl/                          # SSL Zertifikate
```

### Secrets Management

Für Production empfohlen:
- HashiCorp Vault
- AWS Secrets Manager
- Docker Secrets
- Kubernetes Secrets

---

**Stand:** November 2025
