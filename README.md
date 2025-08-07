# 🛡️ Complyo - Website Compliance Platform

## 📁 Saubere Projekt-Struktur

```
/opt/projects/saas-project-2/
├── backend/              # FastAPI Backend
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── dashboard/            # Next.js Dashboard  
│   ├── pages/
│   ├── package.json
│   └── Dockerfile
├── landing/              # Static Landing Page
│   ├── index.html
│   └── Dockerfile
├── docker-compose.yml    # Orchestrierung
├── .env                  # Zentrale Konfiguration
└── README.md
```

## 🚀 Deployment

```bash
# Build & Start
docker-compose up -d --build

# Status prüfen
docker-compose ps

# Logs anzeigen
docker-compose logs -f [service]
```

## 🌐 Services

- **Landing:** https://complyo.tech
- **Backend:** https://api.complyo.tech  
- **Dashboard:** https://app.complyo.tech

## 📋 Features

- ✅ Vereinfachte Struktur
- ✅ Alles auf einer Ebene
- ✅ Ein docker-compose.yml
- ✅ Eine .env Datei
- ✅ Klare Trennung der Services
- ✅ Funktional & übersichtlich
