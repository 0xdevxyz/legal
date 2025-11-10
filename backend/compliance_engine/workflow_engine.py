"""
Complyo Workflow Engine - Complete User Journey Orchestration
Seamless end-to-end process from registration to 100% compliance
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import json
import uuid

logger = logging.getLogger(__name__)

class WorkflowStage(Enum):
    ONBOARDING = "onboarding"
    WEBSITE_ANALYSIS = "website_analysis" 
    GUIDED_OPTIMIZATION = "guided_optimization"
    COMPLIANCE_VERIFICATION = "compliance_verification"
    MAINTENANCE = "maintenance"

class UserSkillLevel(Enum):
    ABSOLUTE_BEGINNER = "absolute_beginner"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

@dataclass
class WorkflowStep:
    """Individual step in the workflow"""
    id: str
    stage: WorkflowStage
    title: str
    description: str
    instructions: List[str]
    validation_method: str
    estimated_time_minutes: int
    requires_technical_knowledge: bool
    dependencies: List[str]
    success_criteria: Dict[str, Any]
    failure_recovery: List[str]
    visual_aids: List[str]  # Screenshots, videos, etc.

@dataclass
class UserJourney:
    """Complete user journey tracking"""
    user_id: str
    website_url: str
    skill_level: UserSkillLevel
    current_stage: WorkflowStage
    current_step: Optional[str]
    completed_steps: List[str]
    failed_attempts: Dict[str, int]
    start_date: datetime
    estimated_completion: datetime
    actual_completion: Optional[datetime]
    satisfaction_score: Optional[float]
    support_interactions: List[Dict[str, Any]]

class WorkflowEngine:
    """
    Orchestrates the complete user journey from registration to compliance
    Provides seamless, guided experience for non-tech users
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Load workflow templates
        self.workflow_templates = self._initialize_workflow_templates()

    def _initialize_workflow_templates(self) -> Dict[WorkflowStage, List[WorkflowStep]]:
        """Initialize predefined workflow templates"""
        
        return {
            WorkflowStage.ONBOARDING: [
                WorkflowStep(
                    id="welcome_tour",
                    stage=WorkflowStage.ONBOARDING,
                    title="Willkommen bei Complyo! 👋",
                    description="Lernen Sie in 2 Minuten, wie Complyo Ihre Website rechtskonform macht",
                    instructions=[
                        "Schauen Sie sich das Willkommensvideo an",
                        "Verstehen Sie, was Complyo für Sie tun kann",
                        "Lernen Sie die wichtigsten Features kennen"
                    ],
                    validation_method="video_completion",
                    estimated_time_minutes=3,
                    requires_technical_knowledge=False,
                    dependencies=[],
                    success_criteria={"video_watched": True, "quiz_completed": True},
                    failure_recovery=["Wiederholen Sie das Video", "Kontaktieren Sie den Support"],
                    visual_aids=["welcome_video.mp4", "feature_overview.png"]
                ),
                WorkflowStep(
                    id="skill_assessment",
                    stage=WorkflowStage.ONBOARDING,
                    title="Ihre Erfahrung einschätzen 📊",
                    description="Kurzer Fragebogen zur Bestimmung Ihres Wissenstands",
                    instructions=[
                        "Beantworten Sie 5 einfache Fragen",
                        "Seien Sie ehrlich - das hilft uns, Sie optimal zu unterstützen",
                        "Die Einschätzung dauert nur 2 Minuten"
                    ],
                    validation_method="questionnaire_completion",
                    estimated_time_minutes=5,
                    requires_technical_knowledge=False,
                    dependencies=["welcome_tour"],
                    success_criteria={"questions_answered": 5, "skill_determined": True},
                    failure_recovery=["Fragen erneut beantworten", "Support um Hilfe bitten"],
                    visual_aids=["questionnaire_guide.png"]
                ),
                WorkflowStep(
                    id="website_connection",
                    stage=WorkflowStage.ONBOARDING,
                    title="Website verbinden 🔗",
                    description="Verbinden Sie Ihre Website mit Complyo",
                    instructions=[
                        "Geben Sie Ihre Website-URL ein",
                        "Wir prüfen die Erreichbarkeit",
                        "Erste Analyse wird gestartet"
                    ],
                    validation_method="website_accessibility_check",
                    estimated_time_minutes=2,
                    requires_technical_knowledge=False,
                    dependencies=["skill_assessment"],
                    success_criteria={"website_accessible": True, "url_valid": True},
                    failure_recovery=["URL überprüfen", "DNS-Einstellungen kontrollieren", "Support kontaktieren"],
                    visual_aids=["url_input_guide.png", "connectivity_check.gif"]
                )
            ],
            
            WorkflowStage.WEBSITE_ANALYSIS: [
                WorkflowStep(
                    id="ai_website_scan",
                    stage=WorkflowStage.WEBSITE_ANALYSIS,
                    title="KI-Analyse läuft 🤖",
                    description="Unsere KI analysiert Ihre Website auf Compliance-Probleme",
                    instructions=[
                        "Die KI prüft alle Seiten Ihrer Website",
                        "DSGVO, TMG, TTDSG und Barrierefreiheit werden überprüft",
                        "Analyse dauert 2-5 Minuten je nach Website-Größe"
                    ],
                    validation_method="ai_scan_completion",
                    estimated_time_minutes=10,
                    requires_technical_knowledge=False,
                    dependencies=["website_connection"],
                    success_criteria={"scan_completed": True, "issues_identified": True},
                    failure_recovery=["Scan wiederholen", "Website-Zugriff prüfen", "Support informieren"],
                    visual_aids=["ai_analysis_demo.mp4", "scan_progress.gif"]
                ),
                WorkflowStep(
                    id="results_explanation",
                    stage=WorkflowStage.WEBSITE_ANALYSIS,
                    title="Ergebnisse verstehen 📋",
                    description="Wir erklären die gefundenen Probleme verständlich",
                    instructions=[
                        "Schauen Sie sich den übersichtlichen Report an",
                        "Verstehen Sie jeden gefundenen Compliance-Verstoß",
                        "Priorisierung nach Wichtigkeit und Risiko"
                    ],
                    validation_method="manual_completion",
                    estimated_time_minutes=5,
                    requires_technical_knowledge=False,
                    dependencies=["ai_website_scan"],
                    success_criteria={"report_reviewed": True, "priorities_understood": True},
                    failure_recovery=["Report erneut anschauen", "Begriffe nachschlagen", "Support um Erklärung bitten"],
                    visual_aids=["report_walkthrough.mp4", "priority_explanation.png"]
                )
            ],
            
            WorkflowStage.GUIDED_OPTIMIZATION: [
                WorkflowStep(
                    id="critical_fixes_implementation",
                    stage=WorkflowStage.GUIDED_OPTIMIZATION,
                    title="Kritische Probleme beheben 🚨",
                    description="Schritt-für-Schritt Lösung der wichtigsten Compliance-Probleme",
                    instructions=[
                        "Befolgen Sie die detaillierten Anleitungen",
                        "Kopieren Sie die bereitgestellten Code-Snippets",
                        "Testen Sie jede Änderung sofort"
                    ],
                    validation_method="live_website_verification",
                    estimated_time_minutes=25,
                    requires_technical_knowledge=True,
                    dependencies=["results_explanation"],
                    success_criteria={"critical_issues_fixed": True, "compliance_improved": True},
                    failure_recovery=["Änderungen rückgängig machen", "Schritt wiederholen", "Experten-Support anfordern"],
                    visual_aids=["step_by_step_guide.mp4", "code_examples.png", "before_after.gif"]
                ),
                WorkflowStep(
                    id="accessibility_framework_integration",
                    stage=WorkflowStage.GUIDED_OPTIMIZATION,
                    title="Barrierefreiheit einbauen ♿",
                    description="Integration des Accessibility-Frameworks für dauerhafte Barrierefreiheit",
                    instructions=[
                        "Installieren Sie unser Accessibility-Framework",
                        "Konfigurieren Sie die Einstellungen für Ihre Website",
                        "Testen Sie die neuen Accessibility-Features"
                    ],
                    validation_method="accessibility_framework_detection",
                    estimated_time_minutes=15,
                    requires_technical_knowledge=True,
                    dependencies=["critical_fixes_implementation"],
                    success_criteria={"framework_installed": True, "accessibility_active": True},
                    failure_recovery=["Installation wiederholen", "Kompatibilität prüfen", "Technischen Support kontaktieren"],
                    visual_aids=["framework_installation.mp4", "configuration_guide.png", "accessibility_demo.gif"]
                ),
                WorkflowStep(
                    id="content_optimization",
                    stage=WorkflowStage.GUIDED_OPTIMIZATION,
                    title="Inhalte optimieren 📝",
                    description="Ihre Texte und Inhalte rechtssicher gestalten",
                    instructions=[
                        "Überprüfen Sie Datenschutzerklärung und Impressum",
                        "Optimieren Sie Cookie-Banner und Einwilligungen",
                        "Stellen Sie rechtssichere Formulare sicher"
                    ],
                    validation_method="content_compliance_check",
                    estimated_time_minutes=5,
                    requires_technical_knowledge=False,
                    dependencies=["accessibility_framework_integration"],
                    success_criteria={"content_compliant": True, "legal_texts_updated": True},
                    failure_recovery=["Texte überarbeiten", "Vorlagen verwenden", "Rechtsberatung einholen"],
                    visual_aids=["content_checklist.pdf", "template_examples.png", "legal_requirements.mp4"]
                )
            ],
            
            WorkflowStage.COMPLIANCE_VERIFICATION: [
                WorkflowStep(
                    id="final_compliance_scan",
                    stage=WorkflowStage.COMPLIANCE_VERIFICATION,
                    title="Finale Prüfung 🔍",
                    description="Abschließende Compliance-Prüfung Ihrer optimierten Website",
                    instructions=[
                        "Automatische Überprüfung aller Verbesserungen",
                        "Validierung der Compliance-Standards",
                        "Erstellung des finalen Compliance-Reports"
                    ],
                    validation_method="final_scan_completion",
                    estimated_time_minutes=8,
                    requires_technical_knowledge=False,
                    dependencies=["content_optimization"],
                    success_criteria={"final_score": 95, "all_critical_fixed": True},
                    failure_recovery=["Nachbesserungen durchführen", "Problematische Bereiche überprüfen", "Support konsultieren"],
                    visual_aids=["final_scan_demo.mp4", "compliance_score.png"]
                ),
                WorkflowStep(
                    id="certificate_generation",
                    stage=WorkflowStage.COMPLIANCE_VERIFICATION,
                    title="Zertifikat erstellen 🏆",
                    description="Offizielles Compliance-Zertifikat für Ihre Website",
                    instructions=[
                        "Generierung des personalisierten Zertifikats",
                        "Download als PDF für Ihre Unterlagen",
                        "Integration in Ihre Website möglich"
                    ],
                    validation_method="certificate_generation",
                    estimated_time_minutes=2,
                    requires_technical_knowledge=False,
                    dependencies=["final_compliance_scan"],
                    success_criteria={"certificate_created": True, "download_available": True},
                    failure_recovery=["Zertifikat erneut generieren", "Daten überprüfen", "Support kontaktieren"],
                    visual_aids=["certificate_preview.png", "integration_guide.pdf"]
                )
            ],
            
            WorkflowStage.MAINTENANCE: [
                WorkflowStep(
                    id="monitoring_setup",
                    stage=WorkflowStage.MAINTENANCE,
                    title="Überwachung aktivieren 📡",
                    description="24/7 Monitoring für dauerhafte Compliance einrichten",
                    instructions=[
                        "Aktivieren Sie die kontinuierliche Überwachung",
                        "Konfigurieren Sie Benachrichtigungseinstellungen",
                        "Legen Sie Prüfintervalle fest"
                    ],
                    validation_method="monitoring_setup",
                    estimated_time_minutes=3,
                    requires_technical_knowledge=False,
                    dependencies=["certificate_generation"],
                    success_criteria={"monitoring_active": True, "alerts_configured": True},
                    failure_recovery=["Einstellungen prüfen", "Konfiguration wiederholen", "Support beauftragen"],
                    visual_aids=["monitoring_dashboard.png", "alert_settings.mp4"]
                ),
                WorkflowStep(
                    id="legal_updates_subscription",
                    stage=WorkflowStage.MAINTENANCE,
                    title="Rechts-Updates abonnieren 📚",
                    description="Automatische Information über neue Gesetze und Vorschriften",
                    instructions=[
                        "Abonnieren Sie Updates zu Rechtsänderungen",
                        "Erhalten Sie proaktive Handlungsempfehlungen",
                        "Bleiben Sie immer auf dem neuesten Stand"
                    ],
                    validation_method="subscription_confirmation",
                    estimated_time_minutes=1,
                    requires_technical_knowledge=False,
                    dependencies=["monitoring_setup"],
                    success_criteria={"subscription_active": True, "preferences_set": True},
                    failure_recovery=["Subscription erneuern", "E-Mail-Einstellungen prüfen", "Support informieren"],
                    visual_aids=["legal_updates_example.png", "notification_settings.mp4"]
                ),
                WorkflowStep(
                    id="support_channel_setup",
                    stage=WorkflowStage.MAINTENANCE,
                    title="Support-Kanäle einrichten 🤝",
                    description="Direkten Zugang zu Experten-Support sicherstellen",
                    instructions=[
                        "Richten Sie bevorzugte Support-Kanäle ein",
                        "Definieren Sie Prioritäten für verschiedene Problem-Typen",
                        "Testen Sie die Erreichbarkeit des Support-Teams"
                    ],
                    validation_method="support_test",
                    estimated_time_minutes=1,
                    requires_technical_knowledge=False,
                    dependencies=["legal_updates_subscription"],
                    success_criteria={"support_configured": True, "contact_verified": True},
                    failure_recovery=["Kontaktdaten aktualisieren", "Support-Test wiederholen", "Alternative Kanäle nutzen"],
                    visual_aids=["support_channels.png", "contact_options.mp4"]
                )
            ]
        }

    async def start_user_journey(self, user_id: str, website_url: str, skill_level: UserSkillLevel) -> UserJourney:
        """Start a new user journey"""
        
        # Create new journey
        journey = UserJourney(
            user_id=user_id,
            website_url=website_url,
            skill_level=skill_level,
            current_stage=WorkflowStage.ONBOARDING,
            current_step="welcome_tour",
            completed_steps=[],
            failed_attempts={},
            start_date=datetime.now(),
            estimated_completion=datetime.now() + timedelta(days=7),
            actual_completion=None,
            satisfaction_score=None,
            support_interactions=[]
        )
        
        # Adjust estimated completion based on skill level
        if skill_level == UserSkillLevel.ABSOLUTE_BEGINNER:
            journey.estimated_completion = datetime.now() + timedelta(days=14)
        elif skill_level == UserSkillLevel.ADVANCED:
            journey.estimated_completion = datetime.now() + timedelta(days=3)
        
        self.logger.info(f"Started user journey for {user_id} with skill level {skill_level.value}")
        
        return journey

    async def get_current_step(self, user_id: str) -> Optional[WorkflowStep]:
        """Get the current step for a user"""
        
        # Use workflow integration for database operations
        from .workflow_integration import workflow_integration
        journey = await workflow_integration.load_user_journey(user_id)
        
        if not journey or not journey.current_step:
            return None
        
        # Find current step in workflow templates
        current_stage_steps = self.workflow_templates.get(journey.current_stage, [])
        
        for step in current_stage_steps:
            if step.id == journey.current_step:
                # Personalize step based on skill level
                return await self._personalize_step(step, journey.skill_level)
        
        return None

    async def complete_step(self, user_id: str, step_id: str, validation_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Mark a step as completed and move to next step"""
        
        # Use workflow integration for database operations
        from .workflow_integration import workflow_integration
        journey = await workflow_integration.load_user_journey(user_id)
        
        if not journey:
            raise ValueError("User journey not found")
        
        # Find current step
        current_step = None
        for stage_steps in self.workflow_templates.values():
            for step in stage_steps:
                if step.id == step_id:
                    current_step = step
                    break
            if current_step:
                break
        
        if not current_step:
            raise ValueError(f"Step {step_id} not found")
        
        # Validate step completion using workflow integration
        validation_success, validation_message = await workflow_integration.validate_step_completion(
            current_step, validation_data or {}, user_id
        )
        
        if validation_success:
            # Mark step as completed
            journey.completed_steps.append(step_id)
            
            # Determine next step
            next_step = await self._determine_next_step(journey)
            journey.current_step = next_step.id if next_step else None
            
            # Update stage if necessary
            if next_step and next_step.stage != journey.current_stage:
                journey.current_stage = next_step.stage
            
            # Save journey
            await workflow_integration.save_user_journey(journey)
            
            # Prepare response
            response = {
                "status": "completed",
                "completed_step": step_id,
                "next_step": next_step.__dict__ if next_step else None,
                "progress_percentage": len(journey.completed_steps) / self._get_total_steps_count() * 100,
                "congratulation_message": self._generate_congratulation_message(journey),
                "estimated_time_remaining": self._calculate_remaining_time(journey)
            }
            
            # Check if journey is complete
            if not next_step:
                response["journey_completed"] = True
                response["celebration_message"] = "🎉 Herzlichen Glückwunsch! Ihre Website ist jetzt 100% compliant!"
                journey.actual_completion = datetime.now()
                await workflow_integration.save_user_journey(journey)
            
            return response
        
        else:
            # Handle validation failure
            journey.failed_attempts[step_id] = journey.failed_attempts.get(step_id, 0) + 1
            await workflow_integration.save_user_journey(journey)
            
            return {
                "status": "validation_failed",
                "step_id": step_id,
                "retry_count": journey.failed_attempts[step_id],
                "help_resources": current_step.failure_recovery,
                "support_available": journey.failed_attempts[step_id] >= 2,
                "validation_message": validation_message
            }

    async def _personalize_step(self, step: WorkflowStep, skill_level: UserSkillLevel) -> WorkflowStep:
        """Personalize step instructions based on user skill level"""
        
        # Create a copy to avoid modifying the original
        personalized_step = WorkflowStep(
            id=step.id,
            stage=step.stage,
            title=step.title,
            description=step.description,
            instructions=step.instructions.copy(),
            validation_method=step.validation_method,
            estimated_time_minutes=step.estimated_time_minutes,
            requires_technical_knowledge=step.requires_technical_knowledge,
            dependencies=step.dependencies.copy(),
            success_criteria=step.success_criteria.copy(),
            failure_recovery=step.failure_recovery.copy(),
            visual_aids=step.visual_aids.copy()
        )
        
        # Adjust based on skill level
        if skill_level == UserSkillLevel.ABSOLUTE_BEGINNER:
            # Add more detailed explanations
            personalized_step.instructions = [
                f"📝 {instruction} (Detaillierte Hilfe verfügbar)" 
                for instruction in step.instructions
            ]
            personalized_step.estimated_time_minutes = int(step.estimated_time_minutes * 1.5)
            personalized_step.visual_aids.extend(["beginner_guide.pdf", "video_walkthrough.mp4"])
        
        elif skill_level == UserSkillLevel.ADVANCED:
            # Provide more technical details and shortcuts
            personalized_step.instructions = [
                f"⚡ {instruction}" for instruction in step.instructions
            ]
            personalized_step.estimated_time_minutes = int(step.estimated_time_minutes * 0.7)
            personalized_step.visual_aids.append("advanced_shortcuts.pdf")
        
        return personalized_step

    async def _determine_next_step(self, journey: UserJourney) -> Optional[WorkflowStep]:
        """Determine the next step based on current progress"""
        
        current_stage_steps = self.workflow_templates.get(journey.current_stage, [])
        
        # Find next uncompleted step in current stage
        for step in current_stage_steps:
            if step.id not in journey.completed_steps:
                # Check if dependencies are satisfied
                dependencies_satisfied = all(
                    dep in journey.completed_steps for dep in step.dependencies
                )
                
                if dependencies_satisfied:
                    return step
        
        # If no more steps in current stage, move to next stage
        stages = list(WorkflowStage)
        current_stage_index = stages.index(journey.current_stage)
        
        if current_stage_index + 1 < len(stages):
            next_stage = stages[current_stage_index + 1]
            next_stage_steps = self.workflow_templates.get(next_stage, [])
            
            if next_stage_steps:
                return next_stage_steps[0]  # Return first step of next stage
        
        # No more steps - journey complete
        return None

    async def get_journey_progress(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive progress information for a user"""
        
        # Use workflow integration for database operations
        from .workflow_integration import workflow_integration
        journey = await workflow_integration.load_user_journey(user_id)
        
        if not journey:
            return {"error": "Journey not found"}
        
        total_steps = self._get_total_steps_count()
        completed_steps = len(journey.completed_steps)
        progress_percentage = (completed_steps / total_steps) * 100
        
        # Calculate stage progress
        stage_progress = {}
        for stage, steps in self.workflow_templates.items():
            stage_completed = sum(1 for step in steps if step.id in journey.completed_steps)
            stage_total = len(steps)
            stage_progress[stage.value] = {
                "completed": stage_completed,
                "total": stage_total,
                "percentage": (stage_completed / stage_total) * 100 if stage_total > 0 else 0
            }
        
        return {
            "user_id": journey.user_id,
            "website_url": journey.website_url,
            "skill_level": journey.skill_level.value,
            "current_stage": journey.current_stage.value,
            "current_step": journey.current_step,
            "progress_percentage": progress_percentage,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "stage_progress": stage_progress,
            "start_date": journey.start_date.isoformat(),
            "estimated_completion": journey.estimated_completion.isoformat(),
            "actual_completion": journey.actual_completion.isoformat() if journey.actual_completion else None,
            "failed_attempts": journey.failed_attempts,
            "support_interactions": len(journey.support_interactions),
            "estimated_time_remaining": self._calculate_remaining_time(journey)
        }

    def _get_total_steps_count(self) -> int:
        """Get total number of steps in workflow"""
        return sum(len(steps) for steps in self.workflow_templates.values())

    def _generate_congratulation_message(self, journey: UserJourney) -> str:
        """Generate congratulation message"""
        messages = [
            "🎉 Großartig! Sie haben wieder einen Schritt geschafft!",
            "👏 Perfekt! Ihre Website wird immer besser!",
            "✨ Super Arbeit! Sie sind auf dem besten Weg!",
            "🚀 Fantastisch! Weitermachen!",
            "💪 Klasse! Sie meistern das großartig!"
        ]
        
        import random
        return random.choice(messages)

    def _calculate_remaining_time(self, journey: UserJourney) -> str:
        """Calculate estimated remaining time"""
        # Simplified calculation
        remaining_steps = self._get_total_steps_count() - len(journey.completed_steps)
        avg_time_per_step = 10  # minutes
        
        total_minutes = remaining_steps * avg_time_per_step
        
        if total_minutes < 60:
            return f"ca. {total_minutes} Minuten"
        elif total_minutes < 1440:  # Less than 24 hours
            hours = total_minutes // 60
            return f"ca. {hours} Stunden"
        else:
            days = total_minutes // 1440
            return f"ca. {days} Tage"

# Global workflow engine instance
workflow_engine = WorkflowEngine()