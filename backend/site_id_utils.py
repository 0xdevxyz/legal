"""
Site-ID-Ableitung — Python-Port von
dashboard-react/src/lib/siteIdUtils.ts::generateSiteId.

MUSS bit-identisch zum Frontend bleiben: Die Barrierefreiheitserklärung sucht
in accessibility_fix_packages mit der vom Frontend erzeugten site_id. Weicht die
Backend-Ableitung ab, findet die Erklärung die vom Scan geschriebene Zeile nicht.
"""
import re


def derive_site_id(url: str) -> str:
    """Wandelt eine Website-URL in eine konsistente Site-ID um.

    "https://www.complyo.tech/path?x=1" -> "complyo-tech"
    Liefert "unknown-site", wenn das Ergebnis kürzer als 3 Zeichen ist.
    """
    try:
        domain = re.sub(r'^https?://', '', url or '')
        domain = re.sub(r'^www\.', '', domain)
        domain = domain.split('/')[0].split('?')[0].split('#')[0]
        domain = domain.split(':')[0]
        site_id = domain.replace('.', '-').lower()
        if len(site_id) < 3:
            return 'unknown-site'
        return site_id
    except Exception:
        return 'unknown-site'
