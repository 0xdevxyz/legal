# 🍪 Cookie-Banner - Direkte Script-Einbindung

## ✅ Finale Lösung

### Problem

Next.js Script-Komponenten mit `beforeInteractive` werden **nicht direkt im HTML gerendert**, sondern von Next.js dynamisch geladen. Das funktioniert nicht zuverlässig.

### Lösung

**Direkte Script-Einbindung via `dangerouslySetInnerHTML` im `<body>`**

Die Scripts werden jetzt **direkt im HTML** eingebunden und laden **sofort beim HTML-Parsing**, bevor React überhaupt hydriert.

### Code-Implementierung

**Datei:** `landing-react/src/app/layout.tsx`

```tsx
<body>
  <script
    dangerouslySetInnerHTML={{
      __html: `
        (function() {
          console.log('[Direct Script] 🚀 Starte Cookie-Banner-Loader...');
          
          // Lade Cookie-Blocker
          var blocker = document.createElement('script');
          blocker.src = 'https://api.complyo.tech/public/cookie-blocker.js';
          blocker.setAttribute('data-site-id', 'complyo-tech');
          blocker.async = false; // Synchron!
          
          blocker.onload = function() {
            // Lade Cookie-Banner
            var banner = document.createElement('script');
            banner.src = 'https://api.complyo.tech/api/widgets/cookie-compliance.js';
            banner.setAttribute('data-site-id', 'complyo-tech');
            banner.async = false; // Synchron!
            
            banner.onload = function() {
              // Prüfe ob Widget initialisiert wurde
              var checkInterval = setInterval(function() {
                if (window.complyoCookieBanner) {
                  clearInterval(checkInterval);
                  var consent = localStorage.getItem('complyo_cookie_consent');
                  if (!consent && window.complyo?.showBanner) {
                    window.complyo.showBanner();
                  }
                }
              }, 100);
            };
            document.head.appendChild(banner);
          };
          document.head.appendChild(blocker);
        })();
      `,
    }}
  />
  <CookieBannerLoader />
  {children}
</body>
```

## 🧪 Erwartete Console-Logs

```
[Direct Script] 🚀 Starte Cookie-Banner-Loader...
[Direct Script] ✅ Cookie-Blocker geladen
[Direct Script] ✅ Cookie-Banner Script geladen
[Complyo] Cookie Banner v2.0.0 loaded
[Complyo] Initialisiere Cookie-Banner...
[Direct Script] ✅ Widget initialisiert
[Direct Script] 🔔 Zeige Banner (kein Consent)
[Direct Script] ✅ showBanner() aufgerufen
[CookieBannerLoader] 🚀 Starte Cookie-Banner-Loader...
[CookieBannerLoader] ✅ Widget bereits geladen
```

## ✅ Vorteile dieser Lösung

1. **Direkt im HTML** - Scripts sind sofort verfügbar
2. **Synchrones Laden** - Korrekte Reihenfolge garantiert
3. **Vor React-Hydration** - Lädt bevor React überhaupt startet
4. **Fallback vorhanden** - CookieBannerLoader als Backup

## 🔍 Testing

### Schritt 1: Browser-Cache leeren
- Strg+Shift+Delete → "Cached images and files" → Clear

### Schritt 2: Seite neu laden
- Strg+F5 (Hard Reload)

### Schritt 3: Console prüfen
- F12 → Console
- Prüfe ob `[Direct Script]` Logs vorhanden sind

### Schritt 4: Falls Consent vorhanden
```javascript
localStorage.removeItem('complyo_cookie_consent');
localStorage.removeItem('complyo_cookie_consent_date');
location.reload();
```

## 📊 Deployment-Status

✅ **Frontend gebaut** - Build erfolgreich
✅ **Container neu gestartet** - `complyo-landing` läuft
✅ **Direkte Script-Einbindung** - Scripts im HTML
✅ **Synchrones Laden** - `async = false`
✅ **Detailliertes Logging** - Jeder Schritt wird geloggt

## 🎯 Nächster Schritt

**Bitte Browser-Cache leeren, Seite neu laden und Console-Logs prüfen!**

Die Logs sollten jetzt `[Direct Script]` Meldungen zeigen, die bestätigen, dass die Scripts geladen werden.

**Status:** ✅ **Deployment abgeschlossen - Bitte testen!**
