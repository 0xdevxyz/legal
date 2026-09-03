"""
Deep Content Analyzer
Analysiert tatsächlichen Seiteninhalt statt nur Link-Existenz

Features:
- Crawlt und analysiert Impressum/Datenschutz-Seiten
- Pattern-basierte Erkennung (schnell, 90% Fälle)
- KI-Validierung bei Unsicherheit (10% Fälle)
- Qualitätsbewertung der Inhalte
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ContentQuality(Enum):
    """Qualitätsbewertung des Inhalts"""
    EXCELLENT = "excellent"  # Alle Pflichtangaben vorhanden, hochwertig
    GOOD = "good"            # Alle Pflichtangaben vorhanden
    ACCEPTABLE = "acceptable" # Meiste Pflichtangaben vorhanden
    POOR = "poor"            # Einige Pflichtangaben fehlen
    INSUFFICIENT = "insufficient"  # Viele Pflichtangaben fehlen


@dataclass
class ContentValidation:
    """Ergebnis einer Content-Validierung"""
    field_name: str
    found: bool
    confidence: float  # 0.0 - 1.0
    extracted_value: Optional[str] = None
    location: Optional[str] = None  # CSS-Selector oder Text-Position
    quality_score: float = 0.0  # 0-100


@dataclass
class DeepAnalysisResult:
    """Ergebnis einer Deep-Content-Analyse"""
    url: str
    page_type: str  # "impressum", "datenschutz", etc.
    overall_quality: ContentQuality
    validations: List[ContentValidation] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    confidence: float = 0.0  # Gesamtvertrauen in die Analyse


class DeepContentAnalyzer:
    """
    Deep Content Analyzer für Compliance-Prüfung
    
    Prüft tatsächlichen Inhalt von Seiten statt nur Link-Existenz
    """
    
    def __init__(self):
        """Initialisiert Analyzer mit Pattern-Definitionen"""
        
        # ========================================================================
        # IMPRESSUM PATTERNS
        # ========================================================================
        
        self.impressum_patterns = {
            "firmenname": {
                "patterns": [
                    # Name nach der Impressums-Ueberschrift (Einzelunternehmen,
                    # Freiberufler, Praxen fuehren keine Rechtsform im Namen).
                    # Stoppwoerter verhindern Treffer wie "sind wir gemäß" aus
                    # dem Haftungstext.
                    r"(?:angaben\s+gem(?:ä|ae)(?:ß|ss)\s*§\s*5\s*(?:TMG|DDG)|"
                    r"diensteanbieter|anbieterkennzeichnung|"
                    r"verantwortlich\s+f(?:ü|ue)r\s+den\s+inhalt(?:\s+nach\s+§\s*\d+[^:]{0,40})?|"
                    r"verantwortliche\s+stelle|betreiber\s+dieser\s+(?:website|seite))"
                    r"[\s:.\-]*"
                    r"((?!(?-i:Als|Sind|Wir|Die|Der|Das|Nach|Gemäß|Haftung|Inhalte|Diese|Ist)\b)"
                    r"(?:(?-i:[A-ZÄÖÜ])[\wäöüß&.\-]*\s+){0,4}(?-i:[A-ZÄÖÜ])[\wäöüß&.\-]*)",
                    # Explizite Markierungen
                    r"(?:firma|firmenname|company|unternehmen)[\s:]+"
                    r"((?:(?-i:[A-ZÄÖÜ])[\wäöüß&.\-]*\s+){0,3}(?-i:[A-ZÄÖÜ])[\wäöüß&.\-]*)",
                    # Nach bekannten Rechtsformen
                    r"((?:(?-i:[A-ZÄÖÜ])[\wäöüß&.\-]*\s+){0,3}(?-i:[A-ZÄÖÜ])[\wäöüß&.\-]*\s*"
                    r"(?-i:g?GmbH(?:\s*&\s*Co\.\s*KG)?|mbH|AG|SE|UG(?:\s*\(haftungsbeschränkt\))?|"
                    r"e\.\s?K\.|e\.\s?V\.|e\.\s?G\.|KG|OHG|PartG(?:mbB)?|GbR|Einzelunternehmen))",
                    # Strukturierte Daten
                    r"<[^>]*(?:itemprop|property)=['\"]name['\"][^>]*>([^<]+)<",
                ],
                "required": True,
                "min_confidence": 0.75
            },

            "adresse": {
                "patterns": [
                    # Strasse + Hausnummer + PLZ + Ort. Strassenname auch getrennt
                    # geschrieben ("Herrnsdorfer Straße"), "ss" statt "ß",
                    # Hausnummer mit Zusatz ("4/2", "12a") und Klammerzusatz.
                    r"((?:(?-i:[A-ZÄÖÜ])[\wäöüß.\-]*\s+){0,2}(?-i:[A-ZÄÖÜ])[\wäöüß.\-]*"
                    r"(?:stra(?:ß|ss)e|str\.|weg|platz|allee|ring|gasse|damm|ufer|chaussee)"
                    r"[\s,]*\d+\s?[a-z]?(?:\s*[/\-]\s*\d+\s?[a-z]?)?(?:\s*\([^)]{1,20}\))?"
                    r"[\s,]+(?<![\d/\-.])\d{5}[\s,]+(?-i:[A-ZÄÖÜ])[a-zäöüß]+(?:-(?-i:[A-ZÄÖÜ])[a-zäöüß]+)*)",
                    # PLZ + Ort + Strasse (umgekehrte Reihenfolge)
                    r"((?<![\d/\-.])\d{5}[\s,]+(?-i:[A-ZÄÖÜ])[a-zäöüß]+(?:-(?-i:[A-ZÄÖÜ])[a-zäöüß]+)*"
                    r"[\s,]+(?:(?-i:[A-ZÄÖÜ])[\wäöüß.\-]*\s+){0,2}(?-i:[A-ZÄÖÜ])[\wäöüß.\-]*"
                    r"(?:stra(?:ß|ss)e|str\.|weg|platz|allee)[\s,]*\d+)",
                    # Address-Tag
                    r"<address[^>]*>([^<]+)</address>",
                    # Schema.org markup
                    r"itemprop=['\"]streetAddress['\"][^>]*>([^<]+)",
                ],
                "required": True,
                "min_confidence": 0.8
            },

            "plz_ort": {
                "patterns": [
                    # PLZ darf nicht Teil einer laengeren Ziffernfolge sein —
                    # "Steuer-Nr. 221/204/01878 Haftungsausschluss" wurde sonst
                    # als "01878 Haftungsausschluss" gelesen. Ortsname: ein Wort,
                    # optional mit Bindestrichteilen ("Limbach-Oberfrohna").
                    r"((?<![\d/\-.])\d{5}\s+(?-i:[A-ZÄÖÜ])[a-zäöüß]+(?:-(?-i:[A-ZÄÖÜ])[a-zäöüß]+)*)",
                    r"itemprop=['\"]postalCode['\"][^>]*>(\d{5})",
                ],
                "required": True,
                "min_confidence": 0.8
            },

            "email": {
                "patterns": [
                    r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                    r"mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                    r"itemprop=['\"]email['\"][^>]*>([^<]+@[^<]+)",
                ],
                "required": True,
                "min_confidence": 0.8
            },
            
            "telefon": {
                "patterns": [
                    # Deutsch: +49, 0, (0)
                    r"(?:tel:|telefon:|phone:)?\s*(\+49[\s\-./]*\(?0?\)?[\s\-./]*\d{2,5}[\s\-./]*\d{3,9})",
                    r"(\(?\+?49\)?[\s\-./]*\(?\d{2,5}\)?[\s\-./]*\d{3,9})",
                    r"(0\d{2,5}[\s\-./]*\d{3,9})",
                    r"itemprop=['\"]telephone['\"][^>]*>([^<]+)",
                ],
                "required": True,
                "min_confidence": 0.8
            },
            
            "handelsregister": {
                "patterns": [
                    r"(?:handelsregister|registernummer|register)[\s:]*((?:HRB|HRA|VR|GnR|PR)\s*\d+\s*[A-Z]?)",
                    r"((?:HRB|HRA|VR|GnR|PR)\s*\d+\s*[A-Z]?)",
                    r"(?:amtsgericht|registergericht)[\s:]*([A-ZÄÖÜ][a-zäöüß-]+[\s,]+(?:HRB|HRA)\s*\d+)",
                    r"((?:HRB|HRA)\s*\d+[\s,]+AG\s+[A-ZÄÖÜ][a-zäöüß]+)",
                ],
                "required": False,  # Nur für Unternehmen
                "min_confidence": 0.8
            },
            
            "ust_id": {
                "patterns": [
                    r"(?:umsatzsteuer-id|ust-id|vat|uid|ust\.?-?id\.?)[\s:]*([A-Z]{2}\s*\d{8,12})",
                    r"\b(DE\d{9})\b",
                ],
                "required": False,  # Optional
                "min_confidence": 0.8
            },
            
            "geschaeftsfuehrer": {
                "patterns": [
                    r"(?:geschäftsführer|geschäftsführung|ceo|managing director)[\s:]+([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)",
                ],
                "required": False,
                "min_confidence": 0.7
            }
        }
        
        # ========================================================================
        # DATENSCHUTZ PATTERNS
        # ========================================================================
        
        self.datenschutz_patterns = {
            "verantwortlicher": {
                "patterns": [
                    # "Die verantwortliche Stelle ... ist: Complyo GmbH"
                    r"verantwortliche[rns]?\s+stelle[^:]{0,80}:\s*"
                    r"((?:(?-i:[A-ZÄÖÜ])[\wäöüß&.\-]*\s+){0,4}(?-i:[A-ZÄÖÜ])[\wäöüß&.\-]*)",
                    r"(?:verantwortlich(?:e[rns]?)?|data controller|controller)[\s:]+"
                    r"((?-i:[A-ZÄÖÜ])[a-zäöüß\s&.\-]+)",
                    r"(?:im\s+sinne\s+(?:der|des)\s+dsgvo|nach\s+art\.\s*13|gemäß\s+art\.\s*13)[\s:]+([A-ZÄÖÜ][a-zäöüß\s]+)",
                ],
                "required": True,
                "min_confidence": 0.7
            },
            
            "zwecke": {
                "patterns": [
                    r"(?:zweck|zwecke|purpose|purposes)\s+(?:der\s+)?(?:datenverarbeitung|verarbeitung|processing)[\s:]+([^.]{20,200})",
                    r"(?:wir\s+(?:verarbeiten|nutzen|verwenden|erheben)\s+(?:ihre\s+)?(?:personen)?daten\s+(?:zu|für))[\s:]+([^.]{20,200})",
                ],
                "required": True,
                "min_confidence": 0.7
            },
            
            "rechtsgrundlage": {
                "patterns": [
                    r"(?:rechtsgrundlage|legal basis)[\s:]+([^.]{20,300})",
                    r"(?:art\.?\s*6\s+abs\.?\s*1|artikel\s+6)[\s:]+([^.]{10,200})",
                ],
                "required": True,
                "min_confidence": 0.7
            },
            
            "speicherdauer": {
                "patterns": [
                    r"(?:speicherdauer|aufbewahrungsfrist|retention period|storage duration)[\s:]+([^.]{10,200})",
                    r"(?:wir\s+speichern\s+(?:ihre\s+)?daten\s+(?:für|bis))[\s:]+([^.]{10,150})",
                ],
                "required": True,
                "min_confidence": 0.7
            },
            
            "betroffenenrechte": {
                "patterns": [
                    r"(?:ihre\s+)?(?:rechte|betroffenenrechte|rights)[\s:]+([^.]{30,500})",
                    r"(?:auskunft|berichtigung|löschung|widerruf|widerspruch)[\s,]+(?:berichtigung|löschung|widerruf|widerspruch)",
                ],
                "required": True,
                "min_confidence": 0.65
            },
            
            "beschwerderecht": {
                "patterns": [
                    r"(?:beschwerderecht|right to lodge a complaint|aufsichtsbehörde|supervisory authority)[\s:]+([^.]{20,300})",
                ],
                "required": True,
                "min_confidence": 0.7
            },
            
            "datenschutzbeauftragter": {
                "patterns": [
                    r"(?:datenschutzbeauftragter|data protection officer|dpo)[\s:]+([A-ZÄÖÜ][a-zäöüß\s]+)",
                ],
                "required": False,  # Nur wenn benötigt
                "min_confidence": 0.7
            },
            
            "drittland": {
                "patterns": [
                    r"(?:drittland|third country|außerhalb der eu|outside the eu)",
                ],
                "required": False,
                "min_confidence": 0.65
            },
            
            "ssl_verschluesselung": {
                "patterns": [
                    r"(?:ssl|tls|verschlüsselung|encryption|https)",
                ],
                "required": False,
                "min_confidence": 0.65
            }
        }
    
    # ========================================================================
    # MAIN ANALYSIS METHODS
    # ========================================================================
    
    async def analyze_impressum_page(
        self,
        url: str,
        html: str
    ) -> DeepAnalysisResult:
        """
        Analysiert Impressum-Seite im Detail
        
        Args:
            url: URL der Impressum-Seite
            html: HTML-Content der Seite
        
        Returns:
            DeepAnalysisResult mit Validierungen
        """
        logger.info(f"🔍 Deep-Analyse: Impressum {url}")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Entferne Script/Style-Tags
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        
        # Extrahiere Text-Content
        text_content = soup.get_text(separator=' ', strip=True)
        
        # Validiere alle Felder
        validations = []
        for field_name, field_config in self.impressum_patterns.items():
            validation = self._validate_field(
                field_name,
                field_config,
                text_content,
                soup
            )
            validations.append(validation)
        
        # Berechne Gesamtqualität
        overall_quality, missing_fields, warnings = self._calculate_quality(
            validations,
            self.impressum_patterns
        )
        
        # Gesamtvertrauen
        confidence = sum(v.confidence for v in validations) / len(validations) if validations else 0.0
        
        result = DeepAnalysisResult(
            url=url,
            page_type="impressum",
            overall_quality=overall_quality,
            validations=validations,
            missing_fields=missing_fields,
            warnings=warnings,
            confidence=confidence
        )
        
        logger.info(f"✅ Impressum-Analyse: {overall_quality.value} (Confidence: {confidence:.2f})")
        
        return result
    
    async def analyze_datenschutz_page(
        self,
        url: str,
        html: str
    ) -> DeepAnalysisResult:
        """
        Analysiert Datenschutzerklärung im Detail
        
        Args:
            url: URL der Datenschutz-Seite
            html: HTML-Content der Seite
        
        Returns:
            DeepAnalysisResult mit Validierungen
        """
        logger.info(f"🔍 Deep-Analyse: Datenschutz {url}")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Entferne Script/Style-Tags
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        
        text_content = soup.get_text(separator=' ', strip=True)
        
        # Validiere alle Felder
        validations = []
        for field_name, field_config in self.datenschutz_patterns.items():
            validation = self._validate_field(
                field_name,
                field_config,
                text_content,
                soup
            )
            validations.append(validation)
        
        # Berechne Qualität
        overall_quality, missing_fields, warnings = self._calculate_quality(
            validations,
            self.datenschutz_patterns
        )
        
        confidence = sum(v.confidence for v in validations) / len(validations) if validations else 0.0
        
        result = DeepAnalysisResult(
            url=url,
            page_type="datenschutz",
            overall_quality=overall_quality,
            validations=validations,
            missing_fields=missing_fields,
            warnings=warnings,
            confidence=confidence
        )
        
        logger.info(f"✅ Datenschutz-Analyse: {overall_quality.value} (Confidence: {confidence:.2f})")
        
        return result
    
    # ========================================================================
    # VALIDATION LOGIC
    # ========================================================================
    
    def _validate_field(
        self,
        field_name: str,
        field_config: Dict[str, Any],
        text_content: str,
        soup: BeautifulSoup
    ) -> ContentValidation:
        """
        Validiert einzelnes Feld mit Pattern-Matching
        
        Returns:
            ContentValidation mit Ergebnis
        """
        patterns = field_config["patterns"]
        min_confidence = field_config["min_confidence"]
        
        best_match = None
        best_confidence = 0.0
        extracted_value = None
        
        # Teste alle Patterns
        for pattern in patterns:
            try:
                matches = re.finditer(pattern, text_content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    # Extrahiere Value (erste Gruppe oder ganzer Match)
                    value = match.group(1) if match.groups() else match.group(0)
                    
                    # Confidence basierend auf Pattern-Typ und Match-Qualität
                    confidence = self._calculate_match_confidence(
                        field_name,
                        pattern,
                        value,
                        text_content
                    )
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        extracted_value = value.strip()
                        best_match = match
            
            except Exception as e:
                logger.warning(f"⚠️ Pattern-Fehler für {field_name}: {e}")
                continue
        
        # Resultat
        found = best_confidence >= min_confidence
        
        return ContentValidation(
            field_name=field_name,
            found=found,
            confidence=best_confidence,
            extracted_value=extracted_value,
            quality_score=best_confidence * 100
        )
    
    def _calculate_match_confidence(
        self,
        field_name: str,
        pattern: str,
        value: str,
        full_text: str
    ) -> float:
        """
        Berechnet Confidence-Score für ein Match
        
        Faktoren:
        - Länge des Matches (zu kurz/lang = suspicious)
        - Kontext (steht "Impressum" oder "Pflichtangaben" in der Nähe?)
        - Format-Validierung (z.B. Email-Format, Telefon-Format)
        """
        confidence = 0.5  # Base confidence
        
        # Längen-Check
        if len(value) < 3:
            confidence *= 0.5  # Zu kurz
        elif 10 <= len(value) <= 200:
            confidence *= 1.3  # Optimale Länge
        elif len(value) > 500:
            confidence *= 0.7  # Zu lang
        
        # Kontext-Check (steht in der Nähe ein relevantes Keyword?)
        # Fuer die meisten Felder fehlte hier ein Eintrag; ohne Kontextbonus
        # blieb ein Treffer bei 0.65 und damit unter jeder Schwelle.
        context_keywords = {
            "firmenname": ["firma", "unternehmen", "company", "diensteanbieter",
                           "verantwortlich", "anbieter", "betreiber", "inhaber", "impressum"],
            "adresse": ["anschrift", "address", "sitz", "adresse", "postanschrift",
                        "impressum", "straße", "strasse"],
            "plz_ort": ["straße", "strasse", "str.", "str ", "weg", "platz", "allee",
                        "ring", "gasse", "anschrift", "adresse", "sitz",
                        "deutschland", "germany"],
            "email": ["e-mail", "email", "kontakt", "mail", "@"],
            "telefon": ["tel", "phone", "fon", "kontakt", "ruf"],
            "handelsregister": ["handelsregister", "registergericht", "amtsgericht",
                                "register", "rechtsform"],
            "ust_id": ["umsatzsteuer", "ust", "vat", "steuer", "§ 27", "27 a"],
            "geschaeftsfuehrer": ["geschäftsführer", "geschäftsführung", "vertreten durch",
                                  "inhaber", "vorstand", "ceo"],
            "verantwortlicher": ["verantwortlich", "controller", "verantwortliche stelle"],
            "zwecke": ["zweck", "verarbeitung", "verarbeiten"],
            "rechtsgrundlage": ["rechtsgrundlage", "dsgvo", "art. 6", "artikel 6", "einwilligung"],
            "speicherdauer": ["speicher", "aufbewahr", "löschung", "frist"],
            "betroffenenrechte": ["recht", "dsgvo", "auskunft", "berichtigung"],
            "beschwerderecht": ["beschwerde", "aufsichtsbehörde", "datenschutzbehörde"],
            "datenschutzbeauftragter": ["datenschutzbeauftragt", "dsb"],
            "drittland": ["drittland", "übermittlung", "eu", "usa"],
        }
        
        if field_name in context_keywords:
            # Suche in ±100 Zeichen um das Match
            value_pos = full_text.find(value)
            if value_pos != -1:
                context = full_text[max(0, value_pos-100):min(len(full_text), value_pos+len(value)+100)].lower()
                
                for keyword in context_keywords[field_name]:
                    if keyword in context:
                        confidence *= 1.2
                        break
        
        # Format-Validierung. Ein Wert, der die Formprobe seines Feldes besteht,
        # ist ein eigenstaendiger Beleg — er hebt die Confidence ueber die
        # Schwelle, waehrend ein zufaelliger Zahlentreffer darunter bleibt.
        if field_name == "email":
            # Erweiterte Email-Validierung
            if "@" in value and "." in value.split("@")[1]:
                confidence *= 1.3
        
        elif field_name == "ust_id":
            # USt-ID Format: Laenderkennung + Ziffern
            if re.match(r"^[A-Z]{2}\s?\d{8,12}$", value.replace(" ", "").upper()):
                confidence *= 1.4

        elif field_name == "firmenname":
            geputzt = value.strip()
            # Durchgaengige Grossschreibung ist eine Abschnitts-Ueberschrift
            # ("REGISTEREINTRAG"), kein Firmenname.
            if len(geputzt) > 3 and geputzt.isupper():
                confidence *= 0.4
            # Rechtsform am Ende ist der belastbare Teil der Angabe
            elif re.search(r"(?:GmbH|AG|UG|e\.\s?K\.|e\.\s?V\.|KG|OHG|PartG|GbR|Einzelunternehmen)\s*$",
                           geputzt, re.IGNORECASE):
                confidence *= 1.25

        elif field_name == "adresse":
            # Vollstaendig heisst: Strasse mit Hausnummer UND PLZ mit Ort
            hat_strasse = bool(re.search(r"(?:stra(?:ß|ss)e|str\.|weg|platz|allee|ring|gasse)"
                                         r"[\s,]*\d+", value, re.IGNORECASE))
            hat_plz_ort = bool(re.search(r"\b\d{5}\b[\s,]+[A-ZÄÖÜ]", value))
            if hat_strasse and hat_plz_ort:
                confidence *= 1.3

        elif field_name == "plz_ort":
            # Deutsche PLZ (keine fuehrende 0 ausser 01-09) plus Ortsname
            if re.match(r"^\d{5}[\s,]+[A-ZÄÖÜ][a-zäöüß.]+(?:[\s\-][A-ZÄÖÜa-zäöü][a-zäöüß.]*){0,3}$",
                        value.strip()):
                confidence *= 1.25

        elif field_name == "telefon":
            # Nur echte Rufnummern zaehlen als Beleg: Laendervorwahl oder
            # fuehrende Null, und genug Ziffern fuer Vorwahl + Anschluss.
            ziffern = re.sub(r"\D", "", value)
            plausibel = (
                len(ziffern) >= 9
                and (value.strip().startswith("+") or ziffern.startswith("49") or ziffern.startswith("0"))
            )
            if plausibel:
                confidence *= 1.25

        elif field_name == "handelsregister":
            if re.search(r"(?:HRB|HRA|VR|GnR|PR)\s*\d+", value, re.IGNORECASE):
                confidence *= 1.25

        # Cap at 1.0
        return min(1.0, confidence)
    
    def _calculate_quality(
        self,
        validations: List[ContentValidation],
        patterns_config: Dict[str, Dict]
    ) -> Tuple[ContentQuality, List[str], List[str]]:
        """
        Berechnet Gesamtqualität basierend auf Validierungen
        
        Returns:
            (ContentQuality, missing_fields, warnings)
        """
        required_fields = [
            name for name, config in patterns_config.items()
            if config.get("required", False)
        ]
        
        found_required = [
            v for v in validations
            if v.field_name in required_fields and v.found
        ]
        
        missing_fields = [
            v.field_name for v in validations
            if v.field_name in required_fields and not v.found
        ]
        
        warnings = []
        
        # Qualitätsberechnung
        required_count = len(required_fields)
        found_count = len(found_required)
        
        if required_count == 0:
            return ContentQuality.EXCELLENT, missing_fields, warnings
        
        completion_rate = found_count / required_count
        
        # Durchschnittliche Confidence der gefundenen Felder
        avg_confidence = sum(v.confidence for v in found_required) / found_count if found_count > 0 else 0.0
        
        # Kombiniere Completion Rate und Confidence
        quality_score = (completion_rate * 0.7) + (avg_confidence * 0.3)
        
        # Bestimme Qualitätsstufe
        if quality_score >= 0.95 and avg_confidence >= 0.9:
            quality = ContentQuality.EXCELLENT
        elif quality_score >= 0.85:
            quality = ContentQuality.GOOD
        elif quality_score >= 0.7:
            quality = ContentQuality.ACCEPTABLE
            warnings.append(f"{len(missing_fields)} Pflichtangabe(n) fehlen")
        elif quality_score >= 0.5:
            quality = ContentQuality.POOR
            warnings.append(f"Mehrere wichtige Angaben fehlen ({len(missing_fields)} Felder)")
        else:
            quality = ContentQuality.INSUFFICIENT
            warnings.append(f"Unvollständig: {len(missing_fields)}/{required_count} Pflichtangaben fehlen")
        
        return quality, missing_fields, warnings

