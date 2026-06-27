"""
Complyo AI Compliance Engine - Intelligente Website-Optimierung
KI-gesteuerter Prozess für non-tech User zur 100% Compliance
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
from enum import Enum

# ✅ FIX: Import centralized Score Calculator
from compliance_engine.score_calculator import ScoreCalculator

logger = logging.getLogger(__name__)

class UserExpertiseLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class ComplianceIssueType(Enum):
    DSGVO = "dsgvo"
    TTDSG = "ttdsg"
    ACCESSIBILITY = "accessibility"
    TECHNICAL = "technical"
    LEGAL = "legal"

@dataclass
class ComplianceIssue:
    """Einzelnes Compliance-Problem mit KI-generierten Lösungsvorschlägen"""
    id: str
    type: ComplianceIssueType
    severity: str  # "critical", "high", "medium", "low"
    title: str
    description: str
    affected_elements: List[str]
    fix_instructions: List[Dict[str, str]]  # KI-generierte Anleitungen
    estimated_time: int  # Minuten
    requires_developer: bool
    legal_risk_score: float

@dataclass
class OptimizationStep:
    """Ein Schritt im geführten Optimierungsprozess"""
    id: str
    title: str
    description: str
    instructions: List[str]
    validation_method: str
    estimated_time: int
    difficulty_level: str
    video_tutorial_url: Optional[str] = None
    code_snippet: Optional[str] = None
    
class AIComplianceEngine:
    """
    KI-Engine für intelligente Website-Compliance-Optimierung
    Führt non-tech User durch kompletten Optimierungsprozess
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # KI-Templates für verschiedene Problembereiche
        self.fix_templates = {
            ComplianceIssueType.DSGVO: {
                "missing_privacy_policy": {
                    "title": "Datenschutzerklärung fehlt",
                    "instructions": [
                        "Gehen Sie zu Ihrer Website-Verwaltung",
                        "Erstellen Sie eine neue Seite 'Datenschutz'", 
                        "Fügen Sie unseren generierten Datenschutztext ein",
                        "Verlinken Sie die Seite im Footer Ihrer Website"
                    ],
                    "code_template": '<a href="/datenschutz">Datenschutz</a>',
                    "time_estimate": 15
                },
                "missing_cookie_consent": {
                    "title": "Cookie-Consent fehlt",
                    "instructions": [
                        "Laden Sie unser Cookie-Consent-Script herunter",
                        "Fügen Sie den Code vor dem </body>-Tag ein",
                        "Konfigurieren Sie Ihre Cookie-Kategorien",
                        "Testen Sie das Cookie-Banner auf verschiedenen Geräten"
                    ],
                    "code_template": '<script src="complyo-cookies.js"></script>',
                    "time_estimate": 30
                }
            },
            ComplianceIssueType.ACCESSIBILITY: {
                "missing_alt_texts": {
                    "title": "Bilder ohne Alt-Text",
                    "instructions": [
                        "Öffnen Sie Ihre Website im Browser",
                        "Rechtsklick auf Bilder ohne Alt-Text",
                        "Wählen Sie 'Element untersuchen'",
                        "Fügen Sie alt='Beschreibung des Bildes' hinzu"
                    ],
                    "time_estimate": 5
                },
                "poor_contrast": {
                    "title": "Schlechter Farbkontrast",
                    "instructions": [
                        "Öffnen Sie Ihre CSS-Datei",
                        "Suchen Sie nach den markierten Farbwerten",
                        "Ersetzen Sie sie durch unsere empfohlenen Farben",
                        "Testen Sie die Lesbarkeit auf verschiedenen Geräten"
                    ],
                    "time_estimate": 20
                }
            }
        }
        
        # Rechtliche Updates und Trends
        self.legal_updates_db = [
            {
                "date": "2024-01-15",
                "title": "Neue TTDSG-Anforderungen für Analytics",
                "description": "Verschärfte Consent-Regelungen für Google Analytics und ähnliche Tools",
                "impact_level": "high",
                "affected_websites": "all"
            },
            {
                "date": "2024-02-01", 
                "title": "WCAG 2.2 wird Standard",
                "description": "Neue Accessibility-Anforderungen treten in Kraft",
                "impact_level": "medium",
                "affected_websites": "public_sector"
            }
        ]

    async def _get_knowledge_context(self, check_type: str, detected_issues: List = None) -> List[Dict]:
        """Retrieves relevant knowledge context from the Knowledge Vault for RAG enrichment."""
        try:
            from knowledge.knowledge_retriever import KnowledgeRetriever
            retriever = KnowledgeRetriever()
            issue_summary = ""
            if detected_issues:
                issue_summary = " ".join([
                    getattr(i, "title", "") for i in (detected_issues or [])[:5]
                ])
            query = f"{check_type} {issue_summary}".strip()
            context_docs = await retriever.retrieve(query, top_k=5)
            return context_docs
        except Exception as e:
            self.logger.warning(f"Knowledge context retrieval failed (non-critical): {e}")
            return []

    async def analyze_website_with_ai(self, website_url: str, user_level: UserExpertiseLevel) -> Dict[str, Any]:
        """
        Hauptfunktion: KI-Analyse der Website mit personalisierten Empfehlungen
        """
        try:
            self.logger.info(f"Starting AI analysis for {website_url} (User level: {user_level.value})")
            
            # 1. Technische Analyse durchführen
            technical_analysis = await self._perform_technical_analysis(website_url)
            
            # 2. KI-basierte Problemerkennung
            detected_issues = await self._ai_detect_compliance_issues(technical_analysis)
            
            # 3. Knowledge Vault RAG-Kontext abrufen
            knowledge_context = await self._get_knowledge_context(
                check_type="compliance website analysis",
                detected_issues=detected_issues,
            )
            
            # 4. Personalisierte Lösungsvorschläge generieren (mit Wissenskontext)
            personalized_fixes = await self._generate_personalized_fixes(
                detected_issues, user_level, knowledge_context=knowledge_context
            )
            
            # 5. Optimierungs-Roadmap erstellen
            optimization_roadmap = await self._create_optimization_roadmap(personalized_fixes, user_level)
            
            # 6. Risikobewertung
            risk_assessment = await self._calculate_compliance_risks(detected_issues)
            
            return {
                "analysis_id": f"ai_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "website_url": website_url,
                "user_level": user_level.value,
                "overall_score": self._calculate_overall_score(detected_issues),
                "detected_issues": [issue.__dict__ for issue in detected_issues],
                "optimization_roadmap": [step.__dict__ for step in optimization_roadmap],
                "risk_assessment": risk_assessment,
                "estimated_total_time": sum(step.estimated_time for step in optimization_roadmap),
                "priority_actions": self._get_priority_actions(detected_issues),
                "knowledge_context": knowledge_context[:3],
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"AI analysis failed for {website_url}: {e}")
            raise

    async def _perform_technical_analysis(self, website_url: str) -> Dict[str, Any]:
        """Führt technische Website-Analyse durch"""
        # Integration mit bestehendem Website-Scanner
        from .scanner import ComplianceScanner
        
        async with ComplianceScanner() as scanner:
            scan_result = await scanner.scan_website(website_url)
        
        # Erweitere um spezielle KI-relevante Daten
        technical_data = {
            "base_scan": scan_result,
            "dom_structure": await self._analyze_dom_structure(website_url),
            "accessibility_tree": await self._extract_accessibility_tree(website_url),
            "performance_metrics": await self._gather_performance_data(website_url),
            "security_headers": await self._check_security_headers(website_url)
        }
        
        return technical_data

    async def _ai_detect_compliance_issues(self, technical_analysis: Dict[str, Any]) -> List[ComplianceIssue]:
        """KI-basierte Erkennung von Compliance-Problemen"""
        issues = []
        base_scan = technical_analysis.get("base_scan", {})
        
        for issue_data in base_scan.get("issues", []):
            issue_type_map = {
                "datenschutz": ComplianceIssueType.DSGVO,
                "cookie-compliance": ComplianceIssueType.TTDSG,
                "barrierefreiheit": ComplianceIssueType.ACCESSIBILITY,
                "impressum": ComplianceIssueType.LEGAL,
                "sicherheit": ComplianceIssueType.TECHNICAL,
            }
            issue_type = issue_type_map.get(issue_data.get("category", "").lower(), ComplianceIssueType.TECHNICAL)

            issues.append(ComplianceIssue(
                id=f"{issue_type.value}_{issue_data.get('title', 'unknown').replace(' ', '_').lower()}",
                type=issue_type,
                severity=issue_data.get("severity", "low"),
                title=issue_data.get("title", "Unbekanntes Problem"),
                description=issue_data.get("description", ""),
                affected_elements=[], # Placeholder
                fix_instructions=[],  # Wird später gefüllt
                estimated_time=15, # Placeholder
                requires_developer=not issue_data.get("auto_fixable", False),
                legal_risk_score=issue_data.get("risk_euro", 0) / 5000.0 # Normalize risk
            ))

        # Erweitere Issues um KI-generierte Fix-Anleitungen
        for issue in issues:
            issue.fix_instructions = await self._generate_fix_instructions(issue)
        
        return issues

    async def _generate_personalized_fixes(
        self,
        issues: List[ComplianceIssue],
        user_level: UserExpertiseLevel,
        knowledge_context: List[Dict] = None,
    ) -> List[ComplianceIssue]:
        """Generiert personalisierte Fix-Anleitungen basierend auf User-Level und Knowledge-Vault-Kontext."""

        if knowledge_context:
            high_impact_updates = [k for k in knowledge_context if k.get("impact") == "high"]
            if high_impact_updates:
                self.logger.info(
                    f"Enriching fixes with {len(high_impact_updates)} high-impact knowledge items"
                )

        for issue in issues:
            # Passe Anleitungen an User-Level an
            if user_level == UserExpertiseLevel.BEGINNER:
                issue.fix_instructions = await self._simplify_instructions(issue.fix_instructions)
                issue.estimated_time = int(issue.estimated_time * 1.5)  # Mehr Zeit für Anfänger
                
            elif user_level == UserExpertiseLevel.ADVANCED:
                issue.fix_instructions = await self._add_technical_details(issue.fix_instructions)
                issue.estimated_time = int(issue.estimated_time * 0.7)  # Weniger Zeit für Experten
        
        return issues

    async def _create_optimization_roadmap(self, issues: List[ComplianceIssue], user_level: UserExpertiseLevel) -> List[OptimizationStep]:
        """Erstellt Schritt-für-Schritt Optimierungs-Roadmap"""
        
        # Sortiere Issues nach Priorität und Abhängigkeiten
        prioritized_issues = sorted(issues, key=lambda x: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3}[x.severity],
            -x.legal_risk_score
        ))
        
        roadmap = []
        step_counter = 1
        
        for issue in prioritized_issues:
            # Erstelle Optimierungsschritt für jedes Issue
            step = OptimizationStep(
                id=f"step_{step_counter}_{issue.id}",
                title=f"Schritt {step_counter}: {issue.title}",
                description=issue.description,
                instructions=await self._format_step_instructions(issue.fix_instructions, user_level),
                validation_method=await self._create_validation_method(issue),
                estimated_time=issue.estimated_time,
                difficulty_level=self._assess_difficulty(issue, user_level),
                video_tutorial_url=await self._get_tutorial_url(issue.type, user_level),
                code_snippet=await self._generate_code_snippet(issue)
            )
            
            roadmap.append(step)
            step_counter += 1
        
        return roadmap

    async def _generate_fix_instructions(self, issue: ComplianceIssue) -> List[Dict[str, str]]:
        """Generiert detaillierte Fix-Anleitungen für ein Issue"""
        
        # Hole Template aus Knowledge Base
        template_key = issue.id.replace(f"{issue.type.value}_", "")
        template = self.fix_templates.get(issue.type, {}).get(template_key, {})
        
        if template:
            instructions = []
            for i, instruction in enumerate(template.get("instructions", []), 1):
                instructions.append({
                    "step": i,
                    "instruction": instruction,
                    "type": "action",
                    "help_text": await self._generate_help_text(instruction)
                })
            return instructions
        
        # Fallback: Generiere generische Anleitung
        return [
            {
                "step": 1,
                "instruction": f"Beheben Sie das Problem: {issue.title}",
                "type": "generic",
                "help_text": issue.description
            }
        ]

    async def _simplify_instructions(self, instructions: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Vereinfacht Anleitungen für Anfänger"""
        simplified = []
        
        for instruction in instructions:
            # Entferne technische Begriffe, füge Screenshots hinzu
            simplified_text = instruction["instruction"]
            
            # Ersetze technische Begriffe
            replacements = {
                "</body>-Tag": "Ende Ihrer Website (kurz vor dem letzten </body>)",
                "CSS-Datei": "Style-Datei (meist style.css)",
                "alt=": "Bildbeschreibung mit alt=",
                "Element untersuchen": "Rechtsklick → Element untersuchen"
            }
            
            for tech_term, simple_term in replacements.items():
                simplified_text = simplified_text.replace(tech_term, simple_term)
            
            simplified.append({
                **instruction,
                "instruction": simplified_text,
                "additional_help": "📺 Video-Tutorial verfügbar",
                "screenshot_available": True
            })
        
        return simplified

    async def _add_technical_details(self, instructions: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Fügt technische Details für fortgeschrittene User hinzu"""
        enhanced = []
        
        for instruction in instructions:
            enhanced.append({
                **instruction,
                "technical_details": await self._get_technical_context(instruction),
                "api_reference": await self._get_api_reference(instruction),
                "best_practices": await self._get_best_practices(instruction)
            })
        
        return enhanced

    async def get_next_step_recommendation(self, user_id: str, current_progress: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Empfiehlt nächsten Optimierungsschritt basierend auf Fortschritt"""
        
        try:
            # Lade User-Roadmap aus Database
            roadmap = await self._get_user_roadmap(user_id)
            completed_steps = current_progress.get("completed_steps", [])
            
            # Finde nächsten offenen Schritt
            for step in roadmap:
                if step["id"] not in completed_steps:
                    # Prüfe Abhängigkeiten
                    if await self._check_step_dependencies(step, completed_steps):
                        return {
                            "next_step": step,
                            "progress_percentage": len(completed_steps) / len(roadmap) * 100,
                            "estimated_completion": await self._estimate_completion_time(roadmap, completed_steps),
                            "motivation_message": await self._generate_motivation_message(len(completed_steps), len(roadmap))
                        }
            
            # Alle Schritte abgeschlossen
            return {
                "status": "completed",
                "message": "🎉 Glückwunsch! Ihre Website ist jetzt 100% compliant!",
                "final_score": await self._calculate_final_score(user_id),
                "certificate_url": await self._generate_compliance_certificate(user_id)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting next step for user {user_id}: {e}")
            return None

    async def predict_compliance_risks(self, website_data: Dict[str, Any]) -> Dict[str, Any]:
        """Vorhersage zukünftiger Compliance-Risiken"""
        
        risks = {
            "immediate_risks": [],
            "upcoming_changes": [],
            "long_term_trends": [],
            "proactive_recommendations": []
        }
        
        # Immediate Risks basierend auf aktueller Website
        current_issues = website_data.get("detected_issues", [])
        for issue in current_issues:
            if issue["severity"] == "critical":
                risks["immediate_risks"].append({
                    "type": issue["type"],
                    "description": f"{issue['title']} - Sofortiges Handeln erforderlich",
                    "legal_consequence": await self._assess_legal_consequence(issue),
                    "deadline": "Sofort"
                })
        
        # Upcoming Legal Changes
        for update in self.legal_updates_db:
            if update["impact_level"] == "high":
                risks["upcoming_changes"].append({
                    "title": update["title"],
                    "description": update["description"],
                    "effective_date": update["date"],
                    "preparation_time": "2-4 Wochen",
                    "action_required": await self._determine_required_action(update, website_data)
                })
        
        # Long-term Trends
        risks["long_term_trends"] = [
            {
                "trend": "Verschärfung der Accessibility-Anforderungen",
                "timeline": "6-12 Monate", 
                "impact": "Alle Websites müssen WCAG 2.2 AA erfüllen",
                "preparation": "Jetzt mit Accessibility-Optimierung beginnen"
            },
            {
                "trend": "KI-Regulierung (AI Act)",
                "timeline": "12-24 Monate",
                "impact": "Websites mit KI-Features brauchen Transparenz-Hinweise",
                "preparation": "KI-Nutzung dokumentieren und Hinweise vorbereiten"
            }
        ]
        
        return risks

    async def generate_proactive_notifications(self, user_subscriptions: List[str]) -> List[Dict[str, Any]]:
        """Generiert proaktive Benachrichtigungen für User"""
        
        notifications = []
        
        for subscription_type in user_subscriptions:
            if subscription_type == "legal_updates":
                notifications.extend(await self._generate_legal_update_notifications())
            elif subscription_type == "compliance_tips":
                notifications.extend(await self._generate_weekly_tips())
            elif subscription_type == "industry_news":
                notifications.extend(await self._generate_industry_notifications())
        
        return notifications

    # Utility Methods
    async def _analyze_dom_structure(self, website_url: str) -> Dict[str, Any]:
        """Analysiert DOM-Struktur für AI-Insights"""
        # Implementierung für DOM-Analyse
        return {"elements_count": 0, "semantic_structure": "good"}

    async def _extract_accessibility_tree(self, website_url: str) -> Dict[str, Any]:
        """Extrahiert Accessibility-Tree"""
        return {"tree_depth": 5, "missing_labels": 3}

    async def _gather_performance_data(self, website_url: str) -> Dict[str, Any]:
        """Sammelt Performance-Daten"""
        return {"load_time": 2.3, "core_web_vitals": "good"}

    async def _check_security_headers(self, website_url: str) -> Dict[str, Any]:
        """Prüft Security Headers"""
        return {"csp_header": False, "hsts_header": True}

    def _calculate_overall_score(self, issues: List[ComplianceIssue]) -> float:
        """
        ✅ FIX v3.0: Gesamtscore = Mittelwert der 4 Säulen (eine Quelle!)
        Verhindert, dass Gesamt- und Säulen-Scores auseinanderlaufen.
        """
        return float(ScoreCalculator.compute(issues)["overall_score"])

    def _get_priority_actions(self, issues: List[ComplianceIssue]) -> List[str]:
        """Bestimmt prioritäre Aktionen"""
        critical_issues = [issue for issue in issues if issue.severity == "critical"]
        return [issue.title for issue in critical_issues[:3]]

    async def _format_step_instructions(self, instructions: List[Dict[str, str]], user_level: UserExpertiseLevel) -> List[str]:
        """Formatiert Schritt-Anweisungen für User-Level"""
        return [instr["instruction"] for instr in instructions]

    async def _create_validation_method(self, issue: ComplianceIssue) -> str:
        """Erstellt Validierungsmethode für Issue"""
        return f"Überprüfen Sie, ob {issue.title} behoben wurde"

    def _assess_difficulty(self, issue: ComplianceIssue, user_level: UserExpertiseLevel) -> str:
        """Bewertet Schwierigkeit basierend auf Issue und User-Level"""
        base_difficulty = {
            ComplianceIssueType.DSGVO: "medium",
            ComplianceIssueType.TTDSG: "high", 
            ComplianceIssueType.ACCESSIBILITY: "low"
        }.get(issue.type, "medium")
        
        if user_level == UserExpertiseLevel.BEGINNER:
            return "high" if base_difficulty in ["medium", "high"] else "medium"
        elif user_level == UserExpertiseLevel.ADVANCED:
            return "low" if base_difficulty in ["low", "medium"] else "medium"
        
        return base_difficulty

# Global AI Engine Instance
ai_compliance_engine = AIComplianceEngine()