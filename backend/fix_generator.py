"""
Fix Generator Service für Complyo
Generiert KI-basierte Lösungen für Compliance-Issues
"""

import asyncpg
import aiohttp
import hashlib
import json
import os
import redis.asyncio as redis
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from prompts.fix_prompts import get_prompt_for_category

logger = logging.getLogger(__name__)

class FixGenerator:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-3.5-sonnet"
        self.redis_client = None
        self.cache_ttl = 604800  # 7 days
        
        # Initialize Redis for caching
        try:
            redis_url = os.getenv("REDIS_URL", "redis://complyo-redis:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)

        except Exception as e:
            logger.warning(f"⚠️ Redis not available, caching disabled: {e}")
        
        if not self.openrouter_api_key:
            logger.warning("⚠️ OPENROUTER_API_KEY not set - falling back to static templates")
    
    async def generate_fix(
        self, 
        issue_id: str,
        issue_category: str,
        user_id: int,
        plan_type: str = 'ai'
    ) -> Dict[str, Any]:
        """
        Generiert einen Fix für ein Issue
        
        Args:
            issue_id: ID des Issues
            issue_category: Kategorie (impressum, datenschutz, etc.)
            user_id: User ID
            plan_type: 'ai' oder 'expert'
        
        Returns:
            Dict mit Fix-Daten
        """
        try:
            # Check Plan-Limits
            await self._check_limits(user_id, plan_type)
            
            # Hole Website-Struktur und Firmendaten
            website_structure = await self._get_website_structure(user_id)
            company_data = await self._get_user_company_data(user_id)
            
            # Generiere Fix basierend auf Plan
            if plan_type == 'ai':
                # Versuche AI-personalisierte Fixes, fallback zu statischen Templates
                if self.openrouter_api_key:
                    try:
                        fix_data = await self._generate_ai_personalized_fix(
                            issue_category=issue_category,
                            website_structure=website_structure,
                            company_data=company_data,
                            issue_description=f"Problem mit {issue_category}"
                        )
                    except Exception as ai_error:
                        logger.warning(f"AI fix generation failed, using static template: {ai_error}")
                        fix_data = await self._generate_code_snippet(issue_category)
                else:
                    fix_data = await self._generate_code_snippet(issue_category)
            else:  # expert
                fix_data = await self._generate_full_document(issue_category, user_id)
            
            # Speichere Fix in Datenbank
            fix_db_id = await self._save_fix(
                user_id=user_id,
                issue_id=issue_id,
                issue_category=issue_category,
                fix_type=fix_data['type'],
                plan_type=plan_type,
                content=fix_data.get('code', fix_data.get('html', ''))
            )
            
            # Markiere: Erster Fix = Geld-zurück verfällt
            await self._mark_fix_used(user_id)
            
            fix_data['fix_id'] = fix_db_id
            fix_data['generated_at'] = datetime.now().isoformat()
            
            return fix_data
            
        except Exception as e:
            logger.error(f"Error generating fix: {e}")
            raise
    
    async def _check_limits(self, user_id: int, plan_type: str):
        """Prüft ob User noch Fixes generieren darf"""
        async with self.db_pool.acquire() as conn:
            limits = await conn.fetchrow(
                "SELECT * FROM user_limits WHERE user_id = $1",
                user_id
            )
            
            if not limits:
                # Erstelle Default-Limits wenn nicht vorhanden
                await conn.execute(
                    """
                    INSERT INTO user_limits (user_id, plan_type, websites_max, ai_fixes_count, ai_fixes_max)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    user_id,
                    plan_type,
                    3,  # 3 Analysen erlaubt
                    0,  # Noch keine Fixes verwendet
                    1 if plan_type == 'ai' else 999  # 1 Optimierung für AI Plan, unbegrenzt für Expert
                )
                return
            
            # Check AI-Fix-Limit (nur für AI Plan)
            if plan_type == 'ai':
                ai_fixes_used = limits.get('ai_fixes_count', 0)
                ai_fixes_max = limits.get('ai_fixes_max', 1)
                
                if ai_fixes_used >= ai_fixes_max:
                    raise Exception(
                        f"⚠️ Optimierungs-Limit erreicht!\n\n"
                        f"Sie haben bereits {ai_fixes_used} von {ai_fixes_max} Optimierung(en) verwendet.\n\n"
                        f"🚀 Upgraden Sie auf den Expert-Plan für unbegrenzte Optimierungen!"
                    )
    
    async def _generate_ai_personalized_fix(
        self,
        issue_category: str,
        website_structure: Dict[str, Any],
        company_data: Dict[str, Any],
        issue_description: str
    ) -> Dict[str, Any]:
        """
        Generiert personalisierte AI-Fixes basierend auf echter Website-Struktur
        
        Args:
            issue_category: Kategorie des Issues
            website_structure: Gecrawlte Website-Struktur
            company_data: Firmendaten des Users
            issue_description: Beschreibung des Problems
            
        Returns:
            Dict mit personalisierten Fix-Daten inkl. Schritte, Code, Tests
        """
        try:
            logger.info(f"🤖 Generating AI-personalized fix for category: {issue_category}")
            
            # Try Redis cache first
            if self.redis_client:
                cache_key = self._get_cache_key(issue_category, website_structure)
                try:
                    cached_fix = await self.redis_client.get(cache_key)
                    if cached_fix:
                        logger.info(f"✅ Cache hit for {issue_category}")
                        return json.loads(cached_fix)
                    else:
                        logger.info(f"ℹ️ Cache miss for {issue_category}")
                except Exception as cache_error:
                    logger.warning(f"Cache retrieval error: {cache_error}")
            
            # Hole passendes Prompt-Template
            prompt_template = get_prompt_for_category(issue_category)
            
            # Extrahiere relevante Daten aus Website-Struktur
            cms_type = website_structure.get('cms', {}).get('type', 'custom')
            technology_stack = website_structure.get('technology_stack', {})
            tracking_services = website_structure.get('cookies', {}).get('tracking_detected', {})
            accessibility_info = website_structure.get('accessibility', {})
            
            # Formatiere Prompt mit echten Daten
            formatted_prompt = prompt_template.format(
                website_structure=json.dumps(website_structure, indent=2, ensure_ascii=False),
                company_data=json.dumps(company_data, indent=2, ensure_ascii=False),
                issue_description=issue_description,
                cms_type=cms_type,
                technology_stack=json.dumps(technology_stack, ensure_ascii=False),
                tracking_services=json.dumps(tracking_services, ensure_ascii=False),
                detected_services=json.dumps(tracking_services, ensure_ascii=False),
                cookie_info=json.dumps(website_structure.get('cookies', {}), ensure_ascii=False),
                accessibility_info=json.dumps(accessibility_info, ensure_ascii=False),
                alt_text_coverage=accessibility_info.get('alt_text_coverage', 0),
                images_without_alt=accessibility_info.get('images_without_alt', 0),
                heading_structure=json.dumps(accessibility_info.get('heading_structure', {}), ensure_ascii=False),
                business_type=company_data.get('business_type', 'Online-Shop')
            )
            
            # Rufe OpenRouter API auf
            ai_response = await self._call_openrouter(formatted_prompt)
            
            # Parse AI Response (JSON)
            try:
                fix_data = json.loads(ai_response)
            except json.JSONDecodeError:
                # Falls AI kein valides JSON zurückgibt, extrahiere JSON aus Text
                json_match = None
                import re
                json_pattern = r'\{.*\}'
                matches = re.findall(json_pattern, ai_response, re.DOTALL)
                if matches:
                    fix_data = json.loads(matches[0])
                else:
                    raise ValueError("AI response is not valid JSON")
            
            # Ergänze Metadaten
            fix_data.update({
                'type': 'ai_personalized_fix',
                'format': 'interactive_guide',
                'ai_generated': True,
                'cms_optimized': cms_type,
                'personalized': True
            })
            
            # Cache the result
            if self.redis_client:
                try:
                    cache_key = self._get_cache_key(issue_category, website_structure)
                    await self.redis_client.setex(
                        cache_key,
                        self.cache_ttl,
                        json.dumps(fix_data)
                    )
                    logger.info(f"✅ Cached fix for {issue_category} (TTL: {self.cache_ttl}s)")
                except Exception as cache_error:
                    logger.warning(f"Cache save error: {cache_error}")
            
            logger.info(f"✅ AI-personalized fix generated successfully")
            return fix_data
            
        except Exception as e:
            logger.error(f"❌ AI fix generation failed: {e}", exc_info=True)
            raise
    
    async def _call_openrouter(self, prompt: str) -> str:
        """
        Ruft OpenRouter API auf und gibt die Antwort zurück
        """
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://complyo.tech",
            "X-Title": "Complyo Compliance Fixer"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Du bist ein deutscher Compliance-Experte, der kinderleichte Anleitungen erstellt. Antworte IMMER mit validem JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # Niedrig für konsistentere Outputs
            "max_tokens": 3000
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.openrouter_url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API error {response.status}: {error_text}")
                
                result = await response.json()
                return result['choices'][0]['message']['content']
    
    async def _get_website_structure(self, user_id: int) -> Dict[str, Any]:
        """
        Holt die gecrawlte Website-Struktur des Users aus der Datenbank
        """
        async with self.db_pool.acquire() as conn:
            # Hole primäre Website des Users
            website = await conn.fetchrow(
                """
                SELECT url FROM tracked_websites 
                WHERE user_id = $1 AND is_primary = TRUE AND is_active = TRUE
                LIMIT 1
                """,
                user_id
            )
            
            if website:
                # TODO: Website-Struktur sollte eigentlich gespeichert sein
                # Für jetzt: Crawle on-demand
                from website_crawler import WebsiteCrawler
                crawler = WebsiteCrawler()
                structure = await crawler.crawl_website(website['url'])
                return structure
            
            # Fallback: Leere Struktur
            return {
                'cms': {'type': 'unknown', 'detected': False},
                'technology_stack': {},
                'cookies': {},
                'accessibility': {},
                'structure': {}
            }
    
    async def _generate_code_snippet(self, category: str) -> Dict[str, Any]:
        """
        Generiert Code-Snippet für AI Plan
        
        ✅ MIT eRecht24-INTEGRATION:
        - Versucht zuerst eRecht24-Rechtstexte zu holen
        - Fallback auf statische Templates wenn eRecht24 nicht verfügbar
        """
        # ✅ SCHRITT 1: Versuche eRecht24-Rechtstexte zu holen
        erecht24_content = await self._get_erecht24_content(category)
        
        if erecht24_content:
            logger.info(f"✅ Using eRecht24 legal text for {category}")
            return erecht24_content
        
        # ✅ SCHRITT 2: Fallback auf statische Templates
        logger.info(f"⚠️ Falling back to static template for {category}")
        snippets = {
            'impressum': {
                'type': 'code_snippet',
                'format': 'html',
                'code': '''<!-- Impressum-Link im Footer -->
<footer>
  <nav>
    <a href="/impressum" rel="legal">Impressum</a>
    <a href="/datenschutz" rel="privacy-policy">Datenschutz</a>
    <a href="/agb">AGB</a>
  </nav>
</footer>

<!-- Impressum-Seite: /impressum -->
<h1>Impressum</h1>

<h2>Angaben gemäß § 5 TMG</h2>
<p>
  [Ihr Firmenname]<br>
  [Straße und Hausnummer]<br>
  [PLZ und Ort]
</p>

<h2>Kontakt</h2>
<p>
  Telefon: [Ihre Telefonnummer]<br>
  E-Mail: [Ihre E-Mail-Adresse]
</p>

<h2>Umsatzsteuer-ID</h2>
<p>
  Umsatzsteuer-Identifikationsnummer gemäß § 27 a Umsatzsteuergesetz:<br>
  [Ihre USt-IdNr.]
</p>''',
                'steps': [
                    '1. Erstellen Sie eine neue Seite unter der URL /impressum',
                    '2. Fügen Sie den HTML-Code in die Seite ein',
                    '3. Ersetzen Sie alle Platzhalter [in eckigen Klammern] mit Ihren Daten',
                    '4. Verlinken Sie das Impressum im Footer jeder Seite',
                    '5. Stellen Sie sicher, dass der Link maximal 2 Klicks von jeder Seite entfernt ist'
                ],
                'legal_note': 'Pflichtangaben nach §5 TMG. Bei Fehlen drohen Abmahnungen bis 5.000€.'
            },
            'datenschutz': {
                'type': 'code_snippet',
                'format': 'html',
                'code': '''<!-- Datenschutz-Link im Footer -->
<footer>
  <a href="/datenschutz" rel="privacy-policy">Datenschutzerklärung</a>
</footer>

<!-- Datenschutz-Seite: /datenschutz -->
<h1>Datenschutzerklärung</h1>

<h2>1. Datenschutz auf einen Blick</h2>
<h3>Allgemeine Hinweise</h3>
<p>
  Die folgenden Hinweise geben einen einfachen Überblick darüber, 
  was mit Ihren personenbezogenen Daten passiert, wenn Sie diese Website besuchen.
</p>

<h2>2. Verantwortlicher</h2>
<p>
  Verantwortlich für die Datenverarbeitung auf dieser Website ist:<br>
  [Ihr Firmenname]<br>
  [Ihre Adresse]<br>
  E-Mail: [Ihre E-Mail]
</p>

<h2>3. Erfassung von Daten</h2>
<h3>Server-Log-Dateien</h3>
<p>
  Der Provider der Seiten erhebt und speichert automatisch Informationen 
  in so genannten Server-Log-Dateien:
</p>
<ul>
  <li>Browsertyp und Browserversion</li>
  <li>Verwendetes Betriebssystem</li>
  <li>Referrer URL</li>
  <li>Hostname des zugreifenden Rechners</li>
  <li>Uhrzeit der Serveranfrage</li>
  <li>IP-Adresse</li>
</ul>

<h2>4. Ihre Rechte</h2>
<p>
  Sie haben jederzeit das Recht auf Auskunft, Berichtigung, Löschung oder 
  Einschränkung der Verarbeitung Ihrer gespeicherten Daten.
</p>''',
                'steps': [
                    '1. Erstellen Sie eine Seite unter /datenschutz',
                    '2. Fügen Sie den Basis-HTML-Code ein',
                    '3. Ergänzen Sie ALLE von Ihnen genutzten Dienste (Analytics, Cookies, etc.)',
                    '4. Verlinken Sie die Datenschutzerklärung im Footer',
                    '5. WICHTIG: Aktualisieren Sie bei neuen Diensten sofort die Datenschutzerklärung'
                ],
                'legal_note': 'Pflichtangaben nach DSGVO Art. 13-14. Bußgelder bis 20 Mio. € oder 4% des Umsatzes möglich.'
            },
            'cookies': {
                'type': 'code_snippet',
                'format': 'html',
                'code': '''<!-- Cookie-Consent-Banner mit Vanilla JS -->
<div id="cookie-banner" style="
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #2c3e50;
  color: white;
  padding: 20px;
  z-index: 9999;
  display: none;
">
  <div style="max-width: 1200px; margin: 0 auto;">
    <p>
      Diese Website verwendet Cookies. Mit Ihrer Zustimmung helfen Sie uns, 
      die Website zu verbessern.
      <a href="/datenschutz" style="color: #3498db;">Mehr erfahren</a>
    </p>
    <button onclick="acceptCookies()" style="
      background: #27ae60;
      color: white;
      border: none;
      padding: 10px 20px;
      margin-right: 10px;
      cursor: pointer;
    ">
      Akzeptieren
    </button>
    <button onclick="rejectCookies()" style="
      background: #95a5a6;
      color: white;
      border: none;
      padding: 10px 20px;
      cursor: pointer;
    ">
      Ablehnen
    </button>
  </div>
</div>

<script>
// Cookie-Management
function setCookie(name, value, days) {
  const d = new Date();
  d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
  document.cookie = name + "=" + value + ";expires=" + d.toUTCString() + ";path=/";
}

function getCookie(name) {
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [key, value] = cookie.trim().split('=');
    if (key === name) return value;
  }
  return null;
}

function acceptCookies() {
  setCookie('cookie_consent', 'accepted', 365);
  document.getElementById('cookie-banner').style.display = 'none';
  
  // HIER: Tracking-Dienste aktivieren
  // Beispiel: Google Analytics laden
  // loadGoogleAnalytics();
}

function rejectCookies() {
  setCookie('cookie_consent', 'rejected', 365);
  document.getElementById('cookie-banner').style.display = 'none';
}

// Banner anzeigen wenn noch keine Auswahl
window.addEventListener('load', function() {
  const consent = getCookie('cookie_consent');
  if (!consent) {
    document.getElementById('cookie-banner').style.display = 'block';
  } else if (consent === 'accepted') {
    // HIER: Tracking aktivieren
    // loadGoogleAnalytics();
  }
});
</script>''',
                'steps': [
                    '1. Fügen Sie den Cookie-Banner-Code VOR dem schließenden </body>-Tag ein',
                    '2. Passen Sie das Design an Ihre Website an (Farben, Schriften)',
                    '3. WICHTIG: Alle Tracking-Scripte (Analytics, etc.) NUR bei Zustimmung laden',
                    '4. Dokumentieren Sie alle Cookies in Ihrer Datenschutzerklärung',
                    '5. Testen Sie, dass KEINE Tracking-Cookies vor Zustimmung gesetzt werden'
                ],
                'legal_note': 'Pflicht nach TTDSG §25. Tracking ohne Einwilligung: Bußgeld bis 50.000€.'
            },
            'barrierefreiheit': {
                'type': 'code_snippet',
                'format': 'html',
                'code': '''<!-- Barrierefreiheit: Basis-Implementierung -->

<!-- 1. HTML: Semantisches Markup -->
<nav aria-label="Hauptnavigation">
  <ul>
    <li><a href="/">Startseite</a></li>
    <li><a href="/produkte">Produkte</a></li>
  </ul>
</nav>

<main>
  <h1>Hauptüberschrift</h1>
  <p>Hauptinhalt</p>
</main>

<!-- 2. Bilder: Alt-Texte -->
<img src="produkt.jpg" alt="Produktname - Detaillierte Beschreibung">

<!-- 3. Formulare: Labels -->
<form>
  <label for="email">E-Mail-Adresse:</label>
  <input type="email" id="email" name="email" required>
  
  <button type="submit" aria-label="Formular absenden">
    Absenden
  </button>
</form>

<!-- 4. CSS: Kontraste (mind. 4.5:1 für Text) -->
<style>
  /* Gute Kontraste */
  body {
    color: #333333;  /* Dunkelgrau */
    background: #FFFFFF;  /* Weiß */
  }
  
  /* Skip-Link für Screenreader */
  .skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    background: #000;
    color: #fff;
    padding: 8px;
    z-index: 100;
  }
  
  .skip-link:focus {
    top: 0;
  }
</style>

<!-- 5. Skip-Link -->
<a href="#main-content" class="skip-link">
  Zum Hauptinhalt springen
</a>

<main id="main-content">
  <!-- Hauptinhalt -->
</main>''',
                'steps': [
                    '1. Verwenden Sie semantisches HTML (<header>, <nav>, <main>, <footer>)',
                    '2. Fügen Sie ALLEN Bildern aussagekräftige Alt-Texte hinzu',
                    '3. Stellen Sie Farbkontraste von mindestens 4.5:1 sicher (Tool: contrastchecker.com)',
                    '4. Aktivieren Sie Tastaturbedienung (Tab-Reihenfolge logisch)',
                    '5. Testen Sie mit Screenreader (NVDA für Windows, VoiceOver für Mac)',
                    '6. Fügen Sie ARIA-Labels für interaktive Elemente hinzu'
                ],
                'legal_note': 'Pflicht nach BFSG seit 28.06.2025. Bußgelder bis 100.000€ möglich.'
            }
        }
        
        return snippets.get(
            category,
            {
                'type': 'code_snippet',
                'format': 'text',
                'code': f'<!-- Fix für Kategorie "{category}" -->\nBitte kontaktieren Sie unseren Support für eine individuelle Lösung.',
                'steps': [
                    '1. Prüfen Sie die rechtliche Grundlage',
                    '2. Implementieren Sie die erforderlichen Änderungen',
                    '3. Dokumentieren Sie die Umsetzung'
                ],
                'legal_note': 'Bitte konsultieren Sie einen Rechtsanwalt für spezifische Anforderungen.'
            }
        )
    
    async def _generate_full_document(self, category: str, user_id: int) -> Dict[str, Any]:
        """Generiert vollständiges Dokument für Expert Plan"""
        try:
            # Importiere AI Document Generator
            from ai_document_generator import AIDocumentGenerator
            
            ai_gen = AIDocumentGenerator(self.db_pool)
            
            # Hole User-Daten für Dokument-Generierung
            company_data = await self._get_user_company_data(user_id)
            
            if category == 'impressum':
                return await ai_gen.generate_impressum_document(user_id, company_data)
            
            elif category == 'datenschutz':
                # Ermittle genutzte Services aus Website-Analyse
                services = await self._detect_used_services(user_id)
                return await ai_gen.generate_datenschutz_document(
                    user_id, 
                    company_data, 
                    services
                )
            
            else:
                # Für andere Kategorien: Basis-Template
                return {
                    'type': 'full_document',
                    'format': 'html',
                    'html': f'<h1>{category.title()}-Dokument</h1><p>Vollständige Generierung für diese Kategorie in Entwicklung.</p>',
                    'audit_trail': {
                        'generated_at': datetime.now().isoformat(),
                        'version': '1.0',
                        'user_id': user_id,
                        'note': 'Template-based generation'
                    }
                }
        
        except Exception as e:
            logger.error(f"Error in full document generation: {e}")
            # Fallback
            return {
                'type': 'full_document',
                'format': 'html',
                'html': f'<h1>{category.title()}-Dokument</h1><p>Dokument-Generierung fehlgeschlagen. Bitte kontaktieren Sie den Support.</p>',
                'error': str(e)
            }
    
    async def _get_user_company_data(self, user_id: int) -> Dict[str, str]:
        """Holt Firmendaten des Users aus Datenbank oder gibt Defaults zurück"""
        try:
            async with self.db_pool.acquire() as conn:
                user_data = await conn.fetchrow(
                    """
                    SELECT 
                        company_name,
                        legal_form,
                        street,
                        zip_city,
                        phone,
                        email,
                        vat_id,
                        represented_by
                    FROM user_company_data
                    WHERE user_id = $1
                    """,
                    user_id
                )
                
                if user_data:
                    return dict(user_data)
        except Exception as e:
            logger.warning(f"Could not fetch user company data (table may not exist): {e}")
            
        # Defaults wenn keine Daten vorhanden oder Tabelle existiert nicht
        return {
            'company_name': '[Ihr Firmenname]',
            'legal_form': 'Einzelunternehmen',
            'street': '[Straße Hausnummer]',
            'zip_city': '[PLZ Ort]',
            'phone': '[Telefonnummer]',
            'email': '[E-Mail]',
            'vat_id': '[USt-IdNr]',
            'represented_by': '[Inhaber/Geschäftsführer]'
        }
    
    async def _detect_used_services(self, user_id: int) -> list:
        """Ermittelt genutzte Services aus letzter Website-Analyse"""
        # TODO: Implementierung basierend auf Scan-Ergebnissen
        # Für jetzt: Standard-Services
        return [
            'Server-Log-Dateien',
            'Kontaktformular',
            'E-Mail-Kommunikation'
        ]
    
    async def _save_fix(
        self,
        user_id: int,
        issue_id: str,
        issue_category: str,
        fix_type: str,
        plan_type: str,
        content: str
    ) -> int:
        """Speichert generierten Fix in DB"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        async with self.db_pool.acquire() as conn:
            fix_id = await conn.fetchval(
                """
                INSERT INTO generated_fixes 
                (user_id, issue_id, issue_category, fix_type, plan_type, content_hash)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
                """,
                user_id,
                issue_id,
                issue_category,
                fix_type,
                plan_type,
                content_hash
            )
            
            return fix_id
    
    async def _mark_fix_used(self, user_id: int):
        """Markiert ersten Fix-Usage = Geld-zurück verfällt & incrementiert ai_fixes_count"""
        async with self.db_pool.acquire() as conn:
            # Check ob bereits ein Fix genutzt wurde
            existing = await conn.fetchval(
                "SELECT fix_started FROM user_limits WHERE user_id = $1",
                user_id
            )
            
            # Increment ai_fixes_count (IMMER)
            await conn.execute(
                """
                UPDATE user_limits 
                SET ai_fixes_count = COALESCE(ai_fixes_count, 0) + 1
                WHERE user_id = $1
                """,
                user_id
            )
            
            if not existing:
                # Erster Fix = Geld-zurück verfällt
                await conn.execute(
                    """
                    UPDATE user_limits 
                    SET fix_started = TRUE, money_back_eligible = FALSE
                    WHERE user_id = $1
                    """,
                    user_id
                )
                
                await conn.execute(
                    """
                    UPDATE subscriptions
                    SET fix_first_used_at = CURRENT_TIMESTAMP, refund_eligible = FALSE
                    WHERE user_id = $1 AND fix_first_used_at IS NULL
                    """,
                    user_id
                )
                
                logger.info(f"✅ User {user_id}: Erster Fix verwendet - Geld-zurück verfallen!")
    
    async def export_fix(self, fix_id: int, user_id: int, export_format: str = 'html') -> Dict[str, Any]:
        """
        Exportiert einen Fix und zählt Export-Limit hoch
        """
        async with self.db_pool.acquire() as conn:
            # Check Export-Limit
            can_export = await conn.fetchval(
                "SELECT check_export_limit($1)",
                user_id
            )
            
            if not can_export:
                raise Exception("Export-Limit erreicht (10/Monat für AI Plan)")
            
            # Markiere als exportiert
            await conn.execute(
                """
                UPDATE generated_fixes
                SET exported = TRUE, exported_at = CURRENT_TIMESTAMP, export_format = $1
                WHERE id = $2 AND user_id = $3
                """,
                export_format,
                fix_id,
                user_id
            )
            
            # Export-History tracken
            await conn.execute(
                """
                INSERT INTO export_history (user_id, fix_id, export_format)
                VALUES ($1, $2, $3)
                """,
                user_id,
                fix_id,
                export_format
            )
            
            # Increment export count
            await conn.execute(
                """
                UPDATE user_limits
                SET exports_this_month = exports_this_month + 1
                WHERE user_id = $1
                """,
                user_id
            )
            
            return {
                'success': True,
                'exported_at': datetime.now().isoformat(),
                'format': export_format
            }
    
    def _get_cache_key(self, issue_category: str, website_structure: Dict[str, Any]) -> str:
        """
        Generiert einen Cache-Key basierend auf Kategorie und Website-Struktur
        
        Args:
            issue_category: Issue-Kategorie
            website_structure: Website-Struktur
            
        Returns:
            Cache-Key als String
        """
        # Relevante Teile der Struktur für Cache-Key
        cache_data = {
            'category': issue_category,
            'cms': website_structure.get('cms', {}).get('type', 'unknown'),
            'has_legal_pages': website_structure.get('legal_pages', {}),
            'tracking': website_structure.get('cookies', {}).get('tracking_detected', {})
        }
        
        # Hash für kompakten Key
        cache_str = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_str.encode()).hexdigest()
        
        return f"fix_cache:{issue_category}:{cache_hash}"

    async def _get_erecht24_content(self, category: str) -> Optional[Dict[str, Any]]:
        """
        Holt eRecht24-Rechtstexte wenn verfügbar
        
        ✅ KI-UNTERSTÜTZUNG MIT eRecht24:
        - Generiert rechtssichere Texte direkt von eRecht24
        - Nur für bestimmte Kategorien verfügbar (impressum, datenschutz, agb)
        - Fallback auf statische Templates wenn nicht verfügbar
        
        Args:
            category: Issue-Kategorie (impressum, datenschutz, agb, cookies, etc.)
            
        Returns:
            Dict mit Code-Snippet oder None wenn nicht verfügbar
        """
        try:
            from erecht24_service import erecht24_service
            
            # Mapping: Unsere Kategorien -> eRecht24-Text-Typen
            erecht24_mapping = {
                'impressum': 'impressum',
                'datenschutz': 'datenschutz',
                'agb': 'agb',
                # Für andere Kategorien nutzen wir unsere Fallback-Templates
            }
            
            text_type = erecht24_mapping.get(category)
            if not text_type:
                # Kategorie nicht von eRecht24 unterstützt
                return None
            
            # TODO: Project-ID sollte aus User-Daten kommen
            # Für jetzt: Nutze Mock-Funktion
            legal_text = await erecht24_service.get_legal_text(
                project_id='demo_project',
                text_type=text_type,
                language='de'
            )
            
            if not legal_text:
                return None
            
            # Formatiere als Code-Snippet
            return {
                'type': 'code_snippet',
                'format': 'html',
                'code': legal_text,
                'steps': [
                    f'1. Erstellen Sie eine Seite unter /{text_type}',
                    '2. Fügen Sie den generierten eRecht24-Text ein',
                    '3. Verlinken Sie die Seite im Footer',
                    '4. WICHTIG: Text ist rechtlich geprüft von eRecht24'
                ],
                'legal_note': f'✅ Rechtssicherer Text von eRecht24 - Abmahnschutz inklusive!',
                'source': 'erecht24',
                'erecht24_certified': True
            }
            
        except ImportError:

            return None
        except Exception as e:
            logger.warning(f"Fehler beim Abrufen von eRecht24-Inhalten für {category}: {e}")
            return None
