# 🍪 Cookie-Banner - Debug-Anleitung

## ✅ Scripts sind im HTML

Die Cookie-Banner-Scripts werden jetzt **direkt über Nginx** eingebunden und sind im HTML vorhanden.

**Verifizierung:**
```bash
curl -s https://complyo.tech | grep -o "cookie-blocker\|cookie-compliance"
# Ergebnis: cookie-blocker cookie-compliance ✅
```

## 🔍 Warum wird der Banner nicht angezeigt?

### Mögliche Ursachen:

1. **JavaScript-Fehler blockiert Initialisierung**
2. **Consent bereits vorhanden** (Banner wird nicht angezeigt)
3. **Scripts werden nicht geladen** (Network-Problem)

## 🧪 Debug-Schritte

### Schritt 1: Browser-Console prüfen

1. Öffne `https://complyo.tech`
2. Öffne DevTools (F12) → Console
3. Prüfe auf Fehler (rote Meldungen)

### Schritt 2: Network-Tab prüfen

1. DevTools → Network
2. Seite neu laden
3. Prüfe:
   - `cookie-blocker.js` → Status 200? ✅
   - `cookie-compliance.js` → Status 200? ✅

### Schritt 3: Debug-Script ausführen

Kopiere das Debug-Script aus `COOKIE_BANNER_DEBUG_SCRIPT.js` in die Browser-Console:

```javascript
// In Browser-Console einfügen:
console.log('=== Cookie Banner Debug ===');

// 1. Prüfe Scripts
const blockerScript = document.querySelector('script[src*="cookie-blocker.js"]');
const bannerScript = document.querySelector('script[src*="cookie-compliance.js"]');
console.log('Scripts:', blockerScript ? '✅' : '❌', bannerScript ? '✅' : '❌');

// 2. Prüfe Widget
console.log('ComplyoCookieBanner:', typeof window.ComplyoCookieBanner !== 'undefined' ? '✅' : '❌');
console.log('complyoCookieBanner:', window.complyoCookieBanner ? '✅' : '❌');

// 3. Prüfe Consent
const consent = localStorage.getItem('complyo_cookie_consent');
console.log('Consent:', consent || 'NICHT vorhanden');

// 4. Manuelle Initialisierung
if (!window.complyoCookieBanner && window.ComplyoCookieBanner) {
    console.log('Initialisiere manuell...');
    window.complyoCookieBanner = new window.ComplyoCookieBanner();
    window.complyo = window.complyo || {};
    window.complyo.showBanner = () => window.complyoCookieBanner.showBanner();
    if (!consent) {
        window.complyo.showBanner();
    }
}
```

### Schritt 4: Consent löschen

```javascript
// In Browser-Console:
localStorage.removeItem('complyo_cookie_consent');
localStorage.removeItem('complyo_cookie_consent_date');
location.reload();
```

### Schritt 5: Manuell Banner anzeigen

```javascript
// In Browser-Console:
if (window.complyo && window.complyo.showBanner) {
    window.complyo.showBanner();
} else if (window.complyoCookieBanner) {
    window.complyoCookieBanner.showBanner();
} else {
    console.error('Banner kann nicht angezeigt werden');
}
```

## 📊 Erwartete Console-Logs

Wenn alles funktioniert, sollten diese Logs erscheinen:

```
[Complyo] Cookie Banner v2.0.0 loaded
[Complyo] Initialisiere Cookie-Banner...
[Complyo] Script-Tag gefunden, site-id: complyo-tech
[Complyo] Erstelle neue Banner-Instanz...
[Complyo] Banner-Initialisierung abgeschlossen
[Complyo] Global API registered: window.complyo
```

## 🎯 Nächster Schritt

**Bitte führe das Debug-Script in der Browser-Console aus und teile die Ausgabe!**

Das Debug-Script zeigt genau:
- ✅ Ob Scripts geladen wurden
- ✅ Ob Widget initialisiert wurde
- ✅ Ob Consent vorhanden ist
- ✅ Warum der Banner nicht angezeigt wird

**Status:** ✅ **Scripts sind im HTML - Bitte Debug-Script ausführen!**
