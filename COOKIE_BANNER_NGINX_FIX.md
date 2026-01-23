# 🍪 Cookie-Banner - Nginx Direct Injection

## ✅ Finale Lösung: Scripts über Nginx direkt einbinden

### Problem

Next.js rendert Scripts nicht direkt im HTML, auch nicht mit `dangerouslySetInnerHTML` in Server Components.

### Lösung

**Scripts werden jetzt direkt über Nginx `sub_filter` eingebunden**

Die Scripts werden beim Response-Streaming direkt vor dem `</body>`-Tag eingefügt.

### Nginx-Konfiguration

**Datei:** `/etc/nginx/sites-available/complyo.tech`

```nginx
location / {
    proxy_pass http://complyo_landing;
    # ... andere proxy_set_header ...
    
    # Cookie-Banner Scripts direkt einbinden
    sub_filter "</body>" "<script src=\"https://api.complyo.tech/public/cookie-blocker.js\" data-site-id=\"complyo-tech\"></script><script src=\"https://api.complyo.tech/api/widgets/cookie-compliance.js\" data-site-id=\"complyo-tech\" data-complyo-site-id=\"complyo-tech\"></script></body>";
    sub_filter_once on;
}
```

## ✅ Vorteile

1. **Garantiert im HTML** - Scripts sind immer vorhanden
2. **Unabhängig von Next.js** - Funktioniert auch wenn Next.js Scripts nicht lädt
3. **Sofort verfügbar** - Scripts werden beim HTML-Parsing geladen
4. **Keine React-Abhängigkeit** - Funktioniert vor React-Hydration

## 🧪 Testing

### Schritt 1: Prüfe ob Scripts im HTML sind

```bash
curl -s https://complyo.tech | grep -o "cookie-blocker\|cookie-compliance"
```

Sollte beide Scripts finden!

### Schritt 2: Browser-Cache leeren
- Strg+Shift+Delete → "Cached images and files" → Clear

### Schritt 3: Seite neu laden
- Strg+F5 (Hard Reload)

### Schritt 4: Console prüfen
- F12 → Console
- Erwartete Logs:
  ```
  [Complyo] Cookie Banner v2.0.0 loaded
  [Complyo] Initialisiere Cookie-Banner...
  [Complyo] Script-Tag gefunden, site-id: complyo-tech
  ```

### Schritt 5: Falls Consent vorhanden
```javascript
localStorage.removeItem('complyo_cookie_consent');
localStorage.removeItem('complyo_cookie_consent_date');
location.reload();
```

## 📊 Deployment-Status

✅ **Nginx-Konfiguration aktualisiert** - Scripts werden eingebunden
✅ **Nginx neu geladen** - Änderungen aktiv
✅ **Backup erstellt** - Sicherung vorhanden

## 🎯 Nächster Schritt

**Bitte Browser-Cache leeren, Seite neu laden und prüfen!**

Die Scripts sollten jetzt **garantiert im HTML** sein und der Banner sollte angezeigt werden.

**Status:** ✅ **Deployment abgeschlossen - Bitte testen!**
