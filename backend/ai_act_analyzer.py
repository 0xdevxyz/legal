"""
AI Act Analyzer - EU AI Act Compliance Engine
Classifies AI systems and checks compliance with EU AI Act requirements
"""

import json
import os
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel

class AISystem(BaseModel):
    """AI System Model"""
    id: Optional[str] = None
    name: str
    description: str
    vendor: Optional[str] = None
    purpose: str
    domain: Optional[str] = None  # HR, marketing, customer_service, etc.
    deployment_date: Optional[str] = None
    data_types: Optional[List[str]] = None
    affected_persons: Optional[List[str]] = None

class RiskClassification(BaseModel):
    """Risk Classification Result"""
    risk_category: str  # 'prohibited', 'high', 'limited', 'minimal'
    reasoning: str
    confidence: float  # 0.0-1.0
    relevant_articles: List[str]
    key_concerns: List[str]

class ComplianceResult(BaseModel):
    """Compliance Check Result"""
    compliance_score: int  # 0-100
    overall_risk_score: float
    requirements_met: List[Dict[str, Any]]
    requirements_failed: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    recommendations: str

class AIActAnalyzer:
    """
    EU AI Act Compliance Analyzer
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # AI Act Risk Categories
        self.risk_categories = {
            "prohibited": {
                "name": "Verboten (Prohibited)",
                "description": "KI-Systeme, die nicht verwendet werden dürfen",
                "examples": [
                    "Social Scoring durch Behörden",
                    "Manipulation vulnerabler Gruppen",
                    "Biometrische Echtzeit-Identifikation im öffentlichen Raum",
                    "Emotionserkennung am Arbeitsplatz/Bildungseinrichtungen"
                ],
                "articles": ["Art. 5"]
            },
            "high": {
                "name": "Hochrisiko (High-Risk)",
                "description": "KI-Systeme mit hohem Risiko für Grundrechte",
                "examples": [
                    "Kritische Infrastruktur",
                    "Bildung und Berufsbildung",
                    "Beschäftigung und Personalverwaltung",
                    "Zugang zu wesentlichen Diensten",
                    "Strafverfolgung",
                    "Migration und Asyl",
                    "Justizverwaltung",
                    "Biometrische Identifikation"
                ],
                "articles": ["Art. 6-15", "Annex III"]
            },
            "limited": {
                "name": "Begrenztes Risiko (Limited-Risk)",
                "description": "KI-Systeme mit Transparenzpflichten",
                "examples": [
                    "Chatbots",
                    "Emotionserkennung (außerhalb verbotener Bereiche)",
                    "Deep Fakes",
                    "Biometrische Kategorisierung"
                ],
                "articles": ["Art. 50-52"]
            },
            "minimal": {
                "name": "Minimales Risiko (Minimal-Risk)",
                "description": "KI-Systeme mit minimalem Risiko",
                "examples": [
                    "Spam-Filter",
                    "Empfehlungssysteme (non-critical)",
                    "Spiele-KI",
                    "Bildbearbeitung"
                ],
                "articles": []
            }
        }
        
        # High-Risk AI Requirements (Art. 8-15)
        self.high_risk_requirements = [
            {
                "id": "art_9",
                "article": "Art. 9",
                "title": "Risikomanagementsystem",
                "description": "Etablierung und Dokumentation eines Risikomanagementsystems",
                "mandatory_for": ["high"]
            },
            {
                "id": "art_10",
                "article": "Art. 10",
                "title": "Daten-Governance",
                "description": "Data governance und Management-Praktiken für Trainingsdaten",
                "mandatory_for": ["high"]
            },
            {
                "id": "art_11",
                "article": "Art. 11",
                "title": "Technische Dokumentation",
                "description": "Umfassende technische Dokumentation des AI-Systems",
                "mandatory_for": ["high"]
            },
            {
                "id": "art_12",
                "article": "Art. 12",
                "title": "Aufzeichnungspflichten",
                "description": "Automatische Protokollierung von Ereignissen (Logging)",
                "mandatory_for": ["high"]
            },
            {
                "id": "art_13",
                "article": "Art. 13",
                "title": "Transparenz",
                "description": "Transparenz und Informationspflichten gegenüber Nutzern",
                "mandatory_for": ["high", "limited"]
            },
            {
                "id": "art_14",
                "article": "Art. 14",
                "title": "Menschliche Aufsicht",
                "description": "Human oversight und Möglichkeit zur Intervention",
                "mandatory_for": ["high"]
            },
            {
                "id": "art_15",
                "article": "Art. 15",
                "title": "Genauigkeit, Robustheit, Cybersicherheit",
                "description": "Accuracy, Robustness und Cybersecurity-Maßnahmen",
                "mandatory_for": ["high"]
            }
        ]
    
    async def classify_risk_category(self, ai_system: AISystem) -> RiskClassification:
        """
        Klassifiziert ein KI-System in eine der 4 Risikokategorien
        """
        
        prompt = self._build_classification_prompt(ai_system)
        
        try:
            response = await self._call_ai_api(prompt)
            result = json.loads(response)
            
            return RiskClassification(**result)
        
        except Exception as e:
            print(f"Error in risk classification: {e}")
            # Fallback: Conservative classification
            return RiskClassification(
                risk_category="high",  # Conservative default
                reasoning=f"Automatische Klassifizierung fehlgeschlagen. Konservative Einstufung als High-Risk. Fehler: {str(e)}",
                confidence=0.3,
                relevant_articles=["Art. 6-15"],
                key_concerns=["Manuelle Prüfung erforderlich"]
            )
    
    async def check_compliance(self, ai_system: AISystem, risk_category: str) -> ComplianceResult:
        """
        Prüft Compliance gegen AI Act Requirements
        """
        
        prompt = self._build_compliance_check_prompt(ai_system, risk_category)
        
        try:
            response = await self._call_ai_api(prompt)
            result = json.loads(response)
            
            # Calculate compliance score
            total_requirements = len(result.get("requirements_met", [])) + len(result.get("requirements_failed", []))
            requirements_met = len(result.get("requirements_met", []))
            compliance_score = int((requirements_met / total_requirements * 100)) if total_requirements > 0 else 0
            
            return ComplianceResult(
                compliance_score=compliance_score,
                overall_risk_score=result.get("overall_risk_score", 5.0),
                requirements_met=result.get("requirements_met", []),
                requirements_failed=result.get("requirements_failed", []),
                findings=result.get("findings", []),
                recommendations=result.get("recommendations", "")
            )
        
        except Exception as e:
            print(f"Error in compliance check: {e}")
            return ComplianceResult(
                compliance_score=0,
                overall_risk_score=8.0,
                requirements_met=[],
                requirements_failed=[{"requirement": "Prüfung fehlgeschlagen", "reason": str(e)}],
                findings=[],
                recommendations="Manuelle Compliance-Prüfung durch Experten erforderlich."
            )
    
    def get_required_documentation(self, risk_category: str) -> List[Dict[str, str]]:
        """
        Liefert erforderliche Dokumentation basierend auf Risikokategorie
        """
        
        docs = []
        
        if risk_category == "prohibited":
            docs.append({
                "type": "prohibition_notice",
                "title": "Verbotshinweis",
                "description": "Dokumentation warum das System unter Art. 5 AI Act fällt",
                "mandatory": True
            })
        
        if risk_category == "high":
            docs.extend([
                {
                    "type": "risk_assessment",
                    "title": "Risikoanalyse (Art. 9)",
                    "description": "Umfassende Risikobewertung und Managementplan",
                    "mandatory": True
                },
                {
                    "type": "data_governance",
                    "title": "Data Governance (Art. 10)",
                    "description": "Dokumentation der Daten-Management-Praktiken",
                    "mandatory": True
                },
                {
                    "type": "technical_docs",
                    "title": "Technische Dokumentation (Art. 11)",
                    "description": "Detaillierte technische Spezifikationen und Architekturbeschreibung",
                    "mandatory": True
                },
                {
                    "type": "logging_records",
                    "title": "Logging-Konzept (Art. 12)",
                    "description": "Aufzeichnungspflichten und Log-Management",
                    "mandatory": True
                },
                {
                    "type": "transparency_info",
                    "title": "Transparenz-Informationen (Art. 13)",
                    "description": "Nutzerinformationen und Transparenzpflichten",
                    "mandatory": True
                },
                {
                    "type": "human_oversight",
                    "title": "Human Oversight Konzept (Art. 14)",
                    "description": "Menschliche Aufsicht und Interventionsmöglichkeiten",
                    "mandatory": True
                },
                {
                    "type": "accuracy_robustness",
                    "title": "Genauigkeit & Robustheit (Art. 15)",
                    "description": "Accuracy-Tests und Robustheitsnachweise",
                    "mandatory": True
                },
                {
                    "type": "conformity_assessment",
                    "title": "Konformitätsbewertung",
                    "description": "EU-Konformitätserklärung und CE-Kennzeichnung",
                    "mandatory": True
                }
            ])
        
        if risk_category == "limited":
            docs.extend([
                {
                    "type": "transparency_info",
                    "title": "Transparenz-Informationen (Art. 52)",
                    "description": "Nutzerinformationen über KI-Nutzung",
                    "mandatory": True
                },
                {
                    "type": "ai_disclosure",
                    "title": "KI-Kennzeichnung",
                    "description": "Kennzeichnung als KI-generierter Content",
                    "mandatory": True
                }
            ])
        
        if risk_category == "minimal":
            docs.append({
                "type": "basic_info",
                "title": "Grundinformationen",
                "description": "Basis-Dokumentation des KI-Systems (optional aber empfohlen)",
                "mandatory": False
            })
        
        return docs
    
    def _build_classification_prompt(self, ai_system: AISystem) -> str:
        """Build prompt for risk classification"""
        
        prompt = f"""Du bist ein Experte für den EU AI Act. Klassifiziere das folgende KI-System präzise in eine der 4 Risikokategorien.

**KI-System:**
- Name: {ai_system.name}
- Beschreibung: {ai_system.description}
- Verwendungszweck: {ai_system.purpose}
- Einsatzbereich: {ai_system.domain or 'Nicht spezifiziert'}
- Anbieter: {ai_system.vendor or 'Nicht spezifiziert'}
- Betroffene Datentypen: {', '.join(ai_system.data_types) if ai_system.data_types else 'Nicht spezifiziert'}
- Betroffene Personen: {', '.join(ai_system.affected_persons) if ai_system.affected_persons else 'Nicht spezifiziert'}

**Klassifiziere in eine der 4 Risikokategorien:**

1. **VERBOTEN (prohibited)** - Art. 5 AI Act:
   - Social Scoring durch Behörden
   - Manipulation vulnerabler Gruppen (Kinder, Behinderte)
   - Biometrische Echtzeit-Identifikation im öffentlichen Raum (mit Ausnahmen)
   - Emotionserkennung am Arbeitsplatz oder in Bildungseinrichtungen
   
2. **HOCHRISIKO (high)** - Art. 6 + Annex III AI Act:
   - Kritische Infrastruktur (Verkehr, Wasser, Energie)
   - Bildung und Berufsausbildung (Bewertung, Zulassung)
   - Beschäftigung und Personalmanagement (Recruiting, Beförderung, Überwachung)
   - Zugang zu wesentlichen Diensten (Kreditwürdigkeit, Versicherung, Sozialleistungen)
   - Strafverfolgung (Risikobewertung, Lie Detection, Emotion Recognition)
   - Migration, Asyl, Grenzkontrolle
   - Justizverwaltung (Urteilsfindung, Fallrecherche)
   - Biometrische Identifikation und Kategorisierung
   
3. **BEGRENZTES RISIKO (limited)** - Art. 50-52 AI Act:
   - Chatbots und Konversations-KI
   - Emotionserkennung (außerhalb Arbeitsplatz/Bildung)
   - Deep Fakes und synthetische Medien
   - Biometrische Kategorisierung außerhalb Strafverfolgung
   
4. **MINIMALES RISIKO (minimal)** - Kein regulatorischer Fokus:
   - Spam-Filter
   - Empfehlungssysteme für nicht-kritische Inhalte
   - Spiele-KI
   - Bildbearbeitung und kreative KI-Tools

**Antworte NUR mit validem JSON in folgendem Format:**

{{
  "risk_category": "prohibited|high|limited|minimal",
  "reasoning": "Detaillierte Begründung der Klassifizierung mit Bezug auf spezifische AI Act Artikel",
  "confidence": 0.0-1.0,
  "relevant_articles": ["Art. X", "Art. Y"],
  "key_concerns": ["Concern 1", "Concern 2", "Concern 3"]
}}

WICHTIG: 
- Sei konservativ bei der Einstufung
- Bei Unsicherheit: Wähle höhere Risikokategorie
- Nenne konkrete Artikel aus dem AI Act
- Antworte NUR mit dem JSON-Objekt, keine zusätzlichen Erklärungen"""
        
        return prompt
    
    def _build_compliance_check_prompt(self, ai_system: AISystem, risk_category: str) -> str:
        """Build prompt for compliance checking"""
        
        # Get applicable requirements based on risk category
        applicable_requirements = [
            req for req in self.high_risk_requirements 
            if risk_category in req["mandatory_for"]
        ]
        
        requirements_text = "\n".join([
            f"- {req['article']}: {req['title']} - {req['description']}"
            for req in applicable_requirements
        ])
        
        prompt = f"""Du bist ein EU AI Act Compliance-Auditor. Prüfe das KI-System auf Compliance.

**KI-System:**
- Name: {ai_system.name}
- Beschreibung: {ai_system.description}
- Risikokategorie: {risk_category}
- Verwendungszweck: {ai_system.purpose}

**Zu prüfende Anforderungen:**
{requirements_text}

**Prüfe folgende Aspekte:**

FÜR ALLE SYSTEME:
□ Grundrechtsprüfung durchgeführt
□ Risikoanalyse dokumentiert
□ Verantwortlichkeiten definiert

FÜR HOCHRISIKO-SYSTEME (high):
□ Risikomanagementsystem etabliert (Art. 9)
□ Daten-Governance und Management (Art. 10)
□ Technische Dokumentation vollständig (Art. 11)
□ Aufzeichnungspflichten erfüllt (Art. 12)
□ Transparenz und Informationspflichten (Art. 13)
□ Menschliche Aufsicht gewährleistet (Art. 14)
□ Genauigkeit, Robustheit, Cybersicherheit (Art. 15)
□ Konformitätsbewertung durchgeführt
□ CE-Kennzeichnung vorhanden

FÜR BEGRENZTE RISIKEN (limited):
□ Transparenzpflichten erfüllt (Art. 52)
□ Kennzeichnung als KI vorhanden
□ Nutzer werden über KI-Interaktion informiert

**Antworte NUR mit validem JSON in folgendem Format:**

{{
  "overall_risk_score": 0.0-10.0,
  "requirements_met": [
    {{
      "requirement": "Art. X - Titel",
      "status": "erfüllt",
      "evidence": "Nachweis/Begründung"
    }}
  ],
  "requirements_failed": [
    {{
      "requirement": "Art. X - Titel",
      "status": "nicht erfüllt",
      "reason": "Grund für Nicht-Erfüllung",
      "severity": "critical|high|medium|low"
    }}
  ],
  "findings": [
    {{
      "category": "Kategorie",
      "severity": "critical|high|medium|low",
      "description": "Beschreibung des Findings",
      "recommendation": "Handlungsempfehlung"
    }}
  ],
  "recommendations": "Zusammenfassende Empfehlungen zur Umsetzung der Compliance"
}}

WICHTIG:
- Sei realistisch: Ohne detaillierte Dokumentation sind Requirements meist NICHT erfüllt
- Gib konkrete, umsetzbare Empfehlungen
- Priorisiere nach Severity
- Antworte NUR mit dem JSON-Objekt"""
        
        return prompt
    
    async def _call_ai_api(self, prompt: str, model: str = "anthropic/claude-3.5-sonnet") -> str:
        """
        Call OpenRouter API with Claude
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://complyo.tech",
            "X-Title": "Complyo AI Act Analyzer"
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # Low temperature for consistent, factual responses
            "max_tokens": 2000
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract response content
            content = result["choices"][0]["message"]["content"]
            
            # Clean JSON if wrapped in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return content

# Create singleton instance
ai_act_analyzer = AIActAnalyzer()

