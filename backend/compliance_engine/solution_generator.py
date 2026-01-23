"""
Solution Generator - Erzeugt strukturierte, anfängerfreundliche Lösungen
Erstellt Copy-Paste-ready Code-Fixes mit ausführlichen Erklärungen
"""

from typing import Dict, Any, List
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class DetailedSolution:
    """Strukturierte Lösung mit allen Details"""
    why_legal: str  # Rechtliche Begründung in einfacher Sprache
    what: str  # Konkrete Problembeschreibung
    where: str  # Genauer Ort auf der Website
    why_no_autofix: str  # Erklärung warum keine automatische Behebung
    how: List[str]  # Schritt-für-Schritt Anleitung
    code_example: str  # Copy-Paste-ready Code
    estimated_time: str  # Geschätzte Umsetzungszeit
    validation_steps: List[str]  # Checkliste zur Überprüfung

class SolutionGenerator:
    """Generiert detaillierte, anfängerfreundliche Lösungen"""
    
    def generate_detailed_solution(
        self,
        issue_category: str,
        website_structure: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generiert eine strukturierte Lösung für eine Issue-Kategorie
        
        Args:
            issue_category: z.B. "impressum", "datenschutz", "cookies", "barrierefreiheit"
            website_structure: Optional - Struktur-Infos der Website
            
        Returns:
            Dict mit strukturierter Lösung
        """
        try:
            solution = self._generate_solution_for_category(issue_category, website_structure)
            return asdict(solution)
        except Exception as e:
            logger.error(f"Fehler bei Solution-Generierung für {issue_category}: {e}")
            return self._fallback_solution(issue_category)
    
    def _generate_solution_for_category(
        self,
        category: str,
        website_structure: Dict[str, Any] = None
    ) -> DetailedSolution:
        """Generiert kategorie-spezifische Lösung"""
        
        generators = {
            "impressum": self._generate_impressum_solution,
            "datenschutz": self._generate_datenschutz_solution,
            "cookies": self._generate_cookies_solution,
            "barrierefreiheit": self._generate_accessibility_solution,
            "agb": self._generate_agb_solution,
            "ssl": self._generate_ssl_solution,
        }
        
        generator = generators.get(category, self._generate_generic_solution)
        return generator(website_structure)
    
    # ==================== Kategorie-spezifische Generatoren ====================
    
    def _generate_impressum_solution(self, website_structure: Dict = None) -> DetailedSolution:
        """Lösung für fehlendes/unvollständiges Impressum"""
        return DetailedSolution(
            why_legal=(
                "Das Impressum ist nach § 5 TMG (Telemediengesetz) für alle geschäftsmäßigen "
                "Webseiten in Deutschland verpflichtend. Bei Fehlen oder unvollständigen Angaben "
                "drohen Abmahnungen bis 5.000€ und Bußgelder bis 50.000€."
            ),
            what=(
                "Ihre Website hat kein vollständiges Impressum oder das Impressum ist nicht "
                "leicht auffindbar. Ein Impressum muss mit maximal 2 Klicks erreichbar sein."
            ),
            where=(
                "Das Impressum sollte im Footer jeder Seite verlinkt sein. "
                "Typischer Ort: <footer> Element am Ende der Seite."
            ),
            why_no_autofix=(
                "Wir können Ihr Impressum nicht automatisch erstellen, weil:\n\n"
                "1. **Individuelle Firmendaten**: Nur Sie kennen Ihre korrekten Firmendaten, "
                "Handelsregister-Nummer, Vertretungsberechtigte etc.\n"
                "2. **Rechtliche Verantwortung**: Die Richtigkeit der Angaben liegt in Ihrer "
                "Verantwortung. Falsche Angaben können rechtliche Konsequenzen haben.\n"
                "3. **Website-Struktur**: Jede Website hat eine individuelle Footer-Struktur "
                "und Design-System."
            ),
            how=[
                "1. Erstellen Sie eine neue Seite 'impressum.html' oder '/impressum'",
                "2. Füllen Sie diese Seite mit Ihren Pflichtangaben (siehe Code-Beispiel)",
                "3. Öffnen Sie Ihre Footer-Komponente (meist 'footer.html', 'Footer.tsx' oder im CMS)",
                "4. Fügen Sie den Impressum-Link ein (siehe Code-Beispiel)",
                "5. Testen Sie den Link auf verschiedenen Seiten Ihrer Website",
                "6. Veröffentlichen Sie die Änderungen"
            ],
            code_example="""<!-- Footer-Link zum Impressum -->
<footer>
  <nav aria-label="Rechtliche Links">
    <ul>
      <li><a href="/impressum">Impressum</a></li>
      <li><a href="/datenschutz">Datenschutz</a></li>
    </ul>
  </nav>
</footer>

<!-- Impressum-Seite (impressum.html) -->
<h1>Impressum</h1>

<h2>Angaben gemäß § 5 TMG</h2>
<p>
  [IHR FIRMENNAME]<br>
  [IHR NAME]<br>
  [STRASSE UND HAUSNUMMER]<br>
  [PLZ UND ORT]
</p>

<h2>Kontakt</h2>
<p>
  Telefon: [IHRE TELEFONNUMMER]<br>
  E-Mail: [IHRE E-MAIL]
</p>

<h2>Umsatzsteuer-ID</h2>
<p>
  Umsatzsteuer-Identifikationsnummer gemäß § 27 a Umsatzsteuergesetz:<br>
  [IHRE UST-ID]
</p>

<!-- Weitere Pflichtangaben je nach Rechtsform -->""",
            estimated_time="15-20 Minuten",
            validation_steps=[
                "✓ Impressum-Link ist im Footer sichtbar",
                "✓ Link funktioniert und führt zur Impressum-Seite",
                "✓ Alle Pflichtangaben sind vorhanden (Name, Adresse, Kontakt, USt-ID)",
                "✓ Impressum ist mit maximal 2 Klicks von jeder Seite erreichbar",
                "✓ Impressum ist auf mobilen Geräten gut lesbar"
            ]
        )
    
    def _generate_datenschutz_solution(self, website_structure: Dict = None) -> DetailedSolution:
        """Lösung für Datenschutzerklärung"""
        return DetailedSolution(
            why_legal=(
                "Eine Datenschutzerklärung ist nach Art. 13 DSGVO verpflichtend, sobald "
                "personenbezogene Daten erhoben werden (z.B. durch Kontaktformulare, Cookies, "
                "Analytics). Verstöße können Bußgelder bis 20 Mio. € oder 4% des Jahresumsatzes nach sich ziehen."
            ),
            what=(
                "Ihre Website hat keine oder keine vollständige Datenschutzerklärung. "
                "Diese muss umfassend über alle Datenverarbeitungen informieren."
            ),
            where=(
                "Die Datenschutzerklärung sollte im Footer jeder Seite verlinkt sein, "
                "direkt neben dem Impressum."
            ),
            why_no_autofix=(
                "Wir können Ihre Datenschutzerklärung nicht automatisch erstellen, weil:\n\n"
                "1. **Individuelle Datenverarbeitung**: Nur Sie wissen, welche Tools (Analytics, "
                "Newsletter, CRM) Sie einsetzen und wie Sie Daten verarbeiten.\n"
                "2. **Rechtliche Haftung**: Eine fehlerhafte Datenschutzerklärung kann teuer werden. "
                "Sie müssen die Inhalte verantworten können.\n"
                "3. **Dynamische Anforderungen**: Je nach eingesetzten Tools und Diensten variieren "
                "die Anforderungen stark."
            ),
            how=[
                "1. Nutzen Sie einen Datenschutz-Generator (z.B. eRecht24, activeMind)",
                "2. Geben Sie dort alle verwendeten Tools und Dienste an",
                "3. Laden Sie die generierte Datenschutzerklärung herunter",
                "4. Erstellen Sie eine Seite 'datenschutz.html' oder '/datenschutz'",
                "5. Fügen Sie den generierten Text ein",
                "6. Verlinken Sie die Seite im Footer (siehe Code-Beispiel)",
                "7. Prüfen Sie regelmäßig auf Aktualität (mindestens jährlich)"
            ],
            code_example="""<!-- Footer-Link zur Datenschutzerklärung -->
<footer>
  <nav aria-label="Rechtliche Links">
    <ul>
      <li><a href="/impressum">Impressum</a></li>
      <li><a href="/datenschutz">Datenschutz</a></li>
    </ul>
  </nav>
</footer>

<!-- Datenschutz-Seite (datenschutz.html) -->
<h1>Datenschutzerklärung</h1>

<h2>1. Datenschutz auf einen Blick</h2>
<h3>Allgemeine Hinweise</h3>
<p>
  Die folgenden Hinweise geben einen einfachen Überblick darüber, 
  was mit Ihren personenbezogenen Daten passiert, wenn Sie diese 
  Website besuchen...
</p>

<h2>2. Verantwortlicher</h2>
<p>
  Verantwortlich für die Datenverarbeitung auf dieser Website ist:<br>
  [IHR FIRMENNAME]<br>
  [IHRE ADRESSE]<br>
  E-Mail: [IHRE E-MAIL]
</p>

<!-- Nutzen Sie einen Generator für den vollständigen Text! -->""",
            estimated_time="30-45 Minuten (mit Generator)",
            validation_steps=[
                "✓ Datenschutz-Link ist im Footer sichtbar",
                "✓ Link führt zur vollständigen Datenschutzerklärung",
                "✓ Verantwortlicher ist korrekt benannt",
                "✓ Alle eingesetzten Tools (Analytics, Cookies, etc.) sind aufgeführt",
                "✓ Rechte der Betroffenen sind erklärt (Auskunft, Löschung, Widerruf)",
                "✓ Datenschutzerklärung ist aktuell (Datum prüfen)"
            ]
        )
    
    def _generate_cookies_solution(self, website_structure: Dict = None) -> DetailedSolution:
        """Lösung für Cookie-Consent"""
        return DetailedSolution(
            why_legal=(
                "Cookies dürfen nach § 25 TTDSG nur mit aktiver Einwilligung des Nutzers "
                "gesetzt werden. Das bedeutet: Opt-In statt Opt-Out. Verstöße können mit "
                "bis zu 50.000€ Bußgeld geahndet werden."
            ),
            what=(
                "Ihre Website setzt Cookies ohne vorherige Einwilligung oder hat keinen "
                "Cookie-Consent-Banner. Dies betrifft insbesondere Analytics-Cookies "
                "(Google Analytics, etc.)."
            ),
            where=(
                "Ein Cookie-Consent-Banner sollte beim ersten Besuch erscheinen, "
                "bevor nicht-notwendige Cookies gesetzt werden."
            ),
            why_no_autofix=(
                "Wir können keinen Cookie-Banner automatisch einbauen, weil:\n\n"
                "1. **Technische Integration**: Der Banner muss tief in Ihre Website-Logik "
                "integriert werden, um Cookies tatsächlich zu blockieren.\n"
                "2. **Design-Anpassung**: Der Banner sollte zu Ihrem Corporate Design passen "
                "und nicht wie ein Fremdkörper wirken.\n"
                "3. **Cookie-Inventar**: Nur Sie wissen, welche Cookies Ihre Website setzt "
                "und welche davon notwendig sind."
            ),
            how=[
                "1. Öffnen Sie das Complyo Dashboard und gehen Sie zu 'Cookie-Compliance'",
                "2. Scannen Sie Ihre Website automatisch nach verwendeten Cookies",
                "3. Passen Sie Design und Texte des Cookie-Banners an",
                "4. Kopieren Sie den bereitgestellten JavaScript-Code",
                "5. Fügen Sie den Code im <head> Ihrer Website ein (siehe Beispiel)",
                "6. Testen Sie: Cookies dürfen erst NACH Zustimmung gesetzt werden",
                "7. Verfolgen Sie Opt-In-Raten in der integrierten Statistik"
            ],
            code_example="""<!-- Complyo Cookie-Compliance Widget -->
<head>
  <!-- Complyo Cookie-Banner Script -->
  <script 
    src="https://api.complyo.tech/api/widgets/cookie-compliance.js" 
    data-site-id="[IHRE-SITE-ID]"
    async
  ></script>
</head>

<!-- 
  Das Complyo Cookie-Banner wird automatisch angezeigt
  und blockiert Tracking-Cookies bis zur Zustimmung.
  
  Features:
  - DSGVO & TTDSG konform
  - Automatische Cookie-Erkennung
  - Content Blocker für YouTube, Google Maps, etc.
  - 20+ Service-Vorlagen
  - Consent-Statistiken im Dashboard
  - WCAG 2.2 Level AA barrierefrei
  
  Konfiguration im Dashboard unter:
  https://app.complyo.tech/cookie-compliance
-->""",
            estimated_time="45-60 Minuten",
            validation_steps=[
                "✓ Cookie-Banner erscheint beim ersten Besuch",
                "✓ Cookies werden ERST NACH Zustimmung gesetzt (im Browser-DevTools prüfen)",
                "✓ Nutzer kann Ablehnen und trotzdem die Website nutzen",
                "✓ Cookie-Einstellungen können nachträglich geändert werden",
                "✓ Datenschutzerklärung listet alle verwendeten Cookies auf",
                "✓ Banner ist auf mobilen Geräten nutzbar"
            ]
        )
    
    def _generate_accessibility_solution(self, website_structure: Dict = None) -> DetailedSolution:
        """Lösung für Barrierefreiheit (WCAG/BFSG)"""
        return DetailedSolution(
            why_legal=(
                "Das Barrierefreiheitsstärkungsgesetz (BFSG) verpflichtet ab 28. Juni 2025 "
                "Unternehmen, digitale Produkte barrierefrei nach WCAG 2.1 Level AA zu gestalten. "
                "Verstöße können bis zu 100.000€ Bußgeld kosten."
            ),
            what=(
                "Ihre Website erfüllt nicht die Anforderungen der WCAG 2.1 Level AA. "
                "Häufige Probleme: Fehlende Alt-Texte, schlechte Kontraste, keine Tastaturnavigation."
            ),
            where=(
                "Barrierefreiheit betrifft die gesamte Website: HTML-Struktur, CSS-Styling, "
                "JavaScript-Interaktionen und Medieninhalte."
            ),
            why_no_autofix=(
                "Wir können Barrierefreiheit nicht automatisch herstellen, weil:\n\n"
                "1. **Inhaltliches Verständnis**: Alt-Texte für Bilder erfordern Verständnis des Bildinhalts.\n"
                "2. **Design-Entscheidungen**: Farbkontraste und Schriftgrößen sind Design-Entscheidungen, "
                "die zu Ihrer Corporate Identity passen müssen.\n"
                "3. **Semantische Struktur**: Die HTML-Struktur muss grundlegend überarbeitet werden, "
                "was tiefe Eingriffe in den Code erfordert."
            ),
            how=[
                "1. Prüfen Sie Ihre Website mit dem WAVE Tool (wave.webaim.org)",
                "2. Fügen Sie Alt-Texte zu allen Bildern hinzu (beschreibend, nicht 'Bild1')",
                "3. Verbessern Sie Farbkontraste auf mindestens 4.5:1 (Text zu Hintergrund)",
                "4. Verwenden Sie semantisches HTML (<header>, <nav>, <main>, <footer>)",
                "5. Stellen Sie sicher, dass alle Funktionen per Tastatur erreichbar sind",
                "6. Fügen Sie ARIA-Labels zu interaktiven Elementen hinzu",
                "7. Testen Sie mit einem Screenreader (NVDA für Windows, VoiceOver für Mac)"
            ],
            code_example="""<!-- Barrierefreie Bilder -->
<img 
  src="team-photo.jpg" 
  alt="Team-Foto: Fünf Mitarbeiter vor dem Bürogebäude" 
/>

<!-- Semantisches HTML -->
<header>
  <nav aria-label="Hauptnavigation">
    <ul>
      <li><a href="/">Start</a></li>
      <li><a href="/produkte">Produkte</a></li>
    </ul>
  </nav>
</header>

<main>
  <h1>Willkommen auf unserer Website</h1>
  <p>Hauptinhalt hier...</p>
</main>

<footer>
  <p>&copy; 2025 Firma</p>
</footer>

<!-- Tastaturzugängliche Buttons -->
<button 
  aria-label="Menü öffnen" 
  onclick="openMenu()"
  type="button"
>
  ☰
</button>

<!-- Skip-Link für Screenreader -->
<a href="#main-content" class="skip-link">
  Zum Hauptinhalt springen
</a>
<main id="main-content">...</main>

<style>
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: #000;
  color: #fff;
  padding: 8px;
}
.skip-link:focus {
  top: 0;
}
</style>""",
            estimated_time="2-4 Stunden (je nach Website-Größe)",
            validation_steps=[
                "✓ Alle Bilder haben beschreibende Alt-Texte",
                "✓ Farbkontraste erreichen mindestens WCAG AA (4.5:1)",
                "✓ Website ist vollständig per Tastatur bedienbar (Tab, Enter, Arrows)",
                "✓ Heading-Struktur ist logisch (H1 → H2 → H3, nicht H1 → H4)",
                "✓ Formulare haben sichtbare Labels und Fehlermeldungen",
                "✓ Screenreader kann alle Inhalte vorlesen",
                "✓ Videos haben Untertitel"
            ]
        )
    
    def _generate_agb_solution(self, website_structure: Dict = None) -> DetailedSolution:
        """Lösung für fehlende AGB"""
        return DetailedSolution(
            why_legal="AGB sind für Online-Shops und vertragliche Dienstleistungen Pflicht.",
            what="Ihre Website hat keine AGB oder diese sind nicht verlinkt.",
            where="AGB sollten im Footer und vor Kaufabschluss verlinkt sein.",
            why_no_autofix=(
                "AGB müssen individuell auf Ihr Geschäftsmodell zugeschnitten sein "
                "und können nicht automatisch generiert werden."
            ),
            how=[
                "1. Nutzen Sie einen AGB-Generator (z.B. eRecht24, IT-Recht-Kanzlei)",
                "2. Geben Sie Ihre Geschäftsbedingungen an",
                "3. Laden Sie die generierten AGB herunter",
                "4. Verlinken Sie im Footer und im Checkout-Prozess"
            ],
            code_example="""<footer>
  <a href="/agb">AGB</a> | 
  <a href="/impressum">Impressum</a>
</footer>""",
            estimated_time="30 Minuten",
            validation_steps=[
                "✓ AGB sind im Footer verlinkt",
                "✓ Im Checkout muss Checkbox 'AGB akzeptiert' vorhanden sein",
                "✓ AGB enthalten Widerrufsbelehrung (für Verbraucher)"
            ]
        )
    
    def _generate_ssl_solution(self, website_structure: Dict = None) -> DetailedSolution:
        """Lösung für fehlendes SSL/HTTPS"""
        return DetailedSolution(
            why_legal=(
                "HTTPS ist Pflicht für Websites, die personenbezogene Daten übertragen. "
                "Browser warnen vor unsicheren Verbindungen."
            ),
            what="Ihre Website verwendet kein HTTPS oder das Zertifikat ist abgelaufen.",
            where="HTTPS betrifft die gesamte Website und wird auf Server-Ebene konfiguriert.",
            why_no_autofix=(
                "SSL-Zertifikate müssen auf Ihrem Webserver installiert werden. "
                "Das erfordert Server-Zugang, den wir nicht haben."
            ),
            how=[
                "1. Besorgen Sie ein SSL-Zertifikat (kostenlos: Let's Encrypt)",
                "2. Installieren Sie das Zertifikat auf Ihrem Webserver",
                "3. Leiten Sie HTTP auf HTTPS um (301 Redirect)",
                "4. Aktualisieren Sie alle internen Links auf HTTPS",
                "5. Prüfen Sie das Zertifikat mit SSL Labs"
            ],
            code_example="""<!-- .htaccess für Apache (HTTP → HTTPS Redirect) -->
RewriteEngine On
RewriteCond %{HTTPS} !=on
RewriteRule ^(.*)$ https://%{HTTP_HOST}/$1 [R=301,L]

<!-- Oder in nginx.conf -->
server {
    listen 80;
    server_name example.com;
    return 301 https://$server_name$request_uri;
}""",
            estimated_time="30-60 Minuten",
            validation_steps=[
                "✓ Website ist über https:// erreichbar",
                "✓ http:// leitet automatisch auf https:// weiter",
                "✓ Kein Schloss-Symbol mit Warnung im Browser",
                "✓ SSL Labs Test zeigt mindestens A-Rating"
            ]
        )
    
    def _generate_generic_solution(self, website_structure: Dict = None) -> DetailedSolution:
        """Fallback für unbekannte Kategorien"""
        return DetailedSolution(
            why_legal="Diese Compliance-Anforderung ist für rechtssichere Websites wichtig.",
            what="Es wurde ein Problem in diesem Bereich erkannt.",
            where="Prüfen Sie die betroffenen Bereiche Ihrer Website.",
            why_no_autofix=(
                "Automatische Behebung ist nicht möglich, da individuelle Anpassungen "
                "erforderlich sind."
            ),
            how=[
                "1. Analysieren Sie das Problem im Detail",
                "2. Konsultieren Sie ggf. einen Rechtsexperten",
                "3. Setzen Sie die empfohlenen Maßnahmen um"
            ],
            code_example="<!-- Beispiel-Code wird individuell generiert -->",
            estimated_time="Variabel",
            validation_steps=[
                "✓ Problem wurde behoben",
                "✓ Lösung wurde getestet"
            ]
        )
    
    def _fallback_solution(self, category: str) -> Dict[str, Any]:
        """Fallback bei Fehler"""
        return {
            "why_legal": f"Compliance-Anforderung für {category}",
            "what": "Problem erkannt",
            "where": "Auf Ihrer Website",
            "why_no_autofix": "Manuelle Umsetzung erforderlich",
            "how": ["Bitte kontaktieren Sie den Support"],
            "code_example": "<!-- Code-Beispiel -->",
            "estimated_time": "Variabel",
            "validation_steps": ["Lösung testen"]
        }

# Global Instance
solution_generator = SolutionGenerator()

