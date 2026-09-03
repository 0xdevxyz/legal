# 🔐 Complyo Environment Configuration

> **WICHTIG:** Erstelle eine `.env` Datei im Root-Verzeichnis mit den folgenden Variablen.  
> **NIEMALS** die `.env` Datei ins Git-Repository committen!

---

## 🔴 ERFORDERLICH - Anwendung startet nicht ohne diese

### JWT Secret
```bash
# Generieren mit: openssl rand -base64 64
JWT_SECRET=your-super-secure-jwt-secret-min-64-characters-long
```

### PostgreSQL Datenbank
```bash
POSTGRES_USER=complyo_user
POSTGRES_PASSWORD=your-secure-database-password
POSTGRES_DB=complyo_db
```

---

## 🟠 EMPFOHLEN - Für volle Funktionalität

### OpenRouter API (KI-Features)
```bash
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-api-key
```

### Stripe Payment
```bash
STRIPE_SECRET_KEY=sk_live_your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=whsec_your-stripe-webhook-secret
```

### Firebase Authentication (Backend)
```bash
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@your-project.iam.gserviceaccount.com
```

### Firebase Frontend Config
```bash
NEXT_PUBLIC_FIREBASE_API_KEY=your-firebase-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-firebase-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abcdef
NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID=G-XXXXXXXXXX
```

---

## 🟡 OPTIONAL - Email & Benachrichtigungen

### SMTP Konfiguration

Seit 2026-08-11 in Produktion aktiv (Versand ueber den eigenen Mailserver).
Das Passwort steht NUR in der Server-.env, nie im Repo. Wichtig: Wert in der
.env in einfache Anfuehrungszeichen setzen, wenn er $ oder # enthaelt —
Docker Compose interpoliert sonst bzw. schneidet ab.

```bash
SMTP_HOST=mail.complyo.de
SMTP_PORT=587                      # STARTTLS
SMTP_USERNAME=noreply@complyo.de
SMTP_PASSWORD=<nur-in-server-env>
SENDER_EMAIL=noreply@complyo.de
SENDER_NAME=complyo
```

---

## 🟢 STANDARDWERTE - Müssen normalerweise nicht geändert werden

```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
REDIS_HOST=redis
REDIS_PORT=6379
UNLIMITED_FIXES=false
BYPASS_PAYMENT=false
```

---

## 🛡️ Sicherheitshinweise

1. **JWT_SECRET**: Mindestens 64 Zeichen, zufällig generiert
2. **POSTGRES_PASSWORD**: Starkes Passwort, keine Sonderzeichen die URL-Encoding benötigen
3. **Private Keys**: In Anführungszeichen mit `\n` für Zeilenumbrüche
4. **Stripe Keys**: Verwende `sk_test_` für Entwicklung, `sk_live_` für Produktion

---

## 🚀 Quick Start

```bash
# 1. JWT Secret generieren
echo "JWT_SECRET=$(openssl rand -base64 64 | tr -d '\n')" >> .env

# 2. Datenbank-Credentials setzen
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d '\n')" >> .env

# 3. Weitere Variablen nach Bedarf hinzufügen...

# 4. Docker starten
docker-compose up -d
```

