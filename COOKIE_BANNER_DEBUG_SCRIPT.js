// Debug-Script für Cookie-Banner
// In Browser-Console einfügen:

console.log('=== Cookie Banner Debug ===');

// 1. Prüfe ob Scripts geladen wurden
const blockerScript = document.querySelector('script[src*="cookie-blocker.js"]');
const bannerScript = document.querySelector('script[src*="cookie-compliance.js"]');
console.log('1. Scripts im DOM:');
console.log('   - cookie-blocker.js:', blockerScript ? '✅' : '❌');
console.log('   - cookie-compliance.js:', bannerScript ? '✅' : '❌');

// 2. Prüfe ob Widget-Klasse vorhanden ist
console.log('2. Widget-Klasse:');
console.log('   - ComplyoCookieBanner:', typeof window.ComplyoCookieBanner !== 'undefined' ? '✅' : '❌');

// 3. Prüfe ob Widget initialisiert wurde
console.log('3. Widget-Instanz:');
console.log('   - complyoCookieBanner:', window.complyoCookieBanner ? '✅' : '❌');
console.log('   - complyo API:', window.complyo ? '✅' : '❌');

// 4. Prüfe Consent
console.log('4. Consent-Status:');
const consent = localStorage.getItem('complyo_cookie_consent');
console.log('   - Consent:', consent || 'NICHT vorhanden');

// 5. Versuche Banner manuell zu laden
if (!window.complyoCookieBanner && typeof window.ComplyoCookieBanner !== 'undefined') {
    console.log('5. Versuche manuelle Initialisierung...');
    try {
        window.complyoCookieBanner = new window.ComplyoCookieBanner();
        window.complyo = window.complyo || {};
        window.complyo.showBanner = function() {
            if (window.complyoCookieBanner) {
                window.complyoCookieBanner.showBanner();
            }
        };
        console.log('   ✅ Manuelle Initialisierung erfolgreich');
        
        // Zeige Banner
        if (!consent) {
            console.log('   🔔 Zeige Banner...');
            window.complyo.showBanner();
        }
    } catch (error) {
        console.error('   ❌ Fehler:', error);
    }
} else if (window.complyoCookieBanner) {
    console.log('5. Widget bereits initialisiert');
    if (!consent && window.complyo && window.complyo.showBanner) {
        console.log('   🔔 Zeige Banner...');
        window.complyo.showBanner();
    }
} else {
    console.error('5. ❌ Widget kann nicht initialisiert werden');
    console.log('   - ComplyoCookieBanner:', window.ComplyoCookieBanner);
}

console.log('=== Ende Debug ===');
