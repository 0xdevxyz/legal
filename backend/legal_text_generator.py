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
import re
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

# Knowledge-Vault (Templates + Gesetzestexte).
#
# ACHTUNG, hier lag ein stiller Totalausfall: Der frühere Pfad
# `os.path.dirname(__file__)/../knowledge` stimmt nur im Repo-Layout (backend/../knowledge).
# Im Container liegt der Code direkt in `/app`, also löste er zu `/knowledge` auf — das es
# nicht gibt. Der Vault ist per docker-compose read-only nach `/data/knowledge` gemountet
# (`KNOWLEDGE_VAULT_PATH`). Zusätzlich kollidiert der Name mit dem Python-Paket
# `/app/knowledge`. Folge: JEDER Rechtstext wurde ohne Template und ohne Gesetzeskontext
# generiert — ohne dass ein Fehler sichtbar wurde. Dieselbe Env-Variable nutzen bereits
# `backend/knowledge/knowledge_retriever.py` u. a.
KNOWLEDGE_DIR = os.getenv(
    "KNOWLEDGE_VAULT_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge")),
)
TEMPLATES_DIR = os.path.join(KNOWLEDGE_DIR, "templates", "legal")
LAWS_DIR = os.path.join(KNOWLEDGE_DIR, "laws")

if not os.path.isdir(TEMPLATES_DIR):
    # Laut scheitern: ohne Templates/Gesetze sind die erzeugten Rechtstexte wertlos.
    logger.error(
        f"Knowledge-Vault nicht gefunden: {TEMPLATES_DIR} existiert nicht. "
        f"Rechtstexte würden ohne Template und ohne Gesetzeskontext generiert. "
        f"KNOWLEDGE_VAULT_PATH prüfen (aktuell: {KNOWLEDGE_DIR})."
    )


class DocumentType(str, Enum):
    IMPRINT = "imprint"
    PRIVACY = "privacy"
    TOS = "tos"
    COOKIE_POLICY = "cookie-policy"
    WITHDRAWAL = "withdrawal"  # Widerrufsbelehrung inkl. Muster-Widerrufsformular (B2C)


# Pflicht-Marker je Dokumenttyp: (Label, [Substrings], [Regex]). Ein Marker gilt als
# vorhanden, wenn EIN Substring ODER EIN Regex trifft. Heuristisch/nicht-blockierend —
# dient als Qualitaets-Fruehwarnung fuer den KI-Output (frueher gar nicht geprueft).
_MANDATORY_MARKERS = {
    DocumentType.IMPRINT: [
        ("Kontakt (E-Mail/Telefon)", ["telefon", "tel.", "kontakt"], [r"[\w.%+\-]+@[\w.\-]+\.\w{2,}"]),
        ("Anschrift (PLZ + Ort)", [], [r"\b\d{5}\s+[a-zäöü]"]),
        ("Verantwortlicher/Diensteanbieter", ["verantwortlich", "diensteanbieter", "angaben gem", "vertreten durch"], []),
        # Rechtsform-/umsatzabhaengig — als Marker dennoch sinnvoll, weil der
        # Generator die Firmendaten kennt; Fehlen landet nur in metadata
        # (non-blocking) und dient als Review-Signal.
        ("USt-IdNr", ["ust-id", "umsatzsteuer-identifikationsnummer", "ust.-id"], [r"de\s?\d{9}"]),
        ("Registereintrag", ["handelsregister", "registergericht", "amtsgericht"], [r"hr[ab]\s?\d+"]),
    ],
    DocumentType.PRIVACY: [
        ("Verantwortlicher", ["verantwortlich"], []),
        ("Personenbezogene Daten", ["personenbezogene daten"], []),
        ("Rechtsgrundlage", ["rechtsgrundlage", "art. 6"], []),
        ("Betroffenenrechte", ["betroffenenrechte", "auskunftsrecht", "auskunft"], []),
    ],
    DocumentType.TOS: [
        ("Geltungsbereich", ["geltungsbereich", "anwendungsbereich"], []),
        ("Vertrag/Leistung", ["vertrag", "leistung"], []),
        ("Kündigung/Laufzeit", ["kündig", "laufzeit", "beendigung"], []),
        ("Preise/Vergütung", ["preis", "vergütung", "entgelt", "zahlung"], []),
    ],
    DocumentType.COOKIE_POLICY: [
        ("Cookies", ["cookie"], []),
        ("Einwilligung", ["einwilligung", "consent"], []),
    ],
    DocumentType.WITHDRAWAL: [
        ("Widerrufsrecht", ["widerruf"], []),
        ("Widerrufsfrist", ["widerrufsfrist", "14 tage", "vierzehn tagen"], []),
        ("Muster-Widerrufsformular", ["widerrufsformular"], []),
    ],
}


def validate_document_content(doc_type: "DocumentType", html: str) -> List[str]:
    """Prueft, ob die wichtigsten Pflicht-Marker im generierten Dokument vorkommen.
    Rueckgabe: Liste fehlender Marker-Labels (leer = vollstaendig). Heuristisch und
    nicht-blockierend; validiert den KI-Output, der bisher ungeprueft ausgeliefert wurde."""
    text = (html or "").lower()
    missing: List[str] = []
    for label, subs, rxs in _MANDATORY_MARKERS.get(doc_type, []):
        ok = any(sub in text for sub in subs) or any(re.search(rx, text) for rx in rxs)
        if not ok:
            missing.append(label)
    return missing


# =============================================================================
# SSOT: Rechtsbereich → betroffene Dokumenttypen
# =============================================================================
# Die Schlüssel sind exakt die Werte von legal_change_monitor.LegalArea.
# Bewusst hier (und nicht im Monitor) angesiedelt, weil nur dieses Modul
# DocumentType kennt und die Re-Generation ausführt — der Monitor liefert nur
# den Rechtsbereich, die Übersetzung in Dokumenttypen ist Generator-Wissen.
# Wird ein neuer LegalArea-Wert ergänzt, MUSS er hier eingetragen werden
# (Wächter: tests/test_legal_area_mapping.py).
LEGAL_AREA_TO_DOCUMENT_TYPES: Dict[str, List["DocumentType"]] = {
    # DSGVO
    "datenschutz": [DocumentType.PRIVACY, DocumentType.COOKIE_POLICY],
    # TTDSG / ePrivacy
    "cookie_compliance": [DocumentType.PRIVACY, DocumentType.COOKIE_POLICY],
    # Impressumspflicht (DDG/TMG)
    "impressum": [DocumentType.IMPRINT],
    # BFSG — Barrierefreiheitserklärung wird derzeit im Impressum getragen
    "barrierefreiheit": [DocumentType.IMPRINT],
    # UWG
    "wettbewerbsrecht": [DocumentType.TOS],
    # Verbraucherrecht / Widerrufsrecht / AGB-Recht
    "verbraucherschutz": [DocumentType.TOS, DocumentType.WITHDRAWAL],
    # AI Act erzeugt keinen der generierten Rechtstexte (eigener Doc-Generator)
    "ai_act": [],
    # PPWR: Kennzeichnungs-/Informationspflichten am Produkt und im Shop, kein
    # Rechtstext-Dokument. Bewusst leer — verhindert, dass eine PPWR-Meldung
    # eine unnötige AGB-Re-Generierung auslöst (und die "Unbekannter
    # Rechtsbereich"-Warnung in jedem Monitoring-Lauf).
    "verpackung": [],
}

# Aliasse: Gesetzesname → Rechtsbereich. Erlaubt, dass eine Änderung auch dann
# aufgelöst wird, wenn sie über den Gesetzesnamen statt über den LegalArea-Wert
# hereinkommt. Zielt bewusst NUR auf die SSOT oben, dupliziert sie nicht.
LAW_NAME_TO_LEGAL_AREA: Dict[str, str] = {
    "dsgvo": "datenschutz",
    "bdsg": "datenschutz",
    "ttdsg": "cookie_compliance",
    "eprivacy": "cookie_compliance",
    "impressumspflicht": "impressum",
    "ddg": "impressum",
    "tmg": "impressum",
    "bfsg": "barrierefreiheit",
    "uwg": "wettbewerbsrecht",
    "agb-recht": "verbraucherschutz",
    "widerrufsrecht": "verbraucherschutz",
    "verbraucherrecht": "verbraucherschutz",
    "ai act": "ai_act",
    "ki-verordnung": "ai_act",
}


def resolve_document_types(affected_areas: List[str]) -> List["DocumentType"]:
    """
    Löst Rechtsbereiche (LegalArea-Werte) bzw. Gesetzesnamen in Dokumenttypen auf.

    Unbekannte Einträge werden geloggt und ignoriert — sie dürfen die
    Re-Generation der übrigen Bereiche nicht verhindern.
    """
    doc_types: List[DocumentType] = []
    for raw in affected_areas or []:
        key = str(raw).strip().lower()
        types = LEGAL_AREA_TO_DOCUMENT_TYPES.get(key)
        if types is None:
            # Gesetzesname? -> über Alias auf den Rechtsbereich abbilden
            area = LAW_NAME_TO_LEGAL_AREA.get(key)
            if area is None:
                # Teiltreffer, z.B. "DSGVO-Novelle 2026"
                for law_name, mapped_area in LAW_NAME_TO_LEGAL_AREA.items():
                    if law_name in key:
                        area = mapped_area
                        break
            if area is None:
                logger.warning(
                    f"resolve_document_types: Unbekannter Rechtsbereich '{raw}' — "
                    f"kein Mapping in LEGAL_AREA_TO_DOCUMENT_TYPES/LAW_NAME_TO_LEGAL_AREA"
                )
                continue
            types = LEGAL_AREA_TO_DOCUMENT_TYPES.get(area, [])
        for t in types:
            if t not in doc_types:
                doc_types.append(t)
    return doc_types


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
        affected_areas: List[str],
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

        # Auflösung über die SSOT (LEGAL_AREA_TO_DOCUMENT_TYPES)
        affected_doc_types = set(resolve_document_types(affected_areas))

        if not affected_doc_types:
            logger.info(f"Keine betroffenen Dokumenttypen für areas={affected_areas}")
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
            "HTTP-Referer": "https://complyo.de",
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
        # Kein warning, sondern error: ohne Template erzeugt die KI einen frei improvisierten
        # Rechtstext. Das ist kein Randfall, sondern Produktversagen — entsprechend laut.
        logger.error(
            f"Template nicht gefunden: {filename} (gesucht in {TEMPLATES_DIR}) — "
            f"Rechtstext wird OHNE Vorlage generiert."
        )
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
        missing_markers = validate_document_content(doc_type, html_content)
        if missing_markers:
            logger.warning(
                f"Generiertes Dokument unvollstaendig (user={user_id}, "
                f"type={doc_type.value}): fehlende Pflicht-Marker: "
                f"{', '.join(missing_markers)}"
            )
        meta = {
            "is_active": True,
            "content_validation": {"missing_markers": missing_markers},
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
        """Notfall-Rückgabe, wenn die KI-Generierung nicht durchführbar war
        (kein ``OPENROUTER_API_KEY`` gesetzt oder HTTP-Status ≠ 200).

        Bewusst KEIN fertig aussehendes Dokument: Der frühere Stub
        ("KI-Generierung aktuell nicht verfügbar") sah aus wie ein regulärer
        Rechtstext und konnte so unbemerkt an Endnutzer ausgeliefert werden —
        ein leerer Text im Gewand eines fertigen Dokuments. Stattdessen wird der
        Zustand laut geloggt und ein unmissverständlich als UNFERTIG markierter
        Platzhalter zurückgegeben, der nicht mit einem gültigen Dokument
        verwechselt werden kann.
        """
        logger.error(
            "KI-Generierung fehlgeschlagen — Fallback-Platzhalter wird zurückgegeben. "
            "Kein gültiger Rechtstext erzeugt (OPENROUTER_API_KEY fehlt oder OpenRouter "
            "lieferte keinen Status 200). Ursache prüfen; das Dokument ist NICHT fertig."
        )
        generated_at = datetime.now().strftime("%d.%m.%Y %H:%M")
        return (
            '<div data-document-status="incomplete" role="alert">'
            "<h1>⚠ Rechtstext konnte nicht erzeugt werden</h1>"
            "<p><strong>Status: UNFERTIG — dies ist kein gültiges Rechtsdokument.</strong></p>"
            "<p>Die automatische Generierung war zum Zeitpunkt der Anforderung "
            f"({generated_at}) nicht verfügbar. Es wurde bewusst kein Ersatztext "
            "erstellt, um den falschen Eindruck eines fertigen Dokuments zu vermeiden.</p>"
            "<p>Bitte die Generierung erneut auslösen. Bleibt der Fehler bestehen, "
            "wenden Sie sich an den Support — bis dahin darf dieser Platzhalter nicht "
            "als Rechtstext verwendet oder veröffentlicht werden.</p>"
            "</div>"
        )


legal_text_generator_instance: Optional[LegalTextGenerator] = None


def get_legal_text_generator(db_pool: asyncpg.Pool) -> LegalTextGenerator:
    global legal_text_generator_instance
    if legal_text_generator_instance is None:
        legal_text_generator_instance = LegalTextGenerator(db_pool)
    return legal_text_generator_instance
