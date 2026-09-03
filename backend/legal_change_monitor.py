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

# Prometheus-Zähler für OpenRouter-Aufrufe (Muster wie ai_review_engine).
# Fail-open: ohne metrics-Modul (z.B. isolierte Tests) laufen die Calls ohne Zähler.
try:
    from metrics import openrouter_requests_total as _openrouter_counter
except Exception:
    _openrouter_counter = None


class LegalArea(str, Enum):
    """Rechtsbereiche"""
    COOKIE_COMPLIANCE = "cookie_compliance"
    DATENSCHUTZ = "datenschutz"
    IMPRESSUM = "impressum"
    BARRIEREFREIHEIT = "barrierefreiheit"
    WETTBEWERBSRECHT = "wettbewerbsrecht"
    VERBRAUCHERSCHUTZ = "verbraucherschutz"
    AI_ACT = "ai_act"
    # EU-Verpackungsverordnung (PPWR, VO (EU) 2025/40, erste Pflichten ab 12.08.2026).
    # Trifft Shop-Kunden über Kennzeichnungs- und Informationspflichten; ohne eigenen
    # Enum-Wert verwarf `_change_from_dict()` jede Meldung dazu komplett.
    VERPACKUNG = "verpackung"


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
        Extrahiert Rechtsänderungen aus den neuen RSS-News seit dem letzten Lauf.

        Grounding statt freier LLM-Recherche: Das LLM bekommt AUSSCHLIESSLICH
        das Material der RSS-News-Pipeline (legal_news, täglicher fetch_news-Cron)
        als Quelle. Ohne neue News gibt es KEINEN LLM-Call — der Lauf endet mit
        0 Änderungen. Das verhindert halluzinierte "Gesetzesänderungen" ohne
        belegbare Quelle.
        """
        logger.info("🔍 Starting legal change monitoring...")

        news_items = await self._fetch_news_since_last_run()
        if not news_items:
            logger.info("✅ 0 neue News seit letztem Lauf — kein LLM-Call, 0 Änderungen")
            return []

        prompt = self._build_monitoring_prompt(news_items)

        try:
            changes_data = await self._call_ai_api(prompt)
            changes = self._parse_legal_changes(changes_data)

            logger.info(f"✅ Detected {len(changes)} legal changes aus {len(news_items)} News")
            return changes

        except Exception as e:
            logger.error(f"❌ Legal change monitoring failed: {e}")
            return []

    async def _fetch_news_since_last_run(self) -> List[Dict[str, Any]]:
        """
        Liest neue Einträge der RSS-News-Pipeline (Tabelle legal_news, befüllt
        vom täglichen 06:00-Cron cronjobs/fetch_news.py) seit dem letzten
        erfolgreichen Monitor-Lauf (legal_monitoring_logs.scan_date).

        Ohne db_pool gibt es keine Quellen — dann bewusst leere Liste statt
        eines ungegroundeten LLM-Calls.
        """
        if not self.db_pool:
            logger.warning("_fetch_news_since_last_run: kein db_pool — keine Quellen verfügbar")
            return []
        try:
            async with self.db_pool.acquire() as conn:
                last_run = await conn.fetchval(
                    """
                    SELECT MAX(scan_date) FROM legal_monitoring_logs
                    WHERE status = 'completed'
                    """
                )
                if last_run:
                    rows = await conn.fetch(
                        """
                        SELECT id, title, summary, url, source, published_date,
                               news_type, severity, keywords
                        FROM legal_news
                        WHERE is_active = TRUE
                          AND COALESCE(fetched_date, created_at) > $1
                        ORDER BY published_date DESC NULLS LAST
                        LIMIT 50
                        """,
                        last_run,
                    )
                else:
                    # Erster Lauf ohne Log-Historie: letzte 7 Tage als Startfenster
                    rows = await conn.fetch(
                        """
                        SELECT id, title, summary, url, source, published_date,
                               news_type, severity, keywords
                        FROM legal_news
                        WHERE is_active = TRUE
                          AND COALESCE(fetched_date, created_at) > NOW() - INTERVAL '7 days'
                        ORDER BY published_date DESC NULLS LAST
                        LIMIT 50
                        """
                    )
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"_fetch_news_since_last_run failed: {e}", exc_info=True)
            return []

    async def on_legal_change(self, change: "LegalChange", legal_update_id: str) -> Dict[str, Any]:
        """
        Hook: Wird nach dem Persistieren einer NEUEN (Nicht-Duplikat-)Gesetzesänderung
        aufgerufen. Triggert Re-Generation betroffener Rechtstexte für alle User.
        Aufrufer (monitor_and_persist) ruft nur bei severity high/critical.
        """
        if not self.db_pool:
            return {"skipped": True, "reason": "no db_pool"}

        try:
            from legal_text_generator import get_legal_text_generator
            generator = get_legal_text_generator(self.db_pool)
            # LegalArea-Werte werden im Generator via LEGAL_AREA_TO_DOCUMENT_TYPES aufgelöst
            affected_areas = [area.value for area in change.affected_areas]
            result = await generator.regenerate_affected_users(
                affected_areas=affected_areas,
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
            "duplicates": 0,
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
                    # Duplikat (oder DB-Fehler) — bewusst KOMPLETT überspringen:
                    # keine Pipeline, keine Notifications, keine Re-Generation.
                    summary["duplicates"] += 1
                    continue

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

                # Re-Generation NUR bei hoher Dringlichkeit: medium/low/info lösen
                # keine flächendeckende Rechtstext-Regeneration mehr aus.
                if change.severity in (ChangeSeverity.HIGH, ChangeSeverity.CRITICAL):
                    regen_result = await self.on_legal_change(change, str(saved_id))
                else:
                    regen_result = {
                        "skipped": True,
                        "reason": f"severity '{change.severity.value}' < high",
                    }
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
            f"{summary['duplicates']} duplicates skipped, "
            f"{len(summary['pipeline_results'])} pipeline runs, "
            f"{len(summary['regeneration_results'])} regen runs, "
            f"{_checks_created} new compliance checks"
        )
        return summary

    async def _save_change_to_db(self, change: "LegalChange") -> Optional[int]:
        """
        Speichert eine LegalChange in die legal_updates Tabelle.

        Duplikat-Erkennung: Vergleich über den normalisierten Titel OHNE
        Datumsfenster. Das frühere `AND published_at::date = heute` hat dieselbe
        Änderung an jedem Folgetag erneut gespeichert (83× identische Einträge
        über Wochen).

        Returns:
            ID des neuen Eintrags oder None wenn bereits vorhanden (gleicher Titel).
        """
        try:
            async with self.db_pool.acquire() as conn:
                existing = await conn.fetchval(
                    """
                    SELECT id FROM legal_updates
                    WHERE lower(trim(title)) = lower(trim($1))
                    LIMIT 1
                    """,
                    change.title,
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
            try:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
            except Exception:
                # Jeder fehlgeschlagene OpenRouter-Call zählt als error
                if _openrouter_counter:
                    _openrouter_counter.labels(status="error").inc()
                raise

            if _openrouter_counter:
                _openrouter_counter.labels(status="success").inc()

            data = response.json()

            return data['choices'][0]['message']['content']
    
    def _build_monitoring_prompt(self, news_items: List[Dict[str, Any]]) -> str:
        """
        Erstellt den Prompt für die Extraktion von Rechtsänderungen aus
        RSS-News-Material (Grounding).

        Anti-Halluzination: Das LLM darf AUSSCHLIESSLICH aus dem übergebenen
        Quellmaterial extrahieren — keine freie Recherche, kein eigenes Wissen.
        Das Ausgabeformat (JSON mit "changes"-Array) bleibt exakt das, was
        _parse_legal_changes / monitor_and_persist erwarten.
        """
        material_teile = []
        for item in news_items:
            published = item.get("published_date")
            published_str = (
                published.strftime("%Y-%m-%d")
                if hasattr(published, "strftime")
                else str(published or "unbekannt")
            )
            summary = (item.get("summary") or "").strip()
            material_teile.append(
                f"### News #{item.get('id')}\n"
                f"Titel: {item.get('title', '')}\n"
                f"Quelle: {item.get('source') or 'unbekannt'}\n"
                f"URL: {item.get('url') or '-'}\n"
                f"Veröffentlicht: {published_str}\n"
                f"Zusammenfassung: {summary[:600] or '-'}"
            )
        material = "\n\n".join(material_teile)

        return f"""
Extrahiere Gesetzesänderungen im Bereich Web-Compliance für deutsche Websites
AUSSCHLIESSLICH aus dem folgenden Quellmaterial (RSS-News unserer Pipeline).

# QUELLMATERIAL ({len(news_items)} News-Einträge)
{material}

# STRIKTE REGELN (Anti-Halluzination)
- Verwende NUR Informationen, die im Quellmaterial oben stehen.
- Ergänze NICHTS aus eigenem Wissen — keine Gesetze, Urteile oder Fristen,
  die nicht im Material vorkommen.
- Jede gemeldete Änderung muss sich auf mindestens einen News-Eintrag
  zurückführen lassen; nutze dessen URL als "source_url" und dessen Quelle
  als "source".
- Steht ein Inkrafttretens-Datum nicht im Material, nutze das
  Veröffentlichungsdatum der News als "effective_date".
- Reine Meinungsartikel, Ratgeber oder Produktwerbung ohne konkrete neue
  Rechtspflicht sind KEINE Änderung — weglassen.
- Fasse mehrere News zum selben Sachverhalt zu EINER Änderung zusammen.

# RELEVANTE BEREICHE
- Cookie-Compliance & ePrivacy
- DSGVO / Datenschutz
- Impressumspflicht
- Barrierefreiheit (BFSG, WCAG)
- Wettbewerbsrecht
- Verbraucherschutz
- EU AI Act
- EU-Verpackungsverordnung (PPWR) — Kennzeichnungs- und Informationspflichten für Shops

# AUFGABE
Liste alle Gesetzesänderungen, Urteile oder neuen Anforderungen aus dem
Quellmaterial auf, die KONKRETE Auswirkungen auf Websites haben.

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

"affected_areas" darf AUSSCHLIESSLICH diese Werte enthalten — jeder andere Wert
führt dazu, dass die komplette Meldung verworfen wird:
cookie_compliance | datenschutz | impressum | barrierefreiheit |
wettbewerbsrecht | verbraucherschutz | ai_act | verpackung

WICHTIG: Antworte AUSSCHLIESSLICH mit dem puren JSON-Objekt — keine Einleitung,
keine Erklärung, keine Markdown-Codeblöcke, kein Text davor oder danach.
Wenn das Quellmaterial keine relevanten Änderungen enthält, antworte mit
{{"changes": []}}.
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

