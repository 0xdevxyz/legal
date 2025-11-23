"""
Hybrid Validator
Kombiniert Pattern-Matching (schnell) mit KI-Validierung (präzise)

Strategie:
- 90% der Fälle: Pattern-Matching (< 100ms)
- 10% der Fälle: KI-Analyse bei Unsicherheit (~2s)
"""

import anthropic
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from .checks.deep_content_analyzer import DeepContentAnalyzer, ContentValidation, ContentQuality

logger = logging.getLogger(__name__)


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


class HybridValidator:
    """
    Hybrid Validator - Best of Both Worlds
    
    Nutzt Pattern-Matching für klare Fälle, KI für Grenzfälle
    """
    
    def __init__(self):
        """Initialisiert Validator"""
        self.analyzer = DeepContentAnalyzer()
        
        # KI-Client (Claude)
        self.ai_client = None
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.ai_client = anthropic.Anthropic(api_key=api_key)
            logger.info("✅ Hybrid Validator mit KI-Support initialisiert")
        else:
            logger.warning("⚠️ ANTHROPIC_API_KEY nicht gesetzt - nur Pattern-Matching verfügbar")
        
        # Thresholds für KI-Trigger
        self.uncertain_threshold = 0.6  # < 0.6 Confidence → KI-Check
        self.confident_threshold = 0.85  # >= 0.85 → Pattern ist sicher
    
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
        
        elif validation.confidence < self.uncertain_threshold:
            # ❓ UNSICHER: KI-Check nötig
            
            if not self.ai_client:
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
            # Claude API Call
            response = self.ai_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                temperature=0,  # Deterministisch
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse Response
            ai_response = response.content[0].text
            
            # Extrahiere strukturierte Daten
            result = self._parse_ai_response(ai_response, pattern_result)
            
            logger.info(f"✅ KI-Validierung für {field_name}: {result['found']} (Confidence: {result['confidence']:.2f})")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ KI-Validierung fehlgeschlagen: {e}")
            
            # Fallback zu Pattern-Result
            return {
                "found": pattern_result.found,
                "confidence": pattern_result.confidence * 0.7,  # Reduzierte Confidence
                "value": pattern_result.extracted_value,
                "reasoning": f"KI-Error: {str(e)}"
            }
    
    def _create_validation_prompt(
        self,
        field_name: str,
        field_config: Dict[str, Any],
        text_content: str,
        pattern_result: ContentValidation,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Erstellt Prompt für KI-Validierung"""
        
        # Field-spezifische Beschreibungen
        field_descriptions = {
            "firmenname": "Vollständiger Firmenname oder Name des Unternehmens (oft mit Rechtsform wie GmbH, AG, etc.)",
            "adresse": "Vollständige Postanschrift mit Straße, Hausnummer, PLZ und Ort",
            "email": "E-Mail-Adresse für Kontaktaufnahme",
            "telefon": "Telefonnummer für Kontaktaufnahme",
            "verantwortlicher": "Name des Verantwortlichen im Sinne der DSGVO",
            "zwecke": "Zwecke der Datenverarbeitung (wofür werden Daten genutzt)",
            "rechtsgrundlage": "Rechtsgrundlage für die Datenverarbeitung (z.B. Art. 6 DSGVO)",
        }
        
        description = field_descriptions.get(field_name, f"Das Feld '{field_name}'")
        
        # Limitiere Text auf relevante Teile (max 3000 Zeichen)
        text_sample = text_content[:3000] if len(text_content) > 3000 else text_content
        
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
    
    async def validate_page(
        self,
        page_type: str,
        text_content: str,
        url: str
    ) -> Dict[str, Any]:
        """
        Validiert gesamte Seite (Impressum oder Datenschutz)
        
        Args:
            page_type: "impressum" oder "datenschutz"
            text_content: Text-Content der Seite
            url: URL der Seite
        
        Returns:
            Dict mit Validierungs-Ergebnissen
        """
        logger.info(f"🔍 Hybrid-Validierung: {page_type} ({url})")
        
        # Wähle Pattern-Set
        if page_type == "impressum":
            patterns = self.analyzer.impressum_patterns
        elif page_type == "datenschutz":
            patterns = self.analyzer.datenschutz_patterns
        else:
            raise ValueError(f"Unbekannter Page-Type: {page_type}")
        
        # Validiere alle Felder
        results = []
        ai_calls = 0
        
        for field_name, field_config in patterns.items():
            result = await self.validate_field(
                field_name,
                field_config,
                text_content,
                context={"page_type": page_type, "url": url}
            )
            results.append(result)
            
            if result.method_used == ValidationMethod.AI_ASSISTED:
                ai_calls += 1
        
        # Statistiken
        total_fields = len(results)
        found_fields = sum(1 for r in results if r.found)
        avg_confidence = sum(r.confidence for r in results) / total_fields if total_fields > 0 else 0.0
        
        # Berechne Qualität
        required_fields = [name for name, cfg in patterns.items() if cfg.get("required", False)]
        found_required = [r for r in results if r.field_name in required_fields and r.found]
        
        completeness = len(found_required) / len(required_fields) if required_fields else 1.0
        
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
                    "ai_reasoning": r.ai_reasoning
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

