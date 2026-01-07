/**
 * Utility-Funktionen für Site-ID Generierung
 * 
 * Wandelt Website-URLs in konsistente Site-IDs um
 * z.B. "https://www.complyo.tech" -> "complyo-tech"
 */

/**
 * Generiert eine Site-ID aus einer Website-URL
 * 
 * @param url - Die Website-URL (mit oder ohne Protokoll)
 * @returns Site-ID im Format "domain-tld" (z.B. "complyo-tech")
 */
export function generateSiteId(url: string): string {
  try {
    // Entferne Protokoll falls vorhanden
    let domain = url.replace(/^https?:\/\//, '');
    
    // Entferne www.
    domain = domain.replace(/^www\./, '');
    
    // Entferne Pfade, Query-Parameter, etc.
    domain = domain.split('/')[0].split('?')[0].split('#')[0];
    
    // Entferne Port falls vorhanden
    domain = domain.split(':')[0];
    
    // Ersetze Punkte durch Bindestriche
    const siteId = domain.replace(/\./g, '-').toLowerCase();
    
    // Validiere: Mindestens 3 Zeichen
    if (siteId.length < 3) {
      console.warn(`Generated invalid site-id from ${url}: ${siteId}`);
      return 'unknown-site';
    }
    
    return siteId;
  } catch (error) {
    console.error('Error generating site-id from URL:', url, error);
    return 'unknown-site';
  }
}

/**
 * Validiert eine Site-ID
 * 
 * @param siteId - Die zu validierende Site-ID
 * @returns true wenn valide, false sonst
 */
export function isValidSiteId(siteId: string): boolean {
  // Site-ID sollte nur Kleinbuchstaben, Zahlen und Bindestriche enthalten
  const regex = /^[a-z0-9-]+$/;
  return regex.test(siteId) && siteId.length >= 3 && siteId.length <= 100;
}

/**
 * Extrahiert die Domain aus einer Site-ID zurück
 * 
 * @param siteId - Die Site-ID (z.B. "complyo-tech")
 * @returns Domain (z.B. "complyo.tech")
 */
export function siteIdToDomain(siteId: string): string {
  // Einfache Umkehrung: Bindestriche zu Punkten
  // Achtung: Funktioniert nicht bei Domains mit Bindestrichen im Namen
  return siteId.replace(/-/g, '.');
}

/**
 * Prüft ob eine Site-ID ein Scan-Hash ist
 * 
 * @param siteId - Die zu prüfende Site-ID
 * @returns true wenn es ein Scan-Hash ist (z.B. "scan-91778ad450e1")
 */
export function isScanHash(siteId: string): boolean {
  return siteId.startsWith('scan-') || siteId.length > 50;
}

