# 🍪 Cookie-Banner wird nicht angezeigt - Problem & Lösung

## Problem

Der Cookie-Banner wird auf `complyo.tech` nicht angezeigt, obwohl:
- ✅ Widget-Script ist in `layout.tsx` eingebunden
- ✅ Backend-Endpoint funktioniert (`/api/widgets/cookie-compliance.js`)
- ✅ Widget-Code ist vorhanden

## Ursachen

### 1. **Leere site-id** ❌
```tsx
// VORHER (falsch):
<Script
  src="https://api.complyo.tech/api/widgets/cookie-compliance.js"
  data-site-id=""  // ❌ LEER!
  strategy="afterInteractive"
/>
```

**Problem**: Wenn `data-site-id` leer ist, verwendet das Widget `'demo-site'` als Fallback, aber es könnte sein, dass keine Konfiguration geladen wird.

### 2. **SSL-Problem (Mixed Content)** ⚠️
- Die Seite lädt über **HTTP** (nicht sicher)
- Die Scripts werden von **HTTPS** geladen (`https://api.complyo.tech`)
- Browser blockieren möglicherweise Mixed Content

### 3. **Script-Loading-Strategie** ⚠️
- `strategy="afterInteractive"` bedeutet, dass das Script erst **nach** dem Laden der Seite ausgeführt wird
- Wenn es JavaScript-Fehler gibt, wird das Widget möglicherweise nicht initialisiert

## Lösung

### ✅ Fix 1: site-id setzen

```tsx
// NACHHER (korrekt):
<Script
  src="https://api.complyo.tech/api/widgets/cookie-compliance.js"
  data-site-id="complyo-tech"  // ✅ Site-ID gesetzt
  data-complyo-site-id="complyo-tech"
  strategy="afterInteractive"
/>
```

### ✅ Fix 2: SSL-Problem beheben

**Wichtig**: Die Seite muss über **HTTPS** erreichbar sein!

1. **Prüfe SSL-Status**:
   ```bash
   curl -I https://complyo.tech
   ```

2. **Wenn SSL-Problem**: Siehe `SSL_FIX_ZUSAMMENFASSUNG.md`

3. **Nginx-Konfiguration prüfen**:
   ```bash
   sudo nginx -T | grep -A 10 "server_name complyo.tech"
   ```

### ✅ Fix 3: Script-Loading verbessern

Falls das Widget immer noch nicht lädt, ändere die Loading-Strategie:

```tsx
<Script
  src="https://api.complyo.tech/api/widgets/cookie-compliance.js"
  data-site-id="complyo-tech"
  strategy="beforeInteractive"  // ✅ Lädt früher
  onLoad={() => {
    console.log('Cookie-Banner geladen');
  }}
  onError={(e) => {
    console.error('Cookie-Banner Fehler:', e);
  }}
/>
```

## Debugging

### 1. Browser-Console prüfen

Öffne die Browser-Console (F12) und prüfe:

```javascript
// Prüfe ob Widget geladen wurde
console.log(window.complyoCookieBanner);

// Prüfe Consent-Status
console.log(localStorage.getItem('complyo_cookie_consent'));

// Prüfe ob Script geladen wurde
console.log(document.querySelector('script[src*="cookie-compliance.js"]'));
```

### 2. Network-Tab prüfen

1. Öffne DevTools → Network-Tab
2. Lade Seite neu
3. Prüfe ob `cookie-compliance.js` geladen wurde:
   - ✅ Status 200: Script geladen
   - ❌ Status 0/Blocked: Script blockiert (Mixed Content?)
   - ❌ Status 404: Script nicht gefunden
   - ❌ Status 405: Endpoint-Fehler

### 3. Manuell testen

Füge temporär einen Test-Code hinzu:

```tsx
<Script
  id="cookie-banner-test"
  src="https://api.complyo.tech/api/widgets/cookie-compliance.js"
  data-site-id="complyo-tech"
  strategy="afterInteractive"
  onLoad={() => {
    console.log('✅ Cookie-Banner Script geladen');
    setTimeout(() => {
      if (window.complyoCookieBanner) {
        console.log('✅ Cookie-Banner initialisiert');
        window.complyoCookieBanner.showBanner();
      } else {
        console.error('❌ Cookie-Banner nicht initialisiert');
      }
    }, 1000);
  }}
  onError={(e) => {
    console.error('❌ Cookie-Banner Fehler:', e);
  }}
/>
```

## Implementierte Fixes

### ✅ Fix 1: site-id gesetzt

**Datei**: `landing-react/src/app/layout.tsx`

**Änderung**:
- `data-site-id=""` → `data-site-id="complyo-tech"`
- `data-complyo-site-id=""` → `data-complyo-site-id="complyo-tech"`

### ⚠️ Fix 2: SSL-Problem (siehe SSL_FIX_ZUSAMMENFASSUNG.md)

Die SSL-Zertifikate wurden bereits behoben. Stelle sicher, dass die Seite über HTTPS erreichbar ist.

## Nächste Schritte

1. **Frontend neu bauen**:
   ```bash
   cd landing-react
   npm run build
   ```

2. **Docker-Container neu starten**:
   ```bash
   docker-compose restart complyo-landing
   ```

3. **Testen**:
   - Öffne `https://complyo.tech` (HTTPS!)
   - Prüfe Browser-Console
   - Prüfe ob Cookie-Banner angezeigt wird

4. **Falls immer noch nicht sichtbar**:
   - Prüfe Browser-Console auf Fehler
   - Prüfe Network-Tab ob Script geladen wurde
   - Prüfe ob Consent bereits gespeichert ist (localStorage)

## Erwartetes Verhalten

Nach den Fixes sollte:

1. ✅ Das Cookie-Banner-Script geladen werden
2. ✅ Das Widget initialisiert werden
3. ✅ Der Cookie-Banner angezeigt werden (wenn kein Consent vorhanden)
4. ✅ Der Banner nach Consent verschwinden

## Troubleshooting

### Problem: Banner wird immer noch nicht angezeigt

**Lösung**:
1. Prüfe Browser-Console auf JavaScript-Fehler
2. Prüfe ob Script geladen wurde (Network-Tab)
3. Prüfe ob Consent bereits gespeichert ist:
   ```javascript
   localStorage.removeItem('complyo_cookie_consent');
   location.reload();
   ```

### Problem: Mixed Content Error

**Lösung**:
- Stelle sicher, dass die Seite über HTTPS erreichbar ist
- Prüfe Nginx-Konfiguration (HTTP → HTTPS Redirect)

### Problem: Script wird blockiert

**Lösung**:
- Prüfe Browser-Extensions (Ad-Blocker?)
- Prüfe Content-Security-Policy
- Prüfe ob Script-URL korrekt ist

## Zusammenfassung

✅ **Behoben**:
- site-id gesetzt (`complyo-tech`)
- SSL-Problem behoben (siehe SSL_FIX_ZUSAMMENFASSUNG.md)

⚠️ **Zu prüfen**:
- Frontend neu bauen und deployen
- Seite über HTTPS testen
- Browser-Console auf Fehler prüfen

🎯 **Erwartetes Ergebnis**:
- Cookie-Banner wird angezeigt
- Widget funktioniert korrekt
- Consent wird gespeichert
