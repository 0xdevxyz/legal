"""
Legal Change Monitor
Überwacht automatisch Gesetzesänderungen und generiert Compliance-Updates

Features:
- Automatische Erkennung von Gesetzesänderungen (DSGVO, ePrivacy, Barrierefreiheit, etc.)
- Zuordnung zu betroffenen Bereichen (Cookie-Compliance, Datenschutz, Impressum)
- KI-basierte Generierung von Fixes
- Automatische Benachrichtigung der Kunden
"""

import os
import json
import re
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LegalArea(str, Enum):
    """Rechtsbereiche"""
    COOKIE_COMPLIANCE = "cookie_compliance"
    DATENSCHUTZ = "datenschutz"
    IMPRESSUM = "impressum"
    BARRIEREFREIHEIT = "barrierefreiheit"
    WETTBEWERBSRECHT = "wettbewerbsrecht"
    VERBRAUCHERSCHUTZ = "verbraucherschutz"
    AI_ACT = "ai_act"


class ChangeSeverity(str, Enum):
    """Dringlichkeit der Änderung"""
    CRITICAL = "critical"  # Sofort umsetzen
    HIGH = "high"  # Innerhalb 7 Tage
    MEDIUM = "medium"  # Innerhalb 30 Tage
    LOW = "low"  # Innerhalb 90 Tage
    INFO = "info"  # Nur informativ


class LegalChange:
    """Datenmodell für Gesetzesänderung"""
    
    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        affected_areas: List[LegalArea],
        severity: ChangeSeverity,
        effective_date: datetime,
        source: str,
        source_url: str,
        requirements: List[str],
        detected_at: datetime = None
    ):
        self.id = id
        self.title = title
        self.description = description
        self.affected_areas = affected_areas
        self.severity = severity
        self.effective_date = effective_date
        self.source = source
        self.source_url = source_url
        self.requirements = requirements
        self.detected_at = detected_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "affected_areas": [area.value for area in self.affected_areas],
            "severity": self.severity.value,
            "effective_date": self.effective_date.isoformat(),
            "source": self.source,
            "source_url": self.source_url,
            "requirements": self.requirements,
            "detected_at": self.detected_at.isoformat()
        }


class ComplianceFix:
    """Datenmodell für automatischen Fix"""
    
    def __init__(
        self,
        legal_change_id: str,
        affected_area: LegalArea,
        fix_type: str,
        description: str,
        code_changes: Optional[Dict[str, str]] = None,
        config_changes: Optional[Dict[str, Any]] = None,
        manual_steps: Optional[List[str]] = None,
        priority: int = 5
    ):
        self.legal_change_id = legal_change_id
        self.affected_area = affected_area
        self.fix_type = fix_type
        self.description = description
        self.code_changes = code_changes or {}
        self.config_changes = config_changes or {}
        self.manual_steps = manual_steps or []
        self.priority = priority
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "legal_change_id": self.legal_change_id,
            "affected_area": self.affected_area.value,
            "fix_type": self.fix_type,
            "description": self.description,
            "code_changes": self.code_changes,
            "config_changes": self.config_changes,
            "manual_steps": self.manual_steps,
            "priority": self.priority
        }


class LegalChangeMonitor:
    """
    Hauptklasse für Gesetzesänderungs-Überwachung
    """
    
    def __init__(self, openrouter_api_key: str = None, db_pool=None):
        self.api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.db_pool = db_pool
        
        # Quellen für Gesetzesänderungen
        self.sources = {
            "eu_legislation": "https://eur-lex.europa.eu/homepage.html",
            "bundestag": "https://www.bundestag.de/gesetze",
            "datenschutz_konferenz": "https://www.datenschutzkonferenz-online.de/",
            "bfdi": "https://www.bfdi.bund.de/"
        }
        
        logger.info("🔍 Legal Change Monitor initialized")
    
    async def monitor_legal_changes(self) -> List[LegalChange]:
        """
        Überwacht automatisch Gesetzesänderungen
        """
        logger.info("🔍 Starting legal change monitoring...")
        
        # KI-basierte Recherche von aktuellen Gesetzesänderungen
        prompt = self._build_monitoring_prompt()
        
        try:
            changes_data = await self._call_ai_api(prompt)
            changes = self._parse_legal_changes(changes_data)
            
            logger.info(f"✅ Detected {len(changes)} legal changes")
            return changes
            
        except Exception as e:
            logger.error(f"❌ Legal change monitoring failed: {e}")
            return []

    async def on_legal_change(self, change: "LegalChange", legal_update_id: str) -> Dict[str, Any]:
        """
        Hook: Wird nach dem Persistieren einer Gesetzesänderung aufgerufen.
        Triggert Re-Generation betroffener Rechtstexte für alle User (severity >= medium).
        """
        if not self.db_pool:
            return {"skipped": True, "reason": "no db_pool"}

        try:
            from legal_text_generator import get_legal_text_generator
            generator = get_legal_text_generator(self.db_pool)
            affected_laws = [area.value for area in change.affected_areas]
            result = await generator.regenerate_affected_users(
                affected_laws=affected_laws,
                legal_update_id=str(legal_update_id),
                severity=change.severity.value,
            )
            logger.info(f"on_legal_change: Re-Generation abgeschlossen — {result}")
            return result
        except Exception as e:
            logger.error(f"on_legal_change: Re-Generation fehlgeschlagen: {e}", exc_info=True)
            return {"error": str(e)}

    async def _generate_declarative_check(self, change: "LegalChange", legal_update_id) -> Dict[str, Any]:
        """
        Erzeugt aus einer Gesetzesänderung eine deklarative Website-Prüfung
        (compliance_checks) via LLM. Neue Checks landen je nach Env-Flag als
        'pending_review' (Admin-GO) oder 'active'.
        """
        if not self.db_pool:
            return {"created": False, "reason": "no db_pool"}
        try:
            from compliance_engine.check_generator import generate_check_for_legal_update
            legal_update_dict = {
                "id": legal_update_id,
                "title": change.title,
                "description": change.description,
                "requirements": change.requirements,
                "effective_date": change.effective_date,
            }
            return await generate_check_for_legal_update(
                self.db_pool, legal_update_dict, self._call_ai_api
            )
        except Exception as e:
            logger.error(f"_generate_declarative_check failed: {e}", exc_info=True)
            return {"created": False, "reason": str(e)}

    async def monitor_and_persist(self) -> Dict[str, Any]:
        """
        Kompletter Durchlauf: Überwachen → DB speichern → Pipeline auslösen → Re-Generation.

        Wird vom Cronjob aufgerufen.

        Returns:
            {
                "detected": int,
                "new_saved": int,
                "pipeline_results": List[Dict],
                "regeneration_results": List[Dict]
            }
        """
        from compliance_engine.legal_update_integration import LegalUpdateIntegration

        summary: Dict[str, Any] = {
            "detected": 0,
            "new_saved": 0,
            "pipeline_results": [],
            "regeneration_results": [],
            "generated_checks": [],
        }

        if not self.db_pool:
            logger.warning("monitor_and_persist: kein db_pool — nur Erkennung ohne Persistenz")
            changes = await self.monitor_legal_changes()
            summary["detected"] = len(changes)
            return summary

        changes = await self.monitor_legal_changes()
        summary["detected"] = len(changes)

        integration = LegalUpdateIntegration(self.db_pool)

        for change in changes:
            try:
                saved_id = await self._save_change_to_db(change)
                if saved_id is None:
                    continue  # duplicate — already processed

                summary["new_saved"] += 1
                legal_update_dict = {
                    "id": saved_id,
                    "title": change.title,
                    "description": change.description,
                    "update_type": change.severity.value,
                    "severity": change.severity.value,
                }
                pipeline_result = await integration.process_new_legal_update(legal_update_dict)
                pipeline_result["legal_update_id"] = saved_id
                pipeline_result["title"] = change.title
                summary["pipeline_results"].append(pipeline_result)

                regen_result = await self.on_legal_change(change, str(saved_id))
                regen_result["legal_update_id"] = saved_id
                summary["regeneration_results"].append(regen_result)

                # NEU: Aus der Änderung automatisch eine deklarative Website-Prüfung
                # erzeugen (schließt die Lücke "neues Gesetz -> neue Prüfung").
                check_result = await self._generate_declarative_check(change, saved_id)
                check_result["legal_update_id"] = saved_id
                summary["generated_checks"].append(check_result)

            except Exception as e:
                logger.error(f"monitor_and_persist: Fehler bei change '{change.title}': {e}", exc_info=True)

        _checks_created = sum(1 for c in summary["generated_checks"] if c.get("created"))
        logger.info(
            f"monitor_and_persist: {summary['detected']} detected, "
            f"{summary['new_saved']} new, "
            f"{len(summary['pipeline_results'])} pipeline runs, "
            f"{len(summary['regeneration_results'])} regen runs, "
            f"{_checks_created} new compliance checks"
        )
        return summary

    async def _save_change_to_db(self, change: "LegalChange") -> Optional[int]:
        """
        Speichert eine LegalChange in die legal_updates Tabelle.

        Returns:
            ID des neuen Eintrags oder None wenn bereits vorhanden (duplicate title+date).
        """
        try:
            async with self.db_pool.acquire() as conn:
                existing = await conn.fetchval(
                    """
                    SELECT id FROM legal_updates
                    WHERE title = $1
                      AND published_at::date = $2::date
                    LIMIT 1
                    """,
                    change.title,
                    change.detected_at,
                )
                if existing:
                    return None

                new_id = await conn.fetchval(
                    """
                    INSERT INTO legal_updates
                      (update_type, title, description, severity,
                       source, published_at, effective_date, url)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                    """,
                    change.severity.value,
                    change.title,
                    change.description,
                    change.severity.value,
                    change.source,
                    change.detected_at,
                    change.effective_date,
                    change.source_url,
                )
                return new_id
        except Exception as e:
            logger.error(f"_save_change_to_db failed: {e}", exc_info=True)
            return None
    
    async def analyze_impact(
        self,
        legal_change: LegalChange,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analysiert die Auswirkungen einer Gesetzesänderung auf einen Kunden
        """
        logger.info(f"📊 Analyzing impact of {legal_change.title}...")
        
        prompt = f"""
Analysiere die Auswirkungen folgender Gesetzesänderung auf die Website eines Kunden:

# GESETZESÄNDERUNG
Titel: {legal_change.title}
Beschreibung: {legal_change.description}
Betroffene Bereiche: {', '.join([area.value for area in legal_change.affected_areas])}
Inkrafttreten: {legal_change.effective_date}
Anforderungen:
{chr(10).join([f"- {req}" for req in legal_change.requirements])}

# KUNDEN-KONTEXT
Website: {user_context.get('website_url', 'N/A')}
Aktuelle Compliance-Bereiche: {', '.join(user_context.get('compliance_areas', []))}
Verwendete Services: {', '.join(user_context.get('services', []))}

# AUFGABE
Bewerte:
1. Ist der Kunde von dieser Änderung betroffen? (ja/nein)
2. Welche konkreten Bereiche müssen angepasst werden?
3. Wie dringend ist die Umsetzung? (critical/high/medium/low)
4. Welche Risiken entstehen bei Nicht-Umsetzung?

Antworte im JSON-Format:
{{
    "is_affected": boolean,
    "affected_components": ["component1", "component2"],
    "urgency": "high",
    "risks": ["risk1", "risk2"],
    "estimated_effort": "2 hours",
    "recommendation": "Detaillierte Empfehlung"
}}
"""
        
        try:
            result = await self._call_ai_api(prompt)
            analysis = json.loads(result)
            
            logger.info(f"✅ Impact analysis completed. Affected: {analysis.get('is_affected', False)}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Impact analysis failed: {e}")
            return {
                "is_affected": True,
                "affected_components": ["unknown"],
                "urgency": "medium",
                "risks": ["Manuelle Prüfung erforderlich"],
                "estimated_effort": "unknown",
                "recommendation": "Bitte manuell prüfen"
            }
    
    async def generate_compliance_fixes(
        self,
        legal_change: LegalChange,
        impact_analysis: Dict[str, Any]
    ) -> List[ComplianceFix]:
        """
        Generiert automatisch Fixes für eine Gesetzesänderung
        """
        logger.info(f"🔧 Generating compliance fixes for {legal_change.title}...")
        
        if not impact_analysis.get('is_affected', False):
            logger.info("ℹ️ User not affected, skipping fix generation")
            return []
        
        fixes = []
        
        for area in legal_change.affected_areas:
            fix = await self._generate_fix_for_area(legal_change, area, impact_analysis)
            if fix:
                fixes.append(fix)
        
        logger.info(f"✅ Generated {len(fixes)} compliance fixes")
        return fixes
    
    async def _generate_fix_for_area(
        self,
        legal_change: LegalChange,
        area: LegalArea,
        impact_analysis: Dict[str, Any]
    ) -> Optional[ComplianceFix]:
        """
        Generiert einen Fix für einen spezifischen Bereich
        """
        prompt = f"""
Generiere einen konkreten Fix für folgende Gesetzesänderung im Bereich {area.value}:

# GESETZESÄNDERUNG
{legal_change.title}
{legal_change.description}

Anforderungen:
{chr(10).join([f"- {req}" for req in legal_change.requirements])}

# BEREICH
{area.value}

# IMPACT ANALYSIS
Betroffene Komponenten: {', '.join(impact_analysis.get('affected_components', []))}
Dringlichkeit: {impact_analysis.get('urgency', 'medium')}

# AUFGABE
Erstelle einen konkreten, umsetzbaren Fix:
1. Welche Code-Änderungen sind notwendig?
2. Welche Konfigurationen müssen angepasst werden?
3. Welche manuellen Schritte sind erforderlich?

Antworte im JSON-Format:
{{
    "fix_type": "automated" | "semi-automated" | "manual",
    "description": "Beschreibung des Fixes",
    "code_changes": {{
        "file_path": "code snippet oder Anleitung"
    }},
    "config_changes": {{
        "setting_name": "new_value"
    }},
    "manual_steps": ["Schritt 1", "Schritt 2"],
    "estimated_time": "30 minutes",
    "priority": 1-10
}}
"""
        
        try:
            result = await self._call_ai_api(prompt)
            fix_data = json.loads(result)
            
            fix = ComplianceFix(
                legal_change_id=legal_change.id,
                affected_area=area,
                fix_type=fix_data.get('fix_type', 'manual'),
                description=fix_data.get('description', ''),
                code_changes=fix_data.get('code_changes', {}),
                config_changes=fix_data.get('config_changes', {}),
                manual_steps=fix_data.get('manual_steps', []),
                priority=fix_data.get('priority', 5)
            )
            
            return fix
            
        except Exception as e:
            logger.error(f"❌ Fix generation failed for {area.value}: {e}")
            return None
    
    async def _call_ai_api(self, prompt: str) -> str:
        """
        Ruft die OpenRouter AI API auf
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": os.getenv("OPENROUTER_LEGAL_MODEL", "anthropic/claude-sonnet-4.5"),
            "messages": [
                {
                    "role": "system",
                    "content": "Du bist ein Experte für deutsches und europäisches Recht, spezialisiert auf Datenschutz, Cookie-Compliance und Web-Compliance. Du analysierst Gesetzesänderungen und generierst konkrete, umsetzbare Lösungen."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return data['choices'][0]['message']['content']
    
    def _build_monitoring_prompt(self) -> str:
        """
        Erstellt den Prompt für die Gesetzesänderungs-Überwachung
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        return f"""
Recherchiere aktuelle Gesetzesänderungen im Bereich Web-Compliance für deutsche Websites.

# ZEITRAUM
Letzte 30 Tage bis heute ({today})

# BEREICHE
- Cookie-Compliance & ePrivacy
- DSGVO / Datenschutz
- Impressumspflicht
- Barrierefreiheit (BFSG, WCAG)
- Wettbewerbsrecht
- Verbraucherschutz
- EU AI Act

# QUELLEN
- EU-Recht (eur-lex.europa.eu)
- Deutsche Gesetzgebung
- Datenschutzkonferenz
- BfDI (Bundesbeauftragter für Datenschutz)
- Relevante Gerichtsurteile

# AUFGABE
Liste alle relevanten Gesetzesänderungen, Urteile oder neue Anforderungen auf.

Antworte im JSON-Format:
{{
    "changes": [
        {{
            "id": "unique_id",
            "title": "Titel der Änderung",
            "description": "Detaillierte Beschreibung",
            "affected_areas": ["cookie_compliance", "datenschutz"],
            "severity": "critical" | "high" | "medium" | "low" | "info",
            "effective_date": "2025-01-01",
            "source": "EU-Verordnung 2024/xxx",
            "source_url": "https://...",
            "requirements": ["Anforderung 1", "Anforderung 2"]
        }}
    ]
}}

Fokussiere auf Änderungen, die KONKRETE Auswirkungen auf Websites haben.

WICHTIG: Antworte AUSSCHLIESSLICH mit dem puren JSON-Objekt — keine Einleitung,
keine Erklärung, keine Markdown-Codeblöcke, kein Text davor oder danach.
Wenn keine relevanten Änderungen vorliegen, antworte mit {{"changes": []}}.
"""
    
    @staticmethod
    def _extract_json(text: str) -> str:
        """
        Holt das JSON-Objekt aus einer LLM-Antwort, auch wenn es in
        ```json ... ``` Fences steckt oder von Prosa umgeben ist.
        """
        if not text:
            return text
        # 1) Inhalt eines Markdown-Codefence bevorzugen (greedy bis zum schließenden Fence)
        fence = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if fence:
            text = fence.group(1)
        # 2) Vom ersten { bis zum letzten } greifen
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1]
        return text

    def _change_from_dict(self, change_data: Dict[str, Any]) -> Optional["LegalChange"]:
        """Baut ein LegalChange aus einem Dict; gibt None bei ungültigen Daten zurück."""
        try:
            return LegalChange(
                id=change_data['id'],
                title=change_data['title'],
                description=change_data['description'],
                affected_areas=[LegalArea(area) for area in change_data['affected_areas']],
                severity=ChangeSeverity(change_data['severity']),
                effective_date=datetime.fromisoformat(change_data['effective_date']),
                source=change_data['source'],
                source_url=change_data['source_url'],
                requirements=change_data['requirements'],
            )
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse legal change: {e}")
            return None

    def _parse_legal_changes(self, json_response: str) -> List[LegalChange]:
        """
        Parsed die KI-Antwort zu LegalChange-Objekten.

        Robust gegen LLM-Eigenheiten: extrahiert JSON aus Fences/Prosa und fällt
        bei invalidem Gesamt-JSON auf Pro-Objekt-Salvage zurück (ein fehlerhaftes
        Objekt verwirft nicht mehr die ganze Antwort).
        """
        extracted = self._extract_json(json_response)

        # Pfad A: Gesamt-JSON parsen
        try:
            data = json.loads(extracted)
            changes = [c for c in (self._change_from_dict(cd) for cd in data.get('changes', [])) if c]
            return changes
        except Exception as e:
            logger.warning(f"⚠️ Gesamt-JSON ungültig ({e}) — versuche Pro-Objekt-Salvage")

        # Pfad B: Salvage — einzelne {...}-Objekte im changes-Array bergen
        changes = []
        for obj_match in re.finditer(r"\{[^{}]*\}", extracted, re.DOTALL):
            snippet = obj_match.group(0)
            if '"title"' not in snippet or '"affected_areas"' not in snippet:
                continue
            try:
                change = self._change_from_dict(json.loads(snippet))
                if change:
                    changes.append(change)
            except Exception:
                continue

        if changes:
            logger.info(f"✅ Salvage: {len(changes)} Änderungen aus invalidem JSON geborgen")
        else:
            logger.error("❌ Failed to parse legal changes: auch Salvage ergab 0 Objekte")
        return changes


# Globale Instanz
legal_monitor = None


def init_legal_monitor(openrouter_api_key: str, db_pool=None):
    """Initialisiert den Legal Change Monitor"""
    global legal_monitor
    legal_monitor = LegalChangeMonitor(openrouter_api_key, db_pool=db_pool)
    return legal_monitor

