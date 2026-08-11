"""
AI-powered Alt-Text Generator
Nutzt Claude Vision (über OpenRouter) für intelligente Alt-Text-Vorschläge.

Konsistent mit dem übrigen Complyo-AI-Stack (ai_review_engine.py): OpenRouter
als Gateway, OpenAI-kompatibles Chat-Completions-Format, Default-Modell
Claude Haiku (Vision). Per ENV überschreibbar via COMPLYO_ALT_TEXT_MODEL.
"""

import os
import base64
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

# OpenRouter-Gateway (wie ai_review_engine.py)
OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'
DEFAULT_ALT_TEXT_MODEL = 'anthropic/claude-haiku-4.5'  # Claude Vision, kosteneffizient für Massen-Alt-Texte

# Prometheus-Zähler für OpenRouter-Aufrufe (fail-open ohne metrics-Modul)
try:
    from metrics import openrouter_requests_total as _openrouter_counter
except Exception:
    _openrouter_counter = None


class AIAltTextGenerator:
    """Generiert Alt-Texte mittels Claude Vision (über OpenRouter)"""

    def __init__(self, api_key: Optional[str] = None, db_pool: Optional[Any] = None):
        """
        Initialisiert Generator

        Args:
            api_key: OpenRouter API Key (falls None, wird aus ENV gelesen)
            db_pool: Optionaler asyncpg-Pool für die Lernschleife (falls None,
                     wird zur Laufzeit der Pool aus main_production verwendet)
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.api_url = OPENROUTER_URL
        self.model = os.getenv('COMPLYO_ALT_TEXT_MODEL', DEFAULT_ALT_TEXT_MODEL)
        self.max_tokens = 200
        self.db_pool = db_pool
        self._headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://complyo.de',
            'X-Title': 'Complyo Alt-Text Generator',
        }

    # ------------------------------------------------------------------
    # Lernschleife: Freigaben/Ablehnungen aus accessibility_alt_text_fixes
    # ------------------------------------------------------------------

    def _get_db_pool(self):
        """Pool aus Konstruktor, sonst der laufende Pool aus main_production."""
        if self.db_pool is not None:
            return self.db_pool
        try:
            from main_production import db_pool as main_db_pool
            return main_db_pool
        except Exception:
            return None

    @staticmethod
    def _host_from_url(url: Optional[str]) -> Optional[str]:
        """Extrahiert den Host (ohne www.) aus einer URL, sonst None."""
        if not url:
            return None
        try:
            host = (urlparse(url).netloc or '').split(':')[0].lower()
            if host.startswith('www.'):
                host = host[4:]
            return host or None
        except Exception:
            return None

    async def _load_learning_examples(
        self,
        site_id: Optional[str] = None,
        site_host: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Lädt die letzten freigegebenen Alt-Texte (bis 5, Few-Shot-Beispiele)
        und die letzten Ablehnungsgründe (bis 3, Negativ-Beispiele) einer Site
        aus accessibility_alt_text_fixes.

        Die Tabelle speichert approved/rejected + rejected_reason seit Wochen —
        gelesen wurde sie beim Generieren nie. Diese Methode schließt die
        Schleife: Reviewer-Feedback fließt in künftige Vorschläge ein.

        Fail-open: Bei DB-Fehlern (kein Pool, Tabelle fehlt, ...) kommen leere
        Listen zurück und der Prompt wird ohne Beispiele gebaut.
        """
        examples: Dict[str, List[str]] = {"approved": [], "rejected_reasons": []}
        if not site_id and not site_host:
            return examples
        pool = self._get_db_pool()
        if pool is None:
            return examples
        try:
            if site_id:
                where = "site_id = $1"
                params = [site_id]
            else:
                # Zuordnung über den Host: page_url/image_src enthalten die Domain
                where = ("(page_url ILIKE $1 OR page_url ILIKE $2 "
                         "OR image_src ILIKE $1 OR image_src ILIKE $2)")
                params = [f"%//{site_host}%", f"%//www.{site_host}%"]

            async with pool.acquire() as conn:
                approved_rows = await conn.fetch(
                    f"""
                    SELECT suggested_alt
                    FROM accessibility_alt_text_fixes
                    WHERE {where}
                      AND status IN ('approved', 'deployed')
                      AND suggested_alt IS NOT NULL AND suggested_alt != ''
                    ORDER BY COALESCE(approved_at, updated_at, created_at) DESC
                    LIMIT 5
                    """,
                    *params
                )
                rejected_rows = await conn.fetch(
                    f"""
                    SELECT rejected_reason
                    FROM accessibility_alt_text_fixes
                    WHERE {where}
                      AND status = 'rejected'
                      AND rejected_reason IS NOT NULL AND rejected_reason != ''
                    ORDER BY COALESCE(updated_at, created_at) DESC
                    LIMIT 3
                    """,
                    *params
                )
            examples["approved"] = [r['suggested_alt'] for r in approved_rows]
            examples["rejected_reasons"] = [r['rejected_reason'] for r in rejected_rows]
            if examples["approved"] or examples["rejected_reasons"]:
                logger.info(
                    f"📚 Alt-Text-Lernbeispiele geladen ({site_id or site_host}): "
                    f"{len(examples['approved'])} freigegeben, "
                    f"{len(examples['rejected_reasons'])} Ablehnungsgründe"
                )
        except Exception as e:
            logger.warning(
                f"Alt-Text-Lernbeispiele nicht ladbar ({site_id or site_host}): {e} "
                f"— generiere ohne Beispiele"
            )
        return examples
        
    async def generate_alt_text(
        self,
        image_url: str,
        context: Optional[str] = None,
        language: str = 'de',
        site_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generiert Alt-Text für Bild von URL

        Args:
            image_url: URL des Bildes
            context: Optionaler Kontext (umgebender Text)
            language: Sprache für Alt-Text (de/en)
            site_id: Optionale Site-ID für die Lernschleife (Few-Shots aus
                     Freigaben; falls None, wird die Site über den Host der
                     Bild-URL zugeordnet)

        Returns:
            Dict mit 'alt_text', 'confidence' und 'reasoning'
        """
        if not self.api_key:
            logger.warning("No OpenRouter API key configured, falling back to basic generation")
            return self._fallback_response()

        # Lernschleife: freigegebene Alt-Texte + Ablehnungsgründe der Site
        # als Beispiele in den Prompt aufnehmen (fail-open)
        learning_examples = await self._load_learning_examples(
            site_id=site_id,
            site_host=None if site_id else self._host_from_url(image_url)
        )

        # Bild selbst herunterladen und als base64 senden. Remote-URLs sind
        # über OpenRouter unzuverlässig (je nach Upstream-Provider werden URL-
        # Bildquellen abgelehnt oder können nicht geladen werden), base64 ist
        # provider-übergreifend robust.
        data_url = await self._download_as_data_url(image_url)
        if not data_url:
            logger.warning(f"Bild konnte nicht geladen werden: {image_url}")
            return self._fallback_response()

        return await self.generate_alt_text_from_base64(
            data_url, context, language, learning_examples=learning_examples
        )

    async def _download_as_data_url(self, image_url: str) -> Optional[str]:
        """Lädt ein Bild herunter und gibt eine base64-Data-URL zurück (oder None)."""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; ComplyoScanner/1.0; +https://complyo.de)'}
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(
                    image_url, timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Bild-Download {response.status} für {image_url}")
                        return None
                    content_type = (response.headers.get('content-type') or '').split(';')[0].strip()
                    raw = await response.read()
            if not raw:
                return None
            # Media-Type bestimmen (Content-Type, sonst Magic Bytes, Fallback PNG)
            media_type = content_type if content_type.startswith('image/') else self._sniff_media_type(raw)
            return f"data:{media_type};base64,{base64.b64encode(raw).decode('utf-8')}"
        except Exception as e:
            logger.warning(f"Bild-Download fehlgeschlagen für {image_url}: {e}")
            return None

    @staticmethod
    def _sniff_media_type(raw: bytes) -> str:
        """Erkennt das Bildformat anhand der Magic Bytes."""
        if raw[:8] == b'\x89PNG\r\n\x1a\n':
            return 'image/png'
        if raw[:3] == b'\xff\xd8\xff':
            return 'image/jpeg'
        if raw[:6] in (b'GIF87a', b'GIF89a'):
            return 'image/gif'
        if raw[:4] == b'RIFF' and raw[8:12] == b'WEBP':
            return 'image/webp'
        return 'image/png'

    async def generate_alt_text_from_base64(
        self,
        image_base64: str,
        context: Optional[str] = None,
        language: str = 'de',
        site_id: Optional[str] = None,
        learning_examples: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Generiert Alt-Text für Bild von Base64-String

        Args:
            image_base64: Base64-kodiertes Bild
            context: Optionaler Kontext
            language: Sprache für Alt-Text
            site_id: Optionale Site-ID für die Lernschleife
            learning_examples: Bereits geladene Lernbeispiele (intern, spart
                               doppelte DB-Zugriffe aus generate_alt_text)

        Returns:
            Dict mit Alt-Text-Informationen
        """
        if not self.api_key:
            return self._fallback_response()

        try:
            # Prüfe ob base64 data-url prefix hat
            if not image_base64.startswith('data:image'):
                # Füge prefix hinzu (PNG angenommen)
                image_base64 = f'data:image/png;base64,{image_base64}'

            # Lernschleife auch für den Base64-Weg (falls site_id bekannt)
            if learning_examples is None and site_id:
                learning_examples = await self._load_learning_examples(site_id=site_id)

            prompt = self._build_prompt(context, language, learning_examples)

            async with aiohttp.ClientSession() as session:
                payload = {
                    'model': self.model,
                    'messages': [
                        {
                            'role': 'user',
                            'content': [
                                {
                                    'type': 'text',
                                    'text': prompt
                                },
                                {
                                    'type': 'image_url',
                                    'image_url': {
                                        'url': image_base64
                                    }
                                }
                            ]
                        }
                    ],
                    'max_tokens': self.max_tokens,
                    'temperature': 0.3
                }

                async with session.post(
                    self.api_url,
                    headers=self._headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenRouter API error {response.status}: {error_text}")
                        if _openrouter_counter:
                            _openrouter_counter.labels(status="error").inc()
                        return self._fallback_response()

                    if _openrouter_counter:
                        _openrouter_counter.labels(status="success").inc()
                    data = await response.json()
                    alt_text = data['choices'][0]['message']['content'].strip()
                    alt_text = self._clean_alt_text(alt_text)

                    return {
                        'alt_text': alt_text,
                        'confidence': 0.9,
                        'reasoning': 'Generated by Claude Vision',
                        'source': 'claude_vision',
                        'model': self.model
                    }

        except Exception as e:
            logger.error(f"AI Alt-Text generation (base64) failed: {e}")
            if _openrouter_counter:
                _openrouter_counter.labels(status="error").inc()
            return self._fallback_response()
    
    async def generate_batch_alt_texts(
        self,
        images: list[Dict[str, Any]],
        max_concurrent: int = 5
    ) -> list[Dict[str, Any]]:
        """
        Generiert Alt-Texte für mehrere Bilder parallel
        
        Args:
            images: Liste von Dicts mit 'url' oder 'base64' und optional 'context'
            max_concurrent: Max parallele API-Calls
            
        Returns:
            Liste mit generierten Alt-Texten
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_image(img_data):
            async with semaphore:
                if 'url' in img_data:
                    return await self.generate_alt_text(
                        img_data['url'],
                        img_data.get('context'),
                        img_data.get('language', 'de'),
                        site_id=img_data.get('site_id')
                    )
                elif 'base64' in img_data:
                    return await self.generate_alt_text_from_base64(
                        img_data['base64'],
                        img_data.get('context'),
                        img_data.get('language', 'de'),
                        site_id=img_data.get('site_id')
                    )
                else:
                    return self._fallback_response()
        
        tasks = [process_image(img) for img in images]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtere Exceptions
        cleaned_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch generation error: {result}")
                cleaned_results.append(self._fallback_response())
            else:
                cleaned_results.append(result)
        
        return cleaned_results
    
    def _build_prompt(
        self,
        context: Optional[str],
        language: str,
        learning_examples: Optional[Dict[str, List[str]]] = None
    ) -> str:
        """Baut Prompt für AI basierend auf Kontext, Sprache und Lernbeispielen"""

        if language == 'de':
            base_prompt = (
                "Beschreibe dieses Bild in 1-2 kurzen, präzisen Sätzen als Alt-Text "
                "für eine barrierefreie Website (WCAG 2.1). "
                "Der Alt-Text soll informativ und beschreibend sein, aber nicht mit "
                "'Bild von' oder 'Foto von' beginnen. "
                "Antworte AUSSCHLIESSLICH mit dem reinen Alt-Text – ohne Markdown, "
                "ohne Überschrift, ohne Anführungszeichen, ohne Einleitung."
            )
            if context:
                base_prompt += f"\n\nKontext der Webseite: {context[:200]}"
                base_prompt += "\nNutze diesen Kontext, um den Alt-Text relevanter zu machen."
        else:
            base_prompt = (
                "Describe this image in 1-2 short, precise sentences as alt-text "
                "for an accessible website (WCAG 2.1). "
                "The alt-text should be informative and descriptive, but not start with "
                "'Image of' or 'Photo of'. "
                "Reply with ONLY the plain alt-text – no markdown, no heading, "
                "no quotes, no preamble."
            )
            if context:
                base_prompt += f"\n\nPage context: {context[:200]}"
                base_prompt += "\nUse this context to make the alt-text more relevant."

        # Lernschleife: Reviewer-Feedback der Site als Few-Shot-/Negativ-Beispiele
        if learning_examples:
            approved = learning_examples.get('approved') or []
            rejected = learning_examples.get('rejected_reasons') or []
            if approved:
                beispiele = "\n".join(f'- "{str(t)[:150]}"' for t in approved[:5])
                if language == 'de':
                    base_prompt += (
                        "\n\nBereits FREIGEGEBENE Alt-Texte dieser Website "
                        "(orientiere dich an Ton, Stil und Detailgrad):\n" + beispiele
                    )
                else:
                    base_prompt += (
                        "\n\nPreviously APPROVED alt-texts for this website "
                        "(match their tone, style and level of detail):\n" + beispiele
                    )
            if rejected:
                gruende = "\n".join(f"- {str(g)[:200]}" for g in rejected[:3])
                if language == 'de':
                    base_prompt += (
                        "\n\nFrühere Vorschläge für diese Website wurden aus folgenden "
                        "Gründen ABGELEHNT — vermeide diese Fehler:\n" + gruende
                    )
                else:
                    base_prompt += (
                        "\n\nEarlier suggestions for this website were REJECTED for "
                        "these reasons — avoid these mistakes:\n" + gruende
                    )

        return base_prompt
    
    def _clean_alt_text(self, alt_text: str) -> str:
        """
        Bereinigt und validiert generierten Alt-Text
        
        Args:
            alt_text: Roher Alt-Text von AI
            
        Returns:
            Bereinigter Alt-Text
        """
        # Entferne führende/trailing whitespace
        alt_text = alt_text.strip()

        # Markdown-Überschriften/Aufzählungen zeilenweise entfernen, erste
        # inhaltliche Zeile als Alt-Text verwenden (Claude liefert gelegentlich
        # eine '# Überschrift' + Beschreibung).
        lines = [ln.strip().lstrip('#>*-').strip() for ln in alt_text.splitlines()]
        lines = [ln for ln in lines if ln]
        if lines:
            # Eine '...Überschrift'-Zeile überspringen, wenn eine echte Beschreibung folgt
            if len(lines) > 1 and len(lines[0]) < 40 and 'alt-text' in lines[0].lower():
                alt_text = lines[1]
            else:
                alt_text = lines[0]

        # Entferne Markdown-Fettmarkierungen
        alt_text = alt_text.replace('**', '').replace('__', '').strip()

        # Entferne Anführungszeichen am Anfang/Ende
        alt_text = alt_text.strip('"\'')

        # Entferne "Alt-Text:" prefix falls vorhanden
        prefixes_to_remove = [
            'Alt-Text:',
            'Alt text:',
            'Alternative Text:',
            'Beschreibung:',
            'Description:'
        ]
        for prefix in prefixes_to_remove:
            if alt_text.startswith(prefix):
                alt_text = alt_text[len(prefix):].strip()
        
        # Limitiere Länge (WCAG Empfehlung: max 150 Zeichen)
        if len(alt_text) > 150:
            # Schneide bei letztem Satzende innerhalb der Grenze
            truncated = alt_text[:147]
            last_period = truncated.rfind('.')
            if last_period > 50:  # Mindestens 50 Zeichen behalten
                alt_text = truncated[:last_period + 1]
            else:
                alt_text = truncated + '...'
        
        # Validierung: Mindestlänge
        if len(alt_text) < 3:
            return "Bild"
        
        return alt_text
    
    def _fallback_response(self) -> Dict[str, Any]:
        """Fallback wenn AI nicht verfügbar"""
        return {
            'alt_text': 'Bild',
            'confidence': 0.2,
            'reasoning': 'AI not available, using fallback',
            'source': 'fallback'
        }


# Convenience-Funktionen
async def generate_alt_text_for_url(
    image_url: str,
    context: Optional[str] = None,
    api_key: Optional[str] = None
) -> str:
    """
    Einfache Funktion zum Generieren von Alt-Text
    
    Returns:
        Nur der Alt-Text als String
    """
    generator = AIAltTextGenerator(api_key)
    result = await generator.generate_alt_text(image_url, context)
    return result['alt_text']


async def generate_alt_text_for_base64(
    image_base64: str,
    context: Optional[str] = None,
    api_key: Optional[str] = None
) -> str:
    """
    Einfache Funktion zum Generieren von Alt-Text aus Base64
    
    Returns:
        Nur der Alt-Text als String
    """
    generator = AIAltTextGenerator(api_key)
    result = await generator.generate_alt_text_from_base64(image_base64, context)
    return result['alt_text']

