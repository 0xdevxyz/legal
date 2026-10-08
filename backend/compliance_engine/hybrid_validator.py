"""
Hybrid Validator
Kombiniert Pattern-Matching (schnell) mit KI-Validierung (präzise)

Strategie:
- 90% der Fälle: Pattern-Matching (< 100ms)
- 10% der Fälle: KI-Analyse bei Unsicherheit (~2s)
"""

import aiohttp
import os
import re
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from bs4 import BeautifulSoup

from .checks.deep_content_analyzer import DeepContentAnalyzer, ContentValidation
from . import ai_budget

logger = logging.getLogger(__name__)

# KI läuft über OpenRouter (wie ai_review_engine / legal_text_generator).
# Vorher: direkter anthropic.Anthropic-Client mit ANTHROPIC_API_KEY — der Key
# war im Deployment nie gesetzt, "KI für Grenzfälle" lief daher nie.
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
VALIDATOR_MODEL = os.getenv("COMPLYO_VALIDATOR_MODEL", "anthropic/claude-haiku-4.5")

# Prometheus-Zähler für OpenRouter-Aufrufe (fail-open ohne metrics-Modul)
try:
    from metrics import openrouter_requests_total as _openrouter_counter
except Exception:
    _openrouter_counter = None


_HTML_MARKER = re.compile(r"<\s*(html|body|div|p|section|address|main|span|br|table)\b", re.I)


def zu_fliesstext(inhalt: str) -> str:
    """
    Gibt Fliesstext zurueck, auch wenn der Aufrufer rohes HTML uebergeben hat.

    Der Parameter heisst ueberall `text_content`, die Check-Module reichten
    aber die HTML-Antwort der Impressums-/Datenschutzseite durch. Auf HTML
    scheitern die Muster: "Musterstrasse 123" und "10115 Berlin" stehen dort in
    getrennten <p>-Elementen, kein Adressmuster kann darueber hinweg greifen.
    Deshalb wird hier normalisiert statt an zwei Aufrufstellen.
    """
    if not inhalt:
        return ""
    if "<" not in inhalt or not _HTML_MARKER.search(inhalt):
        return inhalt
    suppe = BeautifulSoup(inhalt, "html.parser")
    for tag in suppe(["script", "style", "noscript", "template", "svg"]):
        tag.decompose()
    return suppe.get_text(separator=" ", strip=True)


class ValidationMethod(Enum):
    """Verwendete Validierungs-Methode"""
    PATTERN_ONLY = "pattern"
    AI_ASSISTED = "ai"
    HYBRID = "hybrid"


@dataclass
class HybridValidationResult:
    """Ergebnis einer Hybrid-Validierung"""
    field_name: str
    found: bool
    confidence: float
    value: Optional[str]
    method_used: ValidationMethod
    ai_reasoning: Optional[str] = None
    processing_time_ms: int = 0
    # Wahr, wenn das Muster sich NICHT sicher war und keine Zweitmeinung
    # eingeholt werden konnte (kein Schluessel, Budget gesperrt, Redis weg).
    # `found` traegt dann die Vermutung des Musters, nicht dessen Feststellung.
    # Wer daraus einen Befund macht, wirft dem Betrieb etwas vor, das nur
    # niemand nachgesehen hat.
    unverifiziert: bool = False


class HybridValidator:
    """
    Hybrid Validator - Best of Both Worlds
    
    Nutzt Pattern-Matching für klare Fälle, KI für Grenzfälle
    """
    
    def __init__(self):
        """Initialisiert Validator"""
        self.analyzer = DeepContentAnalyzer()
        
        # KI via OpenRouter (Claude Haiku) — Key ist im Deployment gesetzt
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.model = VALIDATOR_MODEL
        if self.api_key:
            logger.info(f"✅ Hybrid Validator mit KI-Support initialisiert (OpenRouter, {self.model})")
        else:
            logger.warning("⚠️ OPENROUTER_API_KEY nicht gesetzt - nur Pattern-Matching verfügbar")
        
        # Thresholds für KI-Trigger
        self.uncertain_threshold = 0.6  # < 0.6 Confidence → KI-Check
        self.confident_threshold = 0.85  # >= 0.85 → Pattern ist sicher
    
    def _ist_unsicher(self, validation) -> bool:
        """Darf aus diesem Musterergebnis ein "fehlt" werden? Nein, wenn es unsicher ist.

        Unsicher ist ein Ergebnis unter der Unsicherheitsschwelle (0,6) UND ein
        Treffer, den das Muster gefunden hat, der aber unter der eigenen Schwelle
        des Feldes (`min_confidence`, 0,65 bis 0,7) bleibt. Der zweite Fall lief
        bis zum 07.10.2026 als "Grenzfall" mit `found=False` durch und wurde zum
        kritischen Befund "... fehlt". Gemessen am Pruefstand vom selben Tag an
        zwei Kundenseiten: Der Text enthielt einen eigenen Abschnitt "Beschwerderecht
        bei der Aufsichtsbehoerde", der Scanner meldete trotzdem kritisch
        "Beschwerderecht fehlt". Ein Muster, das etwas fand und sich nicht sicher
        ist, hat nichts Fehlendes festgestellt; es geht zur KI oder, ohne KI, in
        die Liste der nicht abschliessend geprueften Angaben.
        """
        return (validation.confidence < self.uncertain_threshold
                or not validation.found)

    async def validate_field(
        self,
        field_name: str,
        field_config: Dict[str, Any],
        text_content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> HybridValidationResult:
        """
        Validiert einzelnes Feld mit Hybrid-Ansatz
        
        Args:
            field_name: Name des Feldes (z.B. "firmenname", "email")
            field_config: Pattern-Konfiguration
            text_content: Zu prüfender Text
            context: Zusätzlicher Kontext (z.B. domain, page_type)
        
        Returns:
            HybridValidationResult
        """
        import time
        start_time = time.time()
        
        # STUFE 1: Pattern-Matching
        validation = self.analyzer._validate_field(
            field_name,
            field_config,
            text_content,
            None  # soup not needed for text-only validation
        )
        
        # Entscheidung: Ist Pattern-Result vertrauenswürdig?
        if validation.confidence >= self.confident_threshold:
            # ✅ KLAR: Pattern ist sicher
            processing_time = int((time.time() - start_time) * 1000)
            
            logger.info(f"✅ Pattern Match für {field_name}: {validation.confidence:.2f}")
            
            return HybridValidationResult(
                field_name=field_name,
                found=validation.found,
                confidence=validation.confidence,
                value=validation.extracted_value,
                method_used=ValidationMethod.PATTERN_ONLY,
                processing_time_ms=processing_time
            )
        
        elif self._ist_unsicher(validation):
            # ❓ UNSICHER: KI-Check nötig

            if not self.api_key:
                # Kein KI verfügbar → Pattern-Result verwenden (mit Warnung)
                processing_time = int((time.time() - start_time) * 1000)
                
                logger.warning(f"⚠️ {field_name} unsicher ({validation.confidence:.2f}), aber keine KI verfügbar")
                
                return HybridValidationResult(
                    field_name=field_name,
                    found=validation.found,
                    confidence=validation.confidence * 0.8,  # Reduziere Confidence
                    value=validation.extracted_value,
                    method_used=ValidationMethod.PATTERN_ONLY,
                    processing_time_ms=processing_time
                )
            
            # STUFE 2: KI-Validierung
            logger.info(f"🤖 KI-Check für {field_name} (Pattern-Confidence: {validation.confidence:.2f})")
            
            ai_result = await self._ai_validate_field(
                field_name,
                field_config,
                text_content,
                validation,
                context
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return HybridValidationResult(
                field_name=field_name,
                found=ai_result["found"],
                confidence=ai_result["confidence"],
                value=ai_result["value"],
                method_used=ValidationMethod.AI_ASSISTED,
                ai_reasoning=ai_result.get("reasoning"),
                processing_time_ms=processing_time
            )
        
        else:
            # 🔄 GRENZFALL: Pattern OK, aber nicht perfekt → Hybrid
            processing_time = int((time.time() - start_time) * 1000)
            
            logger.info(f"🔄 Hybrid für {field_name}: {validation.confidence:.2f}")
            
            return HybridValidationResult(
                field_name=field_name,
                found=validation.found,
                confidence=validation.confidence,
                value=validation.extracted_value,
                method_used=ValidationMethod.HYBRID,
                processing_time_ms=processing_time
            )
    
    async def _ai_validate_field(
        self,
        field_name: str,
        field_config: Dict[str, Any],
        text_content: str,
        pattern_result: ContentValidation,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        KI-gestützte Validierung bei Unsicherheit
        
        Args:
            field_name: Feldname
            field_config: Konfiguration
            text_content: Text-Content
            pattern_result: Ergebnis des Pattern-Matchings
            context: Zusätzlicher Kontext
        
        Returns:
            Dict mit: {found, confidence, value, reasoning}
        """
        
        # Erstelle Prompt für KI
        prompt = self._create_validation_prompt(
            field_name,
            field_config,
            text_content,
            pattern_result,
            context
        )
        
        try:
            # OpenRouter API Call (async, HTTP-Muster wie ai_review_engine._call_ai)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://complyo.de",
                        "X-Title": "Complyo Hybrid Validator",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 500,
                        "temperature": 0,  # Deterministisch
                    },
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        if _openrouter_counter:
                            _openrouter_counter.labels(status="error").inc()
                        raise RuntimeError(f"OpenRouter Status {resp.status}")
                    data = await resp.json()

            if _openrouter_counter:
                _openrouter_counter.labels(status="success").inc()

            # Parse Response
            ai_response = data["choices"][0]["message"]["content"]

            # Extrahiere strukturierte Daten
            result = self._parse_ai_response(ai_response, pattern_result)

            logger.info(f"✅ KI-Validierung für {field_name}: {result['found']} (Confidence: {result['confidence']:.2f})")

            return result

        except Exception as e:
            logger.error(f"❌ KI-Validierung fehlgeschlagen: {e}")

            # Fallback zu Pattern-Result (fail-open, wie zuvor)
            return {
                "found": pattern_result.found,
                "confidence": pattern_result.confidence * 0.7,  # Reduzierte Confidence
                "value": pattern_result.extracted_value,
                "reasoning": f"KI-Error: {str(e)}"
            }
    
    # Field-spezifische Beschreibungen fuer den Prompt (Einzel- und Batch-Call).
    _FELD_BESCHREIBUNGEN = {
        "firmenname": "Vollständiger Firmenname oder Name des Unternehmens (oft mit Rechtsform wie GmbH, AG, etc.)",
        "adresse": "Vollständige Postanschrift mit Straße, Hausnummer, PLZ und Ort",
        "email": "E-Mail-Adresse für Kontaktaufnahme",
        "telefon": "Telefonnummer für Kontaktaufnahme",
        "verantwortlicher": "Name des Verantwortlichen im Sinne der DSGVO",
        "zwecke": "Zwecke der Datenverarbeitung (wofür werden Daten genutzt)",
        "rechtsgrundlage": "Rechtsgrundlage für die Datenverarbeitung (z.B. Art. 6 DSGVO)",
    }

    # Stichwoerter, an denen die zustaendige Passage im Text erkannt wird.
    _FELD_STICHWOERTER = {
        "firmenname": ["firma", "unternehmen", "diensteanbieter", "verantwortlich für den inhalt", "gmbh", "ug", " ag ", "e.k."],
        "adresse": ["anschrift", "adresse", "sitz", "straße", "str.", "postanschrift"],
        "plz_ort": ["straße", "str.", "deutschland", "anschrift"],
        "email": ["e-mail", "email", "mail:", "kontakt"],
        "telefon": ["telefon", "tel.", "tel:", "fon", "phone", "kontakt"],
        "handelsregister": ["handelsregister", "registergericht", "amtsgericht", "hrb", "hra"],
        "ust_id": ["umsatzsteuer", "ust-id", "ust.-id", "vat", "steuernummer"],
        "geschaeftsfuehrer": ["geschäftsführer", "geschäftsführung", "vertreten durch", "inhaber", "vorstand"],
        "verantwortlicher": ["verantwortlich", "verantwortliche stelle", "controller"],
        "zwecke": ["zweck", "zwecke", "wofür", "verarbeiten wir"],
        "rechtsgrundlage": ["rechtsgrundlage", "art. 6", "artikel 6", "berechtigtes interesse"],
        "speicherdauer": ["speicherdauer", "aufbewahrung", "löschung", "speichern wir"],
        "betroffenenrechte": ["ihre rechte", "betroffenenrechte", "auskunft", "berichtigung"],
        "beschwerderecht": ["beschwerde", "aufsichtsbehörde", "datenschutzbehörde"],
        "datenschutzbeauftragter": ["datenschutzbeauftragter", "datenschutzbeauftragte"],
        "drittland": ["drittland", "außerhalb der eu", "usa"],
    }

    _AUSSCHNITT_ZEICHEN = 3000

    def _relevanter_ausschnitt(
        self,
        field_name: str,
        text_content: str,
        pattern_result: ContentValidation,
    ) -> str:
        """
        Schneidet den Textbereich heraus, in dem die gesuchte Angabe stehen
        muesste. Ankerpunkt ist der Mustertreffer, sonst das erste passende
        Stichwort; ohne beides bleibt es beim Textanfang.
        """
        if len(text_content) <= self._AUSSCHNITT_ZEICHEN:
            return text_content

        anker = -1
        if pattern_result and pattern_result.extracted_value:
            anker = text_content.find(pattern_result.extracted_value)
        if anker == -1:
            unten = text_content.lower()
            for stichwort in self._FELD_STICHWOERTER.get(field_name, []):
                anker = unten.find(stichwort)
                if anker != -1:
                    break
        if anker == -1:
            return text_content[: self._AUSSCHNITT_ZEICHEN]

        halb = self._AUSSCHNITT_ZEICHEN // 2
        start = max(0, anker - halb)
        return text_content[start : start + self._AUSSCHNITT_ZEICHEN]

    def _create_validation_prompt(
        self,
        field_name: str,
        field_config: Dict[str, Any],
        text_content: str,
        pattern_result: ContentValidation,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Erstellt Prompt für KI-Validierung"""

        description = self._FELD_BESCHREIBUNGEN.get(field_name, f"Das Feld '{field_name}'")
        
        # Ausschnitt um die relevante Passage. Frueher: die ersten 3000 Zeichen —
        # bei einer HTML-Seite war das der <head> mit Font-Preloads, die
        # gesuchte Angabe stand weiter unten und die KI antwortete
        # folgerichtig "nicht vorhanden".
        text_sample = self._relevanter_ausschnitt(field_name, text_content, pattern_result)
        
        page_type = context.get("page_type", "unknown") if context else "unknown"
        
        prompt = f"""Du bist ein Compliance-Experte für deutsche Websites.

**Aufgabe:** Prüfe, ob in folgendem Text das Feld "{field_name}" vorhanden ist.

**Feldtyp:** {description}

**Kontext:** {page_type.upper()}-Seite

**Text-Auszug:**
```
{text_sample}
```

**Pattern-Matching-Ergebnis:**
- Gefunden: {pattern_result.found}
- Confidence: {pattern_result.confidence:.2f}
- Extrahierter Wert: {pattern_result.extracted_value or "None"}

**Deine Aufgabe:**
1. Prüfe, ob das Feld "{field_name}" im Text vorhanden ist
2. Wenn ja, extrahiere den relevanten Wert
3. Gib eine Confidence-Bewertung (0.0 - 1.0)
4. Begründe deine Entscheidung kurz

**Antwortformat:**
FOUND: yes|no
VALUE: [extrahierter Wert oder "none"]
CONFIDENCE: [0.0-1.0]
REASONING: [kurze Begründung]

Antworte NUR im angegebenen Format, keine zusätzlichen Erläuterungen."""
        
        return prompt
    
    def _parse_ai_response(
        self,
        ai_response: str,
        fallback: ContentValidation
    ) -> Dict[str, Any]:
        """
        Parsed strukturierte KI-Antwort
        
        Args:
            ai_response: Antwort von Claude
            fallback: Fallback bei Parse-Error
        
        Returns:
            Dict mit found, confidence, value, reasoning
        """
        try:
            lines = ai_response.strip().split('\n')
            result = {}
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('FOUND:'):
                    result['found'] = 'yes' in line.lower()
                
                elif line.startswith('VALUE:'):
                    value = line.replace('VALUE:', '').strip()
                    result['value'] = value if value.lower() != 'none' else None
                
                elif line.startswith('CONFIDENCE:'):
                    conf_str = line.replace('CONFIDENCE:', '').strip()
                    try:
                        result['confidence'] = float(conf_str)
                    except:
                        result['confidence'] = 0.5
                
                elif line.startswith('REASONING:'):
                    result['reasoning'] = line.replace('REASONING:', '').strip()
            
            # Validierung
            if 'found' not in result or 'confidence' not in result:
                raise ValueError("Incomplete AI response")
            
            # Defaults
            result.setdefault('value', None)
            result.setdefault('reasoning', "AI validation completed")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Parse-Error: {e}")
            
            # Fallback
            return {
                "found": fallback.found,
                "confidence": fallback.confidence * 0.8,
                "value": fallback.extracted_value,
                "reasoning": f"Parse error: {str(e)}"
            }
    
    # Der gebuendelte Aufruf liest die Seite in Auszuegen von je rund 6.000
    # Zeichen. Bis zum 08.10.2026 bekam die KI nur die ersten 6.000 Zeichen der
    # Seite und antwortete fuer alles, was weiter hinten steht, mit "nicht
    # gefunden": zu Recht, bezogen auf den Auszug. Der Validator gab das als
    # Feststellung ueber die ganze Seite weiter. Gemessen am Pruefstand vom
    # 08.10.2026 gegen von Hand etikettierte Seiten: "Beschwerderecht fehlt" auf
    # einer Seite mit eigenem Abschnitt "11. Beschwerderecht bei der
    # Aufsichtsbehoerde" (Seitentext 9.700 Zeichen), dasselbe auf einer zweiten,
    # "Rechtsgrundlagen fehlen" bei einer dritten (31.000 Zeichen, Art. 6 steht
    # nach Zeichen 6.000). Von 21 gefundenen Datenschutzerklaerungen sind 15
    # laenger als der Auszug.
    #
    # Kappung (08.10.2026 an 19 etikettierten Erklaerungen gemessen, 4 gegen 8):
    # Mit 4 Auszuegen (rund 23.000 Zeichen) bleiben 7 von 19 Seiten ungelesen, weil
    # sie laenger sind; mit 8 deckt es alles ab (die laengste hat 42.500 Zeichen).
    # Genauigkeit und Trefferquote aendern sich nicht, zwei Feldergebnisse einer
    # Seite werden von "nicht geprueft" zu "gefunden". Kosten: 55 gegen 63 Calls,
    # 0,193 gegen 0,214 EUR fuer die 19 Seiten, im Mittel 1,1 Cent je Seite, die
    # teuerste (8 Calls) 3 Cent. Ein Feld ist nach dem ersten Auszug erledigt, der
    # es enthaelt: die meisten Seiten brauchen weit weniger Calls als Auszuege.
    _BATCH_ZEICHEN = 6000
    _BATCH_UEBERLAPP = 400
    _BATCH_MAX_AUSSCHNITTE = 8
    # Laufzeitgrenze: ein Call dauert rund 4 Sekunden, die laengste Seite brauchte
    # 32 Sekunden. Danach wird nicht weitergelesen, der Rest gilt als nicht geprueft.
    _BATCH_MAX_SEKUNDEN = 45.0

    def _batch_ausschnitte(self, text: str) -> Tuple[List[str], bool]:
        """Zerlegt den Text in aufeinanderfolgende Auszuege.

        Schneidet an Wortgrenzen, mit etwas Ueberlappung, damit ein Satz an der
        Naht in einem der beiden Auszuege ganz steht. Mehr als
        `_BATCH_MAX_AUSSCHNITTE` werden nicht gelesen (Kostengrenze); der zweite
        Rueckgabewert sagt, ob damit der ganze Text abgedeckt ist.
        """
        if len(text) <= self._BATCH_ZEICHEN:
            return [text], True
        teile: List[str] = []
        start = 0
        abgedeckt = 0
        while start < len(text) and len(teile) < self._BATCH_MAX_AUSSCHNITTE:
            ende = min(len(text), start + self._BATCH_ZEICHEN)
            if ende < len(text):
                leer = text.rfind(" ", start + self._BATCH_ZEICHEN - 300, ende)
                if leer != -1:
                    ende = leer
            teile.append(text[start:ende])
            abgedeckt = ende
            if ende >= len(text):
                break
            start = ende - self._BATCH_UEBERLAPP
        return teile, abgedeckt >= len(text)

    async def _ai_validate_fields_batch(
        self,
        unsichere_felder: Dict[str, ContentValidation],
        text_content: str,
        page_type: str,
        user_id: Optional[str],
    ) -> Dict[str, Dict[str, Any]]:
        """
        KI-Zweitmeinung fuer alle unsicheren Felder einer Seite, ausschnittsweise.

        Je Auszug EIN OpenRouter-Call fuer die Felder, die noch nicht gefunden
        sind (statt je Feld und Auszug einer). Ein Feld ist erledigt, sobald ein
        Auszug es enthaelt. "Nicht gefunden" gilt nur, wenn die KI die GANZE
        Seite gesehen hat: bei laengeren Seiten als `_BATCH_MAX_AUSSCHNITTE`
        Auszuege oder wenn ein Call scheitert, kommt das Ergebnis mit
        `unvollstaendig`, und der Aufrufer wertet es als nicht geprueft statt
        als fehlend.

        Bei einem Fehler im ersten Call: leeres Dict, der Aufrufer faellt je Feld
        aufs Pattern-Ergebnis zurueck (wie zuvor, fail-open).
        """
        ausschnitte, vollstaendig = self._batch_ausschnitte(text_content)
        offen = dict(unsichere_felder)
        ergebnisse: Dict[str, Dict[str, Any]] = {}
        letzte_antwort: Dict[str, Dict[str, Any]] = {}
        beantwortet = 0
        beginn = time.monotonic()

        for nr, teil in enumerate(ausschnitte, start=1):
            if not offen:
                break
            if nr > 1 and time.monotonic() - beginn > self._BATCH_MAX_SEKUNDEN:
                logger.warning(f"⏱️ KI-Zweitmeinung nach {nr - 1} von {len(ausschnitte)} Auszuegen abgebrochen (Zeitgrenze)")
                break
            antwort = await self._ai_batch_ausschnitt(
                offen, teil, page_type, user_id, nr, len(ausschnitte))
            if not antwort:
                if nr == 1:
                    return {}
                break
            beantwortet += 1
            for feld in list(offen):
                r = antwort.get(feld)
                if r is None:
                    continue  # Parse-Luecke: das Feld bleibt offen
                if r["found"]:
                    ergebnisse[feld] = r
                    del offen[feld]
                else:
                    letzte_antwort[feld] = r

        alles_gesehen = vollstaendig and beantwortet == len(ausschnitte)
        for feld in offen:
            r = letzte_antwort.get(feld)
            if r is None:
                continue
            ergebnisse[feld] = r if alles_gesehen else {**r, "unvollstaendig": True}
        return ergebnisse

    async def _ai_batch_ausschnitt(
        self,
        unsichere_felder: Dict[str, ContentValidation],
        text_content: str,
        page_type: str,
        user_id: Optional[str],
        ausschnitt_nr: int = 1,
        ausschnitte_gesamt: int = 1,
    ) -> Dict[str, Dict[str, Any]]:
        """
        EIN OpenRouter-Call fuer ALLE uebergebenen Felder an EINEM Textauszug.

        Vorher rief validate_page pro unsicherem Feld einen eigenen
        _ai_validate_field-Call auf — bei einer Seite mit vielen Grenzfaellen
        bis zu 16 einzelne Requests, jeder mit vollem Prompt-Overhead. Das war
        der Kern des Vorfalls vom 04.09.2026. Ein gebuendelter Call mit einem
        Prompt fuer alle Felder ersetzt das 1:1 funktional, kostet aber nur
        noch einen Bruchteil.

        Bei Fehler: leeres Dict.
        """
        prompt = self._create_batch_validation_prompt(
            unsichere_felder, text_content, page_type, ausschnitt_nr, ausschnitte_gesamt)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://complyo.de",
                        "X-Title": "Complyo Hybrid Validator",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": min(4000, 200 * len(unsichere_felder) + 150),
                        "temperature": 0,
                    },
                    timeout=aiohttp.ClientTimeout(total=25),
                ) as resp:
                    if resp.status != 200:
                        if _openrouter_counter:
                            _openrouter_counter.labels(status="error").inc()
                        logger.error(f"❌ Batch-KI-Validierung fehlgeschlagen: OpenRouter Status {resp.status}")
                        return {}
                    data = await resp.json()

            if _openrouter_counter:
                _openrouter_counter.labels(status="success").inc()

            usage = data.get("usage") or {}
            kosten = ai_budget.kosten_eur(
                self.model,
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0),
            )
            await ai_budget.kosten_buchen(user_id, kosten)

            ai_response = data["choices"][0]["message"]["content"]
            ergebnisse = self._parse_batch_ai_response(ai_response, unsichere_felder)

            logger.info(
                f"✅ Batch-KI-Validierung: {len(ergebnisse)}/{len(unsichere_felder)} Felder "
                f"in einem Call ({kosten:.4f} EUR)"
            )
            return ergebnisse

        except Exception as e:
            logger.error(f"❌ Batch-KI-Validierung fehlgeschlagen: {e}")
            return {}

    def _create_batch_validation_prompt(
        self,
        unsichere_felder: Dict[str, ContentValidation],
        text_content: str,
        page_type: str,
        ausschnitt_nr: int = 1,
        ausschnitte_gesamt: int = 1,
    ) -> str:
        """Ein Prompt fuer mehrere Felder statt einem Prompt je Feld.

        Der Textauszug wird einmal fuer alle Felder gemeinsam genommen (statt
        je Feld um den eigenen Treffer herum ausgeschnitten). Laengere Seiten
        kommen als mehrere aufeinanderfolgende Auszuege, siehe
        `_ai_validate_fields_batch`; der Prompt sagt der KI, dass sie nur einen
        Teil sieht, damit "nein" heisst "nicht in DIESEM Auszug".
        """
        text_sample = text_content[: self._BATCH_ZEICHEN]
        if ausschnitte_gesamt > 1:
            auszug_hinweis = (
                f"\n**Hinweis:** Das ist Auszug {ausschnitt_nr} von {ausschnitte_gesamt} einer "
                f"längeren Seite. Die anderen Auszüge siehst du nicht. Antworte FOUND: no nur, wenn "
                f"die Angabe in DIESEM Auszug fehlt.\n"
            )
        else:
            auszug_hinweis = ""

        felder_block = []
        antwort_bloecke = []
        for i, (field_name, pattern_result) in enumerate(unsichere_felder.items(), start=1):
            description = self._FELD_BESCHREIBUNGEN.get(field_name, f"Das Feld '{field_name}'")
            felder_block.append(
                f"{i}. FELD: {field_name}\n"
                f"   Beschreibung: {description}\n"
                f"   Pattern-Ergebnis: gefunden={pattern_result.found}, "
                f"confidence={pattern_result.confidence:.2f}, "
                f"wert={pattern_result.extracted_value or 'None'}"
            )
            antwort_bloecke.append(
                f"### {i}\nFOUND: yes|no\nVALUE: [extrahierter Wert oder \"none\"]\n"
                f"CONFIDENCE: [0.0-1.0]\nREASONING: [kurze Begründung]"
            )

        felder_text = "\n\n".join(felder_block)
        antwort_text = "\n\n".join(antwort_bloecke)

        return f"""Du bist ein Compliance-Experte für deutsche Websites.

**Aufgabe:** Prüfe im folgenden Text-Auszug ALLE unten aufgeführten Felder — jedes für sich — und antworte für JEDES Feld in einem eigenen, nummerierten Block.

**Kontext:** {page_type.upper()}-Seite
{auszug_hinweis}
**Text-Auszug:**
```
{text_sample}
```

**Zu prüfende Felder:**

{felder_text}

**Antwortformat — GENAU EIN Block pro Feld, in der Reihenfolge oben, mit der Nummer als Überschrift:**

{antwort_text}

Antworte NUR mit den nummerierten Blöcken, keine zusätzlichen Erläuterungen."""

    def _parse_batch_ai_response(
        self,
        ai_response: str,
        unsichere_felder: Dict[str, ContentValidation],
    ) -> Dict[str, Dict[str, Any]]:
        """Zerlegt die Batch-Antwort an den '### N'-Markern und parst jeden
        Block mit derselben Logik wie eine Einzelantwort."""
        feld_reihenfolge = list(unsichere_felder.keys())
        ergebnisse: Dict[str, Dict[str, Any]] = {}

        teile = re.split(r'^###\s*(\d+)\s*$', ai_response, flags=re.MULTILINE)
        # re.split mit Fangruppe: [vor_erstem, num1, block1, num2, block2, ...]
        for i in range(1, len(teile) - 1, 2):
            try:
                index = int(teile[i]) - 1
            except ValueError:
                continue
            if index < 0 or index >= len(feld_reihenfolge):
                continue
            field_name = feld_reihenfolge[index]
            ergebnisse[field_name] = self._parse_ai_response(
                teile[i + 1], unsichere_felder[field_name]
            )

        return ergebnisse

    async def validate_page(
        self,
        page_type: str,
        text_content: str,
        url: str,
        user_id: Optional[str] = None,
        plan_type: str = "free",
    ) -> Dict[str, Any]:
        """
        Validiert gesamte Seite (Impressum oder Datenschutz)

        Args:
            page_type: "impressum" oder "datenschutz"
            text_content: Text-Content der Seite
            url: URL der Seite
            user_id: Konto, dem der Scan gehoert (fuer das KI-Monatsbudget;
                None beim oeffentlichen Vorschau-Scan)
            plan_type: Tarif des Kontos (bestimmt das Budget, siehe ai_budget)

        Returns:
            Dict mit Validierungs-Ergebnissen
        """
        logger.info(f"🔍 Hybrid-Validierung: {page_type} ({url})")

        # Aufrufer reichen teils die rohe HTML-Antwort durch — die Muster
        # brauchen Fliesstext, sonst trennen Tags zusammengehoerige Angaben.
        text_content = zu_fliesstext(text_content)

        # Wähle Pattern-Set
        if page_type == "impressum":
            patterns = self.analyzer.impressum_patterns
        elif page_type == "datenschutz":
            patterns = self.analyzer.datenschutz_patterns
        else:
            raise ValueError(f"Unbekannter Page-Type: {page_type}")

        # STUFE 1: Pattern-Matching fuer alle Felder — schnell, kostenlos.
        # Teilt die Felder in sicher (Pattern reicht), Grenzfall (Pattern OK,
        # keine KI noetig) und unsicher (KI-Kandidat) auf.
        results_by_field: Dict[str, HybridValidationResult] = {}
        unsichere_felder: Dict[str, ContentValidation] = {}

        for field_name, field_config in patterns.items():
            validation = self.analyzer._validate_field(field_name, field_config, text_content, None)

            if validation.confidence >= self.confident_threshold:
                results_by_field[field_name] = HybridValidationResult(
                    field_name=field_name, found=validation.found,
                    confidence=validation.confidence, value=validation.extracted_value,
                    method_used=ValidationMethod.PATTERN_ONLY,
                )
            elif self._ist_unsicher(validation):
                unsichere_felder[field_name] = validation
            else:
                results_by_field[field_name] = HybridValidationResult(
                    field_name=field_name, found=validation.found,
                    confidence=validation.confidence, value=validation.extracted_value,
                    method_used=ValidationMethod.HYBRID,
                )

        # STUFE 2: EIN gebuendelter KI-Call fuer ALLE unsicheren Felder dieser
        # Seite statt bis zu 16 Einzelcalls — siehe _ai_validate_fields_batch.
        if unsichere_felder:
            if not self.api_key:
                logger.warning(f"⚠️ {len(unsichere_felder)} Felder unsicher, aber keine KI verfügbar")
                for field_name, validation in unsichere_felder.items():
                    results_by_field[field_name] = HybridValidationResult(
                        field_name=field_name, found=validation.found,
                        confidence=validation.confidence * 0.8, value=validation.extracted_value,
                        method_used=ValidationMethod.PATTERN_ONLY,
                        unverifiziert=True,
                    )
            else:
                budget_ok = await ai_budget.budget_frei(user_id, plan_type)
                if not budget_ok:
                    logger.warning(
                        f"⚠️ KI-Budget erschöpft — {len(unsichere_felder)} unsichere Felder "
                        f"bleiben bei Pattern-Ergebnis ({page_type}, {url})"
                    )
                    for field_name, validation in unsichere_felder.items():
                        results_by_field[field_name] = HybridValidationResult(
                            field_name=field_name, found=validation.found,
                            confidence=validation.confidence * 0.8, value=validation.extracted_value,
                            method_used=ValidationMethod.PATTERN_ONLY,
                            unverifiziert=True,
                        )
                else:
                    logger.info(f"🤖 Batch-KI-Check für {len(unsichere_felder)} unsichere Felder ({page_type})")
                    ai_ergebnisse = await self._ai_validate_fields_batch(
                        unsichere_felder, text_content, page_type, user_id
                    )
                    for field_name, validation in unsichere_felder.items():
                        ai_result = ai_ergebnisse.get(field_name)
                        if ai_result is None:
                            # Feld fehlte in der Antwort (Parse-Luecke o.ae.) → Pattern-Fallback.
                            results_by_field[field_name] = HybridValidationResult(
                                field_name=field_name, found=validation.found,
                                confidence=validation.confidence * 0.7, value=validation.extracted_value,
                                method_used=ValidationMethod.PATTERN_ONLY,
                                unverifiziert=True,
                            )
                        else:
                            results_by_field[field_name] = HybridValidationResult(
                                field_name=field_name, found=ai_result["found"],
                                confidence=ai_result["confidence"], value=ai_result["value"],
                                method_used=ValidationMethod.AI_ASSISTED,
                                ai_reasoning=ai_result.get("reasoning"),
                                # Die KI hat nicht die ganze Seite gesehen: ihr "nein"
                                # gilt dem Auszug, nicht der Seite.
                                unverifiziert=bool(ai_result.get("unvollstaendig")),
                            )

        # Urspruengliche Feldreihenfolge wiederherstellen
        results = [results_by_field[fn] for fn in patterns.keys()]
        ai_calls = sum(1 for r in results if r.method_used == ValidationMethod.AI_ASSISTED)

        # Statistiken
        total_fields = len(results)
        found_fields = sum(1 for r in results if r.found)
        avg_confidence = sum(r.confidence for r in results) / total_fields if total_fields > 0 else 0.0
        
        # Berechne Qualität
        # Vollstaendigkeit nur ueber das, was tatsaechlich geprueft wurde.
        #
        # Am 09.09.2026 im Bestandsdurchlauf gemessen: war Redis nicht
        # erreichbar, sperrte die Budgetpruefung die KI, der Validator fiel auf
        # das Muster zurueck — und neun von 24 Seiten bekamen daraufhin
        # "Anschrift fehlt im Impressum", kritisch, 2.000 EUR. Nicht weil die
        # Anschrift fehlte, sondern weil niemand nachgesehen hatte. Ein nicht
        # geprueftes Feld darf die Note nicht druecken; sonst haengt das
        # Ergebnis daran, ob ein fremder Dienst gerade antwortet.
        required_fields = [name for name, cfg in patterns.items() if cfg.get("required", False)]
        geprueft_required = [
            r for r in results if r.field_name in required_fields and not r.unverifiziert
        ]
        found_required = [r for r in geprueft_required if r.found]

        completeness = (
            len(found_required) / len(geprueft_required) if geprueft_required else 1.0
        )
        
        # Gesamtbewertung
        overall_score = (completeness * 0.7) + (avg_confidence * 0.3)
        
        if overall_score >= 0.9:
            quality = "excellent"
        elif overall_score >= 0.75:
            quality = "good"
        elif overall_score >= 0.6:
            quality = "acceptable"
        elif overall_score >= 0.4:
            quality = "poor"
        else:
            quality = "insufficient"
        
        logger.info(f"✅ Hybrid-Validierung abgeschlossen: {quality} ({ai_calls} KI-Calls)")
        
        return {
            "url": url,
            "page_type": page_type,
            "quality": quality,
            "completeness": completeness,
            "avg_confidence": avg_confidence,
            "overall_score": overall_score,
            "results": [
                {
                    "field": r.field_name,
                    "found": r.found,
                    "confidence": r.confidence,
                    "value": r.value,
                    "method": r.method_used.value,
                    "ai_reasoning": r.ai_reasoning,
                    "unverifiziert": r.unverifiziert,
                }
                for r in results
            ],
            "statistics": {
                "total_fields": total_fields,
                "found_fields": found_fields,
                "required_fields": len(required_fields),
                "found_required": len(found_required),
                "ai_calls": ai_calls,
                "pattern_only": sum(1 for r in results if r.method_used == ValidationMethod.PATTERN_ONLY),
                "hybrid": sum(1 for r in results if r.method_used == ValidationMethod.HYBRID),
            }
        }

