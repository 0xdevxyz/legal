"""
Selbstlernendes Feedback-System für KI-Klassifizierungen
========================================================

Das System lernt kontinuierlich aus User-Verhalten und Feedback:
- Tracking von User-Aktionen auf Gesetzesänderungen
- Feedback-Collection (War die Klassifizierung hilfreich?)
- ML-basierte Muster-Erkennung
- Automatische Verbesserung der Klassifizierungs-Prompts
- A/B-Testing von verschiedenen Klassifizierungs-Strategien

Features:
- Implizites Feedback (User-Verhalten: Klicks, Ignorieren, Aktionen)
- Explizites Feedback (User-Bewertungen, Reports)
- Pattern-Learning (Welche Klassifizierungen waren erfolgreich?)
- Kontinuierliche Verbesserung der KI-Prompts
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Art des Feedbacks"""
    IMPLICIT_CLICK = "implicit_click"  # User hat geklickt
    IMPLICIT_IGNORE = "implicit_ignore"  # User hat ignoriert (>7 Tage keine Interaktion)
    IMPLICIT_DISMISS = "implicit_dismiss"  # User hat explizit abgelehnt
    EXPLICIT_HELPFUL = "explicit_helpful"  # User sagt "hilfreich"
    EXPLICIT_NOT_HELPFUL = "explicit_not_helpful"  # User sagt "nicht hilfreich"
    EXPLICIT_WRONG = "explicit_wrong"  # User meldet Fehler
    ACTION_COMPLETED = "action_completed"  # User hat empfohlene Aktion ausgeführt
    ACTION_SKIPPED = "action_skipped"  # User hat Aktion übersprungen


class UserActionType(str, Enum):
    """Typ der User-Aktion"""
    VIEW_DETAIL = "view_detail"
    CLICK_PRIMARY_BUTTON = "click_primary_button"
    CLICK_SECONDARY_BUTTON = "click_secondary_button"
    DISMISS = "dismiss"
    MARK_AS_READ = "mark_as_read"
    START_SCAN = "start_scan"
    UPDATE_SETTINGS = "update_settings"
    CONSULT_GUIDE = "consult_guide"
    CONTACT_SUPPORT = "contact_support"


@dataclass
class FeedbackEvent:
    """Ein Feedback-Event"""
    user_id: int
    update_id: str
    classification_id: int
    feedback_type: FeedbackType
    user_action: Optional[UserActionType]
    
    # Context
    time_to_action: Optional[int]  # Sekunden bis zur Aktion
    context_data: Dict[str, Any]  # Zusätzliche Kontext-Daten
    
    # Metadata
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "update_id": self.update_id,
            "classification_id": self.classification_id,
            "feedback_type": self.feedback_type.value,
            "user_action": self.user_action.value if self.user_action else None,
            "time_to_action": self.time_to_action,
            "context_data": self.context_data,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class LearningInsight:
    """Erkenntnisse aus dem Lern-Prozess"""
    pattern_type: str
    description: str
    confidence: float  # 0.0 - 1.0
    sample_size: int
    recommendation: str
    created_at: datetime


class AIFeedbackLearning:
    """
    Selbstlernendes System für kontinuierliche Verbesserung
    """
    
    def __init__(self, db_service):
        self.db = db_service
        logger.info("🧠 AI Feedback Learning System initialized")
    
    async def record_feedback(
        self,
        user_id: int,
        update_id: str,
        classification_id: int,
        feedback_type: FeedbackType,
        user_action: Optional[UserActionType] = None,
        time_to_action: Optional[int] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Zeichnet Feedback auf
        
        Returns:
            True wenn erfolgreich
        """
        try:
            event = FeedbackEvent(
                user_id=user_id,
                update_id=update_id,
                classification_id=classification_id,
                feedback_type=feedback_type,
                user_action=user_action,
                time_to_action=time_to_action,
                context_data=context_data or {},
                created_at=datetime.now()
            )
            
            # Speichere in DB
            async with self.db.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO ai_classification_feedback (
                        user_id, update_id, classification_id, feedback_type,
                        user_action, time_to_action, context_data, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    event.user_id,
                    event.update_id,
                    event.classification_id,
                    event.feedback_type.value,
                    event.user_action.value if event.user_action else None,
                    event.time_to_action,
                    json.dumps(event.context_data),
                    event.created_at
                )
            
            logger.info(f"✅ Feedback recorded: {feedback_type.value} for update {update_id}")
            
            # Trigger Learning (async)
            await self._trigger_learning_if_needed()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to record feedback: {e}")
            return False
    
    async def analyze_classification_performance(
        self,
        classification_id: int
    ) -> Dict[str, Any]:
        """
        Analysiert die Performance einer spezifischen Klassifizierung
        
        Returns:
            Performance-Metriken
        """
        async with self.db.pool.acquire() as conn:
            # Hole alle Feedback-Events
            feedback_rows = await conn.fetch(
                """
                SELECT feedback_type, user_action, time_to_action, context_data
                FROM ai_classification_feedback
                WHERE classification_id = $1
                """,
                classification_id
            )
            
            if not feedback_rows:
                return {
                    "total_feedback": 0,
                    "accuracy_score": 0.0,
                    "engagement_rate": 0.0,
                    "completion_rate": 0.0
                }
            
            # Analysiere Feedback
            total = len(feedback_rows)
            positive = sum(1 for r in feedback_rows if r['feedback_type'] in [
                FeedbackType.EXPLICIT_HELPFUL.value,
                FeedbackType.ACTION_COMPLETED.value
            ])
            negative = sum(1 for r in feedback_rows if r['feedback_type'] in [
                FeedbackType.EXPLICIT_NOT_HELPFUL.value,
                FeedbackType.EXPLICIT_WRONG.value,
                FeedbackType.IMPLICIT_IGNORE.value
            ])
            
            engaged = sum(1 for r in feedback_rows if r['user_action'] is not None)
            completed = sum(1 for r in feedback_rows if r['feedback_type'] == FeedbackType.ACTION_COMPLETED.value)
            
            # Berechne Scores
            accuracy_score = (positive - negative) / total if total > 0 else 0.0
            engagement_rate = engaged / total if total > 0 else 0.0
            completion_rate = completed / total if total > 0 else 0.0
            
            # Durchschnittliche Zeit bis zur Aktion
            times = [r['time_to_action'] for r in feedback_rows if r['time_to_action']]
            avg_time = sum(times) / len(times) if times else None
            
            return {
                "total_feedback": total,
                "positive_feedback": positive,
                "negative_feedback": negative,
                "accuracy_score": accuracy_score,
                "engagement_rate": engagement_rate,
                "completion_rate": completion_rate,
                "avg_time_to_action_seconds": avg_time
            }
    
    async def get_learning_insights(
        self,
        days: int = 30,
        min_sample_size: int = 10
    ) -> List[LearningInsight]:
        """
        Extrahiert Lern-Erkenntnisse aus den gesammelten Daten
        
        Args:
            days: Anzahl Tage zurück
            min_sample_size: Mindest-Anzahl Samples für valide Insights
        
        Returns:
            Liste von Erkenntnissen
        """
        insights = []
        since = datetime.now() - timedelta(days=days)
        
        async with self.db.pool.acquire() as conn:
            # Pattern 1: Welche Action-Types haben höchste Completion-Rate?
            action_performance = await conn.fetch(
                """
                SELECT 
                    acl.primary_action_type,
                    COUNT(*) as total,
                    SUM(CASE WHEN f.feedback_type = 'action_completed' THEN 1 ELSE 0 END) as completed,
                    AVG(CASE WHEN f.time_to_action IS NOT NULL THEN f.time_to_action ELSE NULL END) as avg_time
                FROM ai_classifications acl
                LEFT JOIN ai_classification_feedback f ON acl.id = f.classification_id
                WHERE acl.created_at >= $1
                GROUP BY acl.primary_action_type
                HAVING COUNT(*) >= $2
                ORDER BY (SUM(CASE WHEN f.feedback_type = 'action_completed' THEN 1 ELSE 0 END)::float / COUNT(*)) DESC
                """,
                since,
                min_sample_size
            )
            
            for row in action_performance:
                completion_rate = row['completed'] / row['total'] if row['total'] > 0 else 0
                
                if completion_rate > 0.5:  # Erfolgreiche Actions
                    insights.append(LearningInsight(
                        pattern_type="high_completion_action",
                        description=f"Action-Type '{row['primary_action_type']}' hat hohe Completion-Rate ({completion_rate:.1%})",
                        confidence=min(completion_rate, 0.95),
                        sample_size=row['total'],
                        recommendation=f"Empfehle '{row['primary_action_type']}' häufiger für ähnliche Updates",
                        created_at=datetime.now()
                    ))
            
            # Pattern 2: Welche Severities führen zu schnellerer Reaktion?
            severity_response = await conn.fetch(
                """
                SELECT 
                    acl.severity,
                    COUNT(*) as total,
                    AVG(f.time_to_action) as avg_response_time
                FROM ai_classifications acl
                JOIN ai_classification_feedback f ON acl.id = f.classification_id
                WHERE acl.created_at >= $1 AND f.time_to_action IS NOT NULL
                GROUP BY acl.severity
                HAVING COUNT(*) >= $2
                ORDER BY AVG(f.time_to_action) ASC
                """,
                since,
                min_sample_size
            )
            
            for row in severity_response:
                if row['avg_response_time'] < 3600:  # Schneller als 1 Stunde
                    insights.append(LearningInsight(
                        pattern_type="fast_response_severity",
                        description=f"Severity '{row['severity']}' führt zu schneller Reaktion (Ø {row['avg_response_time']:.0f}s)",
                        confidence=0.8,
                        sample_size=row['total'],
                        recommendation=f"Severity-Klassifizierung '{row['severity']}' ist effektiv für dringende Updates",
                        created_at=datetime.now()
                    ))
            
            # Pattern 3: Welche Button-Farben führen zu höherem Engagement?
            button_engagement = await conn.fetch(
                """
                SELECT 
                    acl.primary_button_color,
                    COUNT(*) as total,
                    SUM(CASE WHEN f.user_action IS NOT NULL THEN 1 ELSE 0 END) as engaged
                FROM ai_classifications acl
                LEFT JOIN ai_classification_feedback f ON acl.id = f.classification_id
                WHERE acl.created_at >= $1
                GROUP BY acl.primary_button_color
                HAVING COUNT(*) >= $2
                ORDER BY (SUM(CASE WHEN f.user_action IS NOT NULL THEN 1 ELSE 0 END)::float / COUNT(*)) DESC
                """,
                since,
                min_sample_size
            )
            
            for row in button_engagement:
                engagement_rate = row['engaged'] / row['total'] if row['total'] > 0 else 0
                
                if engagement_rate > 0.3:  # Gutes Engagement
                    insights.append(LearningInsight(
                        pattern_type="effective_button_color",
                        description=f"Button-Farbe '{row['primary_button_color']}' hat hohes Engagement ({engagement_rate:.1%})",
                        confidence=0.75,
                        sample_size=row['total'],
                        recommendation=f"Verwende '{row['primary_button_color']}' für ähnliche Aktionen",
                        created_at=datetime.now()
                    ))
            
            # Pattern 4: False Positives/Negatives erkennen
            false_classifications = await conn.fetch(
                """
                SELECT 
                    acl.update_id,
                    acl.action_required,
                    acl.severity,
                    COUNT(*) as negative_feedback_count
                FROM ai_classifications acl
                JOIN ai_classification_feedback f ON acl.id = f.classification_id
                WHERE acl.created_at >= $1 
                AND f.feedback_type IN ('explicit_not_helpful', 'explicit_wrong')
                GROUP BY acl.update_id, acl.action_required, acl.severity
                HAVING COUNT(*) >= 3
                """,
                since
            )
            
            for row in false_classifications:
                insights.append(LearningInsight(
                    pattern_type="potential_misclassification",
                    description=f"Update {row['update_id']} erhielt {row['negative_feedback_count']} negative Feedbacks",
                    confidence=0.7,
                    sample_size=row['negative_feedback_count'],
                    recommendation="Überprüfe Klassifizierungs-Logik für ähnliche Updates",
                    created_at=datetime.now()
                ))
        
        logger.info(f"📊 Generated {len(insights)} learning insights from {days} days of data")
        return insights
    
    async def get_optimization_suggestions(self) -> Dict[str, Any]:
        """
        Gibt konkrete Optimierungs-Vorschläge zurück
        
        Returns:
            Dict mit Vorschlägen zur Verbesserung
        """
        insights = await self.get_learning_insights(days=30)
        
        suggestions = {
            "prompt_improvements": [],
            "action_recommendations": [],
            "button_optimizations": [],
            "severity_adjustments": []
        }
        
        for insight in insights:
            if insight.pattern_type == "high_completion_action":
                suggestions["action_recommendations"].append({
                    "insight": insight.description,
                    "action": insight.recommendation,
                    "confidence": insight.confidence
                })
            
            elif insight.pattern_type == "effective_button_color":
                suggestions["button_optimizations"].append({
                    "insight": insight.description,
                    "action": insight.recommendation,
                    "confidence": insight.confidence
                })
            
            elif insight.pattern_type == "fast_response_severity":
                suggestions["severity_adjustments"].append({
                    "insight": insight.description,
                    "action": insight.recommendation,
                    "confidence": insight.confidence
                })
            
            elif insight.pattern_type == "potential_misclassification":
                suggestions["prompt_improvements"].append({
                    "insight": insight.description,
                    "action": insight.recommendation,
                    "confidence": insight.confidence
                })
        
        return suggestions
    
    async def _trigger_learning_if_needed(self):
        """
        Prüft ob genug neue Daten vorhanden sind für Re-Learning
        """
        async with self.db.pool.acquire() as conn:
            # Prüfe wann letztes Learning war
            last_learning = await conn.fetchval(
                """
                SELECT MAX(learned_at) FROM ai_learning_cycles
                """
            )
            
            if last_learning and (datetime.now() - last_learning) < timedelta(hours=6):
                return  # Zu früh für neues Learning
            
            # Prüfe ob genug neue Feedback-Events
            new_feedback_count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM ai_classification_feedback
                WHERE created_at > COALESCE($1, '1970-01-01')
                """,
                last_learning
            )
            
            if new_feedback_count < 50:  # Mindestens 50 neue Events
                return
            
            logger.info(f"🎓 Triggering learning cycle ({new_feedback_count} new feedback events)")
            
            # Führe Learning durch
            await self._run_learning_cycle()
    
    async def _run_learning_cycle(self):
        """
        Führt einen kompletten Learning-Zyklus durch
        """
        try:
            # Hole Insights
            insights = await self.get_learning_insights(days=30, min_sample_size=10)
            
            # Hole Optimierungs-Vorschläge
            suggestions = await self.get_optimization_suggestions()
            
            # Speichere Learning-Cycle
            async with self.db.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO ai_learning_cycles (
                        insights_count,
                        suggestions,
                        learned_at
                    ) VALUES ($1, $2, NOW())
                    """,
                    len(insights),
                    json.dumps(suggestions, default=str)
                )
            
            logger.info(f"✅ Learning cycle completed: {len(insights)} insights, {sum(len(v) for v in suggestions.values())} suggestions")
            
        except Exception as e:
            logger.error(f"❌ Learning cycle failed: {e}")


# Globale Instanz
feedback_learning = None


def init_feedback_learning(db_service):
    """Initialisiert das Feedback Learning System"""
    global feedback_learning
    feedback_learning = AIFeedbackLearning(db_service)
    return feedback_learning


def get_feedback_learning() -> Optional[AIFeedbackLearning]:
    """Gibt die globale Feedback Learning Instanz zurück"""
    return feedback_learning

