"""
Legal Text Generator — interner Ersatz für eRecht24-Anbindung.

Generiert Rechtstexte (Impressum, Datenschutz, AGB, Cookie-Policy) vollständig intern:
- Quelle: knowledge/laws/{language}/ + knowledge/templates/legal/
- KI-Backend: OpenRouter (Claude) via ai_document_generator._call_openrouter
- Versionierung: generated_documents-Tabelle mit is_active-Flag
- Auto-Re-Generation: wird von legal_change_monitor getriggert

Kein externer API-Key erforderlich. Kein Abmahnschutz-Versprechen.
Disclaimer wird automatisch angehängt (legal_disclaimer.py).
"""

from __future__ import annotations

import os
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

# asyncpg/aiohttp sind in der Produktion (Docker) vorhanden. Die Imports werden
# tolerant gehalten, damit Template-/Prompt-Logik auch ohne DB/HTTP-Treiber
# (z.B. in Unit-Tests) importierbar bleibt. Annotationen sind via
# `from __future__ import annotations` ohnehin lazy.
try:
    import asyncpg
except ImportError:  # pragma: no cover
    asyncpg = None

try:
    import aiohttp
except ImportError:  # pragma: no cover
    aiohttp = None

from legal_disclaimer import DISCLAIMER_LONG, DISCLAIMER_HTML
from complyo_privacy_clause import build_complyo_privacy_clause
from third_country_clause import build_third_country_clause

logger = logging.getLogger(__name__)

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge", "templates", "legal")
LAWS_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge", "laws")


class DocumentType(str, Enum):
    IMPRINT = "imprint"
    PRIVACY = "privacy"
    TOS = "tos"
    COOKIE_POLICY = "cookie-policy"
    WITHDRAWAL = "withdrawal"  # Widerrufsbelehrung inkl. Muster-Widerrufsformular (B2C)


@dataclass
class GeneratedDocument:
    document_id: Optional[int]
    user_id: int
    document_type: str
    language: str
    html_content: str
    plain_text: str
    template_version: str
    legal_update_id: Optional[str]
    regeneration_trigger: str
    is_active: bool
    generated_at: str
    disclaimer: str
    metadata: Dict[str, Any]


class LegalTextGenerator:
    """
    Hauptklasse für interne Rechtstexte-Generierung.
    Ersetzt eRecht24 vollständig.
    """

    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = "anthropic/claude-sonnet-4.5"
    TEMPLATE_VERSION = "1.0"

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not set — LegalTextGenerator will use fallback templates")

    async def generate_imprint(
        self,
        user_id: int,
        user_data: Dict[str, str],
        language: str = "de",
        legal_update_id: Optional[str] = None,
        regeneration_trigger: str = "manual",
    ) -> GeneratedDocument:
        template = self._load_template(DocumentType.IMPRINT, language)
        laws_context = self._load_laws_context(["Impressumspflicht"], language)
        prompt = self._build_prompt(template, user_data, laws_context, DocumentType.IMPRINT)
        html = await self._call_ai(prompt)
        html_with_disclaimer = html + DISCLAIMER_HTML
        doc_id = await self._save(
            user_id, DocumentType.IMPRINT, language, html_with_disclaimer,
            legal_update_id, regeneration_trigger, user_data=user_data
        )
        return GeneratedDocument(
            document_id=doc_id,
            user_id=user_id,
            document_type=DocumentType.IMPRINT,
            language=language,
            html_content=html_with_disclaimer,
            plain_text=self._strip_html(html_with_disclaimer),
            template_version=self.TEMPLATE_VERSION,
            legal_update_id=legal_update_id,
            regeneration_trigger=regeneration_trigger,
            is_active=True,
            generated_at=datetime.now().isoformat(),
            disclaimer=DISCLAIMER_LONG,
            metadata={"user_data_hash": self._hash(user_data)},
        )

    async def generate_privacy_policy(
        self,
        user_id: int,
        user_data: Dict[str, str],
        services_used: Optional[List[str]] = None,
        language: str = "de",
        legal_update_id: Optional[str] = None,
        regeneration_trigger: str = "manual",
        complyo_context: Optional[Dict[str, Any]] = None,
    ) -> GeneratedDocument:
        template = self._load_template(DocumentType.PRIVACY, language)
        laws_context = self._load_laws_context(["DSGVO", "TTDSG"], language)
        enriched_data = {**user_data}
        if services_used is not None:
            enriched_data["services_used"] = ", ".join(services_used)
        elif "services_used" not in enriched_data:
            enriched_data["services_used"] = ""

        # Complyo-Passus: explizit übergebener Kontext hat Vorrang; andernfalls
        # aus persistierten user_data lesen, damit das Auto-Update
        # (regenerate_affected_users) den Abschnitt identisch reproduziert.
        if complyo_context is None:
            complyo_context = enriched_data.get("complyo_context")
        if complyo_context:
            enriched_data["complyo_context"] = complyo_context

        # Drittland-Abschnitt deterministisch aus der SSOT (Art. 49 / Art. 44 ff.),
        # damit Länderliste und Rechtsgrundlage nicht der KI-Varianz unterliegen.
        # Beim Auto-Update kommt services_used=None — dann aus den persistierten
        # user_data (komma-separiert) rekonstruieren, damit der Abschnitt identisch
        # reproduziert wird statt zu verschwinden.
        effective_services = services_used
        if effective_services is None:
            persisted = enriched_data.get("services_used") or ""
            effective_services = [s.strip() for s in persisted.split(",") if s.strip()]
        third_country_clause = build_third_country_clause(effective_services)

        prompt = self._build_prompt(template, enriched_data, laws_context, DocumentType.PRIVACY)
        if complyo_context:
            # Verhindert, dass die KI einen eigenen, abweichenden Abschnitt zum
            # Consent-Tool erzeugt — der Complyo-Passus wird deterministisch angehängt.
            prompt += (
                "\n\nWICHTIG: Erstelle KEINEN eigenen Abschnitt zum eingesetzten "
                "Cookie-/Consent-Management-Tool oder zum Barrierefreiheits-Assistenten "
                "— dieser wird separat ergänzt.\n"
            )
        if third_country_clause:
            # Doppelten/abweichenden Drittland-Abschnitt der KI vermeiden — der
            # juristische Wortlaut wird deterministisch angehängt.
            prompt += (
                "\n\nWICHTIG: Erstelle KEINEN eigenen, aufgezählten Abschnitt zur "
                "Datenübermittlung in Drittländer für die genannten Dienste — dieser "
                "wird mit geprüftem Wortlaut separat ergänzt.\n"
            )

        html = await self._call_ai(prompt)
        complyo_clause = build_complyo_privacy_clause(complyo_context) if complyo_context else ""
        html_with_disclaimer = html + complyo_clause + third_country_clause + DISCLAIMER_HTML
        doc_id = await self._save(
            user_id, DocumentType.PRIVACY, language, html_with_disclaimer,
            legal_update_id, regeneration_trigger, user_data=enriched_data
        )
        return GeneratedDocument(
            document_id=doc_id,
            user_id=user_id,
            document_type=DocumentType.PRIVACY,
            language=language,
            html_content=html_with_disclaimer,
            plain_text=self._strip_html(html_with_disclaimer),
            template_version=self.TEMPLATE_VERSION,
            legal_update_id=legal_update_id,
            regeneration_trigger=regeneration_trigger,
            is_active=True,
            generated_at=datetime.now().isoformat(),
            disclaimer=DISCLAIMER_LONG,
            metadata={
                "services": services_used or [],
                "complyo_clause": bool(complyo_context),
                "user_data_hash": self._hash(user_data),
            },
        )

    async def generate_tos(
        self,
        user_id: int,
        user_data: Dict[str, str],
        business_type: str = "saas",
        language: str = "de",
        legal_update_id: Optional[str] = None,
        regeneration_trigger: str = "manual",
    ) -> GeneratedDocument:
        template = self._load_template(DocumentType.TOS, language)
        laws_context = self._load_laws_context(["AGB-Recht", "UWG"], language)
        enriched_data = {**user_data}
        if business_type:
            enriched_data["business_type"] = business_type
        elif "business_type" not in enriched_data:
            enriched_data["business_type"] = "saas"
        prompt = self._build_prompt(template, enriched_data, laws_context, DocumentType.TOS)
        html = await self._call_ai(prompt)
        html_with_disclaimer = html + DISCLAIMER_HTML
        doc_id = await self._save(
            user_id, DocumentType.TOS, language, html_with_disclaimer,
            legal_update_id, regeneration_trigger, user_data=enriched_data
        )
        return GeneratedDocument(
            document_id=doc_id,
            user_id=user_id,
            document_type=DocumentType.TOS,
            language=language,
            html_content=html_with_disclaimer,
            plain_text=self._strip_html(html_with_disclaimer),
            template_version=self.TEMPLATE_VERSION,
            legal_update_id=legal_update_id,
            regeneration_trigger=regeneration_trigger,
            is_active=True,
            generated_at=datetime.now().isoformat(),
            disclaimer=DISCLAIMER_LONG,
            metadata={"business_type": business_type, "user_data_hash": self._hash(user_data)},
        )

    async def generate_cookie_policy(
        self,
        user_id: int,
        user_data: Dict[str, str],
        cookie_inventory: Optional[List[Dict[str, str]]] = None,
        language: str = "de",
        legal_update_id: Optional[str] = None,
        regeneration_trigger: str = "manual",
    ) -> GeneratedDocument:
        template = self._load_template(DocumentType.COOKIE_POLICY, language)
        laws_context = self._load_laws_context(["TTDSG", "DSGVO"], language)
        enriched_data = {**user_data}
        if cookie_inventory is not None:
            enriched_data["cookie_inventory"] = json.dumps(cookie_inventory, ensure_ascii=False)
        elif "cookie_inventory" not in enriched_data:
            enriched_data["cookie_inventory"] = "[]"
        prompt = self._build_prompt(template, enriched_data, laws_context, DocumentType.COOKIE_POLICY)
        html = await self._call_ai(prompt)
        html_with_disclaimer = html + DISCLAIMER_HTML
        doc_id = await self._save(
            user_id, DocumentType.COOKIE_POLICY, language, html_with_disclaimer,
            legal_update_id, regeneration_trigger, user_data=enriched_data
        )
        return GeneratedDocument(
            document_id=doc_id,
            user_id=user_id,
            document_type=DocumentType.COOKIE_POLICY,
            language=language,
            html_content=html_with_disclaimer,
            plain_text=self._strip_html(html_with_disclaimer),
            template_version=self.TEMPLATE_VERSION,
            legal_update_id=legal_update_id,
            regeneration_trigger=regeneration_trigger,
            is_active=True,
            generated_at=datetime.now().isoformat(),
            disclaimer=DISCLAIMER_LONG,
            metadata={"cookie_count": len(cookie_inventory or []), "user_data_hash": self._hash(user_data)},
        )

    async def generate_withdrawal(
        self,
        user_id: int,
        user_data: Dict[str, str],
        language: str = "de",
        legal_update_id: Optional[str] = None,
        regeneration_trigger: str = "manual",
    ) -> GeneratedDocument:
        """Widerrufsbelehrung inkl. gesetzlichem Muster-Widerrufsformular (B2C-Fernabsatz)."""
        template = self._load_template(DocumentType.WITHDRAWAL, language)
        laws_context = self._load_laws_context(["Widerrufsrecht", "Verbraucherrecht", "AGB-Recht"], language)
        prompt = self._build_prompt(template, user_data, laws_context, DocumentType.WITHDRAWAL)
        html = await self._call_ai(prompt)
        html_with_disclaimer = html + DISCLAIMER_HTML
        doc_id = await self._save(
            user_id, DocumentType.WITHDRAWAL, language, html_with_disclaimer,
            legal_update_id, regeneration_trigger, user_data=user_data
        )
        return GeneratedDocument(
            document_id=doc_id,
            user_id=user_id,
            document_type=DocumentType.WITHDRAWAL,
            language=language,
            html_content=html_with_disclaimer,
            plain_text=self._strip_html(html_with_disclaimer),
            template_version=self.TEMPLATE_VERSION,
            legal_update_id=legal_update_id,
            regeneration_trigger=regeneration_trigger,
            is_active=True,
            generated_at=datetime.now().isoformat(),
            disclaimer=DISCLAIMER_LONG,
            metadata={"user_data_hash": self._hash(user_data)},
        )

    async def get_active_document(
        self, user_id: int, document_type: DocumentType
    ) -> Optional[Dict[str, Any]]:
        """Holt das aktive Dokument eines Users aus der DB."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, document_type, language, html_content, content,
                       template_version, legal_update_id, regeneration_trigger,
                       metadata, created_at, updated_at
                FROM generated_documents
                WHERE user_id = $1
                  AND document_type = $2
                  AND (metadata->>'is_active')::boolean IS NOT FALSE
                ORDER BY created_at DESC
                LIMIT 1
                """,
                user_id,
                document_type.value,
            )
            if not row:
                return None
            return dict(row)

    async def get_document_history(
        self, user_id: int, document_type: DocumentType, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Gibt die Versionshistorie eines Dokuments zurück."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, document_type, language, template_version,
                       legal_update_id, regeneration_trigger,
                       metadata, created_at
                FROM generated_documents
                WHERE user_id = $1 AND document_type = $2
                ORDER BY created_at DESC
                LIMIT $3
                """,
                user_id,
                document_type.value,
                limit,
            )
            return [dict(r) for r in rows]

    async def regenerate_affected_users(
        self,
        affected_laws: List[str],
        legal_update_id: str,
        severity: str = "medium",
    ) -> Dict[str, Any]:
        """
        Wird von legal_change_monitor getriggert.
        Re-generiert Dokumente für alle User, die betroffene Rechtstexte haben.
        Nur bei severity >= 'medium'.
        """
        severity_order = ["info", "low", "medium", "high", "critical"]
        if severity_order.index(severity.lower()) < severity_order.index("medium"):
            logger.info(f"Re-Generation übersprungen: severity={severity} < medium")
            return {"skipped": True, "reason": f"severity {severity} < medium"}

        doc_type_map = {
            "Impressumspflicht": [DocumentType.IMPRINT],
            "DSGVO": [DocumentType.PRIVACY, DocumentType.COOKIE_POLICY],
            "TTDSG": [DocumentType.PRIVACY, DocumentType.COOKIE_POLICY],
            "AGB-Recht": [DocumentType.TOS, DocumentType.WITHDRAWAL],
            "UWG": [DocumentType.TOS],
            "Widerrufsrecht": [DocumentType.WITHDRAWAL],
            "Verbraucherrecht": [DocumentType.WITHDRAWAL],
            "BFSG": [DocumentType.IMPRINT],
        }
        affected_doc_types = set()
        for law in affected_laws:
            for key, types in doc_type_map.items():
                if key.lower() in law.lower():
                    affected_doc_types.update(types)

        if not affected_doc_types:
            logger.info(f"Keine betroffenen Dokumenttypen für laws={affected_laws}")
            return {"skipped": True, "reason": "no affected document types"}

        async with self.db_pool.acquire() as conn:
            user_ids = await conn.fetch(
                """
                SELECT DISTINCT user_id FROM generated_documents
                WHERE document_type = ANY($1)
                  AND (metadata->>'is_active')::boolean IS NOT FALSE
                """,
                [dt.value for dt in affected_doc_types],
            )

        triggered = 0
        for row in user_ids:
            uid = row["user_id"]
            for dt in affected_doc_types:
                existing = await self.get_active_document(uid, dt)
                if not existing:
                    continue
                meta = existing.get("metadata") or {}
                if isinstance(meta, str):
                    meta = json.loads(meta)
                user_data = meta.get("user_data", {})
                if not user_data:
                    logger.warning(f"Keine user_data für user_id={uid}, doc_type={dt} — skip")
                    continue
                try:
                    if dt == DocumentType.IMPRINT:
                        await self.generate_imprint(uid, user_data, legal_update_id=legal_update_id, regeneration_trigger="legal_update")
                    elif dt == DocumentType.PRIVACY:
                        await self.generate_privacy_policy(uid, user_data, legal_update_id=legal_update_id, regeneration_trigger="legal_update")
                    elif dt == DocumentType.TOS:
                        await self.generate_tos(uid, user_data, legal_update_id=legal_update_id, regeneration_trigger="legal_update")
                    elif dt == DocumentType.COOKIE_POLICY:
                        await self.generate_cookie_policy(uid, user_data, legal_update_id=legal_update_id, regeneration_trigger="legal_update")
                    elif dt == DocumentType.WITHDRAWAL:
                        await self.generate_withdrawal(uid, user_data, legal_update_id=legal_update_id, regeneration_trigger="legal_update")
                    triggered += 1
                except Exception as e:
                    logger.error(f"Re-Generation fehlgeschlagen für user_id={uid}, doc_type={dt}: {e}")

        logger.info(f"Re-Generation abgeschlossen: {triggered} Dokumente für {len(user_ids)} User")
        return {
            "triggered": triggered,
            "affected_users": len(user_ids),
            "affected_doc_types": [dt.value for dt in affected_doc_types],
            "legal_update_id": legal_update_id,
        }

    async def _call_ai(self, prompt: str) -> str:
        if not self.api_key:
            return self._fallback_template(prompt)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://complyo.tech",
            "X-Title": "Complyo Legal Text Generator",
        }
        payload = {
            "model": self.MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Du bist ein Experte für deutsches und europäisches Compliance-Recht. "
                        "Generiere vollständige, strukturierte Rechtstexte im HTML-Format. "
                        "Nutze semantische Tags (h1, h2, h3, p, ul, li). Keine CSS-Inline-Styles. "
                        "Beginne direkt mit dem HTML-Code, ohne Markdown-Wrapper."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 4000,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=90),
            ) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    logger.error(f"OpenRouter Fehler {resp.status}: {err}")
                    return self._fallback_template(prompt)
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    def _build_prompt(
        self,
        template: str,
        user_data: Dict[str, str],
        laws_context: str,
        doc_type: DocumentType,
    ) -> str:
        # generated_at automatisch ergänzen, falls nicht vom Aufrufer gesetzt
        fill_data = {"generated_at": datetime.now().strftime("%d.%m.%Y"), **user_data}
        filled = template
        for key, value in fill_data.items():
            filled = filled.replace(f"{{{{{key}}}}}", str(value))

        doc_labels = {
            DocumentType.IMPRINT: "Impressum gemäß §5 TMG / §55 RStV",
            DocumentType.PRIVACY: "Datenschutzerklärung gemäß DSGVO Art. 13-14 & TTDSG",
            DocumentType.TOS: "Allgemeine Geschäftsbedingungen (AGB)",
            DocumentType.COOKIE_POLICY: "Cookie-Richtlinie gemäß TTDSG & DSGVO",
            DocumentType.WITHDRAWAL: "Widerrufsbelehrung inkl. Muster-Widerrufsformular gemäß §312g, §355 BGB & Art. 246a EGBGB",
        }
        return (
            f"Generiere ein vollständiges {doc_labels[doc_type]}.\n\n"
            f"## Firmendaten\n{filled}\n\n"
            f"## Relevante Rechtsgrundlagen\n{laws_context}\n\n"
            "## Anforderungen\n"
            "- Vollständiges HTML-Dokument\n"
            "- Alle Pflichtangaben gemäß den o.g. Gesetzen\n"
            "- Barrierefreie Struktur (h1, h2, h3, p, ul, li)\n"
            "- Professioneller, sachlicher Stil\n"
            "- Keine CSS-Inline-Styles\n"
            "- Keine Platzhalter im fertigen Text\n"
            "- Beginne direkt mit <h1>...\n"
        )

    def _load_template(self, doc_type: DocumentType, language: str) -> str:
        filename = f"{doc_type.value}_{language}.md"
        path = os.path.join(TEMPLATES_DIR, filename)
        fallback_path = os.path.join(TEMPLATES_DIR, f"{doc_type.value}_de.md")
        for p in (path, fallback_path):
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    return f.read()
        logger.warning(f"Template nicht gefunden: {filename} — nutze leeres Template")
        return f"Erstelle {doc_type.value} für:\n{{{{company_name}}}}, {{{{address}}}}"

    def _load_laws_context(self, law_names: List[str], language: str) -> str:
        parts = []
        for name in law_names:
            for lang in (language, "de"):
                path = os.path.join(LAWS_DIR, lang, f"{name}.md")
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    parts.append(f"### {name}\n{content[:2000]}")
                    break
                root_path = os.path.join(LAWS_DIR, f"{name}.md")
                if os.path.exists(root_path):
                    with open(root_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    parts.append(f"### {name}\n{content[:2000]}")
                    break
        return "\n\n".join(parts) if parts else "Aktuelle DSGVO- und TMG-Anforderungen beachten."

    async def _save(
        self,
        user_id: int,
        doc_type: DocumentType,
        language: str,
        html_content: str,
        legal_update_id: Optional[str],
        regeneration_trigger: str,
        user_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        meta = {
            "is_active": True,
            "template_version": self.TEMPLATE_VERSION,
            "regeneration_trigger": regeneration_trigger,
            "legal_update_id": legal_update_id,
            "generator": "legal_text_generator",
            # user_data wird gespeichert, damit legal_change_monitor die Dokumente
            # bei Gesetzesänderungen automatisch neu generieren kann (Auto-Update).
            "user_data": user_data or {},
            "language": language,
        }
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE generated_documents
                    SET metadata = jsonb_set(metadata::jsonb, '{is_active}', 'false')
                    WHERE user_id = $1 AND document_type = $2
                      AND (metadata->>'is_active')::boolean IS NOT FALSE
                    """,
                    user_id,
                    doc_type.value,
                )
                doc_id = await conn.fetchval(
                    """
                    INSERT INTO generated_documents
                    (user_id, document_type, language, html_content, content,
                     metadata, status, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, 'active', NOW(), NOW())
                    RETURNING id
                    """,
                    user_id,
                    doc_type.value,
                    language,
                    html_content,
                    self._strip_html(html_content),
                    json.dumps(meta),
                )
                return doc_id
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Dokuments (user={user_id}, type={doc_type}): {e}")
            return None

    @staticmethod
    def _strip_html(html: str) -> str:
        import re
        return re.sub(r"<[^>]+>", " ", html).strip()

    @staticmethod
    def _hash(data: Dict) -> str:
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]

    def _fallback_template(self, prompt: str) -> str:
        return (
            "<h1>Dokument</h1>"
            "<p>KI-Generierung aktuell nicht verfügbar. "
            "Bitte füllen Sie das Dokument manuell aus oder wenden Sie sich an den Support.</p>"
        )


legal_text_generator_instance: Optional[LegalTextGenerator] = None


def get_legal_text_generator(db_pool: asyncpg.Pool) -> LegalTextGenerator:
    global legal_text_generator_instance
    if legal_text_generator_instance is None:
        legal_text_generator_instance = LegalTextGenerator(db_pool)
    return legal_text_generator_instance
