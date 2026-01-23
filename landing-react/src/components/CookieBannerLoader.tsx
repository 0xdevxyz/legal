'use client';

import { useEffect } from 'react';

/**
 * Client-Side Cookie-Banner Loader
 * Lädt das Cookie-Banner-Widget SOFORT nach dem Mount
 * 
 * Diese Komponente ist die HAUPT-Methode zum Laden des Cookie-Banners
 * Sie lädt die Scripts dynamisch, da Next.js sie möglicherweise entfernt
 */
export const CookieBannerLoader: React.FC = () => {
  useEffect(() => {
    // WICHTIG: Warte kurz, damit DOM vollständig geladen ist
    const timeoutId = setTimeout(() => {
      const win = window as any;
      
      console.log('[CookieBannerLoader] 🚀 Starte Cookie-Banner-Loader...');
      console.log('[CookieBannerLoader] 📋 DOM readyState:', document.readyState);
      console.log('[CookieBannerLoader] 📋 Scripts im DOM:', document.querySelectorAll('script[src*="cookie"]').length);
    
    // Prüfe ob Widget bereits geladen wurde
    if (win.complyoCookieBanner) {
      console.log('[CookieBannerLoader] ✅ Widget bereits geladen');
      const consent = localStorage.getItem('complyo_cookie_consent');
      if (!consent && win.complyo?.showBanner) {
        console.log('[CookieBannerLoader] 🔔 Zeige Banner (kein Consent)');
        win.complyo.showBanner();
      }
      return;
    }

    // Prüfe ob Scripts bereits im DOM sind (von Nginx eingefügt)
    const existingBlocker = document.querySelector('script[src*="cookie-blocker.js"]');
    const existingBanner = document.querySelector('script[src*="cookie-compliance.js"]');
    
    if (existingBlocker && existingBanner) {
      console.log('[CookieBannerLoader] ⏳ Scripts bereits im DOM, warte auf Initialisierung...');
      // Warte auf Initialisierung
      let attempts = 0;
      const maxAttempts = 30; // 3 Sekunden
      const checkInterval = setInterval(() => {
        attempts++;
        if (win.complyoCookieBanner) {
          clearInterval(checkInterval);
          console.log('[CookieBannerLoader] ✅ Widget initialisiert');
          const consent = localStorage.getItem('complyo_cookie_consent');
          if (!consent && win.complyo?.showBanner) {
            console.log('[CookieBannerLoader] 🔔 Zeige Banner');
            win.complyo.showBanner();
          }
        } else if (attempts >= maxAttempts) {
          clearInterval(checkInterval);
          console.error('[CookieBannerLoader] ❌ Widget nicht initialisiert - lade Scripts manuell');
          loadScriptsManually();
        }
      }, 100);
      return;
    }

    // Scripts nicht im DOM - lade sie manuell
    console.log('[CookieBannerLoader] 📥 Scripts nicht im DOM - lade manuell...');
    loadScriptsManually();

    function loadScriptsManually() {
      // Lade Cookie-Blocker zuerst
      const blockerScript = document.createElement('script');
      blockerScript.src = 'https://api.complyo.tech/public/cookie-blocker.js';
      blockerScript.setAttribute('data-site-id', 'complyo-tech');
      blockerScript.async = false;
      blockerScript.onload = () => {
        console.log('[CookieBannerLoader] ✅ Cookie-Blocker geladen');
        
        // Dann lade Cookie-Banner
        const bannerScript = document.createElement('script');
        bannerScript.src = 'https://api.complyo.tech/api/widgets/cookie-compliance.js';
        bannerScript.setAttribute('data-site-id', 'complyo-tech');
        bannerScript.setAttribute('data-complyo-site-id', 'complyo-tech');
        bannerScript.async = false;
        bannerScript.onload = () => {
          console.log('[CookieBannerLoader] ✅ Cookie-Banner Script geladen');
          
          // Prüfe ob Widget initialisiert wurde
          let attempts = 0;
          const maxAttempts = 30;
          const checkWidget = setInterval(() => {
            attempts++;
            
            if (win.complyoCookieBanner) {
              clearInterval(checkWidget);
              console.log('[CookieBannerLoader] ✅ Widget initialisiert');
              
              const consent = localStorage.getItem('complyo_cookie_consent');
              if (!consent) {
                console.log('[CookieBannerLoader] 🔔 Zeige Banner (kein Consent)');
                if (win.complyo?.showBanner) {
                  win.complyo.showBanner();
                } else if (win.complyoCookieBanner?.showBanner) {
                  win.complyoCookieBanner.showBanner();
                }
              }
            } else if (attempts >= maxAttempts) {
              clearInterval(checkWidget);
              console.error('[CookieBannerLoader] ❌ Widget nicht initialisiert');
              
              // Manuelle Initialisierung
              if (typeof win.ComplyoCookieBanner !== 'undefined') {
                console.log('[CookieBannerLoader] 🔧 Versuche manuelle Initialisierung...');
                try {
                  win.complyoCookieBanner = new win.ComplyoCookieBanner();
                  win.complyo = win.complyo || {};
                  win.complyo.showBanner = () => win.complyoCookieBanner.showBanner();
                  const consent = localStorage.getItem('complyo_cookie_consent');
                  if (!consent) {
                    win.complyo.showBanner();
                  }
                } catch (error) {
                  console.error('[CookieBannerLoader] ❌ Fehler:', error);
                }
              }
            }
          }, 100);
        };
        bannerScript.onerror = (error) => {
          console.error('[CookieBannerLoader] ❌ Cookie-Banner Fehler:', error);
        };
        document.head.appendChild(bannerScript);
      };
      blockerScript.onerror = (error) => {
        console.error('[CookieBannerLoader] ❌ Cookie-Blocker Fehler:', error);
      };
      document.head.appendChild(blockerScript);
    }
    }, 100); // 100ms Delay für DOM-Bereitschaft
    
    return () => clearTimeout(timeoutId);
  }, []);

  return null;
};
