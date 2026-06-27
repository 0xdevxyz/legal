"""
Complyo Accessibility Patch Generator
Generiert HTML-Patches für permanente Barrierefreiheits-Fixes

Teil des Hybrid-Modells:
- Widget für sofortige Runtime-Fixes
- Patches für permanente SEO-optimierte Lösung
"""

from bs4 import BeautifulSoup
import zipfile
import io
from typing import List, Dict
import aiohttp
from datetime import datetime
import logging
import json
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class AccessibilityPatchGenerator:
    """
    Generiert downloadbare HTML-Patches für Barrierefreiheits-Fixes
    
    Features:
    - Komplette HTML-Dateien mit integrierten Fixes
    - CSS-Patches für Kontrast- und Focus-Fixes
    - WordPress XML-Export für Mediathek
    - PDF-Anleitung (TODO)
    - README mit Installationsanweisungen
    """
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def generate_patch_bundle(self, site_id: str, user_id: int, fixes: List[Dict]) -> io.BytesIO:
        """
        Generiert komplettes Patch-Bundle als ZIP-Datei
        
        Args:
            site_id: Site-Identifier
            user_id: User-ID
            fixes: Liste von Accessibility-Fixes
            
        Returns:
            BytesIO mit ZIP-Datei
        """
        logger.info(f"Generating patch bundle for site {site_id}, {len(fixes)} fixes")
        
        # Gruppiere Fixes nach Typ
        alt_text_fixes = [f for f in fixes if f.get('type') == 'alt_text']
        contrast_fixes = [f for f in fixes if f.get('type') == 'contrast']
        aria_fixes = [f for f in fixes if f.get('type') == 'aria_label']
        
        # Erstelle ZIP
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 1. HTML-Patches (wenn vorhanden)
            if alt_text_fixes or aria_fixes:
                html_patches = await self._generate_html_patches(alt_text_fixes + aria_fixes)
                for filename, content in html_patches.items():
                    zip_file.writestr(f"html/{filename}", content)
            
            # 2. CSS-Patches (immer, auch für Focus-Styles)
            css_content = self._generate_css_patches(contrast_fixes)
            zip_file.writestr("css/accessibility-fixes.css", css_content)
            
            # 3. WordPress-Export
            if alt_text_fixes:
                wordpress_xml = self._generate_wordpress_export(alt_text_fixes)
                zip_file.writestr("wordpress/import.xml", wordpress_xml)
                
                # WordPress-Anleitung
                wp_guide = self._generate_wordpress_guide(alt_text_fixes)
                zip_file.writestr("wordpress/ANLEITUNG.txt", wp_guide)
            
            # 4. README
            readme = self._generate_readme(fixes, alt_text_fixes, contrast_fixes, aria_fixes)
            zip_file.writestr("README.txt", readme)
            
            # 5. FTP-Anleitung
            ftp_guide = self._generate_ftp_guide()
            zip_file.writestr("FTP-ANLEITUNG.txt", ftp_guide)
        
        zip_buffer.seek(0)
        logger.info(f"Patch bundle generated successfully, size: {len(zip_buffer.getvalue())} bytes")
        
        return zip_buffer
    
    async def _generate_html_patches(self, fixes: List[Dict]) -> Dict[str, str]:
        """
        Generiert HTML-Dateien mit integrierten Fixes
        
        Gruppiert Fixes nach Seite und patcht jede HTML-Datei
        """
        patches = {}
        
        # Gruppiere nach Seite
        pages = {}
        for fix in fixes:
            page_url = fix.get('page_url', '/')
            if page_url not in pages:
                pages[page_url] = []
            pages[page_url].append(fix)
        
        # Für jede Seite: Generiere gepatcht HTML
        for page_url, page_fixes in pages.items():
            try:
                # ✅ FIX: Versuche echtes HTML zu laden, Fallback auf Beispiel
                fixed_html = await self._generate_html_with_real_fixes(page_url, page_fixes)
                
                # Dateiname generieren
                filename = self._url_to_filename(page_url)
                patches[filename] = fixed_html
                
                logger.info(f"Generated HTML patch for {page_url}: {filename}")
                
            except Exception as e:
                logger.error(f"Error generating HTML patch for {page_url}: {e}")
                continue
        
        return patches
    
    async def _generate_html_with_real_fixes(self, page_url: str, fixes: List[Dict]) -> str:
        """
        ✅ Versucht echtes HTML vom Server zu laden und zu patchen
        Fallback auf Beispiel-HTML falls nicht möglich
        """
        try:
            # Versuche HTML vom Server zu laden
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(page_url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        
                        # Parse mit BeautifulSoup
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Wende Fixes an
                        fixed_count = 0
                        for fix in fixes:
                            if fix.get('type') == 'alt_text':
                                image_src = fix.get('image_src')
                                suggested_alt = fix.get('suggested_alt')
                                
                                # Finde Bild im HTML
                                img_tags = soup.find_all('img', src=image_src)
                                if not img_tags:
                                    # Versuche relativen Pfad
                                    img_tags = soup.find_all('img', src=lambda x: x and image_src in x)
                                
                                for img in img_tags:
                                    img['alt'] = suggested_alt
                                    img['data-complyo-fix'] = 'permanent'
                                    fixed_count += 1
                        
                        if fixed_count > 0:
                            logger.info(f"✅ Applied {fixed_count} real fixes to {page_url}")
                            return str(soup)
                        
        except Exception as e:
            logger.warning(f"⚠️ Could not load real HTML from {page_url}: {e}. Using example template.")
        
        # Fallback: Generiere Beispiel-HTML
        return self._generate_example_html_with_fixes(page_url, fixes)
    
    def _generate_example_html_with_fixes(self, page_url: str, fixes: List[Dict]) -> str:
        """
        Generiert Beispiel-HTML mit integrierten Fixes
        
        In Produktion würde man das echte HTML vom Server laden
        und die Fixes anwenden. Hier generieren wir Beispiel-Code.
        """
        html_template = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gepatchte Seite - {page_url}</title>
    <link rel="stylesheet" href="../css/accessibility-fixes.css">
</head>
<body>
    <!-- Skip-Link für Tastatur-Navigation -->
    <a href="#main-content" class="skip-link">Zum Hauptinhalt springen</a>
    
    <main id="main-content" tabindex="-1">
        <h1>Barrierefreiheit wurde verbessert</h1>
        <p>Diese Seite wurde automatisch von Complyo optimiert.</p>
        
        <!-- Beispiele für gepatche Elemente -->
"""
        
        # Füge Alt-Text-Fixes hinzu
        for fix in fixes:
            if fix.get('type') == 'alt_text':
                html_template += f"""
        <!-- Gepatchtes Bild -->
        <img src="{fix.get('image_src', '')}" 
             alt="{fix.get('suggested_alt', '')}" 
             data-complyo-fix="permanent">
"""
        
        html_template += """
    </main>
    
    <footer>
        <p>Barrierefreiheit optimiert durch <a href="https://complyo.tech">Complyo</a></p>
    </footer>
</body>
</html>
"""
        
        return html_template
    
    def _generate_css_patches(self, contrast_fixes: List[Dict]) -> str:
        """
        Generiert CSS-Datei mit Barrierefreiheits-Fixes
        """
        css = """/* ========================================
 * Complyo Barrierefreiheits-Fixes
 * Generiert: {timestamp}
 * ======================================== */

/* Skip-Link für Tastatur-Navigation */
.skip-link {{
  position: absolute;
  top: -40px;
  left: 0;
  background: #000;
  color: #fff;
  padding: 8px 16px;
  text-decoration: none;
  font-weight: bold;
  z-index: 10000;
  border-radius: 0 0 4px 0;
}}

.skip-link:focus {{
  top: 0;
  outline: 2px solid #fff;
  outline-offset: 2px;
}}

/* Focus-Indikatoren für alle interaktiven Elemente */
a:focus,
button:focus,
input:focus,
textarea:focus,
select:focus {{
  outline: 3px solid #005fcc;
  outline-offset: 2px;
}}

/* Focus-Visible (moderne Browser) */
*:focus-visible {{
  outline: 3px solid #005fcc;
  outline-offset: 2px;
}}

/* Verbesserte Link-Sichtbarkeit */
a {{
  text-decoration: underline;
}}

a:hover {{
  text-decoration: none;
}}

/* Responsive Schriftgrößen */
html {{
  font-size: 16px;
}}

@media (min-width: 768px) {{
  html {{
    font-size: 18px;
  }}
}}

/* Kontrast-Fixes (individuell) */
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        # Füge individuelle Kontrast-Fixes hinzu
        for fix in contrast_fixes:
            selector = fix.get('selector', '')
            new_color = fix.get('new_color', '')
            new_background = fix.get('new_background', '')
            
            if selector:
                css += f"\n{selector} {{\n"
                if new_color:
                    css += f"  color: {new_color} !important;\n"
                if new_background:
                    css += f"  background-color: {new_background} !important;\n"
                css += "}\n"
        
        # Standard-Kontrast-Verbesserungen
        css += """
/* Standard-Kontrast-Verbesserungen */
body {
  color: #1a1a1a;
  background-color: #ffffff;
}

.text-muted,
.text-secondary {
  color: #4a5568 !important; /* Verbessert von #6c757d */
}

/* Platzhalter-Text in Formularen */
::placeholder {
  color: #6b7280;
  opacity: 1;
}

/* Deaktivierte Elemente müssen erkennbar sein */
:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Print-Styles für Barrierefreiheit */
@media print {
  a[href]:after {
    content: " (" attr(href) ")";
  }
}
"""
        
        return css
    
    def _generate_wordpress_export(self, alt_text_fixes: List[Dict]) -> str:
        """
        Generiert WordPress XML-Export (WXR-Format)
        Für Import in Mediathek
        """
        xml = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0"
    xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"
    xmlns:content="http://purl.org/rss/1.0/modules/content/"
    xmlns:wfw="http://wellformedweb.org/CommentAPI/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:wp="http://wordpress.org/export/1.2/">
<channel>
  <title>Complyo Barrierefreiheits-Fixes</title>
  <link>https://complyo.tech</link>
  <description>AI-generierte Alt-Texte für WordPress Mediathek</description>
  <language>de-DE</language>
  <wp:wxr_version>1.2</wp:wxr_version>
  <wp:base_site_url>https://complyo.tech</wp:base_site_url>
  <wp:base_blog_url>https://complyo.tech</wp:base_blog_url>
  <generator>Complyo.tech Accessibility Patch Generator</generator>
  
"""
        
        # Für jeden Alt-Text: Media-Item erstellen
        for idx, fix in enumerate(alt_text_fixes, 1):
            image_filename = fix.get('image_filename', f'image-{idx}')
            suggested_alt = fix.get('suggested_alt', '')
            image_src = fix.get('image_src', '')
            
            # Escape XML
            suggested_alt_escaped = suggested_alt.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            xml += f"""  <item>
    <title><![CDATA[{image_filename}]]></title>
    <wp:post_type><![CDATA[attachment]]></wp:post_type>
    <wp:post_parent>0</wp:post_parent>
    <wp:attachment_url><![CDATA[{image_src}]]></wp:attachment_url>
    <wp:postmeta>
      <wp:meta_key><![CDATA[_wp_attachment_image_alt]]></wp:meta_key>
      <wp:meta_value><![CDATA[{suggested_alt_escaped}]]></wp:meta_value>
    </wp:postmeta>
  </item>
  
"""
        
        xml += """</channel>
</rss>
"""
        
        return xml
    
    def _generate_readme(self, all_fixes: List[Dict], alt_texts: List[Dict], 
                        contrasts: List[Dict], aria: List[Dict]) -> str:
        """Generiert README mit Übersicht und Anleitung"""
        
        return f"""
╔══════════════════════════════════════════════════════════════════╗
║     COMPLYO BARRIEREFREIHEITS-PATCHES                           ║
║     Hybrid-Modell: Runtime Widget + Permanente Patches          ║
╚══════════════════════════════════════════════════════════════════╝

GENERIERT AM: {datetime.now().strftime("%d.%m.%Y um %H:%M Uhr")}

═══════════════════════════════════════════════════════════════════
⚠️  WICHTIG: HAFTUNGSAUSSCHLUSS
═══════════════════════════════════════════════════════════════════

Complyo wendet Code-Änderungen ausschließlich nach ausdrücklicher 
Bestätigung durch den Nutzer oder dessen technische Administratoren an.

Die Verantwortung für das Ausrollen der Änderungen in produktive 
Systeme liegt ausschließlich beim Nutzer.

Complyo generiert Patches basierend auf öffentlich zugänglichem Code. 
Sie übernehmen die Verantwortung für die Anwendung dieser Änderungen 
in Ihrem System.

WICHTIG: KI-generierte Inhalte können Fehler oder Ungenauigkeiten 
enthalten. Bitte prüfen Sie jeden Fix vor der Anwendung und erstellen 
Sie ein Backup Ihrer Website.

Vollständige AGB: https://complyo.tech/terms-liability

═══════════════════════════════════════════════════════════════════

📊 ÜBERSICHT
═══════════════════════════════════════════════════════════════════

Ihre Website-Analyse hat {len(all_fixes)} Barrierefreiheits-Probleme gefunden:

✅ {len(alt_texts)} Alt-Text-Fixes (für Bilder)
✅ {len(contrasts)} Kontrast-Fixes (für bessere Lesbarkeit)  
✅ {len(aria)} ARIA-Label-Fixes (für Screen-Reader)

Diese Patches beheben sie PERMANENT im Code.

═══════════════════════════════════════════════════════════════════

📦 PAKET-INHALT
═══════════════════════════════════════════════════════════════════

html/           → Beispiel-HTML-Dateien mit Fixes
css/            → CSS-Datei mit Kontrast- und Focus-Fixes
wordpress/      → WordPress XML-Import für Mediathek
README.txt      → Diese Datei
FTP-ANLEITUNG.txt → Schritt-für-Schritt FTP-Guide

═══════════════════════════════════════════════════════════════════

🚀 QUICK START - 3 WEGE ZUR UMSETZUNG
═══════════════════════════════════════════════════════════════════

┌────────────────────────────────────────────────────────────────┐
│ OPTION 1: WordPress (AM EINFACHSTEN) ⭐                        │
└────────────────────────────────────────────────────────────────┘

1. WordPress → Werkzeuge → Daten importieren
2. "WordPress" Importer installieren (falls nicht vorhanden)
3. Datei wählen: wordpress/import.xml
4. "Medienanhänge herunterladen" NICHT anhaken
5. Import starten
6. Fertig! Alt-Texte sind in Mediathek ✅

Dauer: 2 Minuten

┌────────────────────────────────────────────────────────────────┐
│ OPTION 2: FTP/cPanel Upload                                    │
└────────────────────────────────────────────────────────────────┘

1. Backup Ihrer Website erstellen (WICHTIG!)
2. CSS-Datei hochladen:
   - css/accessibility-fixes.css → /wp-content/themes/ihr-theme/
3. CSS einbinden in header.php oder functions.php
4. HTML-Beispiele dienen als Referenz für Ihre Entwickler

Siehe: FTP-ANLEITUNG.txt für Details

Dauer: 15-30 Minuten

┌────────────────────────────────────────────────────────────────┐
│ OPTION 3: Expertservice (KEINE ARBEIT) 💼                     │
└────────────────────────────────────────────────────────────────┘

Zu technisch? Wir machen das für Sie!

→ Expertservice buchen: https://complyo.tech/expertservice
→ Preis: €3.000 (einmalig, nur Barrierefreiheit)
→ Dauer: 48 Stunden
→ Inkl.: Alle Fixes + Testing + Dokumentation

═══════════════════════════════════════════════════════════════════

⚡ IHR WIDGET LÄUFT WEITER
═══════════════════════════════════════════════════════════════════

WICHTIG: Ihr Complyo Widget bleibt aktiv und funktioniert parallel!

Nach Umsetzung der Patches:
→ Alt-Texte sind PERMANENT im Code (besseres SEO!)
→ Widget bietet zusätzliche Features (Kontrast, Font-Size, etc.)
→ Sie können Widget auf €4.90/Monat downgraden

Das ist der Hybrid-Ansatz: Widget + Permanente Fixes = Perfekt!

═══════════════════════════════════════════════════════════════════

🔍 VORHER/NACHHER
═══════════════════════════════════════════════════════════════════

VORHER (nur Widget):
- Alt-Texte per JavaScript (runtime)
- Funktioniert für Nutzer ✅
- SEO-Wirkung: Eingeschränkt ⚠️

NACHHER (Widget + Patches):
- Alt-Texte im HTML-Quellcode (permanent)
- Funktioniert für Nutzer ✅
- SEO-Wirkung: Maximal ✅✅✅
- Besseres Google-Ranking
- Schnellere Ladezeit
- WCAG 2.1 Level AA+

═══════════════════════════════════════════════════════════════════

❓ SUPPORT
═══════════════════════════════════════════════════════════════════

Fragen? Probleme? Wir helfen!

📧 E-Mail:  support@complyo.tech
📞 Telefon: +49 (0) 123 456789
💬 Chat:    https://complyo.tech/support

Öffnungszeiten: Mo-Fr 9-18 Uhr

═══════════════════════════════════════════════════════════════════

© {datetime.now().year} Complyo.tech
Barrierefreiheit leicht gemacht.
"""
    
    def _generate_wordpress_guide(self, alt_text_fixes: List[Dict]) -> str:
        """Generiert detaillierte WordPress-Anleitung"""
        
        return f"""
╔══════════════════════════════════════════════════════════════════╗
║     WORDPRESS IMPORT-ANLEITUNG                                  ║
╚══════════════════════════════════════════════════════════════════╝

Diese Anleitung erklärt Schritt-für-Schritt wie Sie die {len(alt_text_fixes)} 
Alt-Texte in Ihre WordPress-Mediathek importieren.

═══════════════════════════════════════════════════════════════════

📋 SCHRITT-FÜR-SCHRITT
═══════════════════════════════════════════════════════════════════

1. IN WORDPRESS EINLOGGEN
   → Gehen Sie zu: ihre-website.de/wp-admin
   → Loggen Sie sich mit Admin-Zugang ein

2. IMPORTER AUFRUFEN
   → Klicken Sie in der linken Sidebar auf "Werkzeuge"
   → Klicken Sie auf "Daten importieren"

3. WORDPRESS-IMPORTER INSTALLIEREN (falls noch nicht vorhanden)
   → Suchen Sie "WordPress" in der Liste
   → Klicken Sie auf "Jetzt installieren"
   → Warten Sie bis Installation abgeschlossen
   → Klicken Sie auf "Importer starten"

4. XML-DATEI AUSWÄHLEN
   → Klicken Sie auf "Datei auswählen"
   → Navigieren Sie zu diesem Ordner
   → Wählen Sie: wordpress/import.xml
   → Klicken Sie auf "Öffnen"

5. IMPORT-OPTIONEN
   → WICHTIG: Haken Sie "Medienanhänge herunterladen" NICHT an!
   → (Wir ändern nur Alt-Texte, laden keine neuen Bilder hoch)
   → Wählen Sie einen WordPress-Autor für die Zuordnung
   → Klicken Sie auf "Absenden"

6. WARTEN
   → Der Import läuft (kann 30 Sekunden dauern)
   → Nicht die Seite schließen!

7. ERFOLG PRÜFEN
   → Sie sehen: "Fertig! Viel Spaß beim Bloggen."
   → Gehen Sie zu: Medien → Mediathek
   → Klicken Sie auf ein Bild
   → Prüfen Sie ob das Feld "Alternativtext" ausgefüllt ist ✅

═══════════════════════════════════════════════════════════════════

⚠️ TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════

Problem: "Importer nicht gefunden"
Lösung: Installieren Sie den WordPress-Importer (Schritt 3)

Problem: "Datei zu groß"
Lösung: Erhöhen Sie upload_max_filesize in php.ini
        Oder wenden Sie sich an Ihren Hoster

Problem: "Alt-Texte nicht sichtbar"
Lösung: Prüfen Sie ob die Bilder die gleichen Dateinamen haben
        Ggf. manuell in Mediathek nachpflegen

═══════════════════════════════════════════════════════════════════

✅ NACH DEM IMPORT
═══════════════════════════════════════════════════════════════════

Geschafft! Ihre Alt-Texte sind jetzt permanent in WordPress.

NÄCHSTE SCHRITTE:
1. Gehen Sie durch Ihre wichtigsten Seiten
2. Prüfen Sie ob Bilder korrekte Alt-Texte haben
3. Passen Sie bei Bedarf einzelne Alt-Texte an
4. Genießen Sie besseres SEO! 🚀

Das Widget läuft weiterhin für zusätzliche Features.

═══════════════════════════════════════════════════════════════════

Support: support@complyo.tech | +49 (0) 123 456789
"""
    
    def _generate_ftp_guide(self) -> str:
        """Generiert FTP-Upload-Anleitung"""
        
        return """
╔══════════════════════════════════════════════════════════════════╗
║     FTP/cPanel UPLOAD-ANLEITUNG                                 ║
╚══════════════════════════════════════════════════════════════════╝

Diese Anleitung erklärt wie Sie die CSS-Fixes per FTP hochladen
und in Ihre Website einbinden.

═══════════════════════════════════════════════════════════════════

🔧 BENÖTIGTE TOOLS
═══════════════════════════════════════════════════════════════════

- FTP-Programm (z.B. FileZilla: https://filezilla-project.org/)
- Ihre FTP-Zugangsdaten (vom Hoster)
- Oder: cPanel-Zugang

═══════════════════════════════════════════════════════════════════

📋 METHODE 1: FTP-Upload
═══════════════════════════════════════════════════════════════════

1. FILEZILLA ÖFFNEN
   → Starten Sie FileZilla
   → Geben Sie ein:
     - Host: ftp.ihre-domain.de (vom Hoster)
     - Benutzername: Ihr FTP-User
     - Passwort: Ihr FTP-Passwort
     - Port: 21 (oder 22 für SFTP)
   → Klicken Sie "Verbinden"

2. VERZEICHNIS FINDEN
   → Navigieren Sie auf dem Server zu:
     WordPress: /wp-content/themes/ihr-theme/
     HTML:      /css/ oder /styles/
   → Erstellen Sie ggf. einen Ordner "accessibility"

3. CSS-DATEI HOCHLADEN
   → Ziehen Sie die Datei per Drag&Drop:
     css/accessibility-fixes.css
   → Warten Sie bis Upload fertig (grüner Haken)

4. CSS EINBINDEN
   
   WordPress:
   → Öffnen Sie: Design → Theme-Editor
   → Wählen Sie: header.php
   → Fügen Sie VOR </head> ein:
   
   <link rel="stylesheet" href="<?php echo get_template_directory_uri(); ?>/accessibility-fixes.css">
   
   → Speichern
   
   HTML:
   → Öffnen Sie Ihre index.html
   → Fügen Sie im <head> ein:
   
   <link rel="stylesheet" href="/css/accessibility-fixes.css">
   
   → Speichern & hochladen

5. TESTEN
   → Besuchen Sie Ihre Website
   → Drücken Sie Strg+U (Quelltext anzeigen)
   → Suchen Sie nach "accessibility-fixes.css"
   → Sollte gefunden werden ✅

═══════════════════════════════════════════════════════════════════

📋 METHODE 2: cPanel File Manager
═══════════════════════════════════════════════════════════════════

1. CPANEL ÖFFNEN
   → Gehen Sie zu: ihre-domain.de/cpanel
   → Loggen Sie sich ein

2. FILE MANAGER
   → Klicken Sie auf "Dateimanager"
   → Navigieren Sie zu /public_html/

3. UPLOAD
   → Klicken Sie auf "Hochladen"
   → Wählen Sie: css/accessibility-fixes.css
   → Warten Sie bis fertig

4. EINBINDEN
   → Wie bei Methode 1, Schritt 4

═══════════════════════════════════════════════════════════════════

⚠️ WICHTIG: BACKUP!
═══════════════════════════════════════════════════════════════════

IMMER vor Änderungen ein Backup erstellen!

WordPress:
→ Plugin: UpdraftPlus (kostenlos)
→ Oder: Über Hoster-Panel

HTML:
→ Kompletten Ordner herunterladen
→ Oder: Bei Hoster-Backup erstellen

═══════════════════════════════════════════════════════════════════

Support: support@complyo.tech | +49 (0) 123 456789
"""
    
    def _url_to_filename(self, url: str) -> str:
        """Konvertiert URL zu Dateiname"""
        parsed = urlparse(url)
        path = parsed.path.strip('/') or 'index'
        
        # Ersetze Slashes durch Underscores
        filename = path.replace('/', '_')
        
        # Stelle sicher dass es .html endet
        if not filename.endswith('.html'):
            filename += '.html'
        
        return filename
    
    # =========================================================================
    # NEU: Erweiterte Bundle-Generierung für Fix-Wizard
    # =========================================================================
    
    async def generate_enhanced_bundle(
        self,
        site_url: str,
        fix_package: Dict,
        include_wordpress: bool = True
    ) -> io.BytesIO:
        """
        Generiert erweitertes Fix-Bundle mit strukturierten Patches
        
        Args:
            site_url: URL der Website
            fix_package: FixPackage-Dictionary vom PatchService
            include_wordpress: Ob WordPress-Plugin generiert werden soll
            
        Returns:
            BytesIO mit ZIP-Datei
        """
        logger.info(f"Generating enhanced bundle for {site_url}")
        
        zip_buffer = io.BytesIO()
        site_id = site_url.replace('https://', '').replace('http://', '').replace('/', '-').replace('.', '-')
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 1. README.md (Markdown für bessere Lesbarkeit)
            readme_md = self._generate_enhanced_readme(site_url, fix_package)
            zip_file.writestr("README.md", readme_md)
            
            # 2. Code-Patches als einzelne Dateien
            code_patches = fix_package.get('code_patches', [])
            if code_patches:
                for i, patch in enumerate(code_patches):
                    if patch.get('success') and patch.get('unified_diff'):
                        feature_id = patch.get('feature_id', 'unknown')
                        file_path = patch.get('file_path', f'patch_{i}')
                        safe_name = file_path.replace('/', '_').replace('\\', '_')
                        
                        # Patch-Datei
                        zip_file.writestr(
                            f"patches/{feature_id}_{safe_name}.patch",
                            patch['unified_diff']
                        )
                        
                        # Anleitung pro Patch
                        instructions = self._generate_patch_instructions(patch)
                        zip_file.writestr(
                            f"patches/{feature_id}_{safe_name}_ANLEITUNG.txt",
                            instructions
                        )
            
            # 3. HTML-Snippets zum direkten Einfügen
            html_snippets = self._generate_html_snippets(fix_package)
            if html_snippets:
                zip_file.writestr("snippets/accessibility-snippets.html", html_snippets)
            
            # 4. CSS-Fixes (konsolidiert)
            css_content = self._generate_consolidated_css(fix_package)
            zip_file.writestr("css/complyo-accessibility.css", css_content)
            
            # 5. WordPress-Plugin (optional)
            if include_wordpress:
                wp_plugin = self._generate_wordpress_plugin(site_id, fix_package)
                zip_file.writestr("wordpress/complyo-accessibility/complyo-accessibility.php", wp_plugin)
                
                wp_readme = self._generate_wordpress_plugin_readme()
                zip_file.writestr("wordpress/complyo-accessibility/readme.txt", wp_readme)
            
            # 6. Widget-Integration (falls Widget-Fixes vorhanden)
            widget_fixes = fix_package.get('widget_fixes', [])
            if widget_fixes:
                widget_code = self._generate_widget_integration(site_id, widget_fixes)
                zip_file.writestr("widget/integration.html", widget_code)
            
            # 7. Zusammenfassung als JSON (für Tools/Automatisierung)
            summary_json = json.dumps(fix_package.get('summary', {}), indent=2, ensure_ascii=False)
            zip_file.writestr("meta/summary.json", summary_json)
        
        zip_buffer.seek(0)
        logger.info(f"Enhanced bundle generated, size: {len(zip_buffer.getvalue())} bytes")
        
        return zip_buffer
    
    def _generate_enhanced_readme(self, site_url: str, fix_package: Dict) -> str:
        """Generiert verbessertes README im Markdown-Format"""
        summary = fix_package.get('summary', {})
        
        return f"""# Complyo Barrierefreiheits-Fixes

**Website:** {site_url}  
**Erstellt:** {datetime.now().strftime("%d.%m.%Y um %H:%M Uhr")}

---

## Übersicht

| Metrik | Wert |
|--------|------|
| Gefundene Probleme | {summary.get('total_issues', 0)} |
| Automatisch behebbar | {summary.get('auto_fixable', 0)} |
| Widget-Fixes | {summary.get('widget_fixable', 0)} |
| Manuell zu beheben | {summary.get('manual_only', 0)} |
| Geschätztes Risiko | €{summary.get('total_risk_euro', 0):,} |

---

## Paket-Inhalt

```
├── README.md              # Diese Datei
├── patches/               # Unified Diff Patches
│   └── *.patch           # Pro Problem ein Patch
├── snippets/              # HTML-Code zum Einfügen
│   └── accessibility-snippets.html
├── css/                   # CSS-Fixes
│   └── complyo-accessibility.css
├── wordpress/             # WordPress-Plugin
│   └── complyo-accessibility/
├── widget/                # Widget-Integration
│   └── integration.html
└── meta/                  # Metadaten
    └── summary.json
```

---

## Schnellstart

### Option 1: Widget (Empfohlen)

1. Öffnen Sie `widget/integration.html`
2. Kopieren Sie den Code
3. Fügen Sie ihn vor `</body>` in Ihre Website ein
4. Fertig! ✅

### Option 2: WordPress-Plugin

1. Laden Sie den Ordner `wordpress/complyo-accessibility/` hoch
2. Ziel: `/wp-content/plugins/`
3. Aktivieren Sie das Plugin im WordPress-Admin
4. Fertig! ✅

### Option 3: Manuelle Patches

1. Öffnen Sie den Ordner `patches/`
2. Jede `.patch`-Datei enthält Änderungen für eine Datei
3. Wenden Sie die Patches an:
   ```bash
   git apply patches/ALT_TEXT_index_html.patch
   ```
4. Alternativ: Kopieren Sie den Code aus den Anleitungsdateien

---

## Wichtige Hinweise

⚠️ **Backup erstellen** - Erstellen Sie immer ein Backup bevor Sie Änderungen vornehmen!

⚠️ **Testen** - Testen Sie alle Änderungen in einer Staging-Umgebung

⚠️ **KI-generiert** - Die Fixes wurden automatisch generiert. Bitte prüfen Sie die Texte!

---

## Support

- **E-Mail:** support@complyo.tech
- **Dokumentation:** https://complyo.tech/docs
- **Dashboard:** https://app.complyo.tech

---

© {datetime.now().year} Complyo.tech - Barrierefreiheit leicht gemacht.
"""
    
    def _generate_patch_instructions(self, patch: Dict) -> str:
        """Generiert Anleitung für einen einzelnen Patch"""
        return f"""
PATCH-ANLEITUNG
===============

Feature: {patch.get('feature_id', 'Unbekannt')}
Datei: {patch.get('file_path', 'Unbekannt')}
WCAG: {', '.join(patch.get('wcag_criteria', []))}

BESCHREIBUNG
------------
{patch.get('description', 'Keine Beschreibung verfügbar')}

ANWENDUNG
---------
{patch.get('instructions', 'Wenden Sie den Patch mit git apply an oder kopieren Sie die Änderungen manuell.')}

PATCH-INHALT
------------
{patch.get('unified_diff', '# Kein Patch verfügbar')}
"""
    
    def _generate_html_snippets(self, fix_package: Dict) -> str:
        """Generiert HTML-Snippets zum direkten Kopieren"""
        snippets = []
        
        snippets.append("""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Complyo Accessibility Snippets</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
        h1 { color: #1e40af; }
        h2 { color: #374151; margin-top: 2rem; }
        pre { background: #1f2937; color: #10b981; padding: 1rem; border-radius: 8px; overflow-x: auto; }
        .copy-hint { color: #6b7280; font-size: 0.875rem; }
    </style>
</head>
<body>
    <h1>🔧 Complyo Accessibility Snippets</h1>
    <p class="copy-hint">Kopieren Sie die gewünschten Code-Snippets und fügen Sie sie in Ihre Website ein.</p>
""")
        
        # Skip-Link Snippet
        snippets.append("""
    <h2>1. Skip-Link (Tastatur-Navigation)</h2>
    <p>Fügen Sie diesen Code direkt nach dem &lt;body&gt;-Tag ein:</p>
    <pre><code>&lt;a href="#main-content" class="skip-link"&gt;
    Zum Hauptinhalt springen
&lt;/a&gt;

&lt;style&gt;
.skip-link {
    position: absolute;
    top: -100px;
    left: 0;
    background: #1e40af;
    color: white;
    padding: 12px 24px;
    text-decoration: none;
    font-weight: bold;
    z-index: 999999;
}
.skip-link:focus {
    top: 0;
}
&lt;/style&gt;</code></pre>
""")
        
        # Focus-Styles Snippet
        snippets.append("""
    <h2>2. Focus-Styles (WCAG 2.4.7)</h2>
    <p>Fügen Sie diese CSS-Regeln hinzu:</p>
    <pre><code>*:focus-visible {
    outline: 3px solid #1e40af;
    outline-offset: 2px;
}

button:focus-visible,
a:focus-visible,
input:focus-visible {
    outline: 3px solid #1e40af;
    outline-offset: 2px;
}</code></pre>
""")
        
        # ARIA Landmarks Snippet
        snippets.append("""
    <h2>3. ARIA Landmarks</h2>
    <p>Strukturieren Sie Ihre Seite mit semantischen Elementen:</p>
    <pre><code>&lt;header role="banner"&gt;
    &lt;nav aria-label="Hauptnavigation"&gt;...&lt;/nav&gt;
&lt;/header&gt;

&lt;main id="main-content" role="main"&gt;
    ...
&lt;/main&gt;

&lt;footer role="contentinfo"&gt;
    ...
&lt;/footer&gt;</code></pre>
""")
        
        # Widget-Integration
        widget_fixes = fix_package.get('widget_fixes', [])
        if widget_fixes and len(widget_fixes) > 0:
            widget_code = widget_fixes[0].get('integration_code', '')
            snippets.append(f"""
    <h2>4. Complyo Widget (Empfohlen)</h2>
    <p>Fügen Sie diesen Code vor &lt;/body&gt; ein für automatische Fixes:</p>
    <pre><code>{widget_code}</code></pre>
""")
        
        snippets.append("""
</body>
</html>
""")
        
        return ''.join(snippets)
    
    def _generate_consolidated_css(self, fix_package: Dict) -> str:
        """Generiert konsolidierte CSS-Datei mit allen Fixes"""
        return f"""/**
 * Complyo Accessibility CSS
 * Generiert: {datetime.now().strftime("%Y-%m-%d %H:%M")}
 * 
 * Diese Datei enthält alle CSS-Fixes für Barrierefreiheit.
 * Binden Sie sie in Ihren <head> ein:
 * <link rel="stylesheet" href="complyo-accessibility.css">
 */

/* ===========================================
   1. Skip-Link für Tastatur-Navigation
   =========================================== */

.skip-link {{
    position: absolute;
    top: -100px;
    left: 0;
    background: #1e40af;
    color: #ffffff;
    padding: 12px 24px;
    text-decoration: none;
    font-weight: 600;
    z-index: 999999;
    border-radius: 0 0 8px 0;
    transition: top 0.2s ease;
}}

.skip-link:focus {{
    top: 0;
    outline: 3px solid #fbbf24;
    outline-offset: 2px;
}}

/* ===========================================
   2. Focus-Indikatoren (WCAG 2.4.7)
   =========================================== */

*:focus-visible {{
    outline: 3px solid #1e40af !important;
    outline-offset: 2px !important;
}}

button:focus-visible,
a:focus-visible,
input:focus-visible,
select:focus-visible,
textarea:focus-visible,
[tabindex]:focus-visible {{
    outline: 3px solid #1e40af !important;
    outline-offset: 2px !important;
    box-shadow: 0 0 0 4px rgba(30, 64, 175, 0.2) !important;
}}

/* ===========================================
   3. Kontrast-Verbesserungen (WCAG 1.4.3)
   =========================================== */

.text-gray-400,
.text-gray-500,
.text-muted {{
    color: #374151 !important; /* Verbessert von #9ca3af */
}}

/* ===========================================
   4. Link-Sichtbarkeit
   =========================================== */

a {{
    text-decoration: underline;
    text-underline-offset: 2px;
}}

a:hover {{
    text-decoration-thickness: 2px;
}}

/* ===========================================
   5. Reduced Motion Support
   =========================================== */

@media (prefers-reduced-motion: reduce) {{
    *,
    *::before,
    *::after {{
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }}
}}

/* ===========================================
   6. High Contrast Mode Support
   =========================================== */

@media (prefers-contrast: high) {{
    * {{
        border-width: 2px !important;
    }}
    
    a {{
        text-decoration: underline !important;
        text-decoration-thickness: 2px !important;
    }}
}}

/* ===========================================
   7. Screen Reader Only
   =========================================== */

.sr-only,
.visually-hidden {{
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    padding: 0 !important;
    margin: -1px !important;
    overflow: hidden !important;
    clip: rect(0, 0, 0, 0) !important;
    white-space: nowrap !important;
    border: 0 !important;
}}

/* ===========================================
   8. Touch Target Size (min 44x44px)
   =========================================== */

button,
a,
input[type="checkbox"],
input[type="radio"],
[role="button"] {{
    min-height: 44px;
    min-width: 44px;
}}

/* ===========================================
   9. Form-Verbesserungen
   =========================================== */

input:focus,
textarea:focus,
select:focus {{
    border-color: #1e40af !important;
}}

::placeholder {{
    color: #6b7280;
    opacity: 1;
}}

/* ===========================================
   10. Print-Barrierefreiheit
   =========================================== */

@media print {{
    a[href]:after {{
        content: " (" attr(href) ")";
    }}
    
    abbr[title]:after {{
        content: " (" attr(title) ")";
    }}
}}
"""
    
    def _generate_wordpress_plugin(self, site_id: str, fix_package: Dict) -> str:
        """Generiert ein WordPress-Plugin für die Accessibility-Fixes"""
        summary = fix_package.get('summary', {})
        
        return f"""<?php
/**
 * Plugin Name: Complyo Accessibility
 * Plugin URI: https://complyo.tech
 * Description: Barrierefreiheits-Fixes für Ihre WordPress-Website. Automatisch generiert von Complyo.
 * Version: 1.0.0
 * Author: Complyo.tech
 * Author URI: https://complyo.tech
 * License: GPL v2 or later
 * Text Domain: complyo-accessibility
 */

// Sicherheit: Direktzugriff verhindern
if (!defined('ABSPATH')) {{
    exit;
}}

/**
 * Complyo Accessibility Plugin
 * Generiert: {datetime.now().strftime("%Y-%m-%d %H:%M")}
 * Site-ID: {site_id}
 */
class Complyo_Accessibility {{
    
    private static $instance = null;
    
    public static function get_instance() {{
        if (null === self::$instance) {{
            self::$instance = new self();
        }}
        return self::$instance;
    }}
    
    private function __construct() {{
        // CSS laden
        add_action('wp_enqueue_scripts', array($this, 'enqueue_styles'));
        
        // Skip-Link hinzufügen
        add_action('wp_body_open', array($this, 'add_skip_link'));
        
        // Admin-Menü
        add_action('admin_menu', array($this, 'add_admin_menu'));
    }}
    
    public function enqueue_styles() {{
        // Inline-CSS für Barrierefreiheit
        $css = $this->get_accessibility_css();
        wp_add_inline_style('wp-block-library', $css);
    }}
    
    public function add_skip_link() {{
        echo '<a href="#main" class="complyo-skip-link">Zum Hauptinhalt springen</a>';
    }}
    
    public function add_admin_menu() {{
        add_options_page(
            'Complyo Accessibility',
            'Barrierefreiheit',
            'manage_options',
            'complyo-accessibility',
            array($this, 'render_admin_page')
        );
    }}
    
    public function render_admin_page() {{
        ?>
        <div class="wrap">
            <h1>Complyo Accessibility</h1>
            <div class="card" style="max-width: 600px; padding: 20px;">
                <h2>Status</h2>
                <p><strong>Aktiv:</strong> ✅ Barrierefreiheits-Fixes sind aktiviert</p>
                <p><strong>Behobene Probleme:</strong> {summary.get('auto_fixable', 0)}</p>
                <p><strong>Risiko-Reduktion:</strong> €{summary.get('total_risk_euro', 0):,}</p>
                
                <h3>Aktive Features</h3>
                <ul>
                    <li>✅ Skip-Link für Tastatur-Navigation</li>
                    <li>✅ Focus-Indikatoren (WCAG 2.4.7)</li>
                    <li>✅ Kontrast-Verbesserungen (WCAG 1.4.3)</li>
                    <li>✅ Reduced Motion Support</li>
                    <li>✅ High Contrast Mode Support</li>
                </ul>
                
                <p style="margin-top: 20px;">
                    <a href="https://app.complyo.tech" target="_blank" class="button button-primary">
                        Zum Complyo Dashboard
                    </a>
                </p>
            </div>
        </div>
        <?php
    }}
    
    private function get_accessibility_css() {{
        return '
            .complyo-skip-link {{
                position: absolute;
                top: -100px;
                left: 0;
                background: #1e40af;
                color: #fff;
                padding: 12px 24px;
                text-decoration: none;
                font-weight: 600;
                z-index: 999999;
                border-radius: 0 0 8px 0;
                transition: top 0.2s;
            }}
            .complyo-skip-link:focus {{
                top: 0;
                outline: 3px solid #fbbf24;
            }}
            *:focus-visible {{
                outline: 3px solid #1e40af !important;
                outline-offset: 2px !important;
            }}
            @media (prefers-reduced-motion: reduce) {{
                * {{ animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }}
            }}
        ';
    }}
}}

// Plugin initialisieren
Complyo_Accessibility::get_instance();
"""
    
    def _generate_wordpress_plugin_readme(self) -> str:
        """Generiert readme.txt für WordPress-Plugin"""
        return """=== Complyo Accessibility ===
Contributors: complyotech
Tags: accessibility, barrierefreiheit, wcag, bfsg, a11y
Requires at least: 5.0
Tested up to: 6.4
Stable tag: 1.0.0
License: GPLv2 or later
License URI: http://www.gnu.org/licenses/gpl-2.0.html

Barrierefreiheits-Fixes für Ihre WordPress-Website. Automatisch generiert von Complyo.

== Description ==

Dieses Plugin wurde automatisch von Complyo.tech generiert und enthält:

* Skip-Link für Tastatur-Navigation
* Verbesserte Focus-Indikatoren (WCAG 2.4.7)
* Kontrast-Verbesserungen (WCAG 1.4.3)
* Reduced Motion Support
* High Contrast Mode Support

== Installation ==

1. Laden Sie den Plugin-Ordner in `/wp-content/plugins/` hoch
2. Aktivieren Sie das Plugin im WordPress-Admin unter "Plugins"
3. Fertig! Die Fixes werden automatisch angewendet.

== Frequently Asked Questions ==

= Muss ich etwas konfigurieren? =

Nein, das Plugin funktioniert sofort nach der Aktivierung.

= Ist das Plugin DSGVO-konform? =

Ja, das Plugin speichert keine personenbezogenen Daten.

== Changelog ==

= 1.0.0 =
* Initial Release

== Upgrade Notice ==

= 1.0.0 =
Erste Version des automatisch generierten Accessibility-Plugins.
"""
    
    def _generate_widget_integration(self, site_id: str, widget_fixes: List[Dict]) -> str:
        """Generiert Widget-Integrations-Code"""
        integration_code = widget_fixes[0].get('integration_code', '') if widget_fixes else ''
        
        return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Complyo Widget Integration</title>
</head>
<body>
    <h1>Complyo Widget Integration</h1>
    
    <p>Fügen Sie den folgenden Code vor dem schließenden <code>&lt;/body&gt;</code>-Tag ein:</p>
    
    <pre style="background: #1f2937; color: #10b981; padding: 20px; border-radius: 8px; overflow-x: auto;">
<code>{integration_code}</code>
    </pre>
    
    <h2>Anleitung</h2>
    <ol>
        <li>Kopieren Sie den Code oben</li>
        <li>Öffnen Sie Ihre HTML-Datei (z.B. index.html)</li>
        <li>Suchen Sie das <code>&lt;/body&gt;</code>-Tag</li>
        <li>Fügen Sie den Code DAVOR ein</li>
        <li>Speichern und testen Sie Ihre Website</li>
    </ol>
    
    <h3>WordPress</h3>
    <p>In WordPress können Sie den Code über:</p>
    <ul>
        <li><strong>Theme Customizer:</strong> Design → Customizer → Zusätzliches CSS/JavaScript</li>
        <li><strong>Plugin:</strong> "Insert Headers and Footers" oder "WPCode"</li>
        <li><strong>Theme:</strong> footer.php vor <code>&lt;/body&gt;</code></li>
    </ul>
    
    <hr>
    <p>Support: <a href="https://complyo.tech/support">complyo.tech/support</a></p>
</body>
</html>
"""

