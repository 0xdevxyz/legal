# 🍪 Cookie-Banner - Deployment-Check

## ✅ Build & Deployment Status

### Build-Status
- ✅ Frontend gebaut - `npm run build` erfolgreich
- ✅ Container neu gestartet - `complyo-landing` läuft

### Cookie-Banner-Implementierung

**Im Root-Layout (`layout.tsx`):**
1. ✅ Direkte Script-Einbindung via `dangerouslySetInnerHTML`
2. ✅ `CookieBannerLoader` Component
3. ✅ Nginx `sub_filter` (Backup)

**Alle Landing-Pages verwenden das Root-Layout automatisch!**

## 🔍 Warum wird der Banner nicht angezeigt?

### Mögliche Ursachen:

1. **Browser-Cache** - Alte Version wird geladen
2. **Scripts werden nicht geladen** - Network-Problem
3. **Widget initialisiert sich nicht** - JavaScript-Fehler
4. **Consent bereits vorhanden** - Banner wird nicht angezeigt

## 🧪 Testing

### Schritt 1: Browser-Cache leeren

**WICHTIG:** Der Browser-Cache muss geleert werden!

- **Chrome/Edge:** Strg+Shift+Delete → "Cached images and files" → Clear
- **Oder:** Inkognito-Modus verwenden (Strg+Shift+N)

### Schritt 2: Hard Reload

- Strg+F5 (Hard Reload)
- Oder: DevTools öffnen (F12) → Rechtsklick auf Reload-Button → "Empty Cache and Hard Reload"

### Schritt 3: Console prüfen

1. Öffne `https://complyo.tech`
2. Öffne DevTools (F12) → Console
3. Prüfe auf Logs:
   - `[Direct Script]` oder
   - `[CookieBannerLoader]`

### Schritt 4: Network-Tab prüfen

1. DevTools → Network
2. Seite neu laden
3. Prüfe:
   - `cookie-blocker.js` → Status 200? ✅
   - `cookie-compliance.js` → Status 200? ✅

### Schritt 5: Debug-Script ausführen

```javascript
// In Browser-Console:
console.log('=== Cookie Banner Debug ===');
console.log('Scripts im DOM:', document.querySelectorAll('script[src*="cookie"]').length);
console.log('ComplyoCookieBanner:', typeof window.ComplyoCookieBanner !== 'undefined' ? '✅' : '❌');
console.log('complyoCookieBanner:', window.complyoCookieBanner ? '✅' : '❌');
console.log('Consent:', localStorage.getItem('complyo_cookie_consent') || 'NICHT vorhanden');

// Falls Widget vorhanden, aber nicht angezeigt:
if (window.complyoCookieBanner && !localStorage.getItem('complyo_cookie_consent')) {
    console.log('🔔 Zeige Banner manuell...');
    if (window.complyo && window.complyo.showBanner) {
        window.complyo.showBanner();
    } else if (window.complyoCookieBanner.showBanner) {
        window.complyoCookieBanner.showBanner();
    }
}
```

## 📊 Status

✅ **Frontend gebaut** - Build erfolgreich
✅ **Container neu gestartet** - `complyo-landing` läuft
✅ **Cookie-Banner eingebunden** - In Root-Layout
✅ **Alle Landing-Pages** - Verwenden Root-Layout

## 🎯 Wichtigste Schritte

1. **Browser-Cache leeren** (Strg+Shift+Delete)
2. **Hard Reload** (Strg+F5)
3. **Console prüfen** (F12 → Console)
4. **Network-Tab prüfen** (F12 → Network)

**Der Banner sollte jetzt angezeigt werden!**
