# 🚀 CI/CD Pipeline Setup

> Complyo verwendet GitHub Actions für Continuous Integration und Deployment.

---

## 📋 Workflows

### 1. CI Pipeline (`.github/workflows/ci.yml`)

**Trigger:** Push/PR auf `main` oder `develop`

| Job | Beschreibung | Dauer |
|-----|--------------|-------|
| `backend-lint` | Ruff Linter für Python | ~1 min |
| `backend-test` | Pytest mit PostgreSQL & Redis | ~3 min |
| `dashboard-lint` | ESLint & TypeScript Check | ~1 min |
| `dashboard-build` | Next.js Production Build | ~2 min |
| `landing-lint` | ESLint Check | ~1 min |
| `landing-build` | Next.js Production Build | ~2 min |
| `docker-build` | Docker Images bauen (ohne Push) | ~5 min |
| `security-scan` | Trivy Vulnerability Scanner | ~2 min |

### 2. Deploy Pipeline (`.github/workflows/deploy.yml`)

**Trigger:** Push auf `main` oder manuell

| Job | Beschreibung |
|-----|--------------|
| `build-and-push` | Docker Images zu GitHub Container Registry |
| `deploy` | SSH-Deployment auf Server |
| `smoke-tests` | Health Checks nach Deployment |

---

## 🔐 Erforderliche GitHub Secrets

Gehe zu: **Repository → Settings → Secrets and variables → Actions**

### Für CI (Optional)
```
CODECOV_TOKEN          # Für Code Coverage Reports
```

### Für Deployment (Erforderlich)
```
# Server-Zugang
SSH_PRIVATE_KEY        # SSH Private Key für Server
SERVER_HOST            # Server IP oder Hostname
SERVER_USER            # SSH Username (z.B. root, deploy)
DEPLOY_PATH            # Pfad zum Projekt (z.B. /opt/projects/saas-project-2)

# Build-Variablen
NEXT_PUBLIC_API_URL    # https://api.complyo.tech

# Notifications (Optional)
SLACK_WEBHOOK_URL      # Für Deployment-Benachrichtigungen
```

---

## 🛠️ Lokale Entwicklung

### Pre-Commit Hooks einrichten (Empfohlen)

```bash
# Installiere pre-commit
pip install pre-commit

# Erstelle .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
EOF

# Installiere Hooks
pre-commit install
```

### Tests lokal ausführen

```bash
# Backend Tests
cd backend
pip install pytest pytest-asyncio pytest-cov
pytest tests/ -v

# Frontend Tests
cd dashboard-react
npm run lint
npm run type-check
npm run build
```

---

## 🔄 Deployment-Prozess

### Automatisches Deployment

1. Code auf `main` pushen
2. CI Pipeline läuft durch
3. Bei Erfolg: Deploy Pipeline startet
4. Docker Images werden gebaut und gepusht
5. Server zieht neue Images und startet Container neu
6. Smoke Tests prüfen Verfügbarkeit

### Manuelles Deployment

```bash
# In GitHub Actions:
# Actions → Deploy to Production → Run workflow
# Environment auswählen: production/staging
```

### Rollback

```bash
# Auf dem Server:
cd /opt/projects/saas-project-2

# Vorherige Version verwenden
docker-compose pull  # Holt :latest
# ODER spezifische Version:
docker pull ghcr.io/user/repo/backend:SHA_HASH

docker-compose up -d
```

---

## 📊 Monitoring

### Health Endpoints

| Service | URL | Erwartete Antwort |
|---------|-----|-------------------|
| Backend | `/health` | `{"status": "healthy"}` |
| Dashboard | `/` | HTTP 200 |
| Landing | `/` | HTTP 200 |

### Logs prüfen

```bash
# Alle Services
docker-compose logs -f

# Einzelner Service
docker-compose logs -f backend

# Letzte 100 Zeilen
docker-compose logs --tail=100 backend
```

---

## ⚠️ Troubleshooting

### CI schlägt fehl

1. **Lint-Fehler:** Lokal `ruff check . --fix` ausführen
2. **Test-Fehler:** Logs in GitHub Actions prüfen
3. **Build-Fehler:** Dependencies prüfen

### Deployment schlägt fehl

1. **SSH-Fehler:** Private Key und Known Hosts prüfen
2. **Docker-Fehler:** Speicherplatz auf Server prüfen
3. **Health Check:** Logs des betroffenen Services prüfen

### Rollback nötig

```bash
# Letztes funktionierendes Image Tag finden
docker images | grep complyo

# Service mit spezifischem Tag starten
docker-compose down
docker tag ghcr.io/.../backend:SHA ghcr.io/.../backend:latest
docker-compose up -d
```

---

## 📈 Metriken

Nach erfolgreichem Setup sollten folgende Badges im README angezeigt werden:

```markdown
![CI](https://github.com/USER/REPO/workflows/CI/badge.svg)
![Deploy](https://github.com/USER/REPO/workflows/Deploy/badge.svg)
```

