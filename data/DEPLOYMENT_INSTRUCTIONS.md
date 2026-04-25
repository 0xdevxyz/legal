# 🚀 Deployment Instructions

**Status**: Code implementiert, aber Container muss neu gebaut werden

---

## Problem

Die neue Datei `score_calculator.py` existiert lokal, aber nicht in der Docker Image:

```bash
$ docker exec complyo-backend ls /app/compliance_engine/score_calculator.py
ls: cannot access '/app/compliance_engine/score_calculator.py': No such file or directory
```

---

## Lösung: Docker Image neu bauen

### Option 1: Mit docker-compose (EMPFOHLEN)

```bash
cd /home/clawd/saas/legal

# Baue Backend Image neu
docker-compose build backend

# Starte neu
docker-compose down
docker-compose up -d backend

# Verifiziere
docker logs complyo-backend | tail -20
```

### Option 2: Manuell mit docker

```bash
# Baue Image neu
docker build -t legal-backend:latest \
  -f backend/Dockerfile \
  backend/

# Stoppe alten Container
docker stop complyo-backend
docker rm complyo-backend

# Starte neuen
docker run -d \
  --name complyo-backend \
  -p 127.0.0.1:8002:8002 \
  -e DATABASE_URL="postgresql://..." \
  legal-backend:latest
```

---

## Verify nach Deploy

```bash
# 1. Check ob Container läuft
docker ps | grep complyo-backend

# 2. Prüfe ob Datei existiert
docker exec complyo-backend ls /app/compliance_engine/score_calculator.py
# Erwartet: /app/compliance_engine/score_calculator.py

# 3. Prüfe ob Import funktioniert
docker exec complyo-backend python3 -c "from compliance_engine.score_calculator import ScoreCalculator; print('✅ OK')"

# 4. Prüfe Logs
docker logs complyo-backend | grep -i "score_calculator\|error" | tail -20
```

---

## Test nach Deployment

Wenn alles funktioniert:

```bash
# Test 1: Backend ist ready
curl http://localhost:8002/health
# Erwartet: 200 OK

# Test 2: Scan mit neuem Score Calculator
curl -X POST http://localhost:8002/api/v2/analyze/complete \
  -H "Content-Type: application/json" \
  -d '{"url": "https://compyo.de"}' \
  -H "Authorization: Bearer <token>" \
  | jq '.compliance_score'

# Führe 3x aus - sollte IDENTISCH sein!
```

---

## Falls Probleme

### Container startet nicht

```bash
# Logs prüfen
docker logs complyo-backend

# Falls Module fehlen: requirements.txt prüfen
docker exec complyo-backend pip list | grep -i fastapi

# Neu bauen mit no-cache
docker-compose build --no-cache backend
```

### Score ist immer noch `null`

```bash
# Prüfe ob score_calculator.py geladen wird
docker logs complyo-backend | grep -i "score"

# Falls kein Log: Backend neustart
docker restart complyo-backend

# Logs nach Restart prüfen
docker logs complyo-backend | tail -50
```

### Import Error: `No module named 'compliance_engine.score_calculator'`

→ Datei ist nicht im Container
→ Docker Image muss neu gebaut werden

```bash
# 1. Prüfe ob Datei lokal existiert
ls -la backend/compliance_engine/score_calculator.py

# 2. Prüfe Dockerfile COPY Commands
grep -n "COPY.*compliance_engine" backend/Dockerfile

# 3. Neu bauen
docker-compose build --no-cache backend
docker-compose up -d backend
```

---

## Checklist vor Production

- [ ] Git push: Code ist commitet
- [ ] Docker build: Image wurde neu gebaut
- [ ] Container restart: Backend läuft neu
- [ ] Score test: 3x gleiche Score
- [ ] Logs check: Keine neuen Fehler
- [ ] API test: /api/v2/analyze/complete antwortet
- [ ] Monitor: Score-Volatilität ist 0%

---

## Rollback Falls Problem

```bash
# Revert Code
git revert <commit-hash>

# Neu bauen
docker-compose build backend

# Restart
docker-compose up -d backend

# Verify
curl http://localhost:8002/health
```

