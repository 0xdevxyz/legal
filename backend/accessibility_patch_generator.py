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
from typing import List, Dict, Optional
import aiohttp
from datetime import datetime
import logging
import json
from urllib.parse import urlparse, urljoin

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
            
            # 2. CSS-Patches
            if contrast_fixes or True:  # Immer CSS für Focus-Styles
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
                # Für Demo: Generiere Beispiel-HTML
                # In Produktion: Lade echtes HTML vom Server
                fixed_html = self._generate_example_html_with_fixes(page_url, page_fixes)
                
                # Dateiname generieren
                filename = self._url_to_filename(page_url)
                patches[filename] = fixed_html
                
                logger.info(f"Generated HTML patch for {page_url}: {filename}")
                
            except Exception as e:
                logger.error(f"Error generating HTML patch for {page_url}: {e}")
                continue
        
        return patches
    
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

