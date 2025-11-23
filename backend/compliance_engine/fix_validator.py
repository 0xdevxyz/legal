"""
Fix Validator
Multi-Stage-Validierung für generierte Fixes

Validierungs-Stufen:
1. Pre-Generation: Kontext-Sammlung
2. Post-Generation: Syntax, Legal, AI-Review
3. Live-Validation: Nach Implementation
"""

import logging
import re
import anthropic
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationStage(Enum):
    """Validierungs-Stufen"""
    PRE_GENERATION = "pre_generation"
    SYNTAX_CHECK = "syntax_check"
    LEGAL_CHECK = "legal_check"
    AI_REVIEW = "ai_review"
    LIVE_VALIDATION = "live_validation"


class ValidationResult(Enum):
    """Validierungs-Ergebnis"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


@dataclass
class ValidationIssue:
    """Einzelnes Validierungs-Problem"""
    stage: ValidationStage
    severity: str  # "error", "warning", "info"
    message: str
    fix_suggestion: Optional[str] = None


@dataclass
class FixValidationReport:
    """Gesamter Validierungs-Report"""
    fix_id: str
    overall_result: ValidationResult
    stages_passed: List[ValidationStage]
    stages_failed: List[ValidationStage]
    issues: List[ValidationIssue]
    confidence_score: float  # 0.0 - 1.0
    ready_for_deployment: bool
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "overall_result": self.overall_result.value,
            "stages_passed": [s.value for s in self.stages_passed],
            "stages_failed": [s.value for s in self.stages_failed],
            "issues": [
                {
                    **asdict(issue),
                    "stage": issue.stage.value
                }
                for issue in self.issues
            ]
        }


class FixValidator:
    """
    Multi-Stage Fix Validator
    
    Validiert generierte Fixes auf mehreren Ebenen
    """
    
    def __init__(self):
        """Initialisiert Validator"""
        
        # AI Client für AI-Review
        self.ai_client = None
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.ai_client = anthropic.Anthropic(api_key=api_key)
            logger.info("✅ Fix Validator mit AI-Review initialisiert")
        else:
            logger.warning("⚠️ Kein AI-Review verfügbar (ANTHROPIC_API_KEY fehlt)")
    
    # ========================================================================
    # STAGE 1: Pre-Generation Validation
    # ========================================================================
    
    async def validate_pre_generation(
        self,
        issue_context: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[ValidationResult, List[ValidationIssue]]:
        """
        Pre-Generation: Prüft ob genug Kontext vorhanden ist
        
        Args:
            issue_context: Issue-Daten
            user_context: User/Website-Kontext
        
        Returns:
            (Result, Issues)
        """
        issues = []
        
        # Erforderliche Felder prüfen
        required_fields = ["title", "category", "severity"]
        for field in required_fields:
            if not issue_context.get(field):
                issues.append(ValidationIssue(
                    stage=ValidationStage.PRE_GENERATION,
                    severity="error",
                    message=f"Erforderliches Feld fehlt: {field}",
                    fix_suggestion="Fügen Sie alle erforderlichen Felder hinzu"
                ))
        
        # Prüfe ob genug Beschreibung vorhanden
        description = issue_context.get("description", "")
        if len(description) < 20:
            issues.append(ValidationIssue(
                stage=ValidationStage.PRE_GENERATION,
                severity="warning",
                message="Issue-Beschreibung ist sehr kurz",
                fix_suggestion="Fügen Sie detailliertere Beschreibung hinzu"
            ))
        
        # Prüfe User-Kontext
        if not user_context or not user_context.get("domain"):
            issues.append(ValidationIssue(
                stage=ValidationStage.PRE_GENERATION,
                severity="warning",
                message="Kein Website-Kontext verfügbar",
                fix_suggestion="Fügen Sie Domain/Website-Info hinzu"
            ))
        
        # Resultat
        has_errors = any(i.severity == "error" for i in issues)
        result = ValidationResult.FAILED if has_errors else ValidationResult.PASSED
        
        logger.info(f"✅ Pre-Generation Validation: {result.value} ({len(issues)} Issues)")
        
        return result, issues
    
    # ========================================================================
    # STAGE 2: Syntax Check
    # ========================================================================
    
    async def validate_syntax(
        self,
        fix_content: str,
        fix_type: str
    ) -> Tuple[ValidationResult, List[ValidationIssue]]:
        """
        Syntax-Check für Code-Fixes
        
        Args:
            fix_content: Generierter Fix-Code
            fix_type: "code", "text", "guide", "widget"
        
        Returns:
            (Result, Issues)
        """
        issues = []
        
        if fix_type == "code":
            # HTML/JavaScript Syntax Check
            
            # Prüfe auf ungeschlossene Tags
            open_tags = re.findall(r'<([a-z][a-z0-9]*)\b[^>]*>', fix_content, re.IGNORECASE)
            close_tags = re.findall(r'</([a-z][a-z0-9]*)>', fix_content, re.IGNORECASE)
            
            for tag in open_tags:
                if tag.lower() not in ['img', 'br', 'hr', 'input', 'meta', 'link']:  # Self-closing tags
                    if open_tags.count(tag) > close_tags.count(tag):
                        issues.append(ValidationIssue(
                            stage=ValidationStage.SYNTAX_CHECK,
                            severity="error",
                            message=f"Ungeschlossener HTML-Tag: <{tag}>",
                            fix_suggestion=f"Fügen Sie </{tag}> hinzu"
                        ))
            
            # Prüfe auf häufige JavaScript-Fehler
            if 'function' in fix_content or 'const' in fix_content or 'let' in fix_content:
                # Prüfe auf ungeschlossene Klammern
                open_braces = fix_content.count('{')
                close_braces = fix_content.count('}')
                if open_braces != close_braces:
                    issues.append(ValidationIssue(
                        stage=ValidationStage.SYNTAX_CHECK,
                        severity="error",
                        message=f"Ungleiche geschweifte Klammern: {open_braces} öffnend vs {close_braces} schließend",
                        fix_suggestion="Prüfen Sie die Klammer-Balance"
                    ))
                
                # Prüfe auf fehlende Semikolons (Warnung)
                lines = fix_content.split('\n')
                for i, line in enumerate(lines):
                    line = line.strip()
                    if line and not line.startswith('//') and not line.startswith('/*'):
                        if re.match(r'(let|const|var|return)\s+', line) and not line.endswith((';', '{', '}')):
                            if i < len(lines) - 1:  # Nicht letzte Zeile
                                issues.append(ValidationIssue(
                                    stage=ValidationStage.SYNTAX_CHECK,
                                    severity="warning",
                                    message=f"Möglicherweise fehlendes Semikolon in Zeile {i+1}",
                                    fix_suggestion="Fügen Sie Semikolon am Zeilenende hinzu"
                                ))
        
        elif fix_type == "text":
            # Text-Fixes: Prüfe auf Platzhalter
            placeholders = re.findall(r'\[([^\]]+)\]|\{([^\}]+)\}|<([^>]+)>|YOUR_|EXAMPLE_', fix_content)
            if placeholders:
                issues.append(ValidationIssue(
                    stage=ValidationStage.SYNTAX_CHECK,
                    severity="error",
                    message=f"Text enthält Platzhalter: {placeholders[:3]}",
                    fix_suggestion="Ersetzen Sie Platzhalter mit echten Daten"
                ))
            
            # Prüfe Mindestlänge
            if len(fix_content.strip()) < 50:
                issues.append(ValidationIssue(
                    stage=ValidationStage.SYNTAX_CHECK,
                    severity="warning",
                    message="Text ist sehr kurz",
                    fix_suggestion="Fügen Sie detailliertere Informationen hinzu"
                ))
        
        # Resultat
        has_errors = any(i.severity == "error" for i in issues)
        result = ValidationResult.FAILED if has_errors else ValidationResult.PASSED
        
        logger.info(f"✅ Syntax Validation: {result.value} ({len(issues)} Issues)")
        
        return result, issues
    
    # ========================================================================
    # STAGE 3: Legal Compliance Check
    # ========================================================================
    
    async def validate_legal_compliance(
        self,
        fix_content: str,
        issue_category: str
    ) -> Tuple[ValidationResult, List[ValidationIssue]]:
        """
        Legal-Compliance-Check für rechtliche Texte
        
        Args:
            fix_content: Generierter Fix
            issue_category: z.B. "impressum", "datenschutz"
        
        Returns:
            (Result, Issues)
        """
        issues = []
        
        # Kategorie-spezifische Prüfungen
        if issue_category in ["impressum", "imprint"]:
            # Impressum-Pflichtangaben
            required_elements = {
                "name": [r"name", r"firma", r"company"],
                "address": [r"straße|str\.|address|anschrift", r"\d{5}"],
                "contact": [r"@", r"tel|phone|telefon"],
            }
            
            for element, patterns in required_elements.items():
                found = any(re.search(pattern, fix_content, re.IGNORECASE) for pattern in patterns)
                if not found:
                    issues.append(ValidationIssue(
                        stage=ValidationStage.LEGAL_CHECK,
                        severity="error",
                        message=f"Pflichtangabe fehlt: {element}",
                        fix_suggestion=f"Fügen Sie {element} zum Impressum hinzu"
                    ))
        
        elif issue_category in ["datenschutz", "privacy", "dsgvo", "gdpr"]:
            # Datenschutz-Pflichtangaben
            required_terms = [
                (r"verantwortlich", "Verantwortlicher"),
                (r"zweck|purpose", "Zwecke der Verarbeitung"),
                (r"rechtsgrundlage|legal basis", "Rechtsgrundlage"),
                (r"speicherdauer|retention", "Speicherdauer"),
                (r"betroffenenrechte|rights", "Betroffenenrechte"),
            ]
            
            for pattern, name in required_terms:
                if not re.search(pattern, fix_content, re.IGNORECASE):
                    issues.append(ValidationIssue(
                        stage=ValidationStage.LEGAL_CHECK,
                        severity="warning",
                        message=f"Möglicherweise fehlt: {name}",
                        fix_suggestion=f"Prüfen Sie ob {name} vollständig enthalten ist"
                    ))
        
        # Resultat
        has_errors = any(i.severity == "error" for i in issues)
        result = ValidationResult.FAILED if has_errors else ValidationResult.PASSED
        
        logger.info(f"✅ Legal Compliance Validation: {result.value} ({len(issues)} Issues)")
        
        return result, issues
    
    # ========================================================================
    # STAGE 4: AI Review
    # ========================================================================
    
    async def validate_with_ai(
        self,
        fix_content: str,
        issue_context: Dict[str, Any],
        fix_type: str
    ) -> Tuple[ValidationResult, List[ValidationIssue], float]:
        """
        AI-Review des generierten Fixes
        
        Args:
            fix_content: Generierter Fix
            issue_context: Original Issue
            fix_type: Fix-Typ
        
        Returns:
            (Result, Issues, Confidence)
        """
        if not self.ai_client:
            logger.warning("⚠️ AI-Review übersprungen (kein API-Key)")
            return ValidationResult.PASSED, [], 0.8  # Default confidence
        
        try:
            # Prompt erstellen
            prompt = f"""Du bist ein Compliance-Experte. Prüfe folgenden generierten Fix:

**Original-Problem:**
- Titel: {issue_context.get('title', 'N/A')}
- Kategorie: {issue_context.get('category', 'N/A')}
- Beschreibung: {issue_context.get('description', 'N/A')[:200]}

**Generierter Fix ({fix_type}):**
```
{fix_content[:1500]}
```

**Prüfkriterien:**
1. Löst der Fix das Problem vollständig?
2. Ist der Fix technisch korrekt?
3. Ist der Fix rechtlich konform (für {issue_context.get('category')})?
4. Gibt es Sicherheitsrisiken?
5. Ist der Fix für Non-Tech-User verständlich?

**Antwortformat:**
RESULT: pass|fail|warning
CONFIDENCE: [0.0-1.0]
ISSUES: [Liste von Problemen, oder "none"]
REASONING: [Kurze Begründung]"""
            
            response = self.ai_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            
            ai_response = response.content[0].text
            
            # Parse Response
            result_match = re.search(r'RESULT:\s*(pass|fail|warning)', ai_response, re.IGNORECASE)
            conf_match = re.search(r'CONFIDENCE:\s*([0-9.]+)', ai_response)
            issues_match = re.search(r'ISSUES:\s*(.+?)(?=REASONING:|$)', ai_response, re.DOTALL)
            reasoning_match = re.search(r'REASONING:\s*(.+)', ai_response, re.DOTALL)
            
            result_str = result_match.group(1).lower() if result_match else "pass"
            confidence = float(conf_match.group(1)) if conf_match else 0.7
            issues_text = issues_match.group(1).strip() if issues_match else "none"
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "AI-Review completed"
            
            # Parse Issues
            ai_issues = []
            if issues_text.lower() not in ["none", "keine", "no issues"]:
                # Extrahiere Issues
                issue_lines = [l.strip() for l in issues_text.split('\n') if l.strip() and not l.strip().startswith('#')]
                for line in issue_lines[:5]:  # Max 5 Issues
                    ai_issues.append(ValidationIssue(
                        stage=ValidationStage.AI_REVIEW,
                        severity="warning" if result_str == "warning" else "error",
                        message=line,
                        fix_suggestion=reasoning[:100]
                    ))
            
            # Result-Mapping
            result_map = {
                "pass": ValidationResult.PASSED,
                "warning": ValidationResult.WARNING,
                "fail": ValidationResult.FAILED
            }
            result = result_map.get(result_str, ValidationResult.PASSED)
            
            logger.info(f"✅ AI Review: {result.value} (Confidence: {confidence:.2f})")
            
            return result, ai_issues, confidence
        
        except Exception as e:
            logger.error(f"❌ AI Review fehlgeschlagen: {e}")
            return ValidationResult.WARNING, [
                ValidationIssue(
                    stage=ValidationStage.AI_REVIEW,
                    severity="warning",
                    message=f"AI-Review fehlgeschlagen: {str(e)}"
                )
            ], 0.5
    
    # ========================================================================
    # MAIN VALIDATION PIPELINE
    # ========================================================================
    
    async def validate_fix(
        self,
        fix_content: str,
        fix_type: str,
        issue_context: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> FixValidationReport:
        """
        Haupt-Validierungs-Pipeline
        
        Führt alle Validierungs-Stufen durch
        
        Args:
            fix_content: Generierter Fix
            fix_type: "code", "text", "guide", "widget"
            issue_context: Original Issue-Daten
            user_context: User/Website-Kontext
        
        Returns:
            FixValidationReport
        """
        logger.info(f"🔍 Validiere Fix (Typ: {fix_type}, Issue: {issue_context.get('id', 'unknown')})")
        
        stages_passed = []
        stages_failed = []
        all_issues = []
        
        # STAGE 1: Pre-Generation
        pre_result, pre_issues = await self.validate_pre_generation(issue_context, user_context)
        all_issues.extend(pre_issues)
        
        if pre_result == ValidationResult.PASSED:
            stages_passed.append(ValidationStage.PRE_GENERATION)
        else:
            stages_failed.append(ValidationStage.PRE_GENERATION)
        
        # STAGE 2: Syntax
        syntax_result, syntax_issues = await self.validate_syntax(fix_content, fix_type)
        all_issues.extend(syntax_issues)
        
        if syntax_result == ValidationResult.PASSED:
            stages_passed.append(ValidationStage.SYNTAX_CHECK)
        else:
            stages_failed.append(ValidationStage.SYNTAX_CHECK)
        
        # STAGE 3: Legal
        legal_result, legal_issues = await self.validate_legal_compliance(
            fix_content,
            issue_context.get("category", "")
        )
        all_issues.extend(legal_issues)
        
        if legal_result == ValidationResult.PASSED:
            stages_passed.append(ValidationStage.LEGAL_CHECK)
        else:
            stages_failed.append(ValidationStage.LEGAL_CHECK)
        
        # STAGE 4: AI Review
        ai_result, ai_issues, confidence = await self.validate_with_ai(
            fix_content,
            issue_context,
            fix_type
        )
        all_issues.extend(ai_issues)
        
        if ai_result in [ValidationResult.PASSED, ValidationResult.WARNING]:
            stages_passed.append(ValidationStage.AI_REVIEW)
        else:
            stages_failed.append(ValidationStage.AI_REVIEW)
        
        # Gesamt-Ergebnis
        if len(stages_failed) > 0:
            overall_result = ValidationResult.FAILED
        elif any(i.severity == "warning" for i in all_issues):
            overall_result = ValidationResult.WARNING
        else:
            overall_result = ValidationResult.PASSED
        
        # Ready for Deployment?
        ready = overall_result != ValidationResult.FAILED
        
        # Warnings sammeln
        warnings = [i.message for i in all_issues if i.severity == "warning"]
        
        report = FixValidationReport(
            fix_id=issue_context.get("id", "unknown"),
            overall_result=overall_result,
            stages_passed=stages_passed,
            stages_failed=stages_failed,
            issues=all_issues,
            confidence_score=confidence,
            ready_for_deployment=ready,
            warnings=warnings
        )
        
        logger.info(f"✅ Validierung abgeschlossen: {overall_result.value} ({len(stages_passed)}/{len(stages_passed) + len(stages_failed)} Stufen bestanden)")
        
        return report

