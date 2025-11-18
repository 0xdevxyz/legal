"""
AI-gestützte Klassifizierungs-Engine für Gesetzesänderungen
============================================================

Intelligente Entscheidung über:
- Handlungsbedarf (Aktion erforderlich vs. nur zur Kenntnis)
- Button-Typ und Aktionen (Scan, Cookie-Update, Datenschutz-Check, etc.)
- Dringlichkeit und Priorisierung
- Automatische Empfehlungen

Features:
- KI-basierte Klassifizierung mit Claude 3.5
- Selbstlernendes System mit Feedback-Loop
- Kontextbewusste Entscheidungen basierend auf User-Profil
- Dynamische Action-Generierung
"""

import os
import json
import httpx
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Typen von Aktionen die empfohlen werden können"""
    SCAN_WEBSITE = "scan_website"  # Neue Compliance-Analyse durchführen
    UPDATE_COOKIE_BANNER = "update_cookie_banner"  # Cookie-Banner anpassen
    UPDATE_PRIVACY_POLICY = "update_privacy_policy"  # Datenschutzerklärung aktualisieren
    UPDATE_IMPRESSUM = "update_impressum"  # Impressum aktualisieren
    CHECK_ACCESSIBILITY = "check_accessibility"  # Barrierefreiheit prüfen
    REVIEW_MANUALLY = "review_manually"  # Manuelle Überprüfung nötig
    CONSULT_LEGAL = "consult_legal"  # Rechtsberatung empfohlen
    INFORMATION_ONLY = "information_only"  # Nur zur Kenntnis


class DecisionConfidence(str, Enum):
    """Konfidenz der KI-Entscheidung"""
    HIGH = "high"  # >90% sicher
    MEDIUM = "medium"  # 70-90% sicher
    LOW = "low"  # <70% sicher


@dataclass
class ActionRecommendation:
    """Eine empfohlene Aktion"""
    action_type: ActionType
    priority: int  # 1-10, 10 = höchste Priorität
    title: str
    description: str
    button_text: str
    button_color: str  # z.B. "red", "orange", "blue", "gray"
    icon: str  # Lucide icon name
    estimated_time: str  # z.B. "5 Minuten", "1 Stunde"
    requires_paid_plan: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClassificationResult:
    """Ergebnis der KI-Klassifizierung"""
    # Hauptentscheidung
    action_required: bool
    confidence: DecisionConfidence
    
    # Klassifizierung
    severity: str  # critical, high, medium, low, info
    impact_score: float  # 0.0 - 10.0
    
    # Aktionen
    recommended_actions: List[ActionRecommendation]
    primary_action: ActionRecommendation  # Hauptaktion (für großen Button)
    
    # Erklärung
    reasoning: str  # Warum wurde so klassifiziert?
    user_impact: str  # Was bedeutet das für den User?
    classified_at: datetime
    
    # Optional fields
    consequences_if_ignored: Optional[str] = None
    model_version: str = "v1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['recommended_actions'] = [a.to_dict() for a in self.recommended_actions]
        result['primary_action'] = self.primary_action.to_dict()
        result['classified_at'] = self.classified_at.isoformat()
        return result


class AILegalClassifier:
    """
    Intelligente KI-Engine zur Klassifizierung von Gesetzesänderungen
    
    Diese Engine entscheidet automatisch:
    - Muss der User aktiv werden?
    - Welche Aktionen sind empfohlen?
    - Wie dringend ist es?
    - Welche Buttons sollen angezeigt werden?
    """
    
    def __init__(self, openrouter_api_key: str = None):
        self.api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-3.7-sonnet:beta"  # ✅ Aktuelles funktionierendes Modell
        
        logger.info("🤖 AI Legal Classifier initialized")
    
    async def classify_legal_update(
        self,
        update_data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> ClassificationResult:
        """
        Klassifiziert eine Gesetzesänderung mit KI
        
        Args:
            update_data: Daten der Gesetzesänderung (title, description, etc.)
            user_context: Optional - Kontext über den User (Website, Services, etc.)
        
        Returns:
            ClassificationResult mit allen Entscheidungen und Empfehlungen
        """
        logger.info(f"🔍 Klassifiziere: {update_data.get('title', 'N/A')}")
        
        try:
            # Baue kontextbewussten Prompt
            prompt = self._build_classification_prompt(update_data, user_context)
            
            # Rufe KI-API auf
            response = await self._call_ai_api(prompt)
            
            # Parse Response
            classification = self._parse_classification_response(response)
            
            logger.info(
                f"✅ Klassifiziert: action_required={classification.action_required}, "
                f"confidence={classification.confidence}, "
                f"impact={classification.impact_score}"
            )
            
            return classification
            
        except Exception as e:
            logger.error(f"❌ Klassifizierung fehlgeschlagen: {e}")
            # Fallback: Konservative Klassifizierung
            return self._get_fallback_classification(update_data)
    
    async def batch_classify(
        self,
        updates: List[Dict[str, Any]],
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[ClassificationResult]:
        """
        Klassifiziert mehrere Updates auf einmal (effizienter)
        """
        results = []
        
        # In Batches verarbeiten (max 5 gleichzeitig)
        batch_size = 5
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            
            # Parallel klassifizieren
            import asyncio
            tasks = [
                self.classify_legal_update(update, user_context)
                for update in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Fehler behandeln
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch-Klassifizierung Fehler: {result}")
                    continue
                results.append(result)
        
        return results
    
    async def reclassify_with_feedback(
        self,
        update_id: str,
        original_classification: ClassificationResult,
        user_feedback: Dict[str, Any]
    ) -> ClassificationResult:
        """
        Re-klassifiziert basierend auf User-Feedback (selbstlernendes System)
        
        Args:
            update_id: ID der Gesetzesänderung
            original_classification: Ursprüngliche Klassifizierung
            user_feedback: User-Feedback (was hat er getan? war es hilfreich?)
        
        Returns:
            Verbesserte Klassifizierung
        """
        logger.info(f"🔄 Re-klassifiziere mit Feedback: {update_id}")
        
        prompt = f"""
Du hast eine Gesetzesänderung wie folgt klassifiziert:

# URSPRÜNGLICHE KLASSIFIZIERUNG
Action Required: {original_classification.action_required}
Severity: {original_classification.severity}
Impact Score: {original_classification.impact_score}
Primary Action: {original_classification.primary_action.action_type}
Reasoning: {original_classification.reasoning}

# USER-FEEDBACK
{json.dumps(user_feedback, indent=2, ensure_ascii=False)}

# AUFGABE
Analysiere das Feedback und entscheide:
1. War die ursprüngliche Klassifizierung korrekt?
2. Was können wir daraus lernen?
3. Wie sollte die verbesserte Klassifizierung aussehen?

Gib die VERBESSERTE Klassifizierung im gleichen JSON-Format zurück.
"""
        
        try:
            response = await self._call_ai_api(prompt)
            improved = self._parse_classification_response(response)
            
            # Markiere als durch Feedback verbessert
            improved.model_version = f"{improved.model_version}_feedback"
            
            return improved
            
        except Exception as e:
            logger.error(f"❌ Re-Klassifizierung fehlgeschlagen: {e}")
            return original_classification
    
    def _build_classification_prompt(
        self,
        update_data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Erstellt den KI-Prompt für die Klassifizierung
        """
        user_info = ""
        if user_context:
            user_info = f"""
# BENUTZER-KONTEXT
Website: {user_context.get('website_url', 'Unbekannt')}
Branche: {user_context.get('industry', 'Unbekannt')}
Aktuelle Compliance-Bereiche: {', '.join(user_context.get('compliance_areas', []))}
Verwendete Services: {', '.join(user_context.get('services', ['Cookie-Banner', 'Tracking']))}
Plan: {user_context.get('subscription_plan', 'Free')}
"""
        
        return f"""
Du bist ein Experte für deutsches und europäisches Recht, spezialisiert auf Web-Compliance.
Deine Aufgabe ist es, Gesetzesänderungen zu analysieren und zu entscheiden:
1. Muss der Website-Betreiber aktiv werden? (action_required: true/false)
2. Wie schwerwiegend ist es? (severity: critical/high/medium/low/info)
3. Welche Aktionen soll er ausführen?
4. Wie dringend ist es?

# GESETZESÄNDERUNG
Titel: {update_data.get('title', 'N/A')}
Typ: {update_data.get('update_type', 'N/A')}
Beschreibung: {update_data.get('description', 'N/A')}
Quelle: {update_data.get('source', 'N/A')}
Veröffentlicht: {update_data.get('published_at', 'N/A')}
Gilt ab: {update_data.get('effective_date', 'N/A')}
{user_info}

# VERFÜGBARE AKTIONEN
Du kannst folgende Aktionen empfehlen:
1. scan_website - Neue Compliance-Analyse durchführen
2. update_cookie_banner - Cookie-Banner anpassen
3. update_privacy_policy - Datenschutzerklärung aktualisieren
4. update_impressum - Impressum aktualisieren
5. check_accessibility - Barrierefreiheit prüfen
6. review_manually - Manuelle Überprüfung nötig
7. consult_legal - Rechtsberatung empfohlen
8. information_only - Nur zur Kenntnis

# AUFGABE
Analysiere die Gesetzesänderung und gib eine strukturierte Klassifizierung zurück.

Antworte im folgenden JSON-Format:
{{
    "action_required": true,  // Muss User aktiv werden?
    "confidence": "high",  // high/medium/low
    "severity": "high",  // critical/high/medium/low/info
    "impact_score": 7.5,  // 0.0 - 10.0
    "reasoning": "Diese Änderung betrifft...",
    "user_impact": "Für den Nutzer bedeutet das...",
    "consequences_if_ignored": "Bei Nicht-Umsetzung drohen...",
    
    "recommended_actions": [
        {{
            "action_type": "scan_website",
            "priority": 10,
            "title": "Website neu scannen",
            "description": "Führen Sie eine neue Compliance-Analyse durch, um...",
            "button_text": "Jetzt neu scannen",
            "button_color": "red",
            "icon": "Search",
            "estimated_time": "2-3 Minuten",
            "requires_paid_plan": false
        }}
    ],
    
    "primary_action": {{
        // Die wichtigste/dringendste Aktion (wird als Haupt-Button angezeigt)
        "action_type": "scan_website",
        "priority": 10,
        "title": "Website neu scannen",
        "description": "...",
        "button_text": "Jetzt neu scannen",
        "button_color": "red",
        "icon": "Search",
        "estimated_time": "2-3 Minuten",
        "requires_paid_plan": false
    }}
}}

WICHTIG:
- Sei konservativ: Wenn unsicher, empfehle action_required=true
- Button-Farben: red (kritisch), orange (wichtig), blue (moderat), gray (info)
- Icons: Verwende Lucide React Icon-Namen (Search, AlertTriangle, Shield, etc.)
- estimated_time: Realistisch einschätzen
- requires_paid_plan: true nur wenn Premium-Features nötig sind
"""
    
    def _parse_classification_response(self, response: str) -> ClassificationResult:
        """
        Parsed die KI-Antwort in ein ClassificationResult
        """
        try:
            # Extrahiere JSON aus der Response (KI könnte Text davor/danach schreiben)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            data = json.loads(json_str)
            
            # Parse Actions
            recommended_actions = []
            for action_data in data.get('recommended_actions', []):
                action = ActionRecommendation(
                    action_type=ActionType(action_data['action_type']),
                    priority=action_data['priority'],
                    title=action_data['title'],
                    description=action_data['description'],
                    button_text=action_data['button_text'],
                    button_color=action_data['button_color'],
                    icon=action_data['icon'],
                    estimated_time=action_data.get('estimated_time', 'Unbekannt'),
                    requires_paid_plan=action_data.get('requires_paid_plan', False)
                )
                recommended_actions.append(action)
            
            # Primary Action
            primary_data = data['primary_action']
            primary_action = ActionRecommendation(
                action_type=ActionType(primary_data['action_type']),
                priority=primary_data['priority'],
                title=primary_data['title'],
                description=primary_data['description'],
                button_text=primary_data['button_text'],
                button_color=primary_data['button_color'],
                icon=primary_data['icon'],
                estimated_time=primary_data.get('estimated_time', 'Unbekannt'),
                requires_paid_plan=primary_data.get('requires_paid_plan', False)
            )
            
            # Erstelle ClassificationResult
            result = ClassificationResult(
                action_required=data['action_required'],
                confidence=DecisionConfidence(data['confidence']),
                severity=data['severity'],
                impact_score=float(data['impact_score']),
                recommended_actions=recommended_actions,
                primary_action=primary_action,
                reasoning=data['reasoning'],
                user_impact=data['user_impact'],
                consequences_if_ignored=data.get('consequences_if_ignored'),
                classified_at=datetime.now()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Parsing fehlgeschlagen: {e}")
            raise
    
    async def _call_ai_api(self, prompt: str) -> str:
        """
        Ruft die OpenRouter AI API auf
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://complyo.tech",
            "X-Title": "Complyo Legal Classifier"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Du bist ein hochspezialisierter KI-Assistent für deutsches und "
                        "europäisches Recht im Bereich Web-Compliance. Du analysierst "
                        "Gesetzesänderungen und triffst intelligente Entscheidungen über "
                        "Handlungsbedarf und Aktionen. Antworte IMMER im geforderten JSON-Format."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2,  # Niedrig für konsistente, verlässliche Antworten
            "max_tokens": 3000,
            "response_format": {"type": "json_object"}  # Erzwingt JSON
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            content = data['choices'][0]['message']['content']
            
            # Log Token-Usage
            if 'usage' in data:
                logger.info(
                    f"📊 API Usage: {data['usage'].get('total_tokens', 0)} tokens, "
                    f"~${data['usage'].get('total_tokens', 0) * 0.000003:.4f}"
                )
            
            return content
    
    def _get_fallback_classification(
        self,
        update_data: Dict[str, Any]
    ) -> ClassificationResult:
        """
        Fallback-Klassifizierung wenn KI-API fehlschlägt
        
        Verwendet einfache Heuristiken basierend auf Keywords
        """
        title = update_data.get('title', '').lower()
        description = update_data.get('description', '').lower()
        text = f"{title} {description}"
        
        # Keyword-basierte Heuristiken
        critical_keywords = ['pflicht', 'bußgeld', 'strafe', 'deadline', 'frist', 'sofort']
        high_keywords = ['anpassen', 'aktualisieren', 'ändern', 'ergänzen']
        cookie_keywords = ['cookie', 'tracking', 'consent', 'einwilligung']
        privacy_keywords = ['datenschutz', 'dsgvo', 'privacy', 'personenbezogen']
        
        # Bestimme Severity
        severity = 'info'
        if any(kw in text for kw in critical_keywords):
            severity = 'critical'
        elif any(kw in text for kw in high_keywords):
            severity = 'high'
        
        # Bestimme Action
        action_type = ActionType.REVIEW_MANUALLY
        if any(kw in text for kw in cookie_keywords):
            action_type = ActionType.UPDATE_COOKIE_BANNER
        elif any(kw in text for kw in privacy_keywords):
            action_type = ActionType.UPDATE_PRIVACY_POLICY
        
        # Erstelle konservative Klassifizierung
        primary_action = ActionRecommendation(
            action_type=action_type,
            priority=7,
            title="Manuelle Überprüfung empfohlen",
            description="Bitte prüfen Sie diese Änderung manuell, da die automatische Klassifizierung fehlgeschlagen ist.",
            button_text="Details ansehen",
            button_color="orange",
            icon="AlertTriangle",
            estimated_time="5-10 Minuten",
            requires_paid_plan=False
        )
        
        return ClassificationResult(
            action_required=True,  # Konservativ: immer true
            confidence=DecisionConfidence.LOW,
            severity=severity,
            impact_score=6.0,
            recommended_actions=[primary_action],
            primary_action=primary_action,
            reasoning="Automatische Klassifizierung fehlgeschlagen. Bitte manuell prüfen.",
            user_impact="Diese Änderung könnte Ihre Website betreffen.",
            consequences_if_ignored="Nicht bekannt - manuelle Prüfung erforderlich.",
            classified_at=datetime.now(),
            model_version="v1.0_fallback"
        )


# Globale Instanz
ai_classifier = None


def init_ai_classifier(openrouter_api_key: str = None):
    """Initialisiert den AI Legal Classifier"""
    global ai_classifier
    ai_classifier = AILegalClassifier(openrouter_api_key)
    return ai_classifier


def get_ai_classifier() -> Optional[AILegalClassifier]:
    """Gibt die globale Classifier-Instanz zurück"""
    return ai_classifier

