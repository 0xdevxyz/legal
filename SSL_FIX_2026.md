# 🔒 SSL-Zertifikat Fix - 2026-01-09

## Problem

**Fehler:** `NET::ERR_CERT_DATE_INVALID`

**Ursache:** Nginx verwendete das **abgelaufene** Zertifikat `complyo.tech` (Expiry: 2025-12-29) statt des **gültigen** Zertifikats `complyo.tech-0001` (Expiry: 2026-01-24).

## Lösung

### ✅ Zertifikat-Status

- ❌ `complyo.tech` - **ABGELAUFEN** (2025-12-29)
- ✅ `complyo.tech-0001` - **GÜLTIG** (2026-01-24, noch 14 Tage)

### ✅ Nginx-Konfiguration aktualisiert

**Datei:** `/etc/nginx/sites-available/complyo.tech`

**Geändert:**
```nginx
# VORHER (abgelaufen):
ssl_certificate /etc/letsencrypt/live/complyo.tech/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/complyo.tech/privkey.pem;

# NACHHER (gültig):
ssl_certificate /etc/letsencrypt/live/complyo.tech-0001/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/complyo.tech-0001/privkey.pem;
```

### ✅ Aktionen durchgeführt

1. ✅ Nginx-Konfiguration aktualisiert
2. ✅ Nginx-Konfiguration getestet (`nginx -t`)
3. ✅ Nginx neu geladen (`systemctl reload nginx`)

## Prüfung

### Zertifikat-Status prüfen:

```bash
sudo certbot certificates | grep -A 5 "complyo.tech"
```

### Nginx-Konfiguration prüfen:

```bash
sudo nginx -t
```

### Zertifikat im Browser prüfen:

1. Öffne `https://complyo.tech`
2. Klicke auf das Schloss-Symbol
3. Prüfe "Zertifikat ist gültig"

## Automatische Erneuerung

Das Zertifikat `complyo.tech-0001` läuft am **2026-01-24** ab.

**Automatische Erneuerung:**
- Certbot-Timer ist aktiv
- Erneuerung erfolgt automatisch 30 Tage vor Ablauf

**Manuelle Erneuerung (falls nötig):**
```bash
sudo certbot renew --cert-name complyo.tech-0001
sudo systemctl reload nginx
```

## Status

✅ **SSL-Problem behoben** - Nginx verwendet jetzt das gültige Zertifikat
✅ **Nginx neu geladen** - Änderungen aktiv
✅ **Zertifikat gültig bis** - 2026-01-24 (14 Tage)

**Bitte Browser-Cache leeren und Seite neu laden!**
