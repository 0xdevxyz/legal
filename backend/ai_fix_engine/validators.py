"""
Complyo AI Fix Engine - Validators v2.0

Validierung von AI-generierten Fixes:
- JSON-Schema-Validation
- Code-Syntax-Check (HTML/CSS/JS)
- Rechtliche Keyword-Prüfung
- Platzhalter-Detection

© 2025 Complyo.tech
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import html.parser
import jsonschema
from jsonschema import validate, ValidationError


# =============================================================================
# Validation Results
# =============================================================================

@dataclass
class ValidationResult:
    """Ergebnis einer Validierung"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


@dataclass
class CodeValidationResult(ValidationResult):
    """Spezielles Ergebnis für Code-Validierung"""
    syntax_errors: List[Dict[str, Any]]
    security_issues: List[str]


@dataclass
class LegalTextValidationResult(ValidationResult):
    """Spezielles Ergebnis für Rechtstext-Validierung"""
    missing_keywords: List[str]
    placeholders_found: List[str]
    legal_compliance_score: float


# =============================================================================
# Schema Validator
# =============================================================================

class SchemaValidator:
    """Validiert AI-Output gegen JSON-Schema"""
    
    def __init__(self):
        self.schemas = {}
    
    def validate_against_schema(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validiert Daten gegen JSON-Schema
        """
        errors = []
        warnings = []
        
        try:
            validate(instance=data, schema=schema)
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                metadata={"schema_valid": True}
            )
        except ValidationError as e:
            errors.append(f"Schema-Validation fehlgeschlagen: {e.message}")
            errors.append(f"Pfad: {' -> '.join(str(p) for p in e.path)}")
            
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                metadata={
                    "schema_valid": False,
                    "error_path": list(e.path),
                    "validator": e.validator
                }
            )
        except Exception as e:
            errors.append(f"Unerwarteter Validierungsfehler: {str(e)}")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=[],
                metadata={"schema_valid": False}
            )


# =============================================================================
# Code Syntax Validator
# =============================================================================

class HTMLValidator:
    """Validiert HTML-Syntax"""
    
    def __init__(self):
        self.parser = html.parser.HTMLParser()
        self.errors = []
    
    def validate(self, html_code: str) -> List[str]:
        """
        Validiert HTML-Syntax
        """
        errors = []
        
        # Basic checks
        if not html_code or not html_code.strip():
            errors.append("HTML-Code ist leer")
            return errors
        
        # Check for unclosed tags
        tag_pattern = r'<(\w+)[^>]*>'
        closing_pattern = r'</(\w+)>'
        
        opening_tags = re.findall(tag_pattern, html_code.lower())
        closing_tags = re.findall(closing_pattern, html_code.lower())
        
        # Self-closing tags die keine Closing-Tags brauchen
        self_closing = {'img', 'br', 'hr', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source'}
        
        opening_tags_filtered = [tag for tag in opening_tags if tag not in self_closing]
        
        # Check balance
        for tag in opening_tags_filtered:
            if opening_tags_filtered.count(tag) > closing_tags.count(tag):
                errors.append(f"Unclosed HTML tag: <{tag}>")
        
        # Check for common issues
        if '<script' in html_code.lower() and '</script>' not in html_code.lower():
            errors.append("Script-Tag nicht geschlossen")
        
        if '<style' in html_code.lower() and '</style>' not in html_code.lower():
            errors.append("Style-Tag nicht geschlossen")
        
        # Check for dangerous patterns
        if re.search(r'javascript:\s*void', html_code, re.IGNORECASE):
            errors.append("Warnung: javascript:void() gefunden - potentielles Sicherheitsrisiko")
        
        if re.search(r'onclick\s*=|onerror\s*=', html_code, re.IGNORECASE):
            errors.append("Warnung: Inline-Event-Handler gefunden - nicht empfohlen")
        
        return errors


class CSSValidator:
    """Validiert CSS-Syntax"""
    
    def validate(self, css_code: str) -> List[str]:
        """
        Validiert CSS-Syntax
        """
        errors = []
        
        if not css_code or not css_code.strip():
            errors.append("CSS-Code ist leer")
            return errors
        
        # Check for balanced braces
        open_braces = css_code.count('{')
        close_braces = css_code.count('}')
        
        if open_braces != close_braces:
            errors.append(f"Unbalanced braces: {open_braces} öffnende, {close_braces} schließende")
        
        # Check for basic CSS structure
        if '{' in css_code and '}' in css_code:
            # Extract rules
            rules = re.findall(r'([^{]+)\{([^}]+)\}', css_code)
            
            for selector, properties in rules:
                # Check selector
                if not selector.strip():
                    errors.append("Leerer CSS-Selektor gefunden")
                
                # Check properties
                if not properties.strip():
                    errors.append(f"Leere Eigenschaften für Selektor: {selector.strip()}")
                    continue
                
                # Check property format
                props = properties.split(';')
                for prop in props:
                    prop = prop.strip()
                    if prop and ':' not in prop:
                        errors.append(f"Ungültige CSS-Eigenschaft (fehlt ':'): {prop}")
        
        # Check for common mistakes
        if re.search(r'color\s*:\s*[^;]+(?!;)', css_code):
            errors.append("Warnung: Möglicherweise fehlendes Semikolon in CSS")
        
        return errors


class JavaScriptValidator:
    """Validiert JavaScript-Syntax (Basic)"""
    
    def validate(self, js_code: str) -> List[str]:
        """
        Validiert JavaScript-Syntax (Basic checks)
        """
        errors = []
        
        if not js_code or not js_code.strip():
            errors.append("JavaScript-Code ist leer")
            return errors
        
        # Check for balanced parentheses, brackets, braces
        paren_balance = js_code.count('(') - js_code.count(')')
        bracket_balance = js_code.count('[') - js_code.count(']')
        brace_balance = js_code.count('{') - js_code.count('}')
        
        if paren_balance != 0:
            errors.append(f"Unbalanced parentheses: {abs(paren_balance)} {'öffnende' if paren_balance > 0 else 'schließende'} fehlen")
        
        if bracket_balance != 0:
            errors.append(f"Unbalanced brackets: {abs(bracket_balance)} fehlen")
        
        if brace_balance != 0:
            errors.append(f"Unbalanced braces: {abs(brace_balance)} fehlen")
        
        # Check for common syntax errors
        if re.search(r'function\s+\w+\s*\([^)]*\)\s*(?!{)', js_code):
            errors.append("Warnung: Function ohne öffnende Brace gefunden")
        
        # Check for dangerous patterns
        if 'eval(' in js_code:
            errors.append("Sicherheitswarnung: eval() gefunden - vermeiden!")
        
        if re.search(r'document\.write\s*\(', js_code):
            errors.append("Warnung: document.write() gefunden - nicht empfohlen")
        
        # Check for console.log (sollte in Production nicht sein)
        console_logs = len(re.findall(r'console\.log\s*\(', js_code))
        if console_logs > 2:
            errors.append(f"Warnung: {console_logs} console.log() Aufrufe gefunden - für Production entfernen")
        
        return errors


class CodeValidator:
    """Haupt-Code-Validator"""
    
    def __init__(self):
        self.html_validator = HTMLValidator()
        self.css_validator = CSSValidator()
        self.js_validator = JavaScriptValidator()
    
    def validate_code(
        self,
        code: str,
        language: str
    ) -> CodeValidationResult:
        """
        Validiert Code basierend auf Sprache
        """
        errors = []
        warnings = []
        syntax_errors = []
        security_issues = []
        
        language_lower = language.lower()
        
        if language_lower == 'html':
            html_errors = self.html_validator.validate(code)
            errors.extend(html_errors)
            
            # Check for security issues in HTML
            if re.search(r'<script[^>]*src\s*=\s*["\']https?://[^"\']*["\']', code, re.IGNORECASE):
                # External scripts
                external_scripts = re.findall(r'<script[^>]*src\s*=\s*["\']([^"\']*)["\']', code, re.IGNORECASE)
                for script_url in external_scripts:
                    if not script_url.startswith('https://'):
                        security_issues.append(f"HTTP (nicht HTTPS) Script: {script_url}")
        
        elif language_lower == 'css':
            css_errors = self.css_validator.validate(code)
            errors.extend(css_errors)
        
        elif language_lower in ['javascript', 'js']:
            js_errors = self.js_validator.validate(code)
            errors.extend(js_errors)
        
        elif language_lower == 'php':
            # Basic PHP validation
            if not code.strip().startswith('<?php') and not code.strip().startswith('<?'):
                warnings.append("PHP-Code sollte mit <?php starten")
            
            if 'mysql_' in code:
                errors.append("Deprecated: mysql_* Funktionen - verwende mysqli oder PDO")
        
        else:
            warnings.append(f"Code-Validierung für '{language}' nicht implementiert")
        
        is_valid = len(errors) == 0
        
        return CodeValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metadata={
                "language": language,
                "code_length": len(code),
                "lines": code.count('\n') + 1
            },
            syntax_errors=syntax_errors,
            security_issues=security_issues
        )


# =============================================================================
# Legal Text Validator
# =============================================================================

class LegalTextValidator:
    """Validiert rechtliche Texte"""
    
    def __init__(self):
        # DSGVO Pflicht-Keywords
        self.dsgvo_keywords = {
            "datenschutz": ["datenschutz", "dsgvo", "personenbezogene daten"],
            "betroffenenrechte": [
                "auskunftsrecht", "löschungsrecht", "widerspruchsrecht",
                "berichtigung", "einschränkung der verarbeitung",
                "datenübertragbarkeit", "widerruf"
            ],
            "rechtsgrundlagen": [
                "rechtsgrundlage", "artikel 6", "art. 6", "einwilligung",
                "vertragserfüllung", "rechtliche verpflichtung"
            ],
            "verantwortlicher": [
                "verantwortlich", "verantwortliche stelle", "kontaktdaten"
            ],
            "speicherdauer": [
                "speicherdauer", "aufbewahrungsfrist", "löschung"
            ],
            "beschwerde": [
                "beschwerderecht", "aufsichtsbehörde", "datenschutzbehörde"
            ]
        }
        
        # TMG Impressum Pflicht-Keywords
        self.impressum_keywords = {
            "anbieter": ["anbieter", "verantwortlich", "betreiber", "firma"],
            "adresse": ["adresse", "straße", "plz", "ort", "stadt"],
            "kontakt": ["telefon", "e-mail", "fax", "kontakt"],
            "register": [
                "handelsregister", "registergericht", "registernummer",
                "hrb", "hra", "vereinsregister"
            ],
            "ust_id": ["umsatzsteuer", "ust-id", "steuer"],
            "tmg": ["§ 5 tmg", "tmg", "telemediengesetz"]
        }
        
        # TTDSG Cookie-Keywords
        self.cookie_keywords = [
            "cookie", "einwilligung", "consent", "tracking",
            "speicherung", "ttdsg", "§ 25"
        ]
    
    def validate_datenschutz(self, text: str) -> LegalTextValidationResult:
        """
        Validiert Datenschutzerklärung auf DSGVO-Konformität
        """
        errors = []
        warnings = []
        missing_keywords = []
        text_lower = text.lower()
        
        # Check für kritische Pflicht-Abschnitte
        for category, keywords in self.dsgvo_keywords.items():
            found = False
            for keyword in keywords:
                if keyword in text_lower:
                    found = True
                    break
            
            if not found:
                if category in ["betroffenenrechte", "verantwortlicher", "rechtsgrundlagen"]:
                    errors.append(f"KRITISCH: Pflichtangabe fehlt - {category}")
                    missing_keywords.extend(keywords[:2])
                else:
                    warnings.append(f"Empfohlen: {category} sollte erwähnt werden")
                    missing_keywords.extend(keywords[:1])
        
        # Check Mindestlänge
        if len(text) < 500:
            errors.append("Datenschutzerklärung zu kurz (< 500 Zeichen)")
        
        # Check für Artikel-Nennungen
        art_count = len(re.findall(r'art(?:ikel)?\s*\d+', text_lower))
        if art_count == 0:
            warnings.append("Keine DSGVO-Artikel genannt - sollten zur Rechtssicherheit erwähnt werden")
        
        # Berechne Compliance-Score
        total_categories = len(self.dsgvo_keywords)
        found_categories = total_categories - len([k for k in missing_keywords if k in sum(self.dsgvo_keywords.values(), [])])
        compliance_score = found_categories / total_categories
        
        # Check Platzhalter
        placeholders = self._find_placeholders(text)
        if placeholders:
            warnings.append(f"{len(placeholders)} Platzhalter gefunden - müssen ersetzt werden")
        
        is_valid = len(errors) == 0
        
        return LegalTextValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metadata={
                "text_length": len(text),
                "articles_mentioned": art_count,
                "categories_checked": total_categories
            },
            missing_keywords=missing_keywords,
            placeholders_found=placeholders,
            legal_compliance_score=compliance_score
        )
    
    def validate_impressum(self, text: str) -> LegalTextValidationResult:
        """
        Validiert Impressum auf TMG § 5 Konformität
        """
        errors = []
        warnings = []
        missing_keywords = []
        text_lower = text.lower()
        
        # Check für Pflichtangaben
        for category, keywords in self.impressum_keywords.items():
            found = False
            for keyword in keywords:
                if keyword in text_lower:
                    found = True
                    break
            
            if not found:
                if category in ["anbieter", "adresse", "kontakt"]:
                    errors.append(f"KRITISCH: TMG-Pflichtangabe fehlt - {category}")
                    missing_keywords.extend(keywords[:2])
                else:
                    warnings.append(f"Möglicherweise fehlend: {category}")
                    missing_keywords.extend(keywords[:1])
        
        # Check ob § 5 TMG erwähnt wird
        if "§ 5 tmg" not in text_lower and "§5 tmg" not in text_lower:
            warnings.append("Hinweis: § 5 TMG sollte zur Rechtssicherheit genannt werden")
        
        # Check Mindestlänge
        if len(text) < 200:
            errors.append("Impressum zu kurz (< 200 Zeichen)")
        
        # Check Email-Format
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if not re.search(email_pattern, text):
            errors.append("Keine gültige E-Mail-Adresse gefunden")
        
        # Berechne Compliance-Score
        total_categories = len(self.impressum_keywords)
        found_categories = total_categories - len([k for k in missing_keywords if k in sum(self.impressum_keywords.values(), [])])
        compliance_score = found_categories / total_categories
        
        # Check Platzhalter
        placeholders = self._find_placeholders(text)
        if placeholders:
            warnings.append(f"{len(placeholders)} Platzhalter gefunden - müssen ersetzt werden")
        
        is_valid = len(errors) == 0
        
        return LegalTextValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metadata={
                "text_length": len(text),
                "has_email": bool(re.search(email_pattern, text)),
                "categories_checked": total_categories
            },
            missing_keywords=missing_keywords,
            placeholders_found=placeholders,
            legal_compliance_score=compliance_score
        )
    
    def _find_placeholders(self, text: str) -> List[str]:
        """
        Findet Platzhalter im Text
        """
        placeholders = []
        
        # Pattern für [PLATZHALTER]
        bracket_placeholders = re.findall(r'\[([A-ZÄÖÜ\s_-]+)\]', text)
        placeholders.extend([f"[{p}]" for p in bracket_placeholders])
        
        # Pattern für {PLATZHALTER}
        brace_placeholders = re.findall(r'\{([A-ZÄÖÜ\s_-]+)\}', text)
        placeholders.extend([f"{{{p}}}" for p in brace_placeholders])
        
        # Pattern für XXX, TODO, FIXME
        todo_patterns = re.findall(r'\b(XXX|TODO|FIXME|PLACEHOLDER|TBD)\b', text, re.IGNORECASE)
        placeholders.extend(todo_patterns)
        
        return list(set(placeholders))


# =============================================================================
# Complete Fix Validator
# =============================================================================

class FixValidator:
    """Haupt-Validator für alle Fix-Typen"""
    
    def __init__(self):
        self.schema_validator = SchemaValidator()
        self.code_validator = CodeValidator()
        self.legal_validator = LegalTextValidator()
    
    def validate_fix(
        self,
        fix_data: Dict[str, Any],
        fix_type: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Validiert Fix basierend auf Typ
        """
        all_errors = []
        all_warnings = []
        metadata = {"fix_type": fix_type}
        
        # 1. Schema-Validation
        if schema:
            schema_result = self.schema_validator.validate_against_schema(fix_data, schema)
            if not schema_result.is_valid:
                all_errors.extend(schema_result.errors)
                all_warnings.extend(schema_result.warnings)
                metadata.update(schema_result.metadata)
        
        # 2. Typ-spezifische Validation
        if fix_type == "code":
            code = fix_data.get("code", "")
            language = fix_data.get("language", "unknown")
            
            code_result = self.code_validator.validate_code(code, language)
            all_errors.extend(code_result.errors)
            all_warnings.extend(code_result.warnings)
            metadata.update(code_result.metadata)
            
            if code_result.security_issues:
                all_warnings.extend([f"Sicherheit: {issue}" for issue in code_result.security_issues])
        
        elif fix_type == "text":
            text_content = fix_data.get("text_content", "")
            text_type = fix_data.get("text_type", "generic")
            
            if text_type == "datenschutz":
                legal_result = self.legal_validator.validate_datenschutz(text_content)
            elif text_type == "impressum":
                legal_result = self.legal_validator.validate_impressum(text_content)
            else:
                # Generic text validation
                if len(text_content) < 50:
                    all_errors.append("Text zu kurz (< 50 Zeichen)")
                legal_result = None
            
            if legal_result:
                all_errors.extend(legal_result.errors)
                all_warnings.extend(legal_result.warnings)
                metadata.update(legal_result.metadata)
                metadata["legal_compliance_score"] = legal_result.legal_compliance_score
                metadata["placeholders_found"] = legal_result.placeholders_found
        
        elif fix_type == "widget":
            integration_code = fix_data.get("integration_code", "")
            
            if not integration_code:
                all_errors.append("Widget-Integration-Code fehlt")
            else:
                # Validate as HTML/JS
                if '<script' in integration_code:
                    html_result = self.code_validator.validate_code(integration_code, "html")
                    all_errors.extend(html_result.errors)
                    all_warnings.extend(html_result.warnings)
        
        elif fix_type == "guide":
            steps = fix_data.get("steps", [])
            
            if not steps or len(steps) == 0:
                all_errors.append("Guide muss mindestens einen Schritt enthalten")
            else:
                for i, step in enumerate(steps, 1):
                    if not step.get("title"):
                        all_errors.append(f"Schritt {i}: Titel fehlt")
                    if not step.get("description"):
                        all_errors.append(f"Schritt {i}: Beschreibung fehlt")
        
        # 3. Common validations
        if not fix_data.get("fix_id"):
            all_errors.append("fix_id fehlt")
        
        if not fix_data.get("title"):
            all_errors.append("title fehlt")
        
        is_valid = len(all_errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=all_errors,
            warnings=all_warnings,
            metadata=metadata
        )
    
    def validate_and_sanitize(
        self,
        fix_data: Dict[str, Any],
        fix_type: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], ValidationResult]:
        """
        Validiert und bereinigt Fix-Daten
        
        Returns:
            (sanitized_data, validation_result)
        """
        validation_result = self.validate_fix(fix_data, fix_type, schema)
        
        # Sanitize data
        sanitized = fix_data.copy()
        
        # Remove potentially dangerous content
        if fix_type == "code":
            code = sanitized.get("code", "")
            # Remove potentially dangerous patterns
            code = re.sub(r'<script[^>]*src\s*=\s*["\']javascript:[^"\']*["\']', '', code, flags=re.IGNORECASE)
            sanitized["code"] = code
        
        # Ensure required fields
        if not sanitized.get("fix_id"):
            sanitized["fix_id"] = "generated_" + str(hash(str(fix_data)))[:8]
        
        if not sanitized.get("estimated_time"):
            sanitized["estimated_time"] = "10-15 Minuten"
        
        if not sanitized.get("priority"):
            sanitized["priority"] = "medium"
        
        return sanitized, validation_result


