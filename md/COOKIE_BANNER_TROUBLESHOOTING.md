# 🍪 Cookie-Banner Troubleshooting

## Aktueller Status

✅ **Scripts sind eingebunden** via Next.js Script-Komponente mit `strategy="beforeInteractive"`
✅ **Client-Side Loader** als Fallback vorhanden
✅ **Backend-Endpoint funktioniert** (`/api/widgets/cookie-compliance.js`)

## Warum wird der Banner nicht angezeigt?

### Mögliche Ursachen:

1. **Consent bereits vorhanden** (wahrscheinlichste Ursache)
   - Lösung: `localStorage.removeItem('complyo_cookie_consent')` + Seite neu laden

2. **Scripts werden blockiert**
   - Ad-Blocker?
   - Browser-Extensions?
   - Network-Firewall?

3. **JavaScript-Fehler**
   - Prüfe Browser-Console auf Fehler
   - Prüfe ob andere Scripts den Banner blockieren

4. **CSS-Problem**
   - Banner wird gerendert, aber nicht sichtbar
   - Z-Index-Problem?
   - Display: none?

## Debugging-Schritte

### Schritt 1: Browser-Console prüfen

Öffne `https://complyo.tech` → F12 → Console

**Erwartete Logs:**
```
[Complyo] Cookie Banner v2.0.0 loaded
[Complyo] Initialisiere Cookie-Banner...
[Complyo] Script-Tag gefunden, site-id: complyo-tech
[Complyo] Kein Consent gefunden - zeige Banner
[CookieBannerLoader] ✅ Cookie-Blocker geladen
[CookieBannerLoader] ✅ Cookie-Banner Script geladen
[CookieBannerLoader] ✅ Widget initialisiert
```

### Schritt 2: Consent prüfen

```javascript
// In Browser-Console:
console.log('Consent:', localStorage.getItem('complyo_cookie_consent'));
console.log('Consent Date:', localStorage.getItem('complyo_cookie_consent_date'));

// Falls vorhanden, löschen:
localStorage.removeItem('complyo_cookie_consent');
localStorage.removeItem('complyo_cookie_consent_date');
location.reload();
```

### Schritt 3: Widget-Status prüfen

```javascript
// In Browser-Console:
console.log('Widget:', window.complyoCookieBanner);
console.log('API:', window.complyo);

// Manuell Banner anzeigen:
if (window.complyo?.showBanner) {
  window.complyo.showBanner();
} else {
  console.error('showBanner nicht verfügbar!');
}
```

### Schritt 4: DOM prüfen

```javascript
// In Browser-Console:
const banner = document.querySelector('.complyo-cookie-banner');
if (banner) {
  console.log('✅ Banner im DOM gefunden:', banner);
  console.log('Display:', window.getComputedStyle(banner).display);
  console.log('Visibility:', window.getComputedStyle(banner).visibility);
  console.log('Opacity:', window.getComputedStyle(banner).opacity);
  console.log('Z-Index:', window.getComputedStyle(banner).zIndex);
} else {
  console.error('❌ Banner nicht im DOM!');
}
```

### Schritt 5: Network-Tab prüfen

1. DevTools → Network
2. Seite neu laden
3. Prüfe:
   - `cookie-blocker.js` → Status 200? ✅
   - `cookie-compliance.js` → Status 200? ✅
   - Falls 404/405: Backend-Problem
   - Falls Blocked: Ad-Blocker/Extension

### Schritt 6: Scripts manuell laden

Falls Scripts nicht geladen werden:

```javascript
// In Browser-Console:
(function() {
  var blocker = document.createElement('script');
  blocker.src = 'https://api.complyo.tech/public/cookie-blocker.js';
  blocker.setAttribute('data-site-id', 'complyo-tech');
  blocker.onload = function() {
    console.log('✅ Blocker geladen');
    var banner = document.createElement('script');
    banner.src = 'https://api.complyo.tech/api/widgets/cookie-compliance.js';
    banner.setAttribute('data-site-id', 'complyo-tech');
    banner.onload = function() {
      console.log('✅ Banner geladen');
      setTimeout(function() {
        if (window.complyo?.showBanner) {
          window.complyo.showBanner();
        }
      }, 1000);
    };
    document.head.appendChild(banner);
  };
  document.head.appendChild(blocker);
})();
```

## Implementierte Lösungen

### ✅ Lösung 1: Next.js Script-Komponente
- `strategy="beforeInteractive"` für frühes Laden
- Scripts werden vor React-Hydration geladen

### ✅ Lösung 2: Client-Side Loader
- `CookieBannerLoader` Component als Fallback
- Lädt Scripts dynamisch falls Next.js Scripts nicht funktionieren

### ✅ Lösung 3: Debug-Logging
- Detaillierte Console-Logs im Widget
- Logs im Client-Side Loader

## Nächste Schritte

1. **Browser-Console öffnen** und Logs prüfen
2. **Consent löschen** falls vorhanden
3. **Network-Tab prüfen** ob Scripts geladen werden
4. **DOM prüfen** ob Banner-Element vorhanden ist
5. **Manuell testen** mit `window.complyo.showBanner()`

## Falls nichts funktioniert

**Letzte Option: Scripts direkt in Nginx einbinden**

Falls Next.js und Client-Side Loader beide nicht funktionieren, können die Scripts direkt in der Nginx-Konfiguration eingebunden werden:

```nginx
# In /etc/nginx/sites-available/complyo.tech
location / {
    proxy_pass http://complyo_landing;
    sub_filter '</head>' '<script src="https://api.complyo.tech/public/cookie-blocker.js" data-site-id="complyo-tech"></script><script src="https://api.complyo.tech/api/widgets/cookie-compliance.js" data-site-id="complyo-tech"></script></head>';
    sub_filter_once on;
}
```

**Status:** ✅ **Deployment abgeschlossen - Bitte Browser-Console prüfen!**
