# 🍪 Cookie-Banner Debugging-Anleitung

## Problem

Der Cookie-Banner wird nicht angezeigt, obwohl:
- ✅ Script ist eingebunden
- ✅ site-id ist gesetzt
- ✅ Backend-Endpoint funktioniert

## Debugging-Schritte

### 1. Browser-Console prüfen

Öffne die Browser-Console (F12) und prüfe die Logs:

```javascript
// Prüfe ob Widget geladen wurde
console.log(window.complyoCookieBanner);

// Prüfe Consent-Status
console.log(localStorage.getItem('complyo_cookie_consent'));

// Prüfe ob Script geladen wurde
console.log(document.querySelector('script[src*="cookie-compliance.js"]'));

// Prüfe globale API
console.log(window.complyo);
```

### 2. Erwartete Console-Logs

Nach dem Laden der Seite sollten folgende Logs erscheinen:

```
✅ Cookie-Blocker geladen
✅ Cookie-Banner Script geladen
[Complyo] Cookie Banner v2.0.0 loaded
[Complyo] Initialisiere Cookie-Banner...
[Complyo] Script-Tag gefunden, site-id: complyo-tech
[Complyo] Erstelle neue Banner-Instanz...
[Complyo] onDOMReady - Consent-Status: Nicht vorhanden
[Complyo] Kein Consent gefunden - zeige Banner
[Complyo] Banner-Initialisierung abgeschlossen
✅ Cookie-Banner initialisiert: [Object]
📋 Consent-Status: Nicht vorhanden
🔔 Banner sollte angezeigt werden
```

### 3. Häufige Probleme

#### Problem 1: Consent bereits vorhanden

**Symptom:**
```
📋 Consent-Status: Vorhanden
ℹ️ Consent bereits vorhanden - Banner wird nicht angezeigt
```

**Lösung:**
```javascript
// Consent löschen und Seite neu laden
localStorage.removeItem('complyo_cookie_consent');
localStorage.removeItem('complyo_cookie_consent_date');
location.reload();
```

#### Problem 2: Script wird nicht geladen

**Symptom:**
```
❌ Cookie-Banner Script Fehler: [Error]
```

**Lösung:**
1. Prüfe Network-Tab ob Script geladen wurde
2. Prüfe ob Mixed Content blockiert wird (HTTP vs HTTPS)
3. Prüfe ob Ad-Blocker das Script blockiert

#### Problem 3: Widget nicht initialisiert

**Symptom:**
```
❌ Cookie-Banner nicht initialisiert!
```

**Lösung:**
1. Prüfe ob JavaScript-Fehler in Console vorhanden
2. Prüfe ob `window.ComplyoCookieBanner` verfügbar ist
3. Versuche manuelle Initialisierung:
   ```javascript
   if (window.ComplyoCookieBanner) {
     window.complyoCookieBanner = new window.ComplyoCookieBanner();
     window.complyoCookieBanner.showBanner();
   }
   ```

### 4. Manuelles Testen

Falls der Banner immer noch nicht angezeigt wird, teste manuell:

```javascript
// 1. Consent löschen
localStorage.removeItem('complyo_cookie_consent');
localStorage.removeItem('complyo_cookie_consent_date');

// 2. Prüfe ob Widget verfügbar ist
if (window.complyoCookieBanner) {
  // 3. Zeige Banner manuell
  window.complyoCookieBanner.showBanner();
} else if (window.complyo?.showBanner) {
  // 4. Oder über globale API
  window.complyo.showBanner();
} else {
  console.error('Widget nicht verfügbar!');
}
```

### 5. Network-Tab prüfen

1. Öffne DevTools → Network-Tab
2. Lade Seite neu
3. Prüfe folgende Requests:
   - `cookie-blocker.js` → Status 200 ✅
   - `cookie-compliance.js` → Status 200 ✅
   - `/api/cookie-compliance/config/complyo-tech` → Status 200 ✅ (optional)

### 6. SSL/Mixed Content prüfen

**Problem:** Seite lädt über HTTP, Scripts über HTTPS

**Lösung:**
- Stelle sicher, dass die Seite über HTTPS erreichbar ist
- Prüfe Nginx-Konfiguration (HTTP → HTTPS Redirect)

### 7. Ad-Blocker prüfen

**Problem:** Ad-Blocker blockiert Cookie-Banner-Scripts

**Lösung:**
- Deaktiviere Ad-Blocker temporär
- Oder verwende alternative URL: `/api/widgets/privacy-manager.js`

## Implementierte Debug-Features

### ✅ Console-Logging

Das Widget loggt jetzt detaillierte Informationen:
- Script-Loading-Status
- Widget-Initialisierung
- Consent-Status
- Banner-Anzeige-Status

### ✅ onLoad/onError Handlers

Die Script-Tags haben jetzt `onLoad` und `onError` Handler für besseres Debugging.

### ✅ Manuelle Banner-Anzeige

Falls der Banner nicht automatisch angezeigt wird, kann er manuell getriggert werden:
```javascript
window.complyo?.showBanner();
```

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

3. **Browser-Console öffnen** und Logs prüfen

4. **Falls Consent vorhanden**: Consent löschen und Seite neu laden

5. **Falls Script nicht lädt**: Network-Tab prüfen und Mixed Content ausschließen
